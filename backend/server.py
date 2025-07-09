from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import pymongo
import os
from bson import ObjectId
import uuid
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import stripe
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image
import aiofiles
import json

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="TrendNest E-Commerce API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/trendnest")
client = AsyncIOMotorClient(MONGO_URL)
db = client.trendnest

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Collections
users_collection = db.users
products_collection = db.products
carts_collection = db.carts
orders_collection = db.orders
reviews_collection = db.reviews
wishlists_collection = db.wishlists
analytics_collection = db.analytics

# Pydantic models
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    stock: int
    image_base64: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    stock: Optional[int] = None
    image_base64: Optional[str] = None

class CartItem(BaseModel):
    product_id: str
    quantity: int

class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    comment: str
    image_base64: Optional[str] = None

class OrderCreate(BaseModel):
    shipping_address: str
    payment_method: str

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await users_collection.find_one({"email": email})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def object_id_str(obj_id):
    return str(obj_id) if obj_id else None

# Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

@app.post("/api/auth/register")
async def register(user: UserRegister):
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "_id": str(uuid.uuid4()),
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_admin": False,
        "is_verified": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await users_collection.insert_one(user_data)
    return {"message": "User registered successfully"}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Find user
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user["email"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["_id"],
            "username": db_user["username"],
            "email": db_user["email"],
            "is_admin": db_user["is_admin"]
        }
    }

@app.get("/api/user/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "phone": current_user.get("phone"),
        "is_admin": current_user["is_admin"]
    }

@app.get("/api/products")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = Query("created_at", regex="^(name|price|created_at|rating)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    # Build query
    query = {}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if min_price is not None or max_price is not None:
        price_query = {}
        if min_price is not None:
            price_query["$gte"] = min_price
        if max_price is not None:
            price_query["$lte"] = max_price
        query["price"] = price_query
    
    # Build sort
    sort_order = 1 if order == "asc" else -1
    sort_field = sort_by if sort_by != "rating" else "average_rating"
    
    # Get products
    skip = (page - 1) * limit
    products_cursor = products_collection.find(query).sort(sort_field, sort_order).skip(skip).limit(limit)
    products = []
    
    async for product in products_cursor:
        product["_id"] = str(product["_id"])
        products.append(product)
    
    # Get total count
    total_count = await products_collection.count_documents(query)
    
    return {
        "products": products,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    product = await products_collection.find_one({"_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product["_id"] = str(product["_id"])
    return product

@app.post("/api/products")
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    product_data = {
        "_id": str(uuid.uuid4()),
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "stock": product.stock,
        "image_base64": product.image_base64,
        "average_rating": 0.0,
        "review_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await products_collection.insert_one(product_data)
    product_data["_id"] = str(product_data["_id"])
    return product_data

@app.get("/api/categories")
async def get_categories():
    categories = await products_collection.distinct("category")
    return {"categories": categories}

@app.get("/api/cart")
async def get_cart(current_user: dict = Depends(get_current_user)):
    cart = await carts_collection.find_one({"user_id": current_user["_id"]})
    if not cart:
        return {"items": [], "total_amount": 0}
    
    # Get product details for cart items
    cart_items = []
    total_amount = 0
    
    for item in cart.get("items", []):
        product = await products_collection.find_one({"_id": item["product_id"]})
        if product:
            item_total = product["price"] * item["quantity"]
            cart_items.append({
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "product": {
                    "id": product["_id"],
                    "name": product["name"],
                    "price": product["price"],
                    "image_base64": product.get("image_base64")
                },
                "total": item_total
            })
            total_amount += item_total
    
    return {"items": cart_items, "total_amount": total_amount}

@app.post("/api/cart/add")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    # Check if product exists
    product = await products_collection.find_one({"_id": item.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product["stock"] < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Get or create cart
    cart = await carts_collection.find_one({"user_id": current_user["_id"]})
    if not cart:
        cart = {
            "user_id": current_user["_id"],
            "items": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    # Check if item already exists in cart
    existing_item = None
    for cart_item in cart["items"]:
        if cart_item["product_id"] == item.product_id:
            existing_item = cart_item
            break
    
    if existing_item:
        existing_item["quantity"] += item.quantity
    else:
        cart["items"].append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "added_at": datetime.utcnow()
        })
    
    cart["updated_at"] = datetime.utcnow()
    
    # Update cart
    await carts_collection.replace_one(
        {"user_id": current_user["_id"]},
        cart,
        upsert=True
    )
    
    return {"message": "Item added to cart"}

@app.put("/api/cart/update")
async def update_cart_item(item: CartItem, current_user: dict = Depends(get_current_user)):
    cart = await carts_collection.find_one({"user_id": current_user["_id"]})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Find and update item
    item_found = False
    for cart_item in cart["items"]:
        if cart_item["product_id"] == item.product_id:
            cart_item["quantity"] = item.quantity
            item_found = True
            break
    
    if not item_found:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    cart["updated_at"] = datetime.utcnow()
    await carts_collection.replace_one({"user_id": current_user["_id"]}, cart)
    
    return {"message": "Cart updated"}

@app.delete("/api/cart/remove/{product_id}")
async def remove_from_cart(product_id: str, current_user: dict = Depends(get_current_user)):
    cart = await carts_collection.find_one({"user_id": current_user["_id"]})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Remove item
    cart["items"] = [item for item in cart["items"] if item["product_id"] != product_id]
    cart["updated_at"] = datetime.utcnow()
    
    await carts_collection.replace_one({"user_id": current_user["_id"]}, cart)
    
    return {"message": "Item removed from cart"}

@app.delete("/api/cart/clear")
async def clear_cart(current_user: dict = Depends(get_current_user)):
    await carts_collection.delete_one({"user_id": current_user["_id"]})
    return {"message": "Cart cleared"}

# Orders endpoints
@app.get("/api/orders")
async def get_orders(current_user: dict = Depends(get_current_user)):
    orders_cursor = orders_collection.find({"user_id": current_user["_id"]}).sort("created_at", -1)
    orders = []
    
    async for order in orders_cursor:
        order["_id"] = str(order["_id"])
        orders.append(order)
    
    return {"orders": orders}

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await orders_collection.find_one({"_id": order_id, "user_id": current_user["_id"]})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order["_id"] = str(order["_id"])
    return order

@app.post("/api/orders")
async def create_order(order_data: OrderCreate, current_user: dict = Depends(get_current_user)):
    # Get cart items
    cart = await carts_collection.find_one({"user_id": current_user["_id"]})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total and get product details
    total_amount = 0
    order_items = []
    
    for item in cart["items"]:
        product = await products_collection.find_one({"_id": item["product_id"]})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
        
        if product["stock"] < item["quantity"]:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['name']}")
        
        item_total = product["price"] * item["quantity"]
        total_amount += item_total
        
        order_items.append({
            "product_id": item["product_id"],
            "product_name": product["name"],
            "quantity": item["quantity"],
            "price": product["price"],
            "total": item_total
        })
    
    # Create order
    order = {
        "_id": str(uuid.uuid4()),
        "user_id": current_user["_id"],
        "items": order_items,
        "total_amount": total_amount,
        "shipping_address": order_data.shipping_address,
        "payment_method": order_data.payment_method,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await orders_collection.insert_one(order)
    
    # Update product stock
    for item in order_items:
        await products_collection.update_one(
            {"_id": item["product_id"]},
            {"$inc": {"stock": -item["quantity"]}}
        )
    
    # Clear cart
    await carts_collection.delete_one({"user_id": current_user["_id"]})
    
    order["_id"] = str(order["_id"])
    return order

# Reviews endpoints
@app.get("/api/products/{product_id}/reviews")
async def get_product_reviews(product_id: str):
    reviews_cursor = reviews_collection.find({"product_id": product_id}).sort("created_at", -1)
    reviews = []
    
    async for review in reviews_cursor:
        review["_id"] = str(review["_id"])
        reviews.append(review)
    
    return {"reviews": reviews}

@app.post("/api/reviews")
async def create_review(review_data: ReviewCreate, current_user: dict = Depends(get_current_user)):
    # Check if product exists
    product = await products_collection.find_one({"_id": review_data.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user already reviewed this product
    existing_review = await reviews_collection.find_one({
        "product_id": review_data.product_id,
        "user_id": current_user["_id"]
    })
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")
    
    # Create review
    review = {
        "_id": str(uuid.uuid4()),
        "product_id": review_data.product_id,
        "user_id": current_user["_id"],
        "username": current_user["username"],
        "rating": review_data.rating,
        "comment": review_data.comment,
        "image_base64": review_data.image_base64,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await reviews_collection.insert_one(review)
    
    # Update product rating
    await update_product_rating(review_data.product_id)
    
    review["_id"] = str(review["_id"])
    return review

async def update_product_rating(product_id: str):
    # Calculate average rating
    pipeline = [
        {"$match": {"product_id": product_id}},
        {"$group": {
            "_id": "$product_id",
            "average_rating": {"$avg": "$rating"},
            "review_count": {"$sum": 1}
        }}
    ]
    
    result = await reviews_collection.aggregate(pipeline).to_list(1)
    if result:
        await products_collection.update_one(
            {"_id": product_id},
            {
                "$set": {
                    "average_rating": round(result[0]["average_rating"], 1),
                    "review_count": result[0]["review_count"]
                }
            }
        )

# Wishlist endpoints
@app.get("/api/wishlist")
async def get_wishlist(current_user: dict = Depends(get_current_user)):
    wishlist = await wishlists_collection.find_one({"user_id": current_user["_id"]})
    if not wishlist:
        return {"items": []}
    
    # Get product details
    wishlist_items = []
    for item in wishlist.get("items", []):
        product = await products_collection.find_one({"_id": item["product_id"]})
        if product:
            product["_id"] = str(product["_id"])
            wishlist_items.append({
                "product": product,
                "added_at": item["added_at"]
            })
    
    return {"items": wishlist_items}

@app.post("/api/wishlist/add")
async def add_to_wishlist(item: dict, current_user: dict = Depends(get_current_user)):
    product_id = item.get("product_id")
    
    # Check if product exists
    product = await products_collection.find_one({"_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get or create wishlist
    wishlist = await wishlists_collection.find_one({"user_id": current_user["_id"]})
    if not wishlist:
        wishlist = {
            "user_id": current_user["_id"],
            "items": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    # Check if item already exists
    for wishlist_item in wishlist["items"]:
        if wishlist_item["product_id"] == product_id:
            raise HTTPException(status_code=400, detail="Item already in wishlist")
    
    # Add item
    wishlist["items"].append({
        "product_id": product_id,
        "added_at": datetime.utcnow()
    })
    
    wishlist["updated_at"] = datetime.utcnow()
    
    await wishlists_collection.replace_one(
        {"user_id": current_user["_id"]},
        wishlist,
        upsert=True
    )
    
    return {"message": "Item added to wishlist"}

@app.delete("/api/wishlist/remove/{product_id}")
async def remove_from_wishlist(product_id: str, current_user: dict = Depends(get_current_user)):
    wishlist = await wishlists_collection.find_one({"user_id": current_user["_id"]})
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    
    # Remove item
    wishlist["items"] = [item for item in wishlist["items"] if item["product_id"] != product_id]
    wishlist["updated_at"] = datetime.utcnow()
    
    await wishlists_collection.replace_one({"user_id": current_user["_id"]}, wishlist)
    
    return {"message": "Item removed from wishlist"}

@app.get("/api/wishlist/check/{product_id}")
async def check_wishlist(product_id: str, current_user: dict = Depends(get_current_user)):
    wishlist = await wishlists_collection.find_one({"user_id": current_user["_id"]})
    if not wishlist:
        return {"in_wishlist": False}
    
    in_wishlist = any(item["product_id"] == product_id for item in wishlist.get("items", []))
    return {"in_wishlist": in_wishlist}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)