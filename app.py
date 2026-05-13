from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from database import Database
from datetime import datetime, timedelta
from auth import login_required, check_login
import sqlite3  # Thêm dòng này nếu chưa có
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
db = Database()

# ==================== TRANG ĐĂNG NHẬP ====================
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if check_login(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Sai tên đăng nhập hoặc mật khẩu!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ==================== TRANG CHỦ ====================
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# ==================== CÁC TRANG KHÁC ====================
@app.route('/products')
@login_required
def products_page():
    return render_template('products.html')

@app.route('/customers')
@login_required
def customers_page():
    return render_template('customers.html')

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/invoices')
@login_required
def invoices_page():
    return render_template('invoices.html')

# ==================== API SẢN PHẨM ====================
@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = db.get_all_products()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    try:
        data = request.json
        print("=" * 60)
        print(f"📦 RAW DATA từ client: {data}")
        print(f"📦 Các keys trong data: {list(data.keys()) if data else 'None'}")
        
        # Nếu có trường 'id' thì xóa ngay lập tức
        if data and 'id' in data:
            print("⚠️⚠️⚠️ PHÁT HIỆN trường 'id'! Đang xóa...")
            del data['id']
            print(f"📦 Dữ liệu sau khi xóa id: {data}")
        
        product_data = {
            'name': data.get('name'),
            'price': int(data.get('price', 0)),
            'cost_price': int(data.get('cost_price', 0)),
            'stock': int(data.get('stock', 0)),
            'category': data.get('category', '')
        }
        
        print(f"📦 Dữ liệu gửi xuống database: {product_data}")
        
        product_id = db.add_product(product_data)
        
        if product_id:
            return jsonify({'success': True, 'id': product_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể thêm sản phẩm'}), 500
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    try:
        data = request.json
        product_data = {
            'name': data['name'],
            'price': int(data['price']),
            'cost_price': int(data.get('cost_price', 0)),
            'stock': int(data.get('stock', 0)),
            'category': data.get('category', '')
        }
        success = db.update_product(product_id, product_data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    success = db.delete_product(product_id)
    return jsonify({'success': success})

# ==================== API KHÁCH HÀNG ====================
@app.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    customers = db.get_all_customers()
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    try:
        data = request.json
        customer_data = {
            'name': data['name'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'address': data.get('address', ''),
            'total_spent': 0
        }
        customer_id = db.add_customer(customer_data)
        if customer_id:
            return jsonify({'success': True, 'id': customer_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể thêm khách hàng'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    try:
        data = request.json
        customer_data = {
            'name': data['name'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'address': data.get('address', '')
        }
        success = db.update_customer(customer_id, customer_data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    success, error = db.delete_customer(customer_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': error}), 400

@app.route('/api/customers/<int:customer_id>/history')
@login_required
def get_customer_history(customer_id):
    history = db.get_customer_history(customer_id)
    return jsonify(history)

# ==================== API ĐƠN HÀNG ====================
@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    orders = db.get_all_orders()
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.json
        order_number = f"DH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order_data = {
            'order_number': order_number,
            'customer_id': data.get('customer_id'),
            'total_amount': data['total_amount'],
            'payment_method': data.get('payment_method', 'cash'),
            'status': 'completed',
            'created_by': 1
        }
        
        order_id, error = db.create_order(order_data, data['items'])
        
        if order_id:
            return jsonify({'success': True, 'order_id': order_id, 'order_number': order_number})
        else:
            return jsonify({'success': False, 'error': error}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API HÓA ĐƠN ====================
@app.route('/api/invoices', methods=['GET'])
@login_required
def get_invoices():
    filter_type = request.args.get('filter', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    invoices = db.get_invoices(filter_type, start_date, end_date)
    return jsonify(invoices)

# Thêm vào sau API invoices (khoảng dòng 220):

@app.route('/api/invoices/<order_number>', methods=['DELETE'])
@login_required
def delete_invoice(order_number):
    """Xóa hóa đơn theo mã đơn hàng"""
    try:
        success, message = db.delete_invoice(order_number)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API THỐNG KÊ ====================
@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/api/reports/detail', methods=['GET'])
@login_required
def report_detail():
    """Báo cáo chi tiết doanh thu theo ngày/tháng/năm"""
    try:
        report_type = request.args.get('type', 'day')
        date_param = request.args.get('date')
        
        # Kiểm tra kết nối database
        if not db.client:
            return jsonify([])
        
        if report_type == 'day':
            if date_param:
                target_date = date_param
            else:
                target_date = datetime.now().strftime('%Y-%m-%d')
            
            # Lấy dữ liệu từ Supabase
            result = db.client.table('orders')\
                .select('created_at, total_amount')\
                .eq('status', 'completed')\
                .gte('created_at', target_date)\
                .lt('created_at', f"{target_date}T23:59:59")\
                .execute()
            
            # Tạo mảng 24 giờ
            reports = []
            for h in range(24):
                reports.append({
                    'hour': f"{h:02d}",
                    'order_count': 0,
                    'revenue': 0,
                    'total_quantity': 0
                })
            
            # Điền dữ liệu thực tế
            for order in result.data:
                hour = int(order['created_at'][11:13])
                reports[hour]['order_count'] += 1
                reports[hour]['revenue'] += order['total_amount'] or 0
            
            return jsonify(reports)
        
        elif report_type == 'month':
            if date_param:
                target_date = date_param
            else:
                target_date = datetime.now().strftime('%Y-%m')
            
            year = int(target_date[:4])
            month = int(target_date[5:7])
            from calendar import monthrange
            days_in_month = monthrange(year, month)[1]
            
            # Lấy dữ liệu từ Supabase
            start_date = f"{target_date}-01"
            end_date = f"{target_date}-{days_in_month}"
            
            result = db.client.table('orders')\
                .select('created_at, total_amount')\
                .eq('status', 'completed')\
                .gte('created_at', start_date)\
                .lte('created_at', end_date)\
                .execute()
            
            # Tạo mảng theo ngày
            reports = []
            day_revenue = {}
            day_count = {}
            
            for order in result.data:
                day = int(order['created_at'][8:10])
                day_revenue[day] = day_revenue.get(day, 0) + (order['total_amount'] or 0)
                day_count[day] = day_count.get(day, 0) + 1
            
            for d in range(1, days_in_month + 1):
                reports.append({
                    'day': f"{year}-{month:02d}-{d:02d}",
                    'order_count': day_count.get(d, 0),
                    'revenue': day_revenue.get(d, 0),
                    'total_quantity': 0
                })
            
            return jsonify(reports)
        
        elif report_type == 'year':
            if date_param:
                year = int(date_param.split('-')[0])
            else:
                year = datetime.now().year
            
            # Lấy dữ liệu từ Supabase
            result = db.client.table('orders')\
                .select('created_at, total_amount')\
                .eq('status', 'completed')\
                .gte('created_at', f"{year}-01-01")\
                .lt('created_at', f"{year + 1}-01-01")\
                .execute()
            
            # Tạo mảng theo tháng
            reports = []
            month_revenue = {}
            month_count = {}
            
            for order in result.data:
                month = int(order['created_at'][5:7])
                month_revenue[month] = month_revenue.get(month, 0) + (order['total_amount'] or 0)
                month_count[month] = month_count.get(month, 0) + 1
            
            for m in range(1, 13):
                reports.append({
                    'month': f"{year}-{m:02d}",
                    'order_count': month_count.get(m, 0),
                    'revenue': month_revenue.get(m, 0),
                    'total_quantity': 0
                })
            
            return jsonify(reports)
        
        return jsonify([])
        
    except Exception as e:
        print(f"ERROR in report_detail: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])  # Trả về mảng rỗng thay vì object lỗi
        
@app.route('/backup/full')
@login_required
def backup_full():
    """Backup đầy đủ dữ liệu"""
    import sqlite3
    from datetime import datetime
    
    conn = sqlite3.connect('data/pos.db')
    conn.row_factory = sqlite3.Row
    
    # Bắt đầu nội dung backup
    lines = []
    lines.append("-- ============================================")
    lines.append(f"-- BACKUP CỬA HÀNG MINH THIÊN PHÚC")
    lines.append(f"-- Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("-- ============================================")
    lines.append("")
    lines.append("PRAGMA foreign_keys=OFF;")
    lines.append("BEGIN TRANSACTION;")
    lines.append("")
    
    # 1. Bảng products
    lines.append("-- ========== PRODUCTS ==========")
    lines.append("DROP TABLE IF EXISTS products;")
    lines.append("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    cost_price INTEGER DEFAULT 0,
    stock INTEGER DEFAULT 0,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id")
    products = cursor.fetchall()
    
    for p in products:
        name = p['name'].replace("'", "''")
        category = p['category'] if p['category'] else ''
        lines.append(f"INSERT INTO products VALUES ({p['id']}, '{name}', {p['price']}, {p['cost_price']}, {p['stock']}, '{category}', '{p['created_at']}');")
    
    lines.append("")
    
    # 2. Bảng customers
    lines.append("-- ========== CUSTOMERS ==========")
    lines.append("DROP TABLE IF EXISTS customers;")
    lines.append("""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    total_spent INTEGER DEFAULT 0,
    last_purchase TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
    
    cursor.execute("SELECT * FROM customers ORDER BY id")
    customers = cursor.fetchall()
    
    for c in customers:
        name = c['name'].replace("'", "''")
        phone = c['phone'] if c['phone'] else ''
        email = c['email'] if c['email'] else ''
        address = c['address'] if c['address'] else ''
        last_purchase = c['last_purchase'] if c['last_purchase'] else ''
        lines.append(f"INSERT INTO customers VALUES ({c['id']}, '{name}', '{phone}', '{email}', '{address}', {c['total_spent']}, '{last_purchase}', '{c['created_at']}');")
    
    lines.append("")
    
    # 3. Bảng orders
    lines.append("-- ========== ORDERS ==========")
    lines.append("DROP TABLE IF EXISTS orders;")
    lines.append("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    total_amount INTEGER NOT NULL,
    payment_method TEXT DEFAULT 'cash',
    status TEXT DEFAULT 'completed',
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
""")
    
    cursor.execute("SELECT * FROM orders ORDER BY id")
    orders = cursor.fetchall()
    
    for o in orders:
        customer_id = str(o['customer_id']) if o['customer_id'] else 'NULL'
        lines.append(f"INSERT INTO orders VALUES ({o['id']}, '{o['order_number']}', {customer_id}, {o['total_amount']}, '{o['payment_method']}', '{o['status']}', {o['created_by'] or 1}, '{o['created_at']}');")
    
    lines.append("")
    
    # 4. Bảng order_items
    lines.append("-- ========== ORDER ITEMS ==========")
    lines.append("DROP TABLE IF EXISTS order_items;")
    lines.append("""
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
""")
    
    cursor.execute("SELECT * FROM order_items ORDER BY id")
    items = cursor.fetchall()
    
    for item in items:
        lines.append(f"INSERT INTO order_items VALUES ({item['id']}, {item['order_id']}, {item['product_id']}, {item['quantity']}, {item['price']});")
    
    lines.append("")
    
    # 5. Thống kê
    lines.append("-- ========== STATISTICS ==========")
    
    cursor.execute("SELECT COUNT(*) as count FROM products")
    total_products = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM customers")
    total_customers = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(total_amount) as total FROM orders WHERE status='completed'")
    total_revenue = cursor.fetchone()['total'] or 0
    
    lines.append(f"-- Tổng sản phẩm: {total_products}")
    lines.append(f"-- Tổng khách hàng: {total_customers}")
    lines.append(f"-- Tổng đơn hàng: {total_orders}")
    lines.append(f"-- Tổng doanh thu: {total_revenue:,.0f} VNĐ")
    
    lines.append("")
    lines.append("COMMIT;")
    
    conn.close()
    
    # Tạo file backup
    content = "\n".join(lines)
    filename = f"backup_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    return content, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': f'attachment; filename={filename}'
    }

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
