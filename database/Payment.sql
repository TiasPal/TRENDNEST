USE TRENDNEST;

CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    method ENUM('credit_card', 'paypal', 'bank_transfer') NOT NULL,
    status ENUM('Pending', 'Completed', 'Failed', 'Refunded', 'Partially Refunded') NOT NULL,
    payment_date DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id), 
    FOREIGN KEY (order_id) REFERENCES orders(id)  
);
