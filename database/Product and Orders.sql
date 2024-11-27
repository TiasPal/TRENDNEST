USE TRENDNEST;

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL, 
    status ENUM('Pending', 'Shipped', 'Delivered', 'Canceled') DEFAULT 'Pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shipping_address VARCHAR(255), 
    total_amount DECIMAL(10, 2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    category VARCHAR(100),
    stock INT DEFAULT 0 CHECK (stock >= 0),
    image_filename VARCHAR(255),
    active tinyint(1) DEFAULT '1'
);

INSERT INTO `product`(`name`,`price`,`category`,`stock`,`image_filename`,`active`) VALUES('Polo Ralph Lauren White Shirt for Men',4689.00,'Fashion',10,'polo_ralph_lauren_men.jpg',1);
INSERT INTO `product`(`name`,`price`,`category`,`stock`,`image_filename`,`active`) VALUES('Gaming Mouse',1500.00,'Electronics',10,'Gaming_Mouse.jpeg',1);
INSERT INTO `product`(`name`,`price`,`category`,`stock`,`image_filename`,`active`) VALUES('Titan Titanium Quartz Analog Blue Dial',17995.00,'Accessories',5,'Watch_Titan.jpeg',1);
INSERT INTO `product`(`name`,`price`,`category`,`stock`,`image_filename`,`active`) VALUES('Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones',460.00,'Book',10,'Atomic_Habit_book.jpeg',1);
INSERT INTO `product`(`name`,`price`,`category`,`stock`,`image_filename`,`active`) VALUES('Black Zara Dress For Women',9878.00,'Fashion',10,'zara_women.jpg',1);
INSERT INTO `product`(`name`,`price`,`category`,`stock`,`image_filename`,`active`) VALUES('Air Jordan 1 Retro High OG ',14000.00,'Shoes',10,'Air-Jordan-1-High-OG-Electro-Orange.jpeg',1);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE
);
RENAME TABLE orders TO `order`;