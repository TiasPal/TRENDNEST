# TRENDNEST
An E commerce website

DESIGN OF THE WEBSITE

TRENDNEST
│
├── /database
│   ├── Cart.sql                  # SQL queries for creating cart tables
│   ├── Payments.sql              # SQL queries for creating payments tables
│   ├── Product and Orders.sql    # SQL queries for creating Product and orders tables
│   └── User.sql                  # SQL queries for creating user table
|
├── /templates                    
│   ├── base.html                 # Base template with enhanced navbar, footer, and notifications
|   ├── home.html                 # Home page of the app
│   ├── register.html             # User registration with email verification
│   ├── login.html                # User login page with "forgot password" and OTP verification
│   ├── cart.html                 # Shopping cart with coupons, multi-item management
│   ├── checkout.html             # Checkout page with multiple shipping methods and saved addresses
|   ├── products.html             # Product page showing all the products available to buy in app
|   ├── order_confirmation.html   # Generates the final bill
│   └── admin_products.html       # Admin dashboard for managing products
│ 
├── /static                       
│   ├── /css                     
│       ├── styles.css            # Main stylesheet with responsive and advanced UI components
│       └── admin.css             # Separate styles for admin dashboard 
│   ├── /uploads                  # Images for the products added to database
│   └── /images                   # Logo of the app
│
├── app.py                        # Main app file with routes for user and admin sections
├── models.py                     # Database models with new tables for orders
├── forms.py                      # Forms used in different pages
├── requirements.txt              # Updated dependencies
└── Design.txt                    # Design of the complete app
