import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from models import Customer
from werkzeug.security import check_password_hash

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        email_or_username = request.form['email']
        password = request.form['password']
        
        error = None
        
        # Check if email or username
        if '@' in email_or_username:
            user = Customer.query.filter_by(email=email_or_username).first()
        else:
            user = Customer.query.filter_by(username=email_or_username).first()
        
        if user is None:
            error = 'Invalid email/username or password.'
        elif not user.check_password(password):
            error = 'Invalid email/username or password.'
        
        if error is None:
            # Successfully logged in
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            
            logger.info(f"User {user.username} logged in successfully")
            
            return redirect(url_for('main_bp.dashboard'))
        
        logger.warning(f"Failed login attempt for {email_or_username}")
        
        flash(error, 'danger')
        return render_template('login.html', error=error)
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        company = request.form.get('company', '')
        
        error = None
        
        # Validate inputs
        if not username or not email or not password:
            error = 'All fields are required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif Customer.query.filter_by(username=username).first() is not None:
            error = f"User {username} is already registered."
        elif Customer.query.filter_by(email=email).first() is not None:
            error = f"Email {email} is already registered."
        
        if error is None:
            # Create new user
            new_user = Customer(username=username, email=email, company_name=company)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            
            # Automatically log in the user
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            
            flash('Registration successful! Welcome to Fractalyx.', 'success')
            return redirect(url_for('main_bp.dashboard'))
        
        flash(error, 'danger')
        return render_template('register.html', error=error)
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """User logout route"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))

# Decorator to require login for routes
def login_required(view):
    """Decorator to require login for routes"""
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth_bp.login'))
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view
