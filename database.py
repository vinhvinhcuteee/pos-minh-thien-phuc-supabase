import os
from supabase import create_client, Client
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.client: Client = None
        self.connect()

    def connect(self):
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            print("=" * 50)
            print("ĐANG KẾT NỐI SUPABASE...")
            print("=" * 50)
            
            if not supabase_url or not supabase_key:
                print("❌ LỖI: Thiếu SUPABASE_URL hoặc SUPABASE_KEY!")
                return
            
            print(f"📡 URL: {supabase_url}")
            self.client = create_client(supabase_url, supabase_key)
            print("✅ KẾT NỐI SUPABASE THÀNH CÔNG!")
            
            # Kiểm tra kết nối
            result = self.client.table('products').select('*', count='exact').limit(1).execute()
            print(f"✅ Kiểm tra thành công! (products table exists)")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ LỖI: {e}")

    # ==================== SẢN PHẨM ====================
    def get_all_products(self):
        try:
            result = self.client.table('products').select('*').order('id', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Lỗi get_all_products: {e}")
            return []

    def add_product(self, data):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO products (name, price, cost_price, stock, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['name'], data['price'], data.get('cost_price', 0), 
                  data.get('stock', 0), data.get('category', '')))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Lỗi add_product: {e}")
            self.conn.rollback()
            return None

    def update_product(self, product_id, data):
        try:
            self.client.table('products').update(data).eq('id', product_id).execute()
            return True
        except Exception as e:
            print(f"Lỗi update_product: {e}")
            return False

    def delete_product(self, product_id):
        try:
            self.client.table('products').delete().eq('id', product_id).execute()
            return True
        except Exception as e:
            print(f"Lỗi delete_product: {e}")
            return False

    # ==================== KHÁCH HÀNG ====================
    def get_all_customers(self):
        try:
            result = self.client.table('customers').select('*').order('total_spent', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Lỗi get_all_customers: {e}")
            return []

    def add_customer(self, data):
        try:
            result = self.client.table('customers').insert(data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"Lỗi add_customer: {e}")
            return None

    def update_customer(self, customer_id, data):
        try:
            self.client.table('customers').update(data).eq('id', customer_id).execute()
            return True
        except Exception as e:
            print(f"Lỗi update_customer: {e}")
            return False

    def delete_customer(self, customer_id):
        try:
            # Kiểm tra xem khách hàng có đơn hàng không
            orders = self.client.table('orders').select('id', count='exact').eq('customer_id', customer_id).execute()
            if orders.count and orders.count > 0:
                return False, "Khách hàng có đơn hàng, không thể xóa"
            
            self.client.table('customers').delete().eq('id', customer_id).execute()
            return True, ""
        except Exception as e:
            return False, str(e)

    def get_customer_history(self, customer_id):
        try:
            result = self.client.table('orders')\
                .select('*, order_items(*, products(name))')\
                .eq('customer_id', customer_id)\
                .order('created_at', desc=True)\
                .execute()
            
            history = []
            for order in result.data:
                for item in order.get('order_items', []):
                    history.append({
                        'order_id': order['id'],
                        'order_number': order['order_number'],
                        'total_amount': order['total_amount'],
                        'created_at': order['created_at'],
                        'payment_method': order['payment_method'],
                        'product_name': item.get('products', {}).get('name', ''),
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'price': item['price']
                    })
            return history
        except Exception as e:
            print(f"Lỗi get_customer_history: {e}")
            return []

    # ==================== ĐƠN HÀNG ====================
    def get_all_orders(self):
        try:
            result = self.client.table('orders')\
                .select('*, customers(name)')\
                .order('created_at', desc=True)\
                .limit(50)\
                .execute()
            
            orders = []
            for order in result.data:
                orders.append({
                    'id': order['id'],
                    'order_number': order['order_number'],
                    'customer_id': order.get('customer_id'),
                    'customer_name': order.get('customers', {}).get('name', 'Khách lẻ'),
                    'total_amount': order['total_amount'],
                    'payment_method': order['payment_method'],
                    'status': order['status'],
                    'created_by': order.get('created_by', 1),
                    'created_at': order['created_at']
                })
            return orders
        except Exception as e:
            print(f"Lỗi get_all_orders: {e}")
            return []

    def create_order(self, order_data, items):
        try:
            # Tạo đơn hàng
            result = self.client.table('orders').insert(order_data).execute()
            if not result.data:
                return None, "Không thể tạo đơn hàng"
            
            order_id = result.data[0]['id']
            
            # Thêm chi tiết đơn hàng
            for item in items:
                self.client.table('order_items').insert({
                    'order_id': order_id,
                    'product_id': item['id'],
                    'quantity': item['quantity'],
                    'price': item['price']
                }).execute()
                
                # Cập nhật tồn kho
                product = self.client.table('products').select('stock').eq('id', item['id']).execute()
                if product.data:
                    new_stock = product.data[0]['stock'] - item['quantity']
                    self.client.table('products').update({'stock': new_stock}).eq('id', item['id']).execute()
            
            # Cập nhật tổng chi tiêu khách hàng
            if order_data.get('customer_id'):
                customer = self.client.table('customers').select('total_spent').eq('id', order_data['customer_id']).execute()
                if customer.data:
                    new_total = customer.data[0]['total_spent'] + order_data['total_amount']
                    self.client.table('customers').update({
                        'total_spent': new_total,
                        'last_purchase': datetime.now().isoformat()
                    }).eq('id', order_data['customer_id']).execute()
            
            return order_id, None
        except Exception as e:
            print(f"Lỗi create_order: {e}")
            return None, str(e)

    # ==================== HÓA ĐƠN (THÊM MỚI) ====================
    def get_invoices(self, filter_type='all', start_date=None, end_date=None):
        """Lấy danh sách hóa đơn"""
        try:
            query = self.client.table('orders')\
                .select('*, order_items(*, products(name))')\
                .eq('status', 'completed')\
                .order('created_at', desc=True)
            
            if filter_type == 'today':
                today = datetime.now().date().isoformat()
                query = query.gte('created_at', today)
            elif filter_type == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
                query = query.gte('created_at', week_ago)
            elif filter_type == 'month':
                month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
                query = query.gte('created_at', month_ago)
            
            if start_date:
                query = query.gte('created_at', start_date)
            if end_date:
                query = query.lte('created_at', end_date)
            
            result = query.execute()
            
            invoices = []
            for order in result.data:
                for item in order.get('order_items', []):
                    invoices.append({
                        'order_number': order['order_number'],
                        'created_at': order['created_at'],
                        'product_name': item.get('products', {}).get('name', ''),
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'subtotal': item['quantity'] * item['price'],
                        'total_amount': order['total_amount']
                    })
            return invoices
        except Exception as e:
            print(f"Lỗi get_invoices: {e}")
            return []

    def delete_invoice(self, order_number):
        """Xóa hóa đơn theo mã đơn hàng"""
        try:
            # Lấy thông tin đơn hàng
            order_result = self.client.table('orders').select('id, customer_id, total_amount').eq('order_number', order_number).execute()
            if not order_result.data:
                return False, "Không tìm thấy đơn hàng"
            
            order = order_result.data[0]
            order_id = order['id']
            
            # Lấy danh sách sản phẩm trong đơn hàng
            items_result = self.client.table('order_items').select('product_id, quantity').eq('order_id', order_id).execute()
            
            # Hoàn lại số lượng tồn kho
            for item in items_result.data:
                product = self.client.table('products').select('stock').eq('id', item['product_id']).execute()
                if product.data:
                    new_stock = product.data[0]['stock'] + item['quantity']
                    self.client.table('products').update({'stock': new_stock}).eq('id', item['product_id']).execute()
            
            # Trừ total_spent của khách hàng
            if order.get('customer_id'):
                customer = self.client.table('customers').select('total_spent').eq('id', order['customer_id']).execute()
                if customer.data:
                    new_total = customer.data[0]['total_spent'] - order['total_amount']
                    self.client.table('customers').update({'total_spent': max(0, new_total)}).eq('id', order['customer_id']).execute()
            
            # Xóa order_items trước
            self.client.table('order_items').delete().eq('order_id', order_id).execute()
            
            # Xóa orders
            self.client.table('orders').delete().eq('id', order_id).execute()
            
            return True, "Xóa thành công"
        except Exception as e:
            print(f"Lỗi delete_invoice: {e}")
            return False, str(e)
    
    def get_order_by_number(self, order_number):
        """Lấy thông tin đơn hàng theo mã"""
        try:
            result = self.client.table('orders')\
                .select('*, customers(name)')\
                .eq('order_number', order_number)\
                .execute()
            
            if result.data:
                order = result.data[0]
                return {
                    'id': order['id'],
                    'order_number': order['order_number'],
                    'customer_id': order.get('customer_id'),
                    'customer_name': order.get('customers', {}).get('name', 'Khách lẻ'),
                    'total_amount': order['total_amount'],
                    'payment_method': order['payment_method'],
                    'status': order['status'],
                    'created_at': order['created_at']
                }
            return None
        except Exception as e:
            print(f"Lỗi get_order_by_number: {e}")
            return None

    # ==================== THỐNG KÊ (SỬA LẠI) ====================
    def get_stats(self):
        """Lấy thống kê tổng quan"""
        try:
            # Tổng số
            products_count = self.client.table('products').select('id', count='exact').execute().count or 0
            customers_count = self.client.table('customers').select('id', count='exact').execute().count or 0
            orders_count = self.client.table('orders').select('id', count='exact').eq('status', 'completed').execute().count or 0
            
            # Doanh thu hôm nay
            today = datetime.now().date().isoformat()
            today_orders = self.client.table('orders').select('total_amount').eq('status', 'completed').gte('created_at', today).execute()
            today_revenue = sum(o['total_amount'] for o in today_orders.data)
            
            # Doanh thu tháng này
            first_day = datetime.now().replace(day=1).date().isoformat()
            month_orders = self.client.table('orders').select('total_amount').eq('status', 'completed').gte('created_at', first_day).execute()
            month_revenue = sum(o['total_amount'] for o in month_orders.data)
            
            # Top 5 sản phẩm bán chạy
            items_result = self.client.table('order_items').select('product_id, quantity, products(name)').execute()
            
            product_sales = {}
            for item in items_result.data:
                product_name = item.get('products', {}).get('name', 'Unknown')
                product_sales[product_name] = product_sales.get(product_name, 0) + item['quantity']
            
            top_products = [{'name': k, 'total_sold': v} for k, v in sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]]
            
            # Tính lợi nhuận
            profit_data = self.client.table('order_items')\
                .select('quantity, price, products(cost_price)')\
                .execute()
            
            profit = 0
            for item in profit_data.data:
                cost = item.get('products', {}).get('cost_price', 0) if item.get('products') else 0
                profit += item['quantity'] * (item['price'] - cost)
            
            profit_margin = (profit / month_revenue * 100) if month_revenue > 0 else 0
            
            return {
                'total_products': products_count,
                'total_customers': customers_count,
                'total_orders': orders_count,
                'today_revenue': today_revenue,
                'month_revenue': month_revenue,
                'profit': profit,
                'profit_margin': profit_margin,
                'top_products': top_products
            }
        except Exception as e:
            print(f"Lỗi get_stats: {e}")
            return {
                'total_products': 0, 'total_customers': 0, 'total_orders': 0,
                'today_revenue': 0, 'month_revenue': 0, 'profit': 0, 'profit_margin': 0, 'top_products': []
            }

    def close(self):
        """Supabase không cần đóng kết nối"""
        pass
