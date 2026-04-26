from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random
import uuid
from datetime import datetime
import re
import json
import os
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import DevelopmentConfig, ProductionConfig
from database import db

# Initialize Flask app with proper configuration
app = Flask(__name__)

# Load configuration
env = os.getenv('FLASK_ENV', 'development')
config = ProductionConfig if env == 'production' else DevelopmentConfig
app.config.from_object(config)

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize database on app creation
with app.app_context():
    db.create_all()

# Admin account
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@gmail.com')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD', 'admin123')  # Use env variable
GMAIL_PRICE = float(os.getenv('GMAIL_PRICE', '5.00'))
REFERRAL_PERCENTAGE = float(os.getenv('REFERRAL_PERCENTAGE', '10'))

# Google Sheets config
SHEETS_CREDENTIALS_FILE = os.getenv('SHEETS_CREDENTIALS_FILE', 'rugged-nucleus-494309-h6-1e1f8ffafa43.json')
SHEETS_SPREADSHEET_ID = os.getenv('SHEETS_SPREADSHEET_ID', '1Czkp_Yflqvd7zQMdZ6dUfAiD_wVexucfJz7ut8f-eVA')

def generate_referral_code():
    """Generate unique 5-digit referral code"""
    from database import User
    
    for _ in range(100):  # Try max 100 times to avoid infinite loop
        code = ''.join(random.choices(string.digits, k=5))
        if not User.query.filter_by(referral_code=code).first():
            return code
    
    # Fallback: use UUID if all attempts fail
    return str(uuid.uuid4())[:5]

# USA Names Lists
USA_FIRST_NAMES = [
    'James', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles', 'Christopher',
    'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth',
    'Kevin', 'Brian', 'George', 'Edward', 'Ronald', 'Timothy', 'Jason', 'Jeffrey', 'Ryan', 'Jacob',
    'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin',
    'Samuel', 'Frank', 'Gregory', 'Alexander', 'Raymond', 'Patrick', 'Jack', 'Dennis', 'Jerry', 'Tyler',
    'Mary', 'Patricia', 'Jennifer', 'Linda', 'Barbara', 'Elizabeth', 'Susan', 'Jessica', 'Sarah', 'Karen',
    'Nancy', 'Lisa', 'Betty', 'Margaret', 'Sandra', 'Ashley', 'Kimberly', 'Emily', 'Donna', 'Michelle',
    'Dorothy', 'Carol', 'Amanda', 'Melissa', 'Deborah', 'Stephanie', 'Rebecca', 'Sharon', 'Laura', 'Cynthia',
    'Kathleen', 'Amy', 'Angela', 'Shirley', 'Anna', 'Brenda', 'Pamela', 'Emma', 'Nicole', 'Helen'
]

USA_LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
    'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
    'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
    'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Peterson', 'Phillips', 'Campbell',
    'Parker', 'Evans', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy', 'Cook',
    'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Hunter', 'Hicks', 'Crawford', 'Henry',
    'Boyd', 'Mason', 'Moreno', 'Kennedy', 'Warren', 'Dixon', 'Ramos', 'Reeves', 'Burns', 'Gordon',
    'Shaw', 'Holmes', 'Rice', 'Robertson', 'Hunt', 'Black', 'Daniels', 'Palmer', 'Mills', 'Nicholson'
]

def generate_gmail_credentials():
    """Generate random Gmail credentials with USA names"""
    first_name = random.choice(USA_FIRST_NAMES)
    last_name = random.choice(USA_LAST_NAMES)
    name = f"{first_name} {last_name}"
    
    # Generate username based on name + 4 random digit/letter mix (lowercase only)
    random_suffix = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    username = f"{first_name.lower()}{last_name.lower()}{random_suffix}"
    
    # Generate strong password
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(12))
    
    return {
        'name': name,
        'username': username,
        'password': password
    }

def is_email_valid(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def find_user_by_email(email):
    """Find user by email from database"""
    from database import User
    try:
        user = User.query.filter_by(email=email.lower()).first()
        return user
    except Exception as e:
        print(f"Error querying user by email: {e}")
        return None

def find_user_by_id(user_id):
    """Find user by ID from database"""
    from database import User
    try:
        user = User.query.get(user_id)
        return user
    except Exception as e:
        print(f"Error querying user by ID: {e}")
        return None

def find_user_by_referral_code(code):
    """Find user by referral code from database"""
    from database import User
    try:
        user = User.query.filter_by(referral_code=code).first()
        return user
    except Exception as e:
        print(f"Error querying user by referral code: {e}")
        return None

# Google Sheets Integration
def get_sheets_service():
    """Initialize Google Sheets API service"""
    try:
        if not os.path.exists(SHEETS_CREDENTIALS_FILE):
            print(f"⚠️ Credentials file not found: {SHEETS_CREDENTIALS_FILE}")
            return None
        
        with open(SHEETS_CREDENTIALS_FILE) as f:
            creds_info = json.load(f)
        
        credentials = Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        print(f"✅ Google Sheets API connected: {creds_info.get('client_email')}")
        return service
    
    except FileNotFoundError:
        print(f"❌ Credentials file not found: {SHEETS_CREDENTIALS_FILE}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in credentials file")
        return None
    except Exception as e:
        print(f"❌ Error initializing Sheets service: {e}")
        return None

def save_gmail_to_google_sheet(gmail_account, user_email='', spreadsheet_id=None, sheet_name='Sheet1'):
    """Save Gmail account to Google Sheet"""
    if spreadsheet_id is None:
        spreadsheet_id = SHEETS_SPREADSHEET_ID
    
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'Google Sheets API unavailable'}
        
        # Prepare row data
        row = [
            gmail_account.get('name', ''),
            f"{gmail_account.get('username', '')}@gmail.com",
            gmail_account.get('password', ''),
            user_email
        ]
        
        # Check if headers exist
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1:D1'
            ).execute()
            
            if not result.get('values'):
                # Add headers if missing
                headers = [['NAME', 'GMAIL', 'PASSWORD', 'SENDER_EMAIL']]
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f'{sheet_name}!A1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
        except Exception as e:
            print(f"⚠️ Could not check/add headers: {e}")
        
        # Append the new row
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A:D',
            valueInputOption='RAW',
            body={'values': [row]}
        ).execute()
        
        return {'success': True, 'message': 'Account saved to Google Sheet'}
    
    except Exception as e:
        print(f"❌ Error saving to Google Sheet: {e}")
        return {'error': str(e)}

def import_gmail_from_sheets(spreadsheet_id=None, sheet_name='Sheet1', admin_user_id='admin'):
    """Import Gmail accounts from Google Sheets into database"""
    if spreadsheet_id is None:
        spreadsheet_id = SHEETS_SPREADSHEET_ID
    
    try:
        from database import GmailAccount, User
        
        service = get_sheets_service()
        if not service:
            return {'error': 'Google Sheets API unavailable'}
        
        # Read data from sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A:D'
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            return {'error': 'No data found in sheet'}
        
        # Skip header row
        data_rows = values[1:]
        imported_count = 0
        errors = []
        
        for idx, row in enumerate(data_rows, start=2):
            try:
                if len(row) < 3:
                    errors.append(f'Row {idx}: Missing columns')
                    continue
                
                name = row[0].strip() if row[0] else ''
                gmail_email = row[1].strip() if row[1] else ''
                password = row[2].strip() if row[2] else ''
                
                if not all([name, gmail_email, password]):
                    errors.append(f'Row {idx}: Missing required data')
                    continue
                
                # Extract username from email
                username = gmail_email.split('@')[0] if '@' in gmail_email else gmail_email
                
                # Check if account already exists
                existing = GmailAccount.query.filter_by(email=gmail_email).first()
                if existing:
                    errors.append(f'Row {idx}: Account already exists')
                    continue
                
                # Create account in database
                account = GmailAccount(
                    user_id=admin_user_id,
                    email=gmail_email,
                    password=password,
                    status='approved'
                )
                
                db.session.add(account)
                imported_count += 1
            
            except Exception as e:
                errors.append(f'Row {idx}: {str(e)[:50]}')
        
        db.session.commit()
        return {
            'success': True,
            'imported': imported_count,
            'total': len(data_rows),
            'errors': errors
        }
    
    except Exception as e:
        db.session.rollback()
        return {'error': f'Import failed: {str(e)}'}

def upload_gmail_to_sheets(gmail_account):
    """Upload single Gmail account to Google Sheets"""
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'Google Sheets API unavailable'}
        
        row = [
            gmail_account.get('name', ''),
            f"{gmail_account.get('username', '')}@gmail.com",
            gmail_account.get('password', ''),
            gmail_account.get('username', '')
        ]
        
        # Append to sheet
        service.spreadsheets().values().append(
            spreadsheetId=SHEETS_SPREADSHEET_ID,
            range='Sheet1!A:D',
            valueInputOption='RAW',
            body={'values': [row]}
        ).execute()
        
        return {'success': True}
    
    except Exception as e:
        print(f"⚠️ Warning: Could not save to Google Sheets: {e}")
        return {'error': str(e)}

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    from database import User, Earnings
    
    try:
        referral_code = request.args.get('ref', '').strip().upper()
        referrer = find_user_by_referral_code(referral_code) if referral_code else None
        referral_error = None if referral_code and referrer else ("Invalid referral code" if referral_code else None)
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            ref_code = request.form.get('referral_code', '').strip().upper()
            
            # Validation
            errors = []
            
            if not email or not is_email_valid(email):
                errors.append('Invalid email format')
            elif find_user_by_email(email):
                errors.append('Email already registered')
            
            if len(password) < 6:
                errors.append('Password must be at least 6 characters')
            elif password != confirm_password:
                errors.append('Passwords do not match')
            
            # Validate referral code
            referrer = find_user_by_referral_code(ref_code) if ref_code else None
            if ref_code and not referrer:
                errors.append('Invalid referral code')
            
            if errors:
                return render_template('register.html', errors=errors, email=email, 
                                     referral_code=ref_code, referral_error=referral_error)
            
            try:
                # Create new user
                new_user = User(
                    email=email.lower(),
                    password_hash=generate_password_hash(password),
                    name=email.split('@')[0],
                    referral_code=generate_referral_code(),
                    referred_by=referrer.id if referrer else None
                )
                
                db.session.add(new_user)
                db.session.flush()
                
                # Add ৳10 bonus to referrer
                if referrer:
                    bonus = Earnings(
                        user_id=referrer.id,
                        amount=10.0,
                        type='referral',
                        status='approved'
                    )
                    db.session.add(bonus)
                
                db.session.commit()
                return redirect(url_for('login'))
            
            except Exception as db_error:
                db.session.rollback()
                return render_template('register.html', 
                                     errors=[f"Error: {str(db_error)[:100]}"], 
                                     email=email)
        
        return render_template('register.html', referral_code=referral_code, 
                             referral_error=referral_error)
    
    except Exception as e:
        print(f"Register error: {e}")
        return render_template('register.html', errors=[f"Error: {str(e)[:100]}"]), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = find_user_by_email(email)
        
        if not user or not check_password_hash(user.password_hash, password):
            return render_template('login.html', error='Invalid email or password')
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session.modified = True
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))

def login_required(f):
    """Decorator to check if user is logged in"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to check if user is admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper functions for earnings calculation from database
def get_user_earnings(user_id):
    """Get all earnings for a user from database"""
    from database import Earnings
    earnings = Earnings.query.filter_by(user_id=user_id).all()
    pending = sum(e.amount for e in earnings if e.status == 'pending')
    approved = sum(e.amount for e in earnings if e.status == 'approved')
    withdrawn = sum(e.amount for e in earnings if e.status == 'withdrawn')
    return {
        'pending': pending,
        'approved': approved,
        'withdrawn': withdrawn,
        'total': pending + approved + withdrawn
    }

def get_referral_earnings(user_id):
    """Get referral earnings for a user from database"""
    from database import Earnings
    earnings = Earnings.query.filter_by(user_id=user_id, type='referral').all()
    pending = sum(e.amount for e in earnings if e.status == 'pending')
    approved = sum(e.amount for e in earnings if e.status == 'approved')
    withdrawn = sum(e.amount for e in earnings if e.status == 'withdrawn')
    return {
        'pending': pending,
        'approved': approved,
        'withdrawn': withdrawn,
        'total': pending + approved + withdrawn
    }

def get_user_gmail_accounts(user_id):
    """Get all Gmail accounts for a user from database"""
    from database import GmailAccount
    accounts = GmailAccount.query.filter_by(user_id=user_id).all()
    return accounts

@app.route('/')
def home():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page"""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    user = find_user_by_id(user_id)
    
    # Get Gmail accounts from database
    user_accounts = get_user_gmail_accounts(user_id)
    
    # Get earnings from database
    earnings = get_user_earnings(user_id)
    referral_earnings_data = get_referral_earnings(user_id)
    
    # Count referrals from database
    from database import User
    referral_count = User.query.filter_by(referred_by=user_id).count()
    
    return render_template('dashboard.html', 
                         accounts=user_accounts, 
                         pending_balance=earnings['pending'],
                         main_balance=earnings['approved'],
                         user_email=user_email,
                         referral_code=user.referral_code if user else '',
                         referral_balance=referral_earnings_data['approved'],
                         referral_count=referral_count)

@app.route('/main-dashboard')
def main_dashboard():
    """Dashboard route"""
    return redirect(url_for('dashboard'))

@app.route('/create-gmail', methods=['GET', 'POST'])
@login_required
def create_gmail_earn():
    """Create Gmail Earn page"""
    from database import GmailAccount, Earnings, User
    
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    if request.method == 'GET':
        # Generate new credentials for display
        credentials = generate_gmail_credentials()
        session['current_credentials'] = credentials
    
    else:  # POST request
        credentials = session.get('current_credentials', generate_gmail_credentials())
        
        try:
            # Save to database
            account = GmailAccount(
                user_id=user_id,
                email=f"{credentials['username']}@gmail.com",
                password=credentials['password'],
                status='pending',
                price=GMAIL_PRICE
            )
            
            db.session.add(account)
            db.session.flush()  # Get the account ID
            
            # Add pending earning
            earning = Earnings(
                user_id=user_id,
                amount=GMAIL_PRICE,
                type='sales',
                gmail_id=account.id,
                status='pending'
            )
            
            db.session.add(earning)
            db.session.commit()
            
            # Try to save to Google Sheet
            upload_gmail_to_sheets({
                'name': credentials['name'],
                'username': credentials['username'],
                'password': credentials['password']
            })
            
            # Clear session
            session.pop('current_credentials', None)
            
            return redirect(url_for('view_accounts'))
        
        except Exception as e:
            db.session.rollback()
            print(f"Error creating Gmail account: {e}")
            return render_template('create_gmail_earn.html', 
                                 error=f"Failed to create account: {str(e)[:100]}", 
                                 name=credentials.get('name'),
                                 username=credentials.get('username'),
                                 password=credentials.get('password'),
                                 price=GMAIL_PRICE,
                                 user_email=user_email)
    
    # Get user earnings for display
    earnings = get_user_earnings(user_id)
    
    return render_template('create_gmail_earn.html',
                         name=credentials['name'],
                         username=credentials['username'],
                         password=credentials['password'],
                         price=GMAIL_PRICE,
                         pending_balance=earnings['pending'],
                         main_balance=earnings['approved'],
                         user_email=user_email)

@app.route('/regenerate-gmail')
@login_required
def regenerate_gmail():
    """Regenerate new Gmail credentials"""
    user_id = session.get('user_id')
    
    credentials = generate_gmail_credentials()
    session['current_credentials'] = credentials
    
    return redirect(url_for('create_gmail_earn'))

@app.route('/api/earnings')
def get_earnings():
    """API endpoint to get user earnings"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    total_earnings = 0
    user_accounts = [acc for acc in gmail_accounts if acc['user_id'] == user_id]
    
    for acc in user_accounts:
        if acc['status'] == 'approved':
            total_earnings += acc['price']
    
    pending_balance = pending_earnings.get(user_id, 0)
    referral_balance = referral_earnings.get(user_id, 0)
    
    return jsonify({
        'total_earnings': total_earnings,
        'pending_balance': pending_balance,
        'referral_balance': referral_balance,
        'total_accounts': len(user_accounts)
    })

@app.route('/referrals')
@login_required
def referrals():
    """Referral page"""
    from database import User
    
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    user = find_user_by_id(user_id)
    
    if not user:
        return redirect(url_for('login'))
    
    referral_code = user.referral_code
    referral_link = f"{request.host_url.rstrip('/')}/register?ref={referral_code}"
    
    # Get referred users from database
    referrals_list = User.query.filter_by(referred_by=user_id).all()
    
    # Get earnings
    earnings = get_referral_earnings(user_id)
    main_earnings_data = get_user_earnings(user_id)
    
    return render_template('referrals.html',
                         user_email=user_email,
                         referral_code=referral_code,
                         referral_link=referral_link,
                         referrals=referrals_list,
                         referral_balance=earnings['approved'],
                         main_balance=main_earnings_data['approved'],
                         referral_count=len(referrals_list),
                         referral_percentage=REFERRAL_PERCENTAGE,
                         gmail_price=GMAIL_PRICE)

@app.route('/api/approve/<account_id>', methods=['POST'])
def approve_account(account_id):
    """Admin endpoint to approve an account"""
    for acc in gmail_accounts:
        if acc['id'] == account_id:
            acc['status'] = 'approved'
            
            # Move amount from pending to main earnings
            user_id = acc['user_id']
            price = acc['price']
            
            # Deduct from pending
            if user_id in pending_earnings:
                pending_earnings[user_id] -= price
                if pending_earnings[user_id] < 0:
                    pending_earnings[user_id] = 0
            
            # Add to main balance
            if user_id not in main_earnings:
                main_earnings[user_id] = 0
            main_earnings[user_id] += price
            
            # Add referral commission to referrer's main balance
            referrer_id = next((u['id'] for u in users if u['id'] == user_id and u.get('referred_by')), None)
            if referrer_id:
                referral_amount = (price * REFERRAL_PERCENTAGE) / 100
                if referrer_id not in referral_earnings:
                    referral_earnings[referrer_id] = 0
                referral_earnings[referrer_id] += referral_amount
            
            return jsonify({'status': 'approved'})
    
    return jsonify({'error': 'Account not found'}), 404

@app.route('/accounts')
@login_required
def view_accounts():
    """View all submitted accounts"""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    user_accounts = [acc for acc in gmail_accounts if acc['user_id'] == user_id]
    pending_balance = pending_earnings.get(user_id, 0)
    main_balance = main_earnings.get(user_id, 0)
    
    return render_template('accounts.html', accounts=user_accounts, user_email=user_email, pending_balance=pending_balance, main_balance=main_balance)

@app.route('/withdrawals')
@login_required
def view_withdrawals():
    """View all withdrawal requests"""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    user_withdrawals = [w for w in withdrawals if w['user_id'] == user_id]
    # Sort by created_at descending (newest first)
    user_withdrawals.sort(key=lambda x: x['created_at'], reverse=True)
    main_balance = main_earnings.get(user_id, 0)
    
    return render_template('my_withdrawals.html', withdrawals=user_withdrawals, user_email=user_email, main_balance=main_balance)

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def create_withdrawal():
    """Create withdrawal request"""
    user_id = session.get('user_id')
    user = find_user_by_id(user_id)
    user_email = session.get('user_email')
    
    pending_balance = pending_earnings.get(user_id, 0)
    main_balance = main_earnings.get(user_id, 0)
    referral_balance = referral_earnings.get(user_id, 0)
    total_balance = main_balance + referral_balance
    
    if request.method == 'POST':
        amount = request.form.get('amount', '0')
        bkash_number = request.form.get('bkash_number', '').strip()
        
        # Validation
        errors = []
        
        try:
            amount = float(amount)
        except ValueError:
            errors.append('Invalid amount')
            amount = 0
        
        if amount <= 0:
            errors.append('Amount must be greater than 0')
        
        if amount < 50:
            errors.append('Minimum withdrawal amount is ৳50')
        
        if amount > total_balance:
            errors.append(f'Insufficient balance. Available: ৳{total_balance:.2f}')
        
        if not bkash_number:
            errors.append('bKash number is required')
        elif len(bkash_number) != 11 or not bkash_number.isdigit():
            errors.append('Invalid bKash number (must be 11 digits)')
        
        if errors:
            return render_template('withdraw.html', errors=errors, pending_balance=pending_balance, 
                                 referral_balance=referral_balance, total_balance=total_balance,
                                 user_email=user_email)
        
        # Create withdrawal request
        withdrawal = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'amount': amount,
            'bkash_number': bkash_number,
            'status': 'pending',
            'created_at': datetime.now()
        }
        withdrawals.append(withdrawal)
        
        # Deduct from balance (from main first, then referral)
        deduct_amount = amount
        if main_balance >= deduct_amount:
            main_earnings[user_id] = main_balance - deduct_amount
        else:
            main_earnings[user_id] = 0
            referral_earnings[user_id] = referral_balance - (deduct_amount - main_balance)
        
        return render_template('withdraw_success.html', withdrawal=withdrawal, user_email=user_email)
    
    return render_template('withdraw.html', pending_balance=pending_balance, main_balance=main_balance,
                         referral_balance=referral_balance, total_balance=total_balance,
                         user_email=user_email)

# ============ ADMIN ROUTES ============

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if email == ADMIN_EMAIL and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_id'] = 'admin'
            session['admin_email'] = email
            session.modified = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid email or password')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    session.modified = True
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    from database import User, GmailAccount, Earnings, Withdrawal
    
    total_users = User.query.count()
    total_accounts = GmailAccount.query.count()
    
    # Get earnings stats
    pending_earnings_total = db.session.query(db.func.sum(Earnings.amount)).filter_by(status='pending').scalar() or 0
    referral_earnings_total = db.session.query(db.func.sum(Earnings.amount)).filter_by(type='referral', status='approved').scalar() or 0
    
    # Get account stats
    approved_accounts = GmailAccount.query.filter_by(status='approved').count()
    pending_accounts = GmailAccount.query.filter_by(status='pending').count()
    rejected_accounts = GmailAccount.query.filter_by(status='rejected').count()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_accounts=total_accounts,
                         total_pending=pending_earnings_total,
                         total_referral=referral_earnings_total,
                         approved_accounts=approved_accounts,
                         pending_accounts=pending_accounts,
                         rejected_accounts=rejected_accounts)

@app.route('/admin/users')
@admin_required
def admin_users():
    """View all users"""
    search = request.args.get('search', '').strip().lower()
    sort_by = request.args.get('sort', 'created_at')
    
    filtered_users = users
    
    # Search filter
    if search:
        filtered_users = [u for u in users if search in u['email'].lower()]
    
    # Sort
    if sort_by == 'email':
        filtered_users = sorted(filtered_users, key=lambda x: x['email'])
    elif sort_by == 'created_at':
        filtered_users = sorted(filtered_users, key=lambda x: x['created_at'], reverse=True)
    elif sort_by == 'referral_count':
        filtered_users = sorted(filtered_users, 
                               key=lambda x: len([u for u in users if u.get('referred_by') == x['id']]), 
                               reverse=True)
    
    # Get user stats
    user_stats = []
    for user in filtered_users:
        accounts = len([acc for acc in gmail_accounts if acc['user_id'] == user['id']])
        pending = pending_earnings.get(user['id'], 0)
        referral = referral_earnings.get(user['id'], 0)
        referral_count = len([u for u in users if u.get('referred_by') == user['id']])
        
        user_stats.append({
            'user': user,
            'accounts': accounts,
            'pending': pending,
            'referral': referral,
            'referral_count': referral_count
        })
    
    return render_template('admin_users.html', user_stats=user_stats, search=search, sort_by=sort_by)

@app.route('/admin/user/<user_id>')
@admin_required
def admin_user_detail(user_id):
    """View specific user details"""
    user = find_user_by_id(user_id)
    if not user:
        return "User not found", 404
    
    user_accounts = [acc for acc in gmail_accounts if acc['user_id'] == user_id]
    pending_balance = pending_earnings.get(user_id, 0)
    referral_balance = referral_earnings.get(user_id, 0)
    referral_count = len([u for u in users if u.get('referred_by') == user_id])
    
    # Get referrals list
    referrals_list = [u for u in users if u.get('referred_by') == user_id]
    
    return render_template('admin_user_detail.html',
                         user=user,
                         accounts=user_accounts,
                         pending_balance=pending_balance,
                         referral_balance=referral_balance,
                         referral_count=referral_count,
                         referrals=referrals_list)

@app.route('/admin/api/user/<user_id>/balance', methods=['POST'])
@admin_required
def admin_update_balance(user_id):
    """Update user's pending balance"""
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    new_balance = float(data.get('balance', 0))
    
    pending_earnings[user_id] = new_balance
    
    return jsonify({'success': True, 'balance': new_balance})

@app.route('/admin/api/user/<user_id>/referral-balance', methods=['POST'])
@admin_required
def admin_update_referral_balance(user_id):
    """Update user's referral balance"""
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    new_balance = float(data.get('balance', 0))
    
    referral_earnings[user_id] = new_balance
    
    return jsonify({'success': True, 'balance': new_balance})

@app.route('/admin/gmail-price', methods=['GET', 'POST'])
@admin_required
def admin_gmail_price():
    """Manage Gmail price"""
    global GMAIL_PRICE
    
    if request.method == 'POST':
        new_price = float(request.form.get('price', GMAIL_PRICE))
        GMAIL_PRICE = new_price
        return render_template('admin_gmail_price.html', 
                             price=GMAIL_PRICE,
                             message='Gmail price updated successfully!')
    
    return render_template('admin_gmail_price.html', price=GMAIL_PRICE)

@app.route('/admin/referral-percentage', methods=['GET', 'POST'])
@admin_required
def admin_referral_percentage():
    """Manage referral percentage"""
    global REFERRAL_PERCENTAGE
    
    if request.method == 'POST':
        new_percentage = float(request.form.get('percentage', REFERRAL_PERCENTAGE))
        REFERRAL_PERCENTAGE = new_percentage
        return render_template('admin_referral_percentage.html', 
                             percentage=REFERRAL_PERCENTAGE,
                             message='Referral percentage updated successfully!')
    
    return render_template('admin_referral_percentage.html', percentage=REFERRAL_PERCENTAGE)

@app.route('/admin/accounts')
@admin_required
def admin_accounts():
    """View all Gmail accounts"""
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip().lower()
    
    filtered_accounts = gmail_accounts
    
    # Status filter
    if status_filter != 'all':
        filtered_accounts = [acc for acc in filtered_accounts if acc['status'] == status_filter]
    
    # Search filter
    if search:
        filtered_accounts = [acc for acc in filtered_accounts 
                            if search in acc['username'].lower() or search in acc['name'].lower()]
    
    # Get user info for each account
    accounts_with_user = []
    for acc in filtered_accounts:
        user = find_user_by_id(acc['user_id'])
        accounts_with_user.append({
            'account': acc,
            'user_email': user['email'] if user else 'Unknown'
        })
    
    accounts_with_user = sorted(accounts_with_user, key=lambda x: x['account']['created_at'], reverse=True)
    
    return render_template('admin_accounts.html', 
                         accounts=accounts_with_user,
                         status_filter=status_filter,
                         search=search)

@app.route('/admin/api/account/<account_id>/status', methods=['POST'])
@admin_required
def admin_update_account_status(account_id):
    """Update account status"""
    from database import GmailAccount, Earnings, User
    
    try:
        data = request.get_json()
        new_status = data.get('status', 'pending')
        
        account = GmailAccount.query.get(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        old_status = account.status
        account.status = new_status
        
        # If approving account, create earnings record
        if new_status == 'approved' and old_status != 'approved':
            existing = Earnings.query.filter_by(gmail_id=account_id).first()
            if not existing:
                earning = Earnings(
                    user_id=account.user_id,
                    amount=account.price,
                    type='sales',
                    gmail_id=account_id,
                    status='approved'
                )
                db.session.add(earning)
                
                # Add referral bonus
                user = account.user
                if user and user.referred_by:
                    referral_amount = (account.price * REFERRAL_PERCENTAGE) / 100
                    referral_earning = Earnings(
                        user_id=user.referred_by,
                        amount=referral_amount,
                        type='referral',
                        status='approved'
                    )
                    db.session.add(referral_earning)
        
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/withdrawals')
@admin_required
def admin_view_withdrawals():
    """Admin view all withdrawals"""
    from database import Withdrawal
    
    status_filter = request.args.get('status', 'all')
    
    if status_filter != 'all':
        withdrawals_list = Withdrawal.query.filter_by(status=status_filter).order_by(Withdrawal.created_at.desc()).all()
    else:
        withdrawals_list = Withdrawal.query.order_by(Withdrawal.created_at.desc()).all()
    
    # Count by status
    total = Withdrawal.query.count()
    pending = Withdrawal.query.filter_by(status='pending').count()
    completed = Withdrawal.query.filter_by(status='completed').count()
    rejected = Withdrawal.query.filter_by(status='rejected').count()
    
    return render_template('admin_withdrawals.html', 
                         withdrawals=withdrawals_list,
                         status_filter=status_filter,
                         status_counts={'all': total, 'pending': pending, 'completed': completed, 'rejected': rejected})

@app.route('/admin/api/withdrawal/<withdrawal_id>/status', methods=['POST'])
@admin_required
def admin_update_withdrawal_status(withdrawal_id):
    """Admin update withdrawal status"""
    from database import Withdrawal
    
    try:
        data = request.get_json()
        new_status = data.get('status', 'pending')
        
        withdrawal = Withdrawal.query.get(withdrawal_id)
        if not withdrawal:
            return jsonify({'error': 'Withdrawal not found'}), 404
        
        withdrawal.status = new_status
        withdrawal.processed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'status': new_status})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/import-from-sheets', methods=['GET', 'POST'])
@admin_required
def admin_import_from_sheets():
    """Admin import Gmail accounts from Google Sheets"""
    if request.method == 'GET':
        return render_template('admin_import_sheets.html')
    
    try:
        spreadsheet_id = request.form.get('spreadsheet_id', '').strip()
        sheet_name = request.form.get('sheet_name', 'Sheet1').strip()
        
        if not spreadsheet_id:
            return render_template('admin_import_sheets.html', error='Spreadsheet ID is required')
        
        result = import_gmail_from_sheets(spreadsheet_id, sheet_name, admin_user_id='admin')
        
        if 'error' in result:
            return render_template('admin_import_sheets.html', error=result['error'])
        
        return render_template('admin_import_sheets.html', result=result, success=True)
    
    except Exception as e:
        return render_template('admin_import_sheets.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
