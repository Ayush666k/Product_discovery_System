from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_products, name='search_products'),
    path('detail/<str:product_id>/', views.product_detail, name='product_detail'),
    path("product/<str:product_id>/review/", views.submit_review, name="submit_reviews"),

]
