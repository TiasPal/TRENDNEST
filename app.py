from flask import Flask,render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from forms import RegistrationForm, LoginForm, ProductForm
from models import Database, User, Product, Cart, Order, Payment,PaymentStatus,PaymentMethod
from datetime import datetime, timedelta
from math import ceil
import os
import logging
import mysql.connector
import pytz

app = Flask(__name__)
app.secret_key = '9510d561e014b104b64773c1fc3c5290848d28305fc34575221fc4be72b683a7'
app.config['WTF_CSRF_ENABLED'] = False
app.config['MYSQL_USER'] = 'Tias'
app.config['MYSQL_PASSWORD'] = 'tias_pal@2007'
app.config['MYSQL_DB'] = 'trendnest'
app.config['MYSQL_HOST'] = 'localhost'

csrf = CSRFProtect(app) 
mysql = Database(app)

user_model = User(mysql)
product_model = Product(mysql)
cart_model = Cart(mysql)
order_model = Order(mysql)
payment_model = Payment(mysql)

def session_timeout():
    if 'last_activity' in session:
        now = datetime.now(pytz.timezone('Asia/Kolkata'))  
        last_activity = session['last_activity']
        if now - last_activity > timedelta(minutes=90):
            session.clear()

@app.before_request
def before_request():
    """Execute before each request to handle session timeouts."""
    session_timeout()

@app.route('/')
def home():
    """Render the homepage with a welcome message."""
    return render_template('home.html')  

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    form = RegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        
        if user_model.register(username, email, password):
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    form = LoginForm()
    
    if form.validate_on_submit(): 
        email = form.email.data.strip() 
        password = form.password.data
        
        user = user_model.login(email, password) 

        if user:
            if not user[5]: 
                return redirect(url_for('login'))
            
            if check_password_hash(user[3], password):  
                session['user_id'] = user[0]  
                session['username'] = user[1]
                session['is_admin'] = user[6] == 'admin' 
                return redirect(url_for('admin_products' if session['is_admin'] else 'products'))  
            
            flash ("Invalid password. Please try again.", "danger")
        else:
            flash("No account found with that email. Please try again.", "danger")
        
        return redirect(url_for('login'))
    
    return render_template('login.html', form=form)

@app.route('/admin/products')
def admin_products():
    form = ProductForm() 
    if form.validate_on_submit():
        pass
    return render_template('admin_products.html', form=form)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_products():
    """Admin view for managing products."""
    form = ProductForm()

    if form.validate_on_submit():
        name = request.form.get('name')
        price = float(request.form.get('price'))
        category = request.form.get('category')
        stock = int(request.form.get('stock'))
        image_file = request.files.get('image')

        upload_directory = os.path.join(app.root_path, 'static/uploads')
        os.makedirs(upload_directory, exist_ok=True)

        if image_file:
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(upload_directory, filename))
        else:
            filename = None
        try:
            success = product_model.add_product(name, price, category, stock, filename)
            if not success:
                flash(f"Error adding product {name}.", "danger")
            else:
                flash("Product added successfully!", "success")
        except Exception as e:
            flash(f"An error occurred while adding the product: {e}", "danger")
        return redirect(url_for('admin_products'))

    return render_template('admin_products.html', form=form)


@app.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search_query', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc')

    products, total_count = product_model.get_filtered_products(
        page=page,
        limit=10,
        sort_by=sort_by,
        order=order,
        category=category,
        min_price=min_price,
        max_price=max_price,
        search_query=search_query
    )

    categories = product_model.get_all_categories()
    total_pages = ceil(total_count / 10)

    return render_template('products.html', 
                           products=products, 
                           page=page, 
                           total_pages=total_pages,
                           categories=categories)

@app.route('/cart', methods=['GET', 'POST'])
def view_cart():
    if 'user_id' not in session:
        flash("You need to log in to view your cart.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'update':
            quantities = request.form.getlist('quantities[]')
            item_ids = request.form.getlist('item_ids[]')

            for item_id, quantity in zip(item_ids, quantities):
                if int(quantity) > 0:
                    success = cart_model.update_cart_item_quantity(int(item_id), int(quantity))
                    if not success:
                        flash(f"Failed to update quantity for item ID {item_id}.", "danger")
                else:
                    flash("Quantity must be at least 1.", "danger")

            flash("Cart updated successfully.", "success")
        else:
            flash("Item ID is missing or invalid.", "danger")

            return redirect(url_for('view_cart'))

    cart_items = cart_model.get_cart_items(user_id)
    cart_total = cart_model.calculate_total_price(user_id)

    return render_template('cart.html', cart_items=cart_items, cart_total=cart_total)


@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash("You need to log in to add items to your cart.", "warning")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    product_id = request.form.get('product_id')  
    quantity = request.form.get('quantity', 1)  

    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        flash("Invalid product ID or quantity.", "danger")
        return redirect(url_for('products'))  

    success = cart_model.add_to_cart(user_id,product_id, quantity)

    if success:
        flash("Item added to cart successfully.", "success")
    else:
        flash("Failed to add item to cart. Please try again.", "danger")
    
    return redirect(url_for('products'))  


@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    if 'user_id' not in session:
        flash("You need to log in to remove items from your cart.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    success = cart_model.clear_cart(user_id)

    if success:
        flash("Your cart has been cleared.", "success")
    else:
        flash("Failed to clear the cart. Please try again.", "danger")

    return redirect(url_for('view_cart')) 
    
    
@app.route('/cart/update', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        flash("You need to log in to update your cart.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    quantities = request.form.getlist('quantities[]')
    item_ids = request.form.getlist('item_ids[]')
    
    if not quantities or not item_ids:
        flash("No items to update.", "danger")
        return redirect(url_for('view_cart'))
    
    for item_id, quantity in zip(item_ids, quantities):
        try:
            quantity = int(quantity)
            item_id = int(item_id)
            if cart_model.update_cart_item_quantity(item_id, quantity):
                flash(f"Quantity of item {item_id} updated to {quantity}.", "success")
        
        except ValueError:
            flash("Invalid input for item ID or quantity.", "danger")
    
    return redirect(url_for('view_cart'))

    
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash("You need to log in to proceed with checkout.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    cart_items = order_model.get_cart_items_order(user_id)

    # If the cart is empty, display a warning and redirect
    if not cart_items:
        flash("Your cart is empty. Please add items before proceeding.", "warning")
        return redirect(url_for('view_cart'))

    total_amount = sum(item['total_price'] for item in cart_items)

    if request.method == 'POST':
        shipping_address = request.form.get('shipping_address')
        payment_method = request.form.get('payment_method')

        if not shipping_address:
            flash("Shipping address is required.", "danger")
        elif not payment_method:
            flash("Payment method is required.", "danger")
        else:
            try:
                order_id = order_model.create_order(user_id, shipping_address, cart_items)

                if not order_id:
                    flash("There was an error creating your order. Please try again.", "danger")
                    return redirect(url_for('view_cart'))

                payment_id = payment_model.create_payment(user_id, order_id, total_amount, PaymentMethod(payment_method))

                if not payment_id:
                    flash("Failed to create payment. Please try again.", "danger")
                    return redirect(url_for('view_cart'))

                # Simulate payment processing (could integrate an actual payment gateway here)
                payment_success = payment_model.process_payment(user_id, total_amount, PaymentMethod(payment_method))

                if payment_success:
                    payment_model.update_payment_status(payment_id, PaymentStatus.COMPLETED)

                    order_model.update_order_status(order_id, 'Shipped')

                    cart_model.clear_cart(user_id)

                    flash(f"Order placed successfully! Your order ID is {order_id}.", "success")
                    return redirect(url_for('order_confirmation', order_id=order_id))
                else:
                    payment_model.update_payment_status(payment_id, PaymentStatus.FAILED)
                    flash("Payment failed. Please try again.", "danger")

            except Exception as e:
                logging.error(f"Error during checkout: {str(e)}")
                flash("An error occurred while processing your order. Please try again.", "danger")

    return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)

@app.route('/order_confirmation/<int:order_id>', methods=['GET'])
def order_confirmation(order_id):
    # Fetch order details using the order_id
    order_details = order_model.get_order_details(order_id)
    
    if isinstance(order_details, tuple):
        # Convert the tuple to a dictionary for easier access
        order_details_dict = {
            "order_id": order_details[0],
            "user_id": order_details[1],
            "shipping_address": order_details[2],
            "total_amount": order_details[5],
            "status": order_details[4]
        }
    else:
        order_details_dict = order_details  

    # Fetch the payment_id from the payments table based on order_id
    payment_details = payment_model.get_payment_details_by_order_id(order_id)

    if not payment_details:
        flash("Payment details not found for the order.", "danger")
        return redirect(url_for('view_orders'))

    # Prepare data to be passed to the template
    return render_template('order_confirmation.html', 
                           order_id=order_id, 
                           order_status=order_details_dict['status'],
                           shipping_address=order_details_dict['shipping_address'],
                           total_amount=order_details_dict['total_amount'],
                           payment_status=payment_details['status'], 
                           payment_method=payment_details['method'], 
                           payment_date=payment_details['payment_date'])


@app.route('/payments/<int:payment_id>/complete', methods=['GET', 'POST'])
def complete_payment(payment_id):
    try:
        user_id = session.get('user_id') 
        is_valid = payment_model.validate_payment(payment_id)
        if not is_valid:
            return render_template("checkout.html", error="Payment validation failed.")

        payment_model.update_payment_status(payment_id, PaymentStatus.COMPLETED)
        success = cart_model.clear_cart(user_id)
        return render_template("checkout.html", message="Payment completed successfully!", payment_id=payment_id)
    except Exception as e:
        logging.error(f"Error completing payment: {str(e)}")
        return render_template("checkout.html", error="Failed to complete payment.")

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
