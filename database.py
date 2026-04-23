import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            # Tạo thư mục data nếu chưa có
            if not os.path.exists('data'):
                os.makedirs('data')
            
            self.conn = sqlite3.connect('data/pos.db', check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            print("✅ Kết nối SQLite thành công!")
            self.create_tables()
            self.insert_sample_data()
        except Exception as e:
            print(f"❌ Lỗi kết nối SQLite: {e}")

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Bảng sản phẩm
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                cost_price INTEGER DEFAULT 0,
                stock INTEGER DEFAULT 0,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng khách hàng
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                total_spent INTEGER DEFAULT 0,
                last_purchase TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng đơn hàng
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                total_amount INTEGER NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                status TEXT DEFAULT 'completed',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # Bảng chi tiết đơn hàng
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        self.conn.commit()
        print("✅ Đã tạo/cập nhật bảng thành công!")

    def insert_sample_data(self):
        cursor = self.conn.cursor()
        
        # Thêm sản phẩm mẫu
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('Cà phê đen', 15000, 8000, 100, 'Đồ uống'),
                ('Cà phê sữa', 20000, 10000, 100, 'Đồ uống'),
                ('Bánh mì thịt', 25000, 15000, 50, 'Đồ ăn'),
                ('Trà đào', 30000, 18000, 80, 'Đồ uống'),
                ('Nước ép cam', 35000, 20000, 60, 'Đồ uống'),
            ]
            cursor.executemany('''
                INSERT INTO products (name, price, cost_price, stock, category)
                VALUES (?, ?, ?, ?, ?)
            ''', sample_products)
            print("✅ Đã thêm 5 sản phẩm mẫu")
        
        # Thêm khách hàng mẫu
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] == 0:
            sample_customers = [
                ('Nguyễn Văn A', '0987654321', 'a@gmail.com', 'Hà Nội'),
                ('Trần Thị B', '0978123456', 'b@gmail.com', 'TP HCM'),
                ('Lê Văn C', '0965111222', 'c@gmail.com', 'Đà Nẵng'),
            ]
            cursor.executemany('''
                INSERT INTO customers (name, phone, email, address)
                VALUES (?, ?, ?, ?)
            ''', sample_customers)
            print("✅ Đã thêm 3 khách hàng mẫu")
        
        self.conn.commit()

    # ==================== SẢN PHẨM ====================
    def get_all_products(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

    def add_product(self, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, price, cost_price, stock, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data['price'], data.get('cost_price', 0), 
              data.get('stock', 0), data.get('category', '')))
        self.conn.commit()
        return cursor.lastrowid

    def update_product(self, product_id, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET name=?, price=?, cost_price=?, stock=?, category=?
            WHERE id=?
        ''', (data['name'], data['price'], data.get('cost_price', 0),
              data.get('stock', 0), data.get('category', ''), product_id))
        self.conn.commit()
        return True

    def delete_product(self, product_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        self.conn.commit()
        return True

    # ==================== KHÁCH HÀNG ====================
    def get_all_customers(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY total_spent DESC")
        return [dict(row) for row in cursor.fetchall()]

    def add_customer(self, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO customers (name, phone, email, address, total_spent)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data.get('phone', ''), data.get('email', ''),
              data.get('address', ''), 0))
        self.conn.commit()
        return cursor.lastrowid

    def update_customer(self, customer_id, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE customers 
            SET name=?, phone=?, email=?, address=?
            WHERE id=?
        ''', (data['name'], data.get('phone', ''), data.get('email', ''),
              data.get('address', ''), customer_id))
        self.conn.commit()
        return True

    def delete_customer(self, customer_id):
        cursor = self.conn.cursor()
        # Kiểm tra xem khách hàng có đơn hàng không
        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE customer_id=?", (customer_id,))
        if cursor.fetchone()['count'] > 0:
            return False, "Khách hàng có đơn hàng, không thể xóa"
        
        cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        self.conn.commit()
        return True, ""

    def get_customer_history(self, customer_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT o.*, oi.product_id, oi.quantity, oi.price, p.name as product_name
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
        ''', (customer_id,))
        return [dict(row) for row in cursor.fetchall()]

    # ==================== ĐƠN HÀNG ====================
    def get_all_orders(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT o.*, c.name as customer_name 
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            ORDER BY o.created_at DESC 
            LIMIT 50
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def create_order(self, order_data, items):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO orders (order_number, customer_id, total_amount, payment_method, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_data['order_number'], order_data.get('customer_id'), 
                  order_data['total_amount'], order_data.get('payment_method', 'cash'),
                  'completed', 1))
            order_id = cursor.lastrowid
            
            for item in items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['id'], item['quantity'], item['price']))
                
                cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", 
                             (item['quantity'], item['id']))
            
            if order_data.get('customer_id'):
                cursor.execute('''
                    UPDATE customers 
                    SET total_spent = total_spent + ?,
                        last_purchase = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (order_data['total_amount'], order_data['customer_id']))
            
            self.conn.commit()
            return order_id, None
        except Exception as e:
            self.conn.rollback()
            return None, str(e)

    # ==================== HÓA ĐƠN ====================
    def get_invoices(self, filter_type='all', start_date=None, end_date=None):
        cursor = self.conn.cursor()
        query = '''
            SELECT 
                o.order_number,
                o.created_at,
                p.name as product_name,
                oi.quantity,
                oi.price,
                (oi.quantity * oi.price) as subtotal,
                o.total_amount
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.status = 'completed'
        '''
        params = []
        
        if filter_type == 'today':
            query += " AND DATE(o.created_at) = DATE('now')"
        elif filter_type == 'week':
            query += " AND o.created_at >= DATE('now', '-7 days')"
        elif filter_type == 'month':
            query += " AND o.created_at >= DATE('now', '-30 days')"
        
        if start_date:
            query += " AND DATE(o.created_at) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(o.created_at) <= ?"
            params.append(end_date)
        
        query += " ORDER BY o.created_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def delete_invoice(self, order_number):
        """Xóa hóa đơn theo mã đơn hàng"""
        cursor = self.conn.cursor()
        try:
            # Lấy order_id từ order_number
            cursor.execute("SELECT id FROM orders WHERE order_number = ?", (order_number,))
            result = cursor.fetchone()
            if not result:
                return False, "Không tìm thấy đơn hàng"
            
            order_id = result['id']
            
            # Lấy danh sách sản phẩm trong đơn hàng để hoàn lại stock
            cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,))
            items = cursor.fetchall()
            
            # Hoàn lại số lượng tồn kho
            for item in items:
                cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", 
                             (item['quantity'], item['product_id']))
            
            # Trừ total_spent của khách hàng
            cursor.execute("SELECT customer_id, total_amount FROM orders WHERE id = ?", (order_id,))
            order = cursor.fetchone()
            if order and order['customer_id']:
                cursor.execute("UPDATE customers SET total_spent = total_spent - ? WHERE id = ?",
                             (order['total_amount'], order['customer_id']))
            
            # Xóa order_items trước
            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            
            # Xóa orders
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            
            self.conn.commit()
            return True, "Xóa thành công"
        except Exception as e:
            self.conn.rollback()
            return False, str(e)
    
    def get_order_by_number(self, order_number):
        """Lấy thông tin đơn hàng theo mã"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT o.*, c.name as customer_name 
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.order_number = ?
        ''', (order_number,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ==================== THỐNG KÊ ====================
    def get_stats(self):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM products")
        total_products = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM customers")
        total_customers = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'completed'")
        total_orders = cursor.fetchone()['count']
        
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders WHERE DATE(created_at) = DATE('now') AND status = 'completed'")
        today_revenue = cursor.fetchone()['revenue']
        
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders WHERE DATE(created_at) >= DATE('now', 'start of month') AND status = 'completed'")
        month_revenue = cursor.fetchone()['revenue']
        
        # Top 5 sản phẩm bán chạy
        cursor.execute('''
            SELECT p.name, SUM(oi.quantity) as total_sold
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            GROUP BY p.id
            ORDER BY total_sold DESC
            LIMIT 5
        ''')
        top_products = [dict(row) for row in cursor.fetchall()]
        
        # Tính lợi nhuận (giả định 30% - có thể tính chính xác từ cost_price)
        cursor.execute('''
            SELECT SUM((oi.price - p.cost_price) * oi.quantity) as profit
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) >= DATE('now', 'start of month')
        ''')
        profit_result = cursor.fetchone()
        profit = profit_result['profit'] if profit_result and profit_result['profit'] else 0
        
        # Tính tỷ suất lợi nhuận
        profit_margin = (profit / month_revenue * 100) if month_revenue > 0 else 0
        
        return {
            'total_products': total_products,
            'total_customers': total_customers,
            'total_orders': total_orders,
            'today_revenue': today_revenue,
            'month_revenue': month_revenue,
            'profit': profit,
            'profit_margin': profit_margin,
            'top_products': top_products
        }
    
    def close(self):
        if self.conn:
            self.conn.close()
