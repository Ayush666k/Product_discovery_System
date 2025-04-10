
# Product Discovery System

A Django-based web application for searching and comparing products from various e-commerce platforms like Flipkart and Amazon.

## Features

- **Product Search**: Search across multiple e-commerce platforms
- **Price Comparison**: Compare prices for the same product
- **User Authentication**: Register, login, and logout functionality
- **Product Tracking**: View recently visited products
- **Review System**: Users can submit product reviews
- **Contact Form**: For user inquiries and feedback

## Technologies Used

- **Backend**: Django (Python)
- **Database**: MongoDB
- **Web Scraping**: BeautifulSoup (Flipkart/Amazon)
- **Search API**: Google Custom Search API
- **Frontend**: HTML, CSS, JavaScript (Bootstrap recommended)
- **Caching**: Django's cache framework

## Installation

### Prerequisites
- Python 3.8+
- MongoDB
- Google API key (for Custom Search API)

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/product-search-app.git
   cd product-search-app

### 1️⃣ Clone the Repository
```sh
$ git clone https://github.com/yourusername/product_discovery.git
$ cd product_discovery
```

### 2️⃣ Set Up Virtual Environment
```sh
$ python -m venv venv
$ source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3️⃣ Install Dependencies
```sh
$ pip install -r requirements.txt
```

### 4️⃣ Set Up MongoDB
- Install MongoDB and start the service.
- Update MongoDB connection settings in `settings.py`.

### 5️⃣ Run the Project
```sh
$ python manage.py runserver
```
Access the app at: `http://127.0.0.1:8000/`


## 📝 API Endpoints
| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/auth/register/` | Register a new user |
| `POST` | `/auth/login/` | Login user |
| `GET` | `/api/search/?q=iphone` | Search for products using the custom API |
| `GET` | `/products/latest/` | Get latest viewed products |

## 🤝 Contribution Guidelines
1. Fork the repo & create a new branch.
2. Commit changes with a meaningful message.
3. Open a pull request for review.

## 📜 License
This project is licensed under the MIT License.

---
🚀 **Happy Coding!** Contributions & feedback are welcome! 😊

