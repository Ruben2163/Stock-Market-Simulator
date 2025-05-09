from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    cash = db.Column(db.Float, default=10000.0)
    email = db.Column(db.String(120), unique=True, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Stock {self.ticker}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    stock = db.relationship('Stock', backref='transactions')  # Add this line

    def __repr__(self):
        return f'<Transaction {self.user_id} {self.stock_id}>'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email'] or None

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect('/signup')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password, email=email)
        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect('/market')
        else:
            flash('Invalid username or password.', 'error')
            return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect('/')

@app.route('/market', methods=['GET', 'POST'])
def market():
    if 'user_id' not in session:
        flash('Please log in to view the market.', 'error')
        return redirect('/login')
    user = User.query.get(session['user_id'])
    stocks = Stock.query.all()

    if request.method == 'POST':
        stock_id = request.form['stock_id']
        quantity = int(request.form['quantity'])
        stock = Stock.query.get(stock_id)

        total_cost = stock.current_price * quantity
        if user.cash < total_cost:
            flash('Not enough cash!', 'error')
        else:
            user.cash -= total_cost
            transaction = Transaction(
                user_id=user.id,
                stock_id=stock.id,
                quantity=quantity,
                price=stock.current_price
            )
            db.session.add(transaction)
            db.session.commit()
            flash(f'Bought {quantity} shares of {stock.ticker}!', 'success')

        return redirect('/market')

    return render_template('market.html', stocks=stocks, user=user)

@app.route('/portfolio')
def portfolio():
    if 'user_id' not in session:
        flash('Please log in to view your portfolio.', 'error')
        return redirect('/login')
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    return render_template('portfolio.html', transactions=transactions, user=user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Stock.query.first():
            stocks = [
                Stock(ticker='AAPL', name='Apple Inc.', sector='Tech', current_price=150.00),
                Stock(ticker='TSLA', name='Tesla Inc.', sector='Auto', current_price=700.00),
                Stock(ticker='GOOGL', name='Google', sector='Tech', current_price=2500.00)
            ]
            db.session.add_all(stocks)
            db.session.commit()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    app.run(debug=True)
