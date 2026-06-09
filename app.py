from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────── MODELS ───────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(300), default='https://via.placeholder.com/400x300?text=Product')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')

# ─────────────── HELPERS ───────────────

def get_cart():
    return session.get('cart', {})

def cart_count():
    cart = get_cart()
    return sum(item['quantity'] for item in cart.values())

def cart_total():
    cart = get_cart()
    return sum(item['price'] * item['quantity'] for item in cart.values())

app.jinja_env.globals.update(cart_count=cart_count, cart_total=cart_total)

# ─────────────── ROUTES ───────────────

@app.route('/')
def index():
    featured = Product.query.filter(Product.stock > 0).order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.all()
    return render_template('index.html', products=featured, categories=categories)

@app.route('/products')
def products():
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    query = Product.query.filter(Product.stock > 0)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    products = query.all()
    categories = Category.query.all()
    return render_template('products.html', products=products, categories=categories,
                           selected_category=category_id, search=search)

@app.route('/product/<int:pid>')
def product_detail(pid):
    product = Product.query.get_or_404(pid)
    related = Product.query.filter(Product.category_id == product.category_id,
                                   Product.id != product.id).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)

# Cart
@app.route('/cart')
def cart():
    cart = get_cart()
    items = []
    for pid, item in cart.items():
        product = Product.query.get(int(pid))
        if product:
            items.append({'product': product, 'quantity': item['quantity'],
                          'subtotal': item['price'] * item['quantity']})
    return render_template('cart.html', items=items, total=cart_total())

@app.route('/cart/add/<int:pid>', methods=['POST'])
def add_to_cart(pid):
    product = Product.query.get_or_404(pid)
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    key = str(pid)
    if key in cart:
        cart[key]['quantity'] += qty
    else:
        cart[key] = {'name': product.name, 'price': product.price, 'quantity': qty,
                     'image': product.image_url}
    session['cart'] = cart
    flash(f'"{product.name}" added to cart!', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/update/<int:pid>', methods=['POST'])
def update_cart(pid):
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    key = str(pid)
    if qty <= 0:
        cart.pop(key, None)
    elif key in cart:
        cart[key]['quantity'] = qty
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:pid>')
def remove_from_cart(pid):
    cart = session.get('cart', {})
    cart.pop(str(pid), None)
    session['cart'] = cart
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

# Checkout
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout.', 'warning')
        return redirect(url_for('login'))
    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))
    if request.method == 'POST':
        address = request.form.get('address')
        order = Order(user_id=session['user_id'], total=cart_total(), address=address)
        db.session.add(order)
        db.session.flush()
        for pid, item in cart.items():
            oi = OrderItem(order_id=order.id, product_id=int(pid),
                           quantity=item['quantity'], price=item['price'])
            db.session.add(oi)
            p = Product.query.get(int(pid))
            if p:
                p.stock = max(0, p.stock - item['quantity'])
        db.session.commit()
        session['cart'] = {}
        flash(f'Order #{order.id} placed successfully!', 'success')
        return redirect(url_for('order_success', oid=order.id))
    return render_template('checkout.html', total=cart_total(), cart=cart)

@app.route('/order/success/<int:oid>')
def order_success(oid):
    order = Order.query.get_or_404(oid)
    return render_template('order_success.html', order=order)

# Auth
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        user = User(name=name, email=email,
                    password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_admin'] = user.is_admin
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return render_template('profile.html', user=user, orders=orders)

# Admin
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required.', 'danger')
        return redirect(url_for('index'))
    stats = {
        'users': User.query.count(),
        'products': Product.query.count(),
        'orders': Order.query.count(),
        'revenue': db.session.query(db.func.sum(Order.total)).scalar() or 0
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, orders=recent_orders)

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        p = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            image_url=request.form.get('image_url') or 'https://via.placeholder.com/400x300?text=Product',
            category_id=int(request.form['category_id']) if request.form.get('category_id') else None
        )
        db.session.add(p)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('admin_products'))
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/products/delete/<int:pid>')
def delete_product(pid):
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
def admin_orders():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/update/<int:oid>', methods=['POST'])
def update_order_status(oid):
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    order = Order.query.get_or_404(oid)
    order.status = request.form['status']
    db.session.commit()
    flash('Order status updated.', 'success')
    return redirect(url_for('admin_orders'))

# ─────────────── SEED DATA ───────────────

def seed_data():
    if Category.query.count() == 0:
        cats = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports']
        for c in cats:
            db.session.add(Category(name=c))
        db.session.commit()

    if Product.query.count() == 0:
        products = [
            ('Wireless Headphones', 'Premium sound quality with noise cancellation. 30hr battery life.', 89.99, 50, 1,
             'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop'),
            ('Mechanical Keyboard', 'RGB backlit mechanical keyboard with Cherry MX switches.', 129.99, 30, 1,
             'https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=400&h=300&fit=crop'),
            ('Smart Watch', 'Track fitness, notifications, heart rate and more.', 199.99, 25, 1,
             'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop'),
            ('Classic T-Shirt', '100% cotton premium quality t-shirt. Available in all sizes.', 24.99, 100, 2,
             'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=300&fit=crop'),
            ('Running Shoes', 'Lightweight and breathable running shoes for all terrains.', 79.99, 40, 5,
             'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=300&fit=crop'),
            ('Python Programming', 'Complete guide to Python from beginner to advanced.', 39.99, 60, 3,
             'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&h=300&fit=crop'),
            ('Indoor Plant Pot', 'Modern ceramic pot perfect for indoor plants.', 19.99, 80, 4,
             'https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=400&h=300&fit=crop'),
            ('Yoga Mat', 'Non-slip eco-friendly yoga mat with carry strap.', 34.99, 45, 5,
             'https://images.unsplash.com/photo-1592432678016-e910b452f9a2?w=400&h=300&fit=crop'),
        ]
        for name, desc, price, stock, cat_id, img in products:
            db.session.add(Product(name=name, description=desc, price=price,
                                   stock=stock, category_id=cat_id, image_url=img))
        db.session.commit()

    if not User.query.filter_by(email='admin@shop.com').first():
        admin = User(name='Admin', email='admin@shop.com',
                     password=generate_password_hash('admin123'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)
