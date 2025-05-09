from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace later

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

@app.route('/market')
def market():
    if 'user_id' not in session:
        flash('Please log in to view the market.', 'error')
        return redirect('/login')
    stocks = Stock.query.all()
    return render_template('market.html', stocks=stocks)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Add fake stocks if none exist
        if not Stock.query.first():
            stocks = [
                Stock(ticker='AAPL', name='Apple Inc.', sector='Tech', current_price=150.00),
                Stock(ticker='TSLA', name='Tesla Inc.', sector='Auto', current_price=700.00),
                Stock(ticker='GOOGL', name='Google', sector='Tech', current_price=2500.00)
            ]
            db.session.add_all(stocks)
            db.session.commit()
    app.run(debug=True)