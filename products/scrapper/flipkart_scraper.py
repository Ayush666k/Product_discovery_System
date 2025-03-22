import requests
from bs4 import BeautifulSoup


def scrape_flipkart(product_title):
    # Construct the search URL
    search_query = product_title.replace(" ", "+")
    url = f"https://www.flipkart.com/search?q={search_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        products = soup.find_all("div", class_="_75nlfW")  # Product containera-offscreen

        for product in products:
            # Extract price
            price = product.find("div", class_="Nx9bqj _4b5DiR").text.strip() if product.find(
                "div", class_="Nx9bqj _4b5DiR") else None


            # Extract rating
            rating = product.find("div", class_="XQDdHH").text.strip() if product.find("div", class_="XQDdHH") else "No Rating"

            # Extract brand (usually the first word in the title)
            brand = product_title.split()[0]  # Example: "Apple iPhone 14" -> "Apple"

            # Extract category (you can scrape this or infer it)
            category = "Uncategorized"  # You can scrape this from the product page or infer it

            return {
                "price": price,
                "rating": rating,
                "brand": brand,
                "category": category
            }
    return None

