from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from auth_app.models import User, users_collection

from mongosh import contacts_collection

def user_register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email').lower()  # Convert to lowercase for consistency
        password = request.POST.get('password')

        if users_collection.find_one({"email": email}):
            messages.error(request, "Email is already taken!")
            return redirect('register')

        new_user = {
            "username": username,
            "email": email,
            "password": make_password(password),  # Store hashed password
        }
        users_collection.insert_one(new_user)

        messages.success(request, "Account created! You can login.")
        return redirect('login')

    return render(request, 'auth_app/register.html')

def user_login(request):
    if "user_id" in request.session:
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        email = email.lower()
        user = User.find_by_email(email)

        if user is None:
            messages.error(request, "User not found!")
            return redirect('login')

        if check_password(password, user['password']):
            request.session["user_id"] = str(user["_id"])
            request.session["username"] = user["username"]
            messages.success(request, "Login successful!")

            # Get the 'next' parameter from the request
            next_url = request.GET.get("next") or request.POST.get("next")

            return redirect(next_url) if next_url else redirect("home")
        else:
            messages.error(request, "Invalid email or password!")
            return redirect('login')

    return render(request, 'auth_app/login.html')

def user_logout(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('login')


def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        contacts_collection.insert_one({
            "name": name,
            "email": email,
            "subject": subject,
            "message": message

        })
        return JsonResponse({"success": True, "message": "Message sent sucessfully!"})

    return render(request, "auth_app/contacts.html")