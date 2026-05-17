from flask import Flask, render_template,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin,login_user,login_required,logout_user
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime
from flask_login import login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moneylog.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = generate_password_hash(password)
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return 'Account created! Now go to /login'
    return render_template('register.html')   

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return 'Logged in successfully! Welcome to MoneyLog'
        return 'Invalid username or password'
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    category_filter = request.args.get('category')
    if category_filter:
        expenses = Expense.query.filter_by(user_id=current_user.id).filter(Expense.category.ilike(category_filter)).all()
    else:
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', expenses=expenses, current_filter=category_filter)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    amount = request.form['amount']
    description = request.form['description']
    category = request.form['category']
    
    new_expense = Expense(
        amount=amount,
        description=description,
        category=category,
        user_id=current_user.id
    )
    db.session.add(new_expense)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)