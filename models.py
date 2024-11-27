from flask import Flask
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Tuple, List, Dict
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import re
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Database:
    def __init__(self, app: Flask):
        """Initialize the Database with Flask app configuration."""
        self.app = app

    @contextmanager
    def get_connection(self):
        """Create and yield a database connection using mysql-connector-python."""
        conn = mysql.connector.connect(
            host=self.app.config['MYSQL_HOST'],
            user=self.app.config['MYSQL_USER'],
            password=self.app.config['MYSQL_PASSWORD'],
            database=self.app.config['MYSQL_DB']
        )
        try:
            yield conn
        except Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

class User:
    def __init__(self, db: Database):
        self.db = db

    def register(self, username: str, email: str, password: str) -> bool:
        """Register a new user."""
        if not self.validate_email(email):
            logging.error('Invalid email format.')
            return False
        if self.is_email_taken(email):
            logging.error('Email is already in use.')
            return False
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        verification_token = str(uuid.uuid4())  # Unique token for email verification
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO user (username, email, password, verification_token, is_verified) VALUES (%s, %s, %s, %s, %s)',
                    (username, email, password_hash, verification_token, True)
                )
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                logging.error(f'Error registering user: {str(e)}')
                return False
            finally:
                cursor.close()

    def validate_email(self, email: str) -> bool:
        """Validate the email format."""
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(regex, email) is not None

    def is_email_taken(self, email: str) -> bool:
        """Check if the email is already in use."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM user WHERE email = %s', (email,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0

    def login(self, email: str, password: str) -> Optional[Tuple]:
        """Log in a user and return their information if successful."""
        logging.debug(f"Attempting to log in with email: {email}")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
            user = cursor.fetchone()
            cursor.close()
        
        if user:
            logging.debug(f"User record found: {user}")
            if not user[5]:  
                logging.warning("User not verified.")
                return None
            if check_password_hash(user[3], password):  
                self.log_user_activity(user[0], "login") 
                return user  
            else:
                logging.warning("Password does not match.")
        else:
            logging.warning("No user found with that email.")
        return None

    def log_user_activity(self, user_id: int, action: str) -> None:
        """Log user activity."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO user_activity (user_id, action, timestamp) VALUES (%s, %s, NOW())',
                    (user_id, action)
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                logging.error(f'Error logging user activity: {str(e)}')
            finally:
                cursor.close()

    def get_user(self, user_id: int) -> Optional[Tuple]:
        """Retrieve user information by user ID."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return user
        
class Product:
    def __init__(self, db: Database):
        self.db = db

    def add_product(self, name: str, price: float, category: str, stock: int = 0, image_filename: str = None) -> bool:
        """Add a new product to the database."""
        if price <= 0 or stock < 0:
            logging.error("Price must be greater than zero and stock must not be negative.")
            return False

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO product (name, price, category, stock, image_filename) VALUES (%s, %s, %s, %s, %s)',
                    (name, price, category, stock, image_filename)
                )
                conn.commit()
                logging.info(f"Added product: {name} (Price: {price}, Category: {category}, Stock: {stock})")
                return True
            except Exception as e:
                conn.rollback()
                logging.error(f"Error adding product: {e}")
                return False
            finally:
                cursor.close()

    def get_all_categories(self):
        """Retrieve unique categories from the product table."""
        query = "SELECT DISTINCT category FROM product ORDER BY category ASC"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            categories = cursor.fetchall()
            return [{'id': idx + 1, 'name': cat[0]} for idx, cat in enumerate(categories)]

        
    def get_filtered_products(self, page: int = 1, limit: int = 10, sort_by: str = 'name', order: str = 'asc',category: Optional[str] = None, min_price: Optional[float] = None,max_price: Optional[float] = None, search_query: Optional[str] = None) -> Tuple[List[Tuple], int]:
        query = "SELECT * FROM product WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM product WHERE 1=1"
        params = []

        if category:
            query += " AND category ILIKE %s"  
            count_query += " AND category ILIKE %s"
            params.append(category)

        if min_price is not None:
            query += " AND price >= %s"
            count_query += " AND price >= %s"
            params.append(min_price)
        if max_price is not None:
            query += " AND price <= %s"
            count_query += " AND price <= %s"
            params.append(max_price)

        if search_query:
            query += " AND (name ILIKE %s OR description ILIKE %s)"
            count_query += " AND (name ILIKE %s OR description ILIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        allowed_sort_fields = ['name', 'price', 'category']
        if sort_by in allowed_sort_fields:
            order_direction = 'ASC' if order.lower() == 'asc' else 'DESC'
            query += f" ORDER BY {sort_by} {order_direction}"
        else:
            query += " ORDER BY name ASC" 

        offset = (page - 1) * limit
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            print("Executing query:", query)
            print("Params:", params)

            cursor.execute(query, tuple(params))
            products = cursor.fetchall()

            cursor.execute(count_query, tuple(params[:-2]))  # Don't include limit and offset in count query
            total_count = cursor.fetchone()[0]

            cursor.close()

        return products, total_count
 

class Cart:
    def __init__(self, db: Database):
        self.db = db

    def get_cart_items(self, user_id: int) -> List[Tuple]:
        """Retrieve all items in the user's cart."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cart_item.id, cart_item.quantity, product.name, product.price, product.image_filename 
                              FROM cart_item 
                              JOIN product ON cart_item.product_id = product.id 
                              WHERE cart_item.user_id = %s''', (user_id,))
            cart_items = cursor.fetchall()
            cursor.close()
            return cart_items if cart_items else []

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> bool:
        """Add a product to the cart, specifying the quantity."""
        if quantity <= 0:
            logging.error("Quantity must be greater than zero.")
            return False
    
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT stock FROM product WHERE id = %s', (product_id,))
                product_stock = cursor.fetchone()
                if not product_stock or product_stock[0] < quantity:
                    logging.error("Not enough stock available for product ID: %s", product_id)
                    return False
            
                cursor.execute('SELECT * FROM cart_item WHERE user_id = %s AND product_id = %s', (user_id, product_id))
                cart_item = cursor.fetchone()

                if cart_item:
                    new_quantity = cart_item[2] + quantity
                    cursor.execute('UPDATE cart_item SET quantity = %s WHERE id = %s', (new_quantity, cart_item[0]))
                    logging.info("Updated cart item ID: %s to new quantity: %s", cart_item[0], new_quantity)
                else:
                    cursor.execute('INSERT INTO cart_item (user_id, product_id, quantity) VALUES (%s, %s, %s)', (user_id, product_id, quantity))
                    logging.info("Added new item to cart: user ID %s, product ID %s, quantity %s", user_id, product_id, quantity)
                conn.commit()
                return True
            except Exception as e:
                logging.exception("Error adding to cart")
                conn.rollback() 
                return False
            finally:
                cursor.close()  

    def clear_cart(self, user_id: int) -> bool:
        """Clear all items from the user's cart."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM cart_item WHERE user_id = %s', (user_id,))
                conn.commit()
                logging.info("Cleared cart for user ID: %s", user_id)
                return True
            except Exception as e:
                logging.error(f'Error clearing cart for user {user_id}: {str(e)}')
                conn.rollback() 
                return False
            finally:
                cursor.close()

    def update_cart_item_quantity(self, item_id: int, quantity: int) -> bool:
        """Update the quantity of an item in the cart."""
        if quantity < 1:
            logging.error("Quantity must be at least 1.")
            return False
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE cart_item SET quantity = %s WHERE id = %s', (quantity, item_id))
                if cursor.rowcount == 0:
                    logging.warning("Item ID %s not found in cart.", item_id)
                    return False
                conn.commit()
                logging.info("Updated cart item ID: %s to quantity: %s", item_id, quantity)
                return True
            except Exception as e:
                logging.error(f'Error updating cart item ID {item_id}: {str(e)}')
                conn.rollback()  
                return False
            finally:
                cursor.close()

    def calculate_total_price(self, user_id: int) -> Optional[float]:
        """Calculate the total price of items in the user's cart."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT SUM(cart_item.quantity * product.price) 
                              FROM cart_item 
                              JOIN product ON cart_item.product_id = product.id 
                              WHERE cart_item.user_id = %s''', (user_id,))
            total_price = cursor.fetchone()[0]
            cursor.close()
            return total_price if total_price is not None else 0.0


class Order:
    def __init__(self, db: Database):
        self.db = db

    def get_cart_items_order(self, user_id: int) -> List[Dict]:
        """Retrieve all items in the user's cart, including product details, formatted for an order."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cart_item.product_id, cart_item.quantity, product.name, product.price
                          FROM cart_item
                          JOIN product ON cart_item.product_id = product.id
                          WHERE cart_item.user_id = %s''', (user_id,))
            cart_items = cursor.fetchall()
            cursor.close()

            cart_items_dict = []
            for item in cart_items:
                 cart_item_dict = {
                'product_id': item[0],
                'quantity': item[1],
                'name': item[2],
                'price': item[3],
                'total_price': item[1] * item[3]  
            }
            cart_items_dict.append(cart_item_dict)

        return cart_items_dict


    def create_order(self, user_id: int, shipping_address: str, cart_items: List[Dict]) -> Optional[int]:
        """Create a new order and return its ID, along with order items."""
        # Calculate total order amount
        total_amount = sum(item['total_price'] for item in cart_items)

        query = """
            INSERT INTO `order` (user_id, status, order_date, shipping_address, total_amount)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_id, 'Pending', datetime.now(), shipping_address, total_amount)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                order_id = cursor.lastrowid  

                for item in cart_items:
                    cursor.execute(
                    'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)',
                    (order_id, item['product_id'], item['quantity'], item['price'])  # Pass price from cart item
                    )

                conn.commit()
                logging.info(f"Order created successfully with order_id: {order_id}")
                return order_id
            except Exception as e:
                conn.rollback()
                logging.error(f"Error creating order for user_id {user_id}: {str(e)}")
                return None
            finally:
                cursor.close()

    def update_order_status(self, order_id: int, new_status: str) -> bool:
        
        query = "UPDATE `order` SET status = %s WHERE id = %s"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (new_status, order_id))
                conn.commit()

                if cursor.rowcount > 0:
                    logging.info(f"Order {order_id} status updated to {new_status}")
                    return True
                else:
                    logging.warning(f"No order found with ID {order_id}")
                    return False
            except Exception as e:
                conn.rollback()
                logging.error(f"Error updating order {order_id} status: {str(e)}")
                return False
            finally:
                cursor.close()            

    def get_order_details(self, order_id: int) -> Optional[Tuple]:
        """Retrieve details for a specific order."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM `order` WHERE id = %s', (order_id,))
            order = cursor.fetchone()
            cursor.close()
            return order

class PaymentStatus(Enum):
    PENDING = 'Pending'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    REFUNDED = 'Refunded'
    PARTIALLY_REFUNDED = 'Partially Refunded'


class PaymentMethod(Enum):
    CREDIT_CARD = 'credit_card'
    PAYPAL = 'paypal'
    BANK_TRANSFER = 'bank_transfer'


class PaymentError(Exception):
    """Custom exception for payment processing errors."""
    pass


class Payment:
    def __init__(self, db):
        self.db = db

    def create_payment(self, user_id: int, order_id: int, amount: float, method: PaymentMethod) -> Optional[int]:
        if amount <= 0:
            raise PaymentError("Payment amount must be greater than zero.")
        query = """
            INSERT INTO payments (user_id, order_id, amount, method, status, payment_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (user_id, order_id, amount, method.value, PaymentStatus.PENDING.value, datetime.now())

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
            
                cursor.execute("SELECT LAST_INSERT_ID()")
                payment_id = cursor.fetchone()[0]  
                logging.info(f"Payment created successfully: ID {payment_id}, Order ID {order_id}")
                return payment_id
            except Exception as e:
                logging.error(f"Error creating payment for order {order_id}: {str(e)}")
                raise PaymentError(f"Failed to create payment: {e}")
            finally:
                cursor.close()

    def process_payment(self, user_id: int, amount: float, method: PaymentMethod) -> bool:
        """
        Processes the payment and returns True if successful, False otherwise.
        In a real application, this is where you would integrate with a payment gateway (e.g., Stripe, PayPal).
        """
        try:
            logging.info(f"Processing payment for user {user_id}, amount: {amount}, method: {method.value}")

            if amount > 0:
                logging.info(f"Payment processed successfully for user {user_id}. Amount: {amount}.")
                return True
            else:
                logging.error("Payment failed due to invalid amount.")
                return False
        except Exception as e:
            logging.error(f"Error processing payment for user {user_id}: {str(e)}")
            return False  

    def get_payment_details_by_order_id(self, order_id: int) -> Optional[Dict[str, str]]:
        query = """
        SELECT id, user_id, order_id, amount, method, status, payment_date 
        FROM payments WHERE order_id = %s
         """
        params = (order_id,)
    
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                result = cursor.fetchone()
                if result:
                    payment_data = result
                    return {
                    "payment_id": payment_data[0],
                    "user_id": payment_data[1],
                    "order_id": payment_data[2],
                    "amount": payment_data[3],
                    "method": payment_data[4],
                    "status": payment_data[5],
                    "payment_date": payment_data[6].strftime('%Y-%m-%d %H:%M:%S')  # Format the datetime field
                    }
                logging.warning(f"Payment details not found for Order ID {order_id}.")
                return None
            except Exception as e:
                logging.error(f"Error fetching payment details for Order ID {order_id}: {str(e)}")
                return None
            finally:
                cursor.close()   

    def update_payment_status(self, payment_id: int, status: PaymentStatus) -> bool:
        if not isinstance(status, PaymentStatus):
            raise PaymentError("Invalid payment status.")
        
        query = "UPDATE payments SET status = %s WHERE id = %s"
        params = (status.value, payment_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                logging.info(f"Payment ID {payment_id} status updated to {status.value}")
                return True
            except Exception as e:
                logging.error(f"Error updating payment status for payment ID {payment_id}: {str(e)}")
                return False
            finally:
                cursor.close()    

    def get_payment_details(self, payment_id: int) -> Optional[Dict[str, str]]:
        query = """
            SELECT id, user_id, order_id, amount, method, status, payment_date FROM payments WHERE id = %s
        """
        params = (payment_id,)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                result = cursor.fetchone()
                if result:
                    payment_data = result
                    return {
                        "payment_id": payment_data[0],
                        "user_id": payment_data[1],
                        "amount": payment_data[2],
                        "method": payment_data[3],
                        "status": payment_data[4],
                        "payment_date": payment_data[5].strftime('%Y-%m-%d %H:%M:%S')
                        }
                logging.warning(f"Payment ID {payment_id} not found.")
                return None
            except Exception as e:
                logging.error(f"Error fetching details for payment ID {payment_id}: {str(e)}")
                return None
            finally:
                cursor.close()

    def validate_payment(self, payment_id: int) -> bool:
        payment_details = self.get_payment_details(payment_id)
        if not payment_details:
            logging.error(f"Cannot validate payment; payment ID {payment_id} not found.")
            return False
        
        if payment_details['status'] not in {PaymentStatus.COMPLETED.value, PaymentStatus.PENDING.value}:
            logging.warning(f"Payment ID {payment_id} has an invalid status for validation.")
            return False
            
        logging.info(f"Payment ID {payment_id} validated successfully.")
        return True