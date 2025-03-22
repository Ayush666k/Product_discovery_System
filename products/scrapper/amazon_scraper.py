from itertools import product

import requests
from bs4 import BeautifulSoup




def scrape_amazon(product_title):
    search_query = product_title.replace(" ", "+")

    url = f"https://www.amazon.in/s?k={search_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        products = soup.find_all("div", attrs={"class": "sg-col-inner"})  # Find all product containers

        for product in products:  # Iterate over each product
                # Find the price element
            price_element = product.find("span", attrs={"class": "a-price"})
            if price_element:  # Check if the price element exists
                newest = price_element.find("span", attrs={"class": "a-offscreen"})
                if newest:  # Check if the price text exists
                    price = newest.text.strip()  # Print the price text
                else:
                    price = None
            else:
                    # Skip products without a price element
                continue

            rating = product.find("span", attrs={"class": "a-icon-alt"})

            rating = rating.text.strip() if rating else "No Rating"

            brand = product_title.split()[0]
            category = "SmartPhones"

            return {
                "price":price,
                "rating": rating,
                "brand": brand,
                "category":category

            }
    return None
