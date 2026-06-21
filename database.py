import mysql.connector


class DatabaseManager:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Ad-135798834",
            database="technic_service"
        )
        self.cursor = self.conn.cursor()
        self.setup_db()
        self.add_default_data()

    def setup_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                role VARCHAR(50) NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS repairs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                technician_name VARCHAR(100) NOT NULL,
                device_model VARCHAR(150) NOT NULL,
                serial_number VARCHAR(100) NOT NULL,
                damage_desc TEXT NOT NULL,
                status VARCHAR(50) NOT NULL,
                price DOUBLE DEFAULT 0,
                estimated_time VARCHAR(100) DEFAULT '-',
                payment_status VARCHAR(50) DEFAULT 'Unpaid',
                process_date VARCHAR(50) NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repair_id INT UNIQUE,
                customer_name VARCHAR(100) NOT NULL,
                rating INT NOT NULL,
                comment TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repair_id INT UNIQUE,
                amount DOUBLE NOT NULL,
                invoice_date VARCHAR(50) NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS warranties (
                id INT AUTO_INCREMENT PRIMARY KEY,
                serial_number VARCHAR(100) UNIQUE NOT NULL,
                expiry_date VARCHAR(50) NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS spare_parts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                price DOUBLE NOT NULL,
                stock INT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS part_usages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repair_id INT NOT NULL,
                part_name VARCHAR(100) NOT NULL,
                quantity INT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_centers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) UNIQUE NOT NULL,
                location VARCHAR(150) NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repair_id INT,
                customer_name VARCHAR(100) NOT NULL,
                technician_name VARCHAR(100) DEFAULT '',
                appointment_date VARCHAR(50) NOT NULL,
                appointment_time VARCHAR(50) NOT NULL,
                delivery_date VARCHAR(50) DEFAULT '-'
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender VARCHAR(100) NOT NULL,
                receiver VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                date VARCHAR(50) DEFAULT ''
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipient VARCHAR(100) NOT NULL DEFAULT '',
                title VARCHAR(150) NOT NULL,
                message TEXT NOT NULL,
                date VARCHAR(50) DEFAULT '',
                is_read INT DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INT PRIMARY KEY,
                theme VARCHAR(50) NOT NULL,
                theme_color VARCHAR(50) NOT NULL DEFAULT 'Blue'
            )
        """)

        self.conn.commit()

    def add_default_data(self):
        default_parts = [
            ("Screen", 1200, 5),
            ("Battery", 700, 8),
            ("Charging Port", 450, 10)
        ]

        for name, price, stock in default_parts:
            self.cursor.execute("""
                INSERT IGNORE INTO spare_parts (name, price, stock)
                VALUES (%s, %s, %s)
            """, (name, price, stock))

        self.cursor.execute("""
            INSERT IGNORE INTO service_centers (name, location)
            VALUES (%s, %s)
        """, ("Central Technical Service", "Istanbul"))

        self.cursor.execute("""
            INSERT IGNORE INTO settings (id, theme, theme_color)
            VALUES (1, 'Dark', 'Blue')
        """)

        self.conn.commit()

    def register_user(self, user_account):
        try:
            self.cursor.execute("""
                INSERT INTO users (username, password, email, role)
                VALUES (%s, %s, %s, %s)
            """, (
                user_account.username,
                user_account.password_hash,
                user_account.email,
                user_account.role
            ))
            self.conn.commit()
            return True, "Success"
        except mysql.connector.IntegrityError as err:
            error_text = str(err).lower()

            if "email" in error_text:
                return False, "This email address is already registered!"

            if "username" in error_text:
                return False, "This username is already taken!"

            return False, "An error occurred during registration!"

    def check_login(self, username, password_hash, selected_role):
        self.cursor.execute("""
            SELECT password, role, email
            FROM users
            WHERE username = %s
        """, (username,))

        user = self.cursor.fetchone()

        if not user:
            return False, "Username was not found.", None

        db_password, db_role, email = user

        if db_password != password_hash:
            return False, "Incorrect password.", None

        if db_role != selected_role:
            return False, "Incorrect role selection.", None

        return True, "Login successful.", email

    def user_exists(self, username):
        self.cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        return self.cursor.fetchone() is not None

    def get_users_by_role(self, role):
        self.cursor.execute("SELECT username FROM users WHERE role = %s", (role,))
        return [row[0] for row in self.cursor.fetchall()]

    def get_all_usernames_except(self, username):
        self.cursor.execute("""
            SELECT username
            FROM users
            WHERE username != %s
            ORDER BY username
        """, (username,))

        return [row[0] for row in self.cursor.fetchall()]

    def repair_exists(self, customer_name, serial_number, damage_desc):
        self.cursor.execute("""
            SELECT id
            FROM repairs
            WHERE customer_name = %s
              AND serial_number = %s
              AND LOWER(TRIM(damage_desc)) = LOWER(TRIM(%s))
        """, (customer_name, serial_number, damage_desc))

        return self.cursor.fetchone() is not None

    def add_repair(self, repair):
        if self.repair_exists(
            repair.customer_name,
            repair.device.serial_number,
            repair.damage_desc
        ):
            return False, "A repair record with the same damage description already exists for this device."

        self.cursor.execute("""
            INSERT INTO repairs
            (customer_name, technician_name, device_model, serial_number, damage_desc,
             status, price, estimated_time, payment_status, process_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            repair.customer_name,
            repair.technician_name,
            repair.device.brand_model,
            repair.device.serial_number,
            repair.damage_desc,
            repair.status,
            repair.price,
            repair.estimated_time,
            repair.payment_status,
            repair.process_date
        ))

        self.conn.commit()
        return True, "Repair request created."

    def update_technician(self, repair_id, new_technician):
        self.cursor.execute("""
            UPDATE repairs
            SET technician_name = %s
            WHERE id = %s AND status = 'Pending'
        """, (new_technician, repair_id))

        self.conn.commit()
        return self.cursor.rowcount > 0

    def update_status(self, repair_id, status, price=None, estimated_time=None):
        if price is not None and estimated_time is not None:
            self.cursor.execute("""
                UPDATE repairs
                SET status = %s, price = %s, estimated_time = %s
                WHERE id = %s
            """, (status, price, estimated_time, repair_id))
        else:
            self.cursor.execute("""
                UPDATE repairs
                SET status = %s
                WHERE id = %s
            """, (status, repair_id))

        self.conn.commit()

    def pay_repair(self, repair_id, total_amount):
        self.cursor.execute("""
            UPDATE repairs
            SET payment_status = 'Paid',
                price = %s
            WHERE id = %s
        """, (total_amount, repair_id))

        self.conn.commit()

    def delete_repair(self, repair_id):
        self.cursor.execute("DELETE FROM repairs WHERE id = %s", (repair_id,))
        self.conn.commit()

    def get_data(self, role, username):
        if role == "Customer":
            self.cursor.execute("SELECT * FROM repairs WHERE customer_name = %s", (username,))
        elif role == "Technician":
            self.cursor.execute("SELECT * FROM repairs WHERE technician_name = %s", (username,))
        else:
            self.cursor.execute("SELECT * FROM repairs")

        return self.cursor.fetchall()

    def get_device_history(self, serial_no):
        self.cursor.execute("""
            SELECT r.id, r.process_date, r.damage_desc, r.status, r.price,
                   COALESCE(a.delivery_date, '-')
            FROM repairs r
            LEFT JOIN appointments a ON a.repair_id = r.id
            WHERE r.serial_number = %s
            ORDER BY r.id DESC
        """, (serial_no,))

        return self.cursor.fetchall()

    def get_delivery_date_by_repair(self, repair_id):
        self.cursor.execute("""
            SELECT delivery_date
            FROM appointments
            WHERE repair_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (repair_id,))

        result = self.cursor.fetchone()
        return result[0] if result else "-"

    def add_feedback(self, repair_id, feedback):
        try:
            self.cursor.execute("""
                INSERT INTO feedbacks (repair_id, customer_name, rating, comment)
                VALUES (%s, %s, %s, %s)
            """, (repair_id, feedback.customer, feedback.rating, feedback.comment))

            self.conn.commit()
            return True, "Feedback saved successfully."
        except mysql.connector.IntegrityError:
            return False, "Feedback has already been submitted for this record."

    def get_feedback_by_repair(self, repair_id):
        self.cursor.execute("""
            SELECT rating, comment
            FROM feedbacks
            WHERE repair_id = %s
        """, (repair_id,))

        return self.cursor.fetchone()

    def get_all_feedbacks(self):
        self.cursor.execute("""
            SELECT repair_id, customer_name, rating, comment
            FROM feedbacks
            ORDER BY id DESC
        """)

        return self.cursor.fetchall()

    def create_invoice(self, invoice, invoice_date):
        try:
            self.cursor.execute("""
                INSERT INTO invoices (repair_id, amount, invoice_date)
                VALUES (%s, %s, %s)
            """, (invoice.repair_id, invoice.amount, invoice_date))

            self.conn.commit()
            return True
        except mysql.connector.IntegrityError:
            return False

    def get_invoice_by_repair(self, repair_id):
        self.cursor.execute("""
            SELECT repair_id, amount, invoice_date
            FROM invoices
            WHERE repair_id = %s
        """, (repair_id,))

        return self.cursor.fetchone()

    def add_warranty(self, warranty):
        self.cursor.execute("""
            INSERT INTO warranties (serial_number, expiry_date)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE expiry_date = VALUES(expiry_date)
        """, (warranty.serial_number, warranty.expiry_date))

        self.conn.commit()

    def get_warranty(self, serial_number):
        self.cursor.execute("""
            SELECT serial_number, expiry_date
            FROM warranties
            WHERE serial_number = %s
        """, (serial_number,))

        return self.cursor.fetchone()

    def get_spare_parts(self):
        self.cursor.execute("""
            SELECT name, price, stock
            FROM spare_parts
            ORDER BY name
        """)

        return self.cursor.fetchall()

    def add_spare_part(self, part):
        self.cursor.execute("""
            INSERT INTO spare_parts (name, price, stock)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                price = VALUES(price),
                stock = VALUES(stock)
        """, (part.name, part.price, part.stock))

        self.conn.commit()

    def use_part(self, part_usage):
        self.cursor.execute("""
            SELECT price, stock
            FROM spare_parts
            WHERE name = %s
        """, (part_usage.part_name,))

        result = self.cursor.fetchone()

        if not result:
            return False, "This part is not in stock."

        price, current_stock = result

        if part_usage.quantity <= 0:
            return False, "Part quantity must be greater than 0."

        if current_stock < part_usage.quantity:
            return False, "Not enough stock."

        self.cursor.execute("""
            UPDATE spare_parts
            SET stock = stock - %s
            WHERE name = %s
        """, (part_usage.quantity, part_usage.part_name))

        self.cursor.execute("""
            INSERT INTO part_usages (repair_id, part_name, quantity)
            VALUES (%s, %s, %s)
        """, (
            part_usage.repair_id,
            part_usage.part_name,
            part_usage.quantity
        ))

        self.conn.commit()
        return True, "Part usage saved."

    def get_part_usages(self, repair_id):
        self.cursor.execute("""
            SELECT part_name, quantity
            FROM part_usages
            WHERE repair_id = %s
        """, (repair_id,))

        return self.cursor.fetchall()

    def get_part_total(self, repair_id):
        self.cursor.execute("""
            SELECT COALESCE(SUM(sp.price * pu.quantity), 0)
            FROM part_usages pu
            JOIN spare_parts sp ON sp.name = pu.part_name
            WHERE pu.repair_id = %s
        """, (repair_id,))

        result = self.cursor.fetchone()
        return result[0] if result else 0

    def add_service_center(self, service_center):
        self.cursor.execute("""
            INSERT INTO service_centers (name, location)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE location = VALUES(location)
        """, (service_center.name, service_center.location))

        self.conn.commit()

    def get_service_centers(self):
        self.cursor.execute("""
            SELECT name, location
            FROM service_centers
            ORDER BY name
        """)

        return self.cursor.fetchall()

    def add_appointment(self, appointment):
        self.cursor.execute("""
            INSERT INTO appointments
            (repair_id, customer_name, technician_name, appointment_date, appointment_time, delivery_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            appointment.repair_id,
            appointment.customer,
            appointment.technician,
            appointment.date,
            appointment.time,
            appointment.delivery_date
        ))

        self.conn.commit()

    def get_appointments(self, username, role):
        if role == "Technician":
            self.cursor.execute("""
                SELECT repair_id, customer_name, technician_name,
                       appointment_date, appointment_time, delivery_date
                FROM appointments
                WHERE technician_name = %s
                ORDER BY id DESC
            """, (username,))
        elif role == "Customer":
            self.cursor.execute("""
                SELECT repair_id, customer_name, technician_name,
                       appointment_date, appointment_time, delivery_date
                FROM appointments
                WHERE customer_name = %s
                ORDER BY id DESC
            """, (username,))
        else:
            self.cursor.execute("""
                SELECT repair_id, customer_name, technician_name,
                       appointment_date, appointment_time, delivery_date
                FROM appointments
                ORDER BY id DESC
            """)

        return self.cursor.fetchall()

    def add_message(self, message):
        self.cursor.execute("""
            INSERT INTO messages (sender, receiver, content, date)
            VALUES (%s, %s, %s, %s)
        """, (message.sender, message.receiver, message.content, message.date))

        self.conn.commit()

    def get_messages(self, username):
        self.cursor.execute("""
            SELECT sender, receiver, content, date
            FROM messages
            WHERE sender = %s OR receiver = %s
            ORDER BY id DESC
        """, (username, username))

        return self.cursor.fetchall()

    def add_notification(self, notification):
        self.cursor.execute("""
            INSERT INTO notifications (recipient, title, message, date, is_read)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            notification.recipient,
            notification.title,
            notification.message,
            notification.date,
            notification.is_read
        ))

        self.conn.commit()

    def get_notifications(self, username):
        self.cursor.execute("""
            SELECT id, title, message, date, is_read
            FROM notifications
            WHERE recipient = %s
            ORDER BY id DESC
        """, (username,))

        return self.cursor.fetchall()

    def mark_notification_as_read(self, notification_id):
        self.cursor.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE id = %s
        """, (notification_id,))

        self.conn.commit()

    def mark_notifications_as_read(self, username):
        self.cursor.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE recipient = %s
        """, (username,))

        self.conn.commit()

    def update_settings(self, settings):
        self.cursor.execute("""
            UPDATE settings
            SET theme = %s, theme_color = %s
            WHERE id = 1
        """, (settings.theme, settings.theme_color))

        self.conn.commit()

    def get_settings(self):
        self.cursor.execute("""
            SELECT theme, theme_color
            FROM settings
            WHERE id = 1
        """)

        return self.cursor.fetchone()

    def close_connection(self):
        if self.conn:
            self.conn.close()