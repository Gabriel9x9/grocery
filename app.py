import io
import csv
import time
from flask import *
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_caching import Cache
from celery.schedules import crontab
from flask_cors import CORS
import sqlite3
from datetime import datetime
from flask_mail import Mail, Message
from flask import Flask, jsonify, request, session


app = Flask(__name__)
CORS(app)
jwt=JWTManager(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'google account-> security-> App passwords'
mail = Mail(app)

from celery import Celery
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
celery_app.conf.timezone = 'Asia/Kolkata'
celery_app.conf.broker_connection_retry = True
celery_app.autodiscover_tasks(['app'])

cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})

app.secret_key = 'random string'


@celery_app.task
def generate_products_csv():
    try:
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("SELECT p.name, p.price, p.stock AS remaining_quantity, COALESCE(SUM(o.quantity), 0) AS quantity_sold FROM products p LEFT JOIN orders o ON p.productId = o.productId GROUP BY p.productId")
            products = conn.fetchall()

            output = io.StringIO()
            csv_writer = csv.writer(output)
            csv_writer.writerow(['Product Name', 'Price', 'Remaining Quantity', 'Quantity Sold'])

            for product in products:
                csv_writer.writerow([product[0], product[1], product[2], product[3]])

            output.seek(0)
            return output.getvalue()

    except Exception as e:
        return str(e)

@celery_app.task
def alertInactiveUsers():
    with app.app_context():
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users LEFT JOIN orders ON users.userId = orders.userId WHERE orders.userId IS NULL;")
            inactive_users = cur.fetchall()

            if inactive_users:
                failed_emails = []
                for user in inactive_users:
                    try:
                        msg = Message(subject='Alert: Visit and Buy!',
                                      recipients=[user[2]],
                                      body='Dear User, We noticed you have not made any purchases recently. Visit our website and explore our latest products!')
                        mail.send(msg)
                        print(f"Email sent successfully to {user[2]}")
                    except Exception as e:
                        failed_emails.append(user[2])
                        print(f"Error sending email to {user[2]}: {e}")
                if failed_emails:
                    return {"message": f"Emails sent to inactive users. Failed emails: {failed_emails}"}
                else:
                    return {"message": "Emails sent to inactive users"}
            else:
                return {"message": "No inactive users found"}

@celery_app.task
def export_orders(user_email, userId, month, year):
    with app.app_context():
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("SELECT * FROM orders WHERE userId=? AND strftime('%Y-%m', date) = ?",
                        (userId, f"{year:04d}-{month:02d}"))
            monthlyActivity = conn.fetchall()

            html_table = "<table border='1'><tr><th>Product Name</th><th>Price</th><th>Quantity</th></tr>"
            total_expense = 0
            for order in monthlyActivity:
                html_table += f"<tr><td>{order[2]}</td><td>{order[3]}</td><td>{order[4]}</td></tr>"
                total_expense += float(order[3]) * float(order[4])
            html_table += "</table>"

            total_expense = round(total_expense, 2)

            html_table += f"<p>Total Expense: ₹ {total_expense}</p>"

            msg = Message(subject='Monthly Activity Report',
                        recipients=[user_email],
                        body='Please find the monthly activity report attached.',
                        html=html_table)

            try:
                mail.send(msg)
                return "Email sent successfully"
            except Exception as e:
                return str(e), 500

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=18, minute=30),
        alertInactiveUsers.s(),
        name='daily-6:30pm-task',
    )

@app.route("/export-products-csv", methods=['GET'])
def export_products_csv():
    task= celery_app.send_task('app.generate_products_csv')
    # task = generate_products_csv.delay()
    return jsonify({"task_id": task.id}), 200 if task else 500

@app.route("/export-products-csv/<task_id>", methods=['GET'])
def export_products_csv_result(task_id):
    result = celery_app.AsyncResult(task_id)
    if result.ready():
        if result.successful():
            csv_data = result.get()
            return csv_data
        else:
            error_message = result.get()
            return jsonify({"status": "error", "message": error_message}), 500
    else:
        return jsonify({"status": "pending", "message": "Task is still in progress"}), 202

@app.route("/alert-inactive-users", methods=['GET'])
def alert_inactive_users():
    task= celery_app.send_task('app.alertInactiveUsers')
    # task = alertInactiveUsers.apply_async(args=[app])
    return jsonify({"task_id": task.id}), 200 if task else 500

@app.route("/alert-inactive-users/<task_id>", methods=['GET'])
def alert_inactive_users_result(task_id):
    max_attempts = 10
    current_attempt = 0
    while current_attempt < max_attempts:
        task_result = celery_app.AsyncResult(task_id)

        if task_result.ready():
            if task_result.successful():
                return jsonify({"status": "Task completed successfully"}), 200
            else:
                return jsonify({"status": "Task failed"}), 500

        time.sleep(5)
        current_attempt += 1

    return jsonify({"status": "Task is still in progress"}), 202

@app.route("/initiate-export-orders", methods=['POST'])
def initiate_export_orders():
    user_email = request.json.get('email')
    userId = request.json.get('userId')
    selected_month = request.json.get('selectedMonth')

    month, year = map(int, selected_month.split('/'))

    task = celery_app.send_task('app.export_orders', args=[user_email, userId, month, year])

    return jsonify({"task_id": task.id}), 200

@app.route("/export-orders-status/<task_id>", methods=['GET'])
def export_orders_status(task_id):
    max_attempts = 10
    current_attempt = 0
    while current_attempt < max_attempts:
        task_result = celery_app.AsyncResult(task_id)
        if task_result.ready():
            if task_result.successful():
                return jsonify({"task_status": task_result.state}), 200
            
        time.sleep(5)
        current_attempt += 1

    return jsonify({"status": "Task is still in progress"}), 202

@app.route('/login')
def loginform():
    if request.args.get('email'):
        email = request.args.get('email')
        password = request.args.get('password')
        if valid(email,password):
            loggedIn, userRole= getLogindetails(email, password)
            session['loggedIn']=loggedIn
            session['userRole']=userRole
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token), 200
        else:
            return "login failed"
    else:
        return redirect('/')
    
def valid(email,password):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("select email, password from users where email='"+email+"'")
    user = cur.fetchall()
    try:
        for i in user:
            if email == i[0] and password == i[1]:
                return True
    except:
        return False

def getLogindetails(email, password):
    loggedIn = False
    userRole = ""

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT role FROM users WHERE email=? AND password=?", (email, password))
            result = cursor.fetchone()

            if result:
                loggedIn = True
                userRole = result[0]
        except sqlite3.Error as e:
            print("SQLite error:", e)
            
    return loggedIn, userRole

@app.route("/")
def root():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()        
        cur.execute('SELECT * FROM categories')            
        categoryData = cur.fetchall()
    return jsonify(categories=categoryData)

@app.route('/shop_by_category')
@cache.cached(timeout=60)
def category():
    categoryId= request.args.get('category_id')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE products.categoryId = ?", (categoryId,))
        products = cur.fetchall()
    return jsonify(products=products)

@app.route("/product/<int:productId>", methods=['GET', 'POST'])
# @cache.cached(timeout=60)
def product(productId):
    if request.method == "GET":
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("SELECT * FROM products WHERE productId=?", (productId,))
            product_info = conn.fetchone()
        return jsonify(product_info)

@app.route('/cart/<int:userId>', methods=['GET'])
# @cache.cached(timeout=60)
def cart(userId):
    if request.method == "GET":
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("SELECT * FROM kart WHERE userId=?", (userId,))
            product_info = conn.fetchall()
        return jsonify(product_info=product_info)
    
@app.route('/orders/<int:userId>', methods=['GET'])
# @cache.cached(timeout=60)
def orders(userId):
    if request.method == "GET":
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("SELECT * FROM orders WHERE userId=?", (userId,))
            orders = conn.fetchall()
        return jsonify(orders=orders)
    
@app.route('/cart/<int:userId>/<productId>', methods=['POST'])
def deleteProductFromCart(userId, productId):
    if request.method == "POST":
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("DELETE FROM kart WHERE userId=? and productId=?", (userId, productId,))
            c.commit()
            return "Product deleted successfully", 200

@app.route('/cart/<int:userId>', methods=['POST'])
def emptyUserCart(userId):
    if request.method == "POST":
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("DELETE FROM kart WHERE userId=?", (userId,))
            c.commit()
            return "cart empty successfully", 200

@app.route('/placeOrder/<int:userId>', methods=['POST'])
def place_order(userId):
    if request.method == 'POST':
        order_data = request.json
        products = order_data['products']

        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            for product in products:
                conn.execute("SELECT * FROM orders WHERE userId=? AND productId=?",
                             (userId, product['productId']))
                existing_product = conn.fetchone()

                if existing_product:
                    existing_order_date = datetime.strptime(existing_product[5], "%Y-%m-%d").date()
                    current_date = datetime.now().date()

                    if existing_order_date == current_date:
                        new_quantity = existing_product[4] + product['quantity']
                        conn.execute("UPDATE orders SET quantity=? WHERE userId=? AND name=? AND price=? AND date=?",
                                    (new_quantity, userId, product['productName'], product['price'], existing_product[5]))
                    else:
                        conn.execute("INSERT INTO orders(userId, name, price, quantity, date, productId) VALUES (?, ?, ?, ?, ?, ?)",
                                     (userId, product['productName'], product['price'], product['quantity'], current_date, product['productId']))
                else:
                    conn.execute("INSERT INTO orders(userId, name, price, quantity, date, productId) VALUES (?, ?, ?, ?, ?, ?)",
                                 (userId, product['productName'], product['price'], product['quantity'], datetime.now().date(), product['productId']))

            c.commit()
        return "Order placed successfully", 200

@app.route("/cart", methods=['POST'])
def addToCart():
    if request.method == 'POST':
        try:
            userId = request.form['userId']
            productId = request.form['productId']
            name = request.form['prod_name']
            price = request.form['prod_price']
            quantity = request.form['prod_quantity']

            with sqlite3.connect('database.db') as con:
                conn = con.cursor()
                conn.execute("INSERT INTO kart (userId, productId, name, price, quantity) VALUES (?, ?, ?, ?, ?)",
                             (userId, productId, name, price, quantity))
                con.commit()
                
                return jsonify(message='Product added to cart successfully'), 200
        except Exception as e:
            return jsonify(message='Something went wrong while adding the product to cart'), 500

@app.route('/user-idrole/<email>')
# @cache.cached(timeout=60)
def userIdAndRole(email):
    with sqlite3.connect('database.db') as con:
        cur = con.cursor()
        cur.execute('SELECT userId, role FROM users WHERE email=?', (email,))
        userIdRole = cur.fetchone()
    return jsonify(userIdRole=userIdRole)

@app.route('/change-role/<int:userId>/<string:userRole>', methods=['POST'])
@jwt_required()
def changeRole(userId, userRole):
        identity=get_jwt_identity()
    # if session.get('userRole') == 'admin':
        newRole = "manager" if userRole == "user" else "user"
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute('UPDATE users SET role=? WHERE userId=?', (newRole, userId,))
            con.commit()
        return jsonify(userRole=userRole)

@app.route('/users', methods=['GET','POST'])
@cache.cached(timeout=60)
@jwt_required()
def usersList():
    identity=get_jwt_identity()

    if request.method=='GET':
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
        return jsonify(users=users)
    
@app.route('/requests', methods=['GET','POST'])
@jwt_required()
def requests():
    identity=get_jwt_identity()
    # if session.get('userRole') == 'admin':
    if request.method=='GET':
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM requests")
            requests = cur.fetchall()
        return jsonify(requests=requests)

@app.route('/get-request/<int:request_id>')
def getRequest(request_id):
    # if session.get('userRole') == 'admin':
    try:
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM requests WHERE requestId=?", (request_id,))
            request_data = cur.fetchone()
            if request_data:
                return jsonify({
                    "requestId": request_data[0],
                    "requestType": request_data[1],
                    "categoryId": request_data[2],
                    "productId": request_data[3],
                    "oldName": request_data[4],
                    "name": request_data[5],
                    "price": request_data[6],
                    "image": request_data[7],
                    "mft": request_data[8],
                    "exp": request_data[9],
                    "stock": request_data[10],
                    "userName": request_data[11],
                    "userId": request_data[12]
                })
            else:
                return jsonify({"error": "Request data not found."}), 404
    except Exception as e:
        return f"Error fetching request data: {str(e)}", 500

@app.route('/post-approved-data', methods=['POST'])
def postApprovedData():
    # if session.get('userRole') == 'admin':
        if request.method == 'POST':
            try:
                data = request.get_json()

                if isinstance(data, dict):
                    with sqlite3.connect('database.db') as con:
                        cur = con.cursor()

                        productId=data.get('productId')
                        categoryId=data.get('categoryId')
                        name = data.get('name')
                        image = data.get('image')
                        price = data.get('price')
                        mft = data.get('mft')
                        exp = data.get('exp')
                        stock = data.get('stock')
                        requestType = data.get('requestType')
                        userName=data.get('userName')

                        if requestType.startswith('edit'):
                            if productId != 'null':
                                cur.execute("UPDATE products SET name=?, image=?, price=?, mft=?, exp=?, stock=? WHERE productId=?", (name, image, price, mft, exp, stock, productId))
                            if categoryId != 'null':
                                cur.execute("UPDATE categories SET name=?, image=? WHERE categoryId=?", (name, image, categoryId))
                        
                        if requestType.startswith('add category'):
                                cur.execute("INSERT INTO categories (image, name) VALUES (?, ?)", (image, name))
                        if requestType.startswith('add product'):
                                cur.execute("INSERT INTO products (name, image, price, mft, exp, stock, categoryId) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, image, price, mft, exp, stock, categoryId))

                        if requestType.startswith('delete category'):
                                cur.execute("DELETE FROM categories WHERE categoryId=?", (categoryId,))
                        if requestType.startswith('delete product'):
                                cur.execute("DELETE FROM products WHERE productId=?", (productId,))
                        
                        if requestType.startswith('manager role'):
                                cur.execute("UPDATE users SET role=? WHERE email=?", ('manager', userName))

                        con.commit()

                    return "200"
                else:
                    return "Invalid data format. Expected a dictionary."
            except Exception as e:
                return f"Error posting data to products table: {str(e)}", 500
        else:
            return "Method Not Allowed", 405

@app.route('/decline-request/<int:request_id>', methods=['POST'])
def decline_request(request_id):
    # if session.get('userRole') == 'admin':
        if request.method == 'POST':
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                try:
                    cur.execute("DELETE FROM requests WHERE requestId=?", (request_id,))
                    con.commit()
                    return "Request deleted successfully"
                except Exception as e:
                    con.rollback()
                    return f"Error deleting request: {str(e)}"
        else:
            return "Method Not Allowed"
    
@app.route('/delete-user/<int:userId>', methods=['POST'])
def deleteUser(userId):
    # if session.get('userRole') == 'admin':
        if request.method=='POST':
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("DELETE FROM users WHERE userId=?", (userId,))
                con.commit()
            return redirect('/')
        else:
            return  "DELETE API is not working"

@app.route('/search', methods=['GET', 'POST'])
# @cache.cached(timeout=60)
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        # search_type = request.form['search_type']

        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            # cur.execute("SELECT p.* FROM products p JOIN categories c ON p.categoryId = c.categoryId WHERE c.name LIKE ? OR p.name LIKE ? OR p.mft LIKE ? OR p.exp LIKE ? OR p.price LIKE ?", ('%' + search_query + '%','%' + search_query + '%','%' + search_query + '%','%' + search_query + '%','%' + search_query + '%'))
            cur.execute("SELECT p.* FROM products p WHERE p.name LIKE ? OR p.mft LIKE ? OR p.exp LIKE ? OR p.price LIKE ?", (search_query + '%', '%'+search_query + '%', '%' + search_query + '%', search_query + '%'))

            # if search_type == 'category':
            #     cur.execute("SELECT products.*, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.name LIKE ?", ('%' + search_query + '%',))
            # elif search_type == 'product':
                # cur.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + search_query + '%',))
            # elif search_type == 'price':
                # cur.execute("SELECT * FROM products WHERE price <= ?", (search_query,))
            # elif search_type == 'mft_date':
                # cur.execute("SELECT * FROM products WHERE mft LIKE ?", ('%' + search_query + '%',))
            
            search_results = cur.fetchall()
        
        return jsonify(search_results=search_results)
    return redirect('/')

    
@app.route('/add-category',methods=['POST','GET'])   
def addCategory():
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            image = request.form['category_img']
            name = request.form['category_name']
            a = "Insert into categories (image,name) values('{}','{}')".format(image,name)
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                try:                
                    cur.execute(a)
                    con.commit()
                    return redirect('/')
                except:
                    con.rollback()
                    return redirect('/')

@app.route('/delete-category/user=<userName>&role=<role>/<int:category_id>/<name>', methods=['POST'])
def deleteCategory(userName, role, category_id, name):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            if role == 'manager':
                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    try:
                        cur.execute("INSERT INTO requests (requestType, categoryId, userName, name) VALUES (?, ?, ?, ?)",
                                    ('delete category', category_id, userName, name))
                        con.commit()
                    except:
                        con.rollback()
                return redirect('/')
            else:

                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    try:
                        cur.execute("DELETE FROM categories WHERE categoryId=?", (category_id,))
                        con.commit()
                        return redirect('/')
                    except:
                        con.rollback()
                        return redirect('/')
        else:
            return "DELETE API is not working"
    
@app.route('/delete-product/user=<userName>&role=<role>/<int:product_id>/<name>', methods=['POST'])
def deleteProduct(product_id, userName, role, name):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            if role == 'manager':
                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    try:
                        cur.execute("INSERT INTO requests (requestType, productId, userName,name) VALUES (?, ?, ?, ?)",
                                    ('delete product', product_id, userName, name))
                        con.commit()
                    except:
                        con.rollback()
                return redirect('/')
            else:
                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    try:
                        cur.execute("DELETE FROM products WHERE productId=?", (product_id,))
                        con.commit()
                        return redirect('/')
                    except:
                        con.rollback()
                        return redirect('/')
        else:
            return  "DELETE API is not working"

@app.route('/edit-category/<int:category_id>', methods=['GET', 'POST'])
def editCategory(category_id):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            name = request.form['updateCategoryName']
            image = request.form['updateCategoryImage']

            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM categories WHERE categoryId=?",(category_id,))
                existing_category = cur.fetchone()

            if name=='': name=existing_category[1]
            if image=='': image=existing_category[2]
            
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("UPDATE categories SET name=?, image=? WHERE categoryId=?", (name, image, category_id))
                con.commit()
                return redirect('/')
        
@app.route('/edit-category-request/user=<userName>&role=<role>/<int:category_id>/<name>', methods=['GET', 'POST'])
def editCategoryRequest(category_id, userName, name, role):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            if role == 'manager':
                categoryName = request.form['updateCategoryName']
                image = request.form['updateCategoryImage']
                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO requests (requestType, categoryId, userName, oldName, name, image) VALUES (?, ?, ?, ?, ?, ?)",
                                        ('edit category', category_id, userName, name, categoryName, image))
                    con.commit()
                    return redirect('/')
            
@app.route('/add-category-request/user=<userName>&role=<role>', methods=['GET', 'POST'])
def addCategoryRequest(userName, role):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            if role == 'manager':
                image = request.form['category_img']
                name = request.form['category_name']

                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO requests (requestType, userName, name, image) VALUES (?, ?, ?, ?)",
                                        ('add category', userName, name, image))
                    con.commit()
                    return redirect('/')

@app.route('/add-product-request/user=<userName>&role=<role>', methods=['GET', 'POST'])
def addProductRequest(userName, role):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            if role == 'manager':
                name = request.form['product_name']
                price = request.form['product_price']
                image = request.form['product_img']
                mft = request.form['product_mft']
                exp = request.form['product_exp']
                stock = request.form['product_stock']
                categoryId = request.form['category_id']
                unit = request.form['unit']

                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO requests (requestType, categoryId, userName, name, image, price, mft, exp, stock, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                        ('add product', categoryId, userName, name, image, price, mft, exp, stock, unit))
                    con.commit()
                    return redirect('/')
                
@app.route('/add-product',methods=['POST','GET'])   
def addProduct():
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            name = request.form['product_name']
            price = request.form['product_price']
            image = request.form['product_img']
            mft = request.form['product_mft']
            exp = request.form['product_exp']
            stock = request.form['product_stock']
            categoryId = request.form['category_id']
            unit = request.form['unit']
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                try:                
                    cur.execute("INSERT INTO products (name, price, image, mft, exp, stock, categoryId, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (name, price, image, mft, exp, stock, categoryId, unit))
                    con.commit()
                    return redirect('/')
                except:
                    con.rollback()
                    return redirect('/')

@app.route('/edit-product-request/user=<userName>&role=<role>/<int:product_id>/<name>', methods=['GET', 'POST'])
def editProductRequest(product_id, userName, name, role):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            if role == 'manager':
                image = request.form['updateProductImage']
                productName = request.form['updateProductName']
                price = request.form['updatePrice']
                mft = request.form['updateManufacturingDate']
                exp = request.form['updateExpiryDate']
                stock = request.form['updateQuantity']
                unit = request.form['updateUnit']
                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO requests (requestType, productId, userName, oldName, name, image, price, mft, exp, stock, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                        ('edit product', product_id, userName, name, productName, image, price, mft, exp, stock, unit))
                    con.commit()
                    return redirect('/')
        
@app.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
def editProduct(product_id):
    # if session.get('userRole') == 'admin' or 'manager':
        if request.method == 'POST':
            image = request.form['updateProductImage']
            name = request.form['updateProductName']
            price = request.form['updatePrice']
            mft = request.form['updateManufacturingDate']
            exp = request.form['updateExpiryDate']
            stock = request.form['updateQuantity']
            unit = request.form['updateUnit']

            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM products WHERE productId=?", (product_id,))
                existing_data = cur.fetchone()

            if name == '': name=existing_data[1]
            if image == '': image=existing_data[3]
            if price == '': price=existing_data[2]
            if mft == '': mft=existing_data[4]
            if exp == '': exp=existing_data[5]
            if stock == '': stock=existing_data[6]
            if unit == '': unit=existing_data[8]

            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("UPDATE products SET name=?, image=?, price=?, mft=?, exp=?, stock=?, unit=? WHERE productId=?", (name, image, price, mft, exp, stock, unit, product_id))
                con.commit()
                return redirect('/')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if role in ['user', 'manager']:
            sql_query = "INSERT INTO users (password, email, firstname, lastName, role) VALUES (?, ?, ?, ?, ?)"
            values = (password, email, firstName, lastName, 'user')

            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                try:
                    cur.execute(sql_query, values)
                    con.commit()
                    
                    if role == 'manager':
                        cur.execute("INSERT INTO requests (requestType, userName) VALUES (?, ?)", ('manager role', email))
                        con.commit()

                    return redirect('/login')

                except sqlite3.Error as e:
                    con.rollback()
                    print("Database error:", e)

@app.route('/logout')
def logout():
    with sqlite3.connect('database.db') as con:
        cur = con.cursor()
        cur.execute('DELETE FROM kart')
        con.commit()
    
    if 'email' in session:
        session.pop('email')
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True,port=4000)