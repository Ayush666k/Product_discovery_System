from datetime import datetime

from pymongo import MongoClient
from django.conf import settings


client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

users_collection = db['users']
search_logs = db['search_logs']
search_results = db['search_results']
search_frequency = db['search_frequency']
products_collection = db["products"]
reviews_collection = db['reviews']
user_visited = db['visited_products']
contacts_collection = db['contacts']

