from django.core.cache import cache
import hashlib
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import requests
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from requests.exceptions import RequestException, Timeout
from django.conf import settings
from django.shortcuts import render, redirect
from datetime import datetime
from mongosh import db, search_logs, search_frequency, products_collection, reviews_collection, user_visited
import re
from django.http import JsonResponse, Http404
from products.scrapper.flipkart_scraper import scrape_flipkart
from products.scrapper.amazon_scraper import  scrape_amazon



# Home view
def home(request):
    top_searches = get_top_searches()
    latest_products = get_latest_products()
    return render(request, 'products/home.html', {'top_searches': top_searches, 'latest_products': latest_products})


def log_visited_product(product_id):
    product = db.products.find_one({"id": str(product_id)})

    if not product:
        return
    product["visited_products"] = datetime.now()
    if product:
        # Add visited time
        product["visited_products"] = datetime.now()

        # Insert or update in 'visited_products' collection
        db.visited_products.update_one(
            {"product_id": product_id},
            {"$set": product},
            upsert=True
        )

        print("Product Logged Successfully ✅")

def get_latest_products():
    return list(db.visited_products.find().sort("visited_products", -1).limit(5))
# Search products view
def search_products(request):
    # Get query parameters
    query = request.GET.get('q', '').strip() # FOR ENSURE IS  NOT NONE
    category = request.GET.get('category', '').strip()
    brand = request.GET.get('brand', '').strip()
    price = request.GET.get('price', '').strip()
    rating = request.GET.get('rating', '')
    page_number = request.GET.get('page', 1)
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    sort = request.GET.get('sort', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # PREVENT EMPTY QUERY
    if not query:
        return render(request, 'products/search.html', {'error_message': "Please enter Search term!"})


    #SAVE SEARCH LOGS IN MONGODB
    search_data = {
        "query": query,
        # "category": category,
        # "brand": brand,
        # "rating": rating,
        # "sort": sort,
        # "min_price": min_price,
        # "max_price": max_price,
        "timestamp": datetime.now()
    }
    search_logs.insert_one(search_data)

    search_results = []
    error_message = None

    # Generate cache key
    raw_key = f"{query}"
    cache_key = hashlib.md5(raw_key.encode()).hexdigest()

    # Check cached results
    cached_results = cache.get(cache_key)
    if cached_results:
        search_results = cached_results
    else:
        # Build filter query for Google Custom Search API
        filter_query = query.strip()
        if category:
            filter_query += f" {category}"
        if brand:
            filter_query += f" {brand}"
        if min_price:
            filter_query += f" above {min_price} rs"
        if max_price:
            filter_query += f" below {max_price} rs"
        if price:
            filter_query += f" under rs{price}"
        if rating:
            filter_query += f" {rating} stars"
        # Fetch results from Google Custom Search API
        flipkart_api_url = (
            f"https://www.googleapis.com/customsearch/v1"
            f"?q=site:flipkart.com {filter_query}"
            f"&cx={settings.GOOGLE_CX_KEY}"
            f"&key={settings.GOOGLE_API_KEY}"
        )
        general_api_url = (
            f"https://www.googleapis.com/customsearch/v1"
            f"?q={filter_query}"
            f"&cx={settings.GOOGLE_CX_KEY}"
            f"&key={settings.GOOGLE_API_KEY}"
        )



        try:
            flipkart_response = requests.get(flipkart_api_url, timeout=10)
            flipkart_response.raise_for_status()  # Raises HTTPError for 4xx/5xx status codes
            flipkart_results = flipkart_response.json().get('items', [])

            general_response = requests.get(general_api_url, timeout=10)
            general_response.raise_for_status()
            general_results  = general_response.json().get('items', [])

            google_results = flipkart_results + general_results


            for idx, result in enumerate(google_results):
                result['id'] = f"google_{idx}"  # Add a unique ID for Google results
                # result['price'] = extract_price(result.get('snippet', ''))
                if 'pagemap' in result and 'cse_image' in result['pagemap']:
                    result['image'] = result['pagemap']['cse_image'][0].get('src', '')
                elif 'image' in result:
                    result['image'] = result['image']['thumbnailLink', ''][0].get('src', '')

                # Save the product in MongoDB
                db.products.update_one(
                    {"id": result['id']},  # Use the unique ID as the key
                    {"$set": result},
                    upsert=True  # Insert if not found, update if found
                )

                if not result.get("price") or not result.get("rating") or not result.get("brand") or not result.get(
                    "brand") or not result.get("category"):
                    if "flipkart.com" in result.get("link", ""):
                        scraped_data = scrape_flipkart(result.get("title", ""))
                    elif "amazon.in" in result.get("link", ""):
                        scraped_data = scrape_amazon(result.get("title", ""))
                    else:
                        scraped_data = None

                    if scraped_data:
                        db.products.update_one(
                            {"id": result['id']},
                            {"$set": scraped_data},
                            upsert=True
                        )
                        print(f"Updated {result['title']} with {scraped_data}")
                search_results.append(result)
            search_results.extend(google_results)
        except Timeout:
            error_message = 'The request timed out. Please try again.'
        except RequestException as e:
            error_message = f'An error occurred: {e}'
        except ValueError:
            error_message = 'Invalid response from the server.'

        # Fetch results from MongoDB
        mongo_query = {}
        if query:
            mongo_query["query"] = {"$regex": query, "$options": "i"}
        if category:
            mongo_query["category"] = category.lower()
        if brand:
            mongo_query["brand"] = brand.lower()
        if min_price or max_price:
            price_query = {}
            if min_price:
                price_query["$gte"] = float(min_price)
            if max_price:
                price_query["$lte"] = float(max_price)
            mongo_query["results.price"] = price_query
        if rating:
            mongo_query["results.rating"] = {"$gte": float(rating)}

        try:
            mongo_results = list(db.products.find(mongo_query, {"_id": 1, "title": 1, "price": 1,  "image": 1}))
            for result in mongo_results:
                result['id'] = str(result['_id'])  # Convert ObjectId to string and add as 'id'
                if 'image' not in result or not result['image']:
                    result['image'] = ''
            search_results.extend(mongo_results)
        except Exception as e:
            error_message = f"An error occurred while fetching data from MongoDB: {str(e)}"

        # Cache the results
        cache.set(cache_key, search_results, timeout=300)

    # Filter results by price range (if applicable)

    for item in search_results:
        snippet = item.get('snippet', '')
        title = item.get('title', '').lower()
        item['price'] = extract_price(snippet)

        # Avoid irrelevant items like covers, cases, warranties
        if any(exclude in title for exclude in ["cover", "case", "warranty", "insurance"]):
                continue

        # Ensure the product name is in the title
        search_terms = query.lower().split()  # Split query into words
        if not all(term in title for term in search_terms):
            continue  # Skip if title doesn't match search terms
        if min_price or max_price:
            filtered_results = [
                item for item in search_results
                if 'price' in item and item['price'] is not None and
                   (not min_price or item['price'] >= float(min_price)) and
                   (not max_price or item['price'] <= float(max_price))

            ]
            search_results = filtered_results

    # Sort results
    if sort == 'title_asc':
        search_results.sort(key=lambda x: x.get('title', '').lower())
    elif sort == 'title_desc':
        search_results.sort(key=lambda x: x.get('title', '').lower(), reverse=True)
    if sort == 'price_asc':
        search_results.sort(key=lambda x: x.get('price', float('inf')))
    elif sort == 'price_desc':
        search_results.sort(key=lambda x: x.get('price', 0), reverse=True)
    if sort == 'rating':
        search_results.sort(key=lambda x: x.get('rating', 0), reverse=True)

    # Filter results by date range (if applicable)
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            search_results = [
                item for item in search_results
                if start_dt <= datetime.strptime(item.get('date', '2000-01-01'), '%Y-%m-%d') <= end_dt
            ]
        except ValueError:
            error_message = "Invalid date format."
    #CALLING A FUNCTON SEARCH QUERIES AND STORED RESULTS
    if query:
        log_search(query, search_results)
        update_search_count(query)

    # Paginate results
    paginator = Paginator(search_results, 5)
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Render the template
    return render(request, 'products/search.html', {
        'sort': sort,
        'page_obj': page_obj,
        'total_results': len(search_results),
        'search_results': search_results,
        'query': query,
        'category': category,
        'brand': brand,
        'price': price,
        'rating': rating,
        'error_message': error_message,
        'min_price': min_price,
        'max_price': max_price,
        'start_date': start_date,
        'end_date': end_date,
    })

def extract_price(snippet):

    price_match = re.search(r'[\$\₹\€\£]\s?(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', snippet)
    if price_match:
        price_str = price_match.group(1).replace(',', '').replace('','')
        return float(price_str) if '.' in price_str else int(price_str)
    return None

def log_search(query, search_results):
    """ LOGS SEARCH QUERIES AND STORE RESULTS """
    if not query:
        return

    log_entry = {
        "query": query,
        "timestamp": datetime.now(),
        "results": []

    }

    for item in search_results:
        image_url = item.get("image")
        if not image_url and "pagemap" in item:
            if "cse_image" in item["pagemap"]:
                image_url = item["pagemap"]["cse_image"][0].get("src", "")
            elif "cse_thumbnail" in item["pagemap"]:
                image_url = item["pagemap"]["cse_thumbnail"][0].get("src", "")

        product_id = item.get("product_id", f"google_{item.get('link', '')[-8:]}")

        log_entry["results"].append({
            "product_id": product_id,
            "title": item.get("title"),
            "link": item.get("link"),
            "image": image_url,
            "price": extract_price(item.get("snippet", "")),
        })
    search_logs.insert_one(log_entry)

def update_search_count(query):
    if not query:
        return

    search_frequency.update_one(
        {"query":query},
        {"$inc":{"count":1}},
        upsert=True
    )

def get_top_searches():
    top_searches = list(search_frequency.find().sort("count", -1).limit(5))

    if not top_searches:
        return []
    for search in top_searches:
        recent_result = search_logs.find_one({"query": search["query"]}, sort=[("timestamp", -1)])
        if recent_result and "results" in recent_result and recent_result["results"]:
            product_data = recent_result["results"][0]
            search["image"] = recent_result["results"][0].get("image", "")  # Pick first image
            search["title"] = recent_result["results"][0].get("title", "")
            search["link"] = recent_result["results"][0].get("link", "")

            if "product_id" in product_data and product_data["product_id"]:
                search["product_id"] = product_data["product_id"]
            else:
                continue
    return top_searches


def product_detail(request, product_id):
    print("Product ID:", product_id)
    # ✅ Step 1: Fetch the product by product_id
    product = products_collection.find_one({"id": str(product_id)})

    if not product:
        raise Http404("Product not found.")

    #  Step 2: Log the visited product with correct product_id
    log_visited_product(product_id)

    #  Step 3: Handle user (Authenticated or Guest)
    if request.user.is_authenticated:
        user_identifier = request.user.id  # For logged-in users
    else:
        if not request.session.session_key:
            request.session.create()  # Create a session for guest users
        user_identifier = request.session.session_key  # For guests

    #  Step 4: Store user's latest searches
    db.latest_searches.update_one(
        {"user_id": user_identifier},
        {"$push": {"searches": product}},
        upsert=True
    )

    #  Step 5: Fetch related products (exclude current product)
    related_products = products_collection.find({"id": {"$ne": product_id}}).limit(5)

    #  Step 6: Fetch product reviews
    reviews = get_reviews(product_id)

    #  Step 7: Render product detail page
    return render(request, 'products/detail.html', {
        "product": product,
        "related_products": list(related_products),
        "reviews": reviews,
    })


def submit_review(request, product_id):
    if "user_id" not in request.session:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}") #/login/
    if request.method == "POST":
        review_text = request.POST.get("review")
        if not review_text:
            messages.error(request, "Review cannot be empty!")
            return redirect("product_detail", product_id=product_id)
        try:
            rating = float(request.POST.get("rating"))
        except ValueError:
            rating = 0


        if review_text and 1 <= rating <= 5:
            review = {
                "product_id": product_id,
                "user_name": request.session["user_id"],
                "review_text": review_text,
                "rating": rating,
                "timestamp": datetime.now()
            }
            reviews_collection.insert_one(review)
            messages.success(request, "Review submitted successfully!")

        return redirect("product_detail", product_id=product_id)

def get_reviews(product_id):
    return list(reviews_collection.find({"product_id": product_id}, {"_id": 0}))

#
# def test_mongodb(request):
#     query = request.GET.get('q', 'Default Query')
#     category = request.GET.get('category', 'Default Category')
#     test_data = {
#         "query": query,
#         "category": category,
#         "brand": "Test Brand",
#         "results": [{"title": "Test Product", "price": 100}],
#         "created_at": datetime.now()
#     }
#     db.search_logs.insert_one(test_data)
#     latest_log = db.search_logs.find_one(sort=[("_id", -1)])
#     latest_log = convert_mongo_obj(latest_log)
#
#     return JsonResponse({
#         "message": "MongoDB Test Successful",
#         "last_log": latest_log
#     })


