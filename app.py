from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
from datetime import datetime
import MySQLdb.cursors
import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = '12345'  # Use a strong secret key in production

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'user_authen'

mysql = MySQL(app)

@app.route('/')
def index():
    return redirect('/signup')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
            mysql.connection.commit()
            return redirect('/signin')  # Redirect after successful signup
        except MySQLdb.IntegrityError:
            return 'Email already exists!'
        finally:
            cursor.close()
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['user_name'] = user[1]  # Store user's name in session
            session['email'] = user[2]      # Store email in session
            return redirect('/home')        # Redirect to home page
        else:
            return "Invalid email or password."

    return render_template('signin.html')

@app.route('/home')
def home():
    if 'user_name' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Return dicts
        cursor.execute("SELECT id, name, description, image_path, daily_charge FROM items")
        items = cursor.fetchall()
        cursor.close()
        return render_template('home.html', user_name=session['user_name'], items=items)
    else:
        return redirect('/signin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/signin')

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        item_name = request.form['name']
        description = request.form['description']
        daily_charge = request.form['daily_charge']

        if 'image' not in request.files:
            return "No image part in the request", 400

        image = request.files['image']
        if image.filename == '':
            return "No selected file", 400

        filename = secure_filename(image.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        image_path = f"uploads/{unique_filename}"

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO items (name, description, image_path, daily_charge, owner_email) VALUES (%s, %s, %s, %s, %s)",
            (item_name, description, image_path, daily_charge, session['email'])
        )
        mysql.connection.commit()
        cursor.close()

        return redirect('/home')

    return render_template('add_item.html')

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()

    if item:
        return render_template('item_detail.html', item=item)
    else:
        return "Item not found", 404

@app.route('/order/<int:item_id>')
def order_page(item_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()

    if item:
        return render_template('order.html', item=item)
    else:
        return "Item not found", 404

@app.route('/place_order/<int:item_id>', methods=['POST'])
def place_order(item_id):
    name = request.form['name']
    address = request.form['address']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    rent_amount = request.form['rent_amount']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    if not item:
        cursor.close()
        return "Item not found", 404

    item_name = item[0]

    cursor.execute("""
        INSERT INTO orders (item_id, item_name, user_name, address, start_date, end_date, rent_amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        item_id,
        item_name,
        name,
        address,
        start_date,
        end_date,
        rent_amount
    ))
    mysql.connection.commit()
    cursor.close()

    return render_template('adhar.html')


@app.route('/adhar', methods=['GET', 'POST'])
def adhar():
    if request.method == 'POST':
        image = request.files['aadhar_image']
        aadhar_id = request.form['aadhar_id']

        if image.filename == '':
            return "No image selected", 400

        filename = secure_filename(image.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        image_path = f"uploads/{unique_filename}"

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO aadhar_data (aadhar_id, image_path) VALUES (%s, %s)", (aadhar_id, image_path))
        mysql.connection.commit()
        cursor.close()

        return render_template('description.html')
    return render_template('description.html')

@app.route('/description')
def description():
    return render_template('description.html')

@app.route('/category/tools')
def tools():
    return render_template('tools.html')

@app.route('/category/electronics')
def electronics():
    return render_template('electronics.html')

@app.route('/category/vehicles')
def vehicles():
    return render_template('vehicles.html')

@app.route('/category/party_supplies')
def party_supplies():
    return render_template('party_supplies.html')

@app.route('/order_status')
def order_status():
    return render_template('order_status.html')


if __name__ == '__main__':
    app.run(debug=True)
