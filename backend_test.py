import requests
import json
import time
import random
import string
from pprint import pprint

# Base URL from frontend .env
BASE_URL = "http://localhost:8001/api"

# Test data
test_user = {
    "username": f"testuser_{int(time.time())}",
    "email": f"testuser_{int(time.time())}@example.com",
    "password": "Password123!",
    "full_name": "Test User",
    "phone": "1234567890"
}

test_admin = {
    "username": f"admin_{int(time.time())}",
    "email": f"admin_{int(time.time())}@example.com",
    "password": "AdminPass123!",
    "full_name": "Admin User",
    "phone": "9876543210"
}

test_product = {
    "name": f"Test Product {int(time.time())}",
    "description": "This is a test product description with details about features and specifications.",
    "price": 99.99,
    "category": "Electronics",
    "stock": 50,
    "image_base64": None
}

test_review = {
    "rating": 4,
    "comment": "Great product, works as expected!"
}

test_order = {
    "shipping_address": "123 Test Street, Test City, Test Country, 12345",
    "payment_method": "credit_card"
}

# Helper functions
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def print_test_result(test_name, response, expected_status=200):
    status = response.status_code
    print(f"\n=== {test_name} ===")
    print(f"Status: {status} {'✅' if status == expected_status else '❌'}")
    if status != expected_status:
        print(f"Expected: {expected_status}")
        print(f"Response: {response.text}")
    else:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
    return status == expected_status

# Main test function
def run_tests():
    print("Starting TrendNest Backend API Tests")
    print("====================================")
    
    # Track test results
    tests_passed = 0
    tests_failed = 0
    
    # Test variables
    access_token = None
    admin_token = None
    product_id = None
    
    # 1. Health Check
    response = requests.get(f"{BASE_URL}/health")
    if print_test_result("Health Check", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 2. Authentication Tests
    
    # 2.1 Register User
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    if print_test_result("User Registration", response, 200):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 2.2 Register Admin (for testing admin-only endpoints)
    admin_data = test_admin.copy()
    response = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
    if print_test_result("Admin Registration", response, 200):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 2.3 Login User
    login_data = {"email": test_user["email"], "password": test_user["password"]}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if print_test_result("User Login", response):
        tests_passed += 1
        # Save token for future requests
        access_token = response.json().get("access_token")
    else:
        tests_failed += 1
    
    # 2.4 Login Admin
    admin_login_data = {"email": admin_data["email"], "password": admin_data["password"]}
    response = requests.post(f"{BASE_URL}/auth/login", json=admin_login_data)
    if print_test_result("Admin Login", response):
        tests_passed += 1
        # Save admin token
        admin_token = response.json().get("access_token")
        
        # Make admin user an admin (this would normally be done in the database)
        # For testing purposes, we'll assume the first registered user is an admin
        print("Note: In a real application, you would need to set is_admin=True in the database")
    else:
        tests_failed += 1
    
    # 2.5 Get User Profile
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/user/profile", headers=headers)
    if print_test_result("Get User Profile", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 2.6 Test Invalid Token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/user/profile", headers=headers)
    if print_test_result("Invalid Token Test", response, 401):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 3. Product Tests
    
    # 3.1 Create Product (Admin only)
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.post(f"{BASE_URL}/products", json=test_product, headers=headers)
    if print_test_result("Create Product (Admin)", response):
        tests_passed += 1
        product_id = response.json().get("_id")
    else:
        tests_failed += 1
        # Try to get a product for further testing
        response = requests.get(f"{BASE_URL}/products")
        if response.status_code == 200 and response.json().get("products"):
            product_id = response.json().get("products")[0].get("_id")
    
    # 3.2 Get Products List
    response = requests.get(f"{BASE_URL}/products")
    if print_test_result("Get Products List", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 3.3 Get Products with Pagination and Filters
    response = requests.get(f"{BASE_URL}/products?page=1&limit=5&category=Electronics&sort_by=price&order=desc")
    if print_test_result("Get Products with Filters", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 3.4 Get Product Details
    if product_id:
        response = requests.get(f"{BASE_URL}/products/{product_id}")
        if print_test_result("Get Product Details", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Get Product Details test - no product ID available")
    
    # 3.5 Get Categories
    response = requests.get(f"{BASE_URL}/categories")
    if print_test_result("Get Categories", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 4. Cart Tests
    
    # 4.1 Get Empty Cart
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/cart", headers=headers)
    if print_test_result("Get Empty Cart", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 4.2 Add Item to Cart
    if product_id:
        cart_item = {"product_id": product_id, "quantity": 2}
        response = requests.post(f"{BASE_URL}/cart/add", json=cart_item, headers=headers)
        if print_test_result("Add Item to Cart", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Add Item to Cart test - no product ID available")
    
    # 4.3 Get Cart with Items
    response = requests.get(f"{BASE_URL}/cart", headers=headers)
    if print_test_result("Get Cart with Items", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 4.4 Update Cart Item
    if product_id:
        cart_item = {"product_id": product_id, "quantity": 3}
        response = requests.put(f"{BASE_URL}/cart/update", json=cart_item, headers=headers)
        if print_test_result("Update Cart Item", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Update Cart Item test - no product ID available")
    
    # 4.5 Remove Item from Cart
    if product_id:
        response = requests.delete(f"{BASE_URL}/cart/remove/{product_id}", headers=headers)
        if print_test_result("Remove Item from Cart", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Remove Item from Cart test - no product ID available")
    
    # 4.6 Add Item Back to Cart for Order Test
    if product_id:
        cart_item = {"product_id": product_id, "quantity": 1}
        response = requests.post(f"{BASE_URL}/cart/add", json=cart_item, headers=headers)
        if print_test_result("Add Item Back to Cart", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Add Item Back to Cart test - no product ID available")
    
    # 5. Order Tests
    
    # 5.1 Create Order
    response = requests.post(f"{BASE_URL}/orders", json=test_order, headers=headers)
    if print_test_result("Create Order", response):
        tests_passed += 1
        order_id = response.json().get("_id")
    else:
        tests_failed += 1
        order_id = None
    
    # 5.2 Get Orders
    response = requests.get(f"{BASE_URL}/orders", headers=headers)
    if print_test_result("Get Orders", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 5.3 Get Order Details
    if order_id:
        response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=headers)
        if print_test_result("Get Order Details", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Get Order Details test - no order ID available")
    
    # 6. Review Tests
    
    # 6.1 Create Review
    if product_id:
        review_data = test_review.copy()
        review_data["product_id"] = product_id
        response = requests.post(f"{BASE_URL}/reviews", json=review_data, headers=headers)
        if print_test_result("Create Review", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Create Review test - no product ID available")
    
    # 6.2 Get Product Reviews
    if product_id:
        response = requests.get(f"{BASE_URL}/products/{product_id}/reviews")
        if print_test_result("Get Product Reviews", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Get Product Reviews test - no product ID available")
    
    # 7. Wishlist Tests
    
    # 7.1 Add to Wishlist
    if product_id:
        wishlist_item = {"product_id": product_id}
        response = requests.post(f"{BASE_URL}/wishlist/add", json=wishlist_item, headers=headers)
        if print_test_result("Add to Wishlist", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Add to Wishlist test - no product ID available")
    
    # 7.2 Get Wishlist
    response = requests.get(f"{BASE_URL}/wishlist", headers=headers)
    if print_test_result("Get Wishlist", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 7.3 Check if Product in Wishlist
    if product_id:
        response = requests.get(f"{BASE_URL}/wishlist/check/{product_id}", headers=headers)
        if print_test_result("Check if Product in Wishlist", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Check if Product in Wishlist test - no product ID available")
    
    # 7.4 Remove from Wishlist
    if product_id:
        response = requests.delete(f"{BASE_URL}/wishlist/remove/{product_id}", headers=headers)
        if print_test_result("Remove from Wishlist", response):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("Skipping Remove from Wishlist test - no product ID available")
    
    # 7.5 Clear Cart
    response = requests.delete(f"{BASE_URL}/cart/clear", headers=headers)
    if print_test_result("Clear Cart", response):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print("\n====================================")
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    print("====================================")
    
    return tests_passed, tests_failed

if __name__ == "__main__":
    run_tests()