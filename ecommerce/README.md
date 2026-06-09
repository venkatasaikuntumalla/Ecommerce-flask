# 🛒 ShopZone – Flask E-Commerce Website

A fully functional e-commerce web application built with **Python Flask**, featuring product browsing, shopping cart, user authentication, order management, and an admin panel.

---

## 📁 Project Structure

```
ecommerce/
├── app.py                  ← Main Flask application (routes, models, logic)
├── requirements.txt        ← Python dependencies
├── instance/
│   └── ecommerce.db        ← SQLite database (auto-created on first run)
├── static/
│   ├── css/
│   │   └── style.css       ← Custom styles
│   └── js/
│       └── main.js         ← Frontend interactions
└── templates/
    ├── base.html           ← Base layout (navbar, footer, flash messages)
    ├── index.html          ← Home page (hero, featured products)
    ├── products.html       ← Product listing with filters
    ├── product_detail.html ← Single product view
    ├── cart.html           ← Shopping cart
    ├── checkout.html       ← Checkout form
    ├── order_success.html  ← Order confirmation
    ├── login.html          ← User login
    ├── register.html       ← User registration
    ├── profile.html        ← User profile & order history
    └── admin/
        ├── dashboard.html  ← Admin stats & overview
        ├── products.html   ← Add/delete products
        └── orders.html     ← Manage order statuses
```

---

## 🚀 How to Run

### Step 1 – Clone / Download the project
Place the `ecommerce/` folder wherever you like.

### Step 2 – Create a virtual environment (recommended)
```bash
cd ecommerce
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 3 – Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 – Run the app
```bash
python app.py
```

### Step 5 – Open in browser
```
http://127.0.0.1:5000
```

The database is created automatically with sample products and categories on first launch.

---

## 🔐 Default Credentials

| Role  | Email             | Password  |
|-------|-------------------|-----------|
| Admin | admin@shop.com    | admin123  |
| User  | Register yourself | your choice |

---

## ✨ Features

### 👤 Customer Features
- **Home Page** – Hero banner, category grid, featured products, feature highlights
- **Product Browsing** – Filter by category, search by name
- **Product Detail** – Full description, stock status, related products
- **Shopping Cart** – Add/update/remove items, live total, shipping calculator
- **Checkout** – Address form, order summary (demo payment)
- **Order Confirmation** – Success page with order ID
- **User Profile** – View account info and complete order history
- **Authentication** – Register, Login, Logout with password hashing

### 🛠️ Admin Features
- **Dashboard** – Stats cards (users, products, orders, revenue), recent orders table
- **Product Management** – Add products with name/price/stock/image/category, delete products
- **Order Management** – View all orders with customer details, update order status

### 🎨 UI/UX
- Fully responsive (mobile-first, Bootstrap 5)
- Sticky navbar with live cart badge counter
- Product hover effects with quick-view overlay
- Auto-dismissing flash notifications
- Professional gradient hero section
- Clean card-based layouts throughout

---

## 🗄️ Database Models

| Model      | Fields                                                |
|------------|-------------------------------------------------------|
| User       | id, name, email, password (hashed), is_admin          |
| Category   | id, name                                              |
| Product    | id, name, description, price, stock, image_url, category_id |
| Order      | id, user_id, total, status, address, created_at       |
| OrderItem  | id, order_id, product_id, quantity, price             |

---

## 🛠 Tech Stack

| Layer     | Technology                    |
|-----------|-------------------------------|
| Backend   | Python, Flask                 |
| Database  | SQLite + Flask-SQLAlchemy ORM |
| Auth      | Werkzeug password hashing     |
| Frontend  | Jinja2, Bootstrap 5, Font Awesome |
| Sessions  | Flask sessions (server-side)  |

---

## 📌 Notes
- This is a **demo project** — the payment form is disabled by design (no real charges).
- To reset the database, delete `instance/ecommerce.db` and restart the app.
- For production, switch `SECRET_KEY` to a secure random string and use PostgreSQL.
