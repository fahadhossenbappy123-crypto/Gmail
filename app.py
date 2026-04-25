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

# Mock database [REMOVED - Now using PostgreSQL via SQLAlchemy]
# NOTE: All data is now stored in PostgreSQL database via SQLAlchemy ORM
# users, gmail_accounts, earnings, withdrawals tables are in the PostgreSQL database

# Admin account
ADMIN_EMAIL = 'admin@gmail.com'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')  # Change this!
GMAIL_PRICE = 5.00  # Default price per Gmail account
REFERRAL_PERCENTAGE = 10  # Default 10% of earnings to referrer

def generate_referral_code():
    """Generate unique 5-digit referral code"""
    from database import User
    code = ''.join(random.choices(string.digits, k=5))
    # Check if code already exists in database
    while User.query.filter_by(referral_code=code).first():
        code = ''.join(random.choices(string.digits, k=5))
    return code

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
    user = User.query.filter_by(email=email.lower()).first()
    return user

def find_user_by_id(user_id):
    """Find user by ID from database"""
    from database import User
    user = User.query.get(user_id)
    return user

def find_user_by_referral_code(code):
    """Find user by referral code from database"""
    from database import User
    user = User.query.filter_by(referral_code=code).first()
    return user

# Google Sheets Integration
def get_sheets_service():
    """Initialize Google Sheets API service"""
    try:
        # Get credentials from JSON file
        creds_file = 'rugged-nucleus-494309-h6-1e1f8ffafa43.json'
        
        if not os.path.exists(creds_file):
            print(f"Error: Credentials file not found: {creds_file}")
            return None
        
        # Load credentials
        with open(creds_file) as f:
            creds_info = json.load(f)
        
        # Create credentials from service account info
        credentials = Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Build Sheets service
        service = build('sheets', 'v4', credentials=credentials)
        print(f"✅ Google Sheets API connected successfully!")
        print(f"   Service Account: {creds_info.get('client_email')}")
        return service
    except Exception as e:
        print(f"❌ Error initializing Sheets service: {e}")
        return None

def save_gmail_to_google_sheet(gmail_account, user_email='', spreadsheet_id='1Czkp_Yflqvd7zQMdZ6dUfAiD_wVexucfJz7ut8f-eVA', sheet_name='Sheet1'):
    """Save Gmail account to Google Sheet
    
    Args:
        gmail_account: Gmail account dict with keys: name, username, password
        user_email: Email of the user who created the account (for sender email)
        spreadsheet_id: Google Sheets ID (default: your provided ID)
        sheet_name: Sheet name (default: 'Sheet1')
    
    Returns:
        Dictionary with success/error status
    """
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'Failed to initialize Google Sheets API'}
        
        # Prepare row data
        # Column A: NAME, B: GMAIL, C: PASSWORD, D: SENDER_EMAIL (User's email who created it)
        row = [
            gmail_account.get('name', ''),
            f"{gmail_account.get('username', '')}@gmail.com",
            gmail_account.get('password', ''),
            user_email  # User's actual email address
        ]
        
        # First, check if headers exist
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A1:D1'
        ).execute()
        
        values = result.get('values', [])
        
        # If no headers, add them
        if not values or len(values) == 0:
            headers = [['NAME', 'GMAIL', 'PASSWORD', 'SENDER_EMAIL']]
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            print(f"✅ Headers added to Google Sheet")
        
        # Append the new row
        body = {'values': [row]}
        response = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A:D',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"✅ Gmail account saved to Google Sheet")
        print(f"   Name: {gmail_account.get('name')}")
        print(f"   Email: {gmail_account.get('username')}@gmail.com")
        print(f"   Sender: {user_email}")
        
        return {
            'success': True,
            'message': 'Account saved to Google Sheet',
            'spreadsheet_id': spreadsheet_id
        }
    
    except Exception as e:
        print(f"❌ Error saving to Google Sheet: {e}")
        return {'error': f'Failed to save to Google Sheet: {str(e)}'}

def import_gmail_from_sheets(spreadsheet_id, sheet_name='Sheet1', admin_user_id='admin'):
    """Import Gmail accounts from Google Sheets
    
    Args:
        spreadsheet_id: Google Sheets ID to import from
        sheet_name: Name of the sheet to read from
        admin_user_id: User ID to assign to imported accounts
    
    Returns:
        Dictionary with success/error status and import details
    """
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'Failed to initialize Google Sheets API'}
        
        # Read data from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A:D'
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return {'error': 'No data found in the sheet'}
        
        # Skip header row if it exists
        data_rows = values[1:] if len(values) > 1 else []
        
        if not data_rows:
            return {'error': 'No Gmail accounts found in the sheet'}
        
        imported_count = 0
        errors = []
        
        # Import each row
        for idx, row in enumerate(data_rows, start=2):
            try:
                # Expecting columns: NAME, GMAIL, PASSWORD, SENDER_GMAIL
                if len(row) < 3:
                    errors.append(f'Row {idx}: Missing required columns (need at least NAME, GMAIL, PASSWORD)')
                    continue
                
                name = row[0].strip() if len(row) > 0 else ''
                gmail_email = row[1].strip() if len(row) > 1 else ''
                password = row[2].strip() if len(row) > 2 else ''
                
                # Validate data
                if not name or not gmail_email or not password:
                    errors.append(f'Row {idx}: Missing required data')
                    continue
                
                # Extract username from email
                if '@' in gmail_email:
                    username = gmail_email.split('@')[0]
                else:
                    # If no @ symbol, treat the entire value as username
                    username = gmail_email
                
                # Check if account already exists
                existing = next((acc for acc in gmail_accounts if acc['username'] == username), None)
                if existing:
                    errors.append(f'Row {idx}: Account {username} already exists')
                    continue
                
                # Create new account
                account = {
                    'id': str(uuid.uuid4()),
                    'user_id': admin_user_id,
                    'name': name,
                    'username': username,
                    'password': password,
                    'email': f'{username}@gmail.com',
                    'status': 'approved',  # Import as approved by default
                    'price': GMAIL_PRICE,
                    'created_at': datetime.now()
                }
                
                gmail_accounts.append(account)
                imported_count += 1
                
            except Exception as e:
                errors.append(f'Row {idx}: Error - {str(e)}')
        
        return {
            'success': True,
            'imported_count': imported_count,
            'total_rows': len(data_rows),
            'errors': errors,
            'spreadsheet_id': spreadsheet_id
        }
    
    except Exception as e:
        return {'error': f'Failed to import from sheets: {str(e)}'}

def upload_gmail_to_sheets(new_account=None, approved_only=False):
    """Upload Gmail accounts to Google Sheets
    
    Args:
        new_account: Single account dict to append (for auto-save on submission)
        approved_only: If True, refresh with only approved accounts (for admin export)
    """
    global sheets_spreadsheet_id
    
    try:
        service = get_sheets_service()
        if not service:
            return {'error': 'Failed to initialize Google Sheets API'}
        
        # Create new spreadsheet if not exists
        if not sheets_spreadsheet_id:
            spreadsheet_body = {
                'properties': {
                    'title': f'Gmail Accounts Submissions'
                }
            }
            spreadsheet = service.spreadsheets().create(body=spreadsheet_body).execute()
            sheets_spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Add headers
            headers = [['NAME', 'GMAIL', 'PASSWORD', 'SENDER GMAIL']]
            body = {'values': headers}
            service.spreadsheets().values().update(
                spreadsheetId=sheets_spreadsheet_id,
                range='Sheet1!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Format headers
            format_request_body = {
                'requests': [{
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 4
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True,
                                    'fontSize': 12
                                },
                                'backgroundColor': {
                                    'red': 0.2,
                                    'green': 0.8,
                                    'blue': 0.2
                                },
                                'horizontalAlignment': 'CENTER'
                            }
                        },
                        'fields': 'userEnteredFormat'
                    }
                }]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheets_spreadsheet_id,
                body=format_request_body
            ).execute()
        
        # Mode 1: Append single new account (auto-save on submission)
        if new_account and not approved_only:
            row = [[
                new_account['name'],
                f"{new_account['username']}@gmail.com",
                new_account['password'],
                f"{new_account['username']}@gmail.com"
            ]]
            
            body = {'values': row}
            service.spreadsheets().values().append(
                spreadsheetId=sheets_spreadsheet_id,
                range='Sheet1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return {
                'success': True,
                'message': 'Account saved to Google Sheets',
                'spreadsheet_id': sheets_spreadsheet_id
            }
        
        # Mode 2: Bulk refresh with only approved accounts (for admin export)
        elif approved_only:
            approved_accounts = [acc for acc in gmail_accounts if acc['status'] == 'approved']
            
            if not approved_accounts:
                return {'error': 'No approved accounts to export'}
            
            # Clear all data except headers
            service.spreadsheets().values().clear(
                spreadsheetId=sheets_spreadsheet_id,
                range='Sheet1!A2:D'
            ).execute()
            
            # Prepare data
            sheet_data = []
            for acc in approved_accounts:
                row = [
                    acc['name'],
                    f"{acc['username']}@gmail.com",
                    acc['password'],
                    f"{acc['username']}@gmail.com"
                ]
                sheet_data.append(row)
            
            # Append approved accounts
            body = {'values': sheet_data}
            service.spreadsheets().values().update(
                spreadsheetId=sheets_spreadsheet_id,
                range='Sheet1!A2',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return {
                'success': True,
                'spreadsheet_id': sheets_spreadsheet_id,
                'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{sheets_spreadsheet_id}',
                'accounts_exported': len(approved_accounts)
            }
        
        return {'success': True, 'spreadsheet_id': sheets_spreadsheet_id}
    
    except Exception as e:
        return {'error': str(e)}

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    # Get referral code from URL parameter
    referral_code = request.args.get('ref', '').strip().upper()
    referrer = None
    referral_error = None
    
    if referral_code:
        referrer = find_user_by_referral_code(referral_code)
        if not referrer:
            referral_error = "Invalid referral code"
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        ref_code = request.form.get('referral_code', '').strip().upper()
        
        # Validation
        errors = []
        
        if not email:
            errors.append('Email is required')
        elif not is_email_valid(email):
            errors.append('Invalid email format')
        elif find_user_by_email(email):
            errors.append('Email already registered')
        
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Validate referral code if provided
        referrer = None
        if ref_code:
            referrer = find_user_by_referral_code(ref_code)
            if not referrer:
                errors.append('Invalid referral code')
        
        if errors:
            return render_template('register.html', errors=errors, email=email, referral_code=ref_code, referral_error=referral_error)
        
        # Create new user in database
        from database import User
        
        referrer_id = referrer.id if referrer else None
        new_user = User(
            email=email.lower(),
            password_hash=generate_password_hash(password),
            name=email.split('@')[0],  # Use email username as default name
            referral_code=generate_referral_code(),
            referred_by=referrer_id
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Add instant ৳10 bonus to referrer if referral exists
        if referrer:
            from database import Earnings
            bonus_earning = Earnings(
                user_id=referrer.id,
                amount=10.0,
                type='referral',
                status='approved'
            )
            db.session.add(bonus_earning)
            db.session.commit()
        
        # Note: Referral earnings (percentage) will be calculated when accounts are approved
        # Based on REFERRAL_PERCENTAGE setting (percentage of approved account value)
        
        return redirect(url_for('login'))
    
    return render_template('register.html', referral_code=referral_code, referral_error=referral_error)

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
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    # Use global GMAIL_PRICE
    price = GMAIL_PRICE
    
    if request.method == 'GET':
        # Check if credentials already exist in session
        if 'current_credentials' in session:
            credentials = session['current_credentials']
            price = session.get('current_price', GMAIL_PRICE)
        else:
            # Generate new credentials only if not in session
            credentials = generate_gmail_credentials()
            session['current_credentials'] = credentials
            session['current_price'] = GMAIL_PRICE  # Use current global price
        
        submitted = False
        name = credentials['name']
        username = credentials['username']
        password = credentials['password']
        
    else:  # POST request
        credentials = session.get('current_credentials', generate_gmail_credentials())
        name = credentials['name']
        username = credentials['username']
        password = credentials['password']
        price = session.get('current_price', GMAIL_PRICE)  # Use stored price or current global
        submitted = True
        
        # Save to database
        account = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'name': name,
            'username': username,
            'password': password,
            'price': price,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        gmail_accounts.append(account)
        
        # Add to pending earnings
        if user_id not in pending_earnings:
            pending_earnings[user_id] = 0
        pending_earnings[user_id] += price
        
        # Auto-upload to Google Sheets
        upload_gmail_to_sheets(new_account=account)
        
        # Save to user's Google Sheet (1Czkp_Yflqvd7zQMdZ6dUfAiD_wVexucfJz7ut8f-eVA)
        save_result = save_gmail_to_google_sheet(credentials, user_email=user_email)
        if 'error' in save_result:
            print(f"⚠️ Warning: Could not save to user's Google Sheet: {save_result['error']}")
        
        # Clear session credentials after submission
        session.pop('current_credentials', None)
        session.pop('current_price', None)
    
    pending_balance = pending_earnings.get(user_id, None)
    main_balance = main_earnings.get(user_id, 0)
    
    # Mark session as modified to ensure it's saved
    session.modified = True
    
    return render_template('create_gmail_earn.html',
                         name=name,
                         username=username,
                         password=password,
                         price=price,
                         submitted=submitted,
                         pending_balance=pending_balance,
                         main_balance=main_balance,
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
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    user = find_user_by_id(user_id)
    
    referral_code = user.get('referral_code', '') if user else ''
    referral_link = f"{request.host_url.rstrip('/')}/register?ref={referral_code}"
    
    # Get list of referrals
    referrals_list = [u for u in users if u.get('referred_by') == user_id]
    referral_balance = referral_earnings.get(user_id, 0)
    
    main_balance = main_earnings.get(user_id, 0)
    return render_template('referrals.html',
                         user_email=user_email,
                         referral_code=referral_code,
                         referral_link=referral_link,
                         referrals=referrals_list,
                         referral_balance=referral_balance,
                         main_balance=main_balance,
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
    # Get all statistics
    total_users = len(users)
    total_accounts = len(gmail_accounts)
    total_pending = sum(pending_earnings.values())
    total_referral = sum(referral_earnings.values())
    
    approved_accounts = len([acc for acc in gmail_accounts if acc['status'] == 'approved'])
    pending_accounts = len([acc for acc in gmail_accounts if acc['status'] == 'pending'])
    rejected_accounts = len([acc for acc in gmail_accounts if acc['status'] == 'rejected'])
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_accounts=total_accounts,
                         total_pending=total_pending,
                         total_referral=total_referral,
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
    data = request.get_json()
    new_status = data.get('status', 'pending')
    
    for acc in gmail_accounts:
        if acc['id'] == account_id:
            old_status = acc['status']
            acc['status'] = new_status
            
            user_id = acc['user_id']
            user = find_user_by_id(user_id)
            price = acc['price']
            
            # If approving account
            if new_status == 'approved' and old_status != 'approved':
                # Move from pending_earnings to main_earnings
                if user_id in pending_earnings:
                    pending_earnings[user_id] -= price
                    if pending_earnings[user_id] < 0:
                        pending_earnings[user_id] = 0
                
                # Add to main earnings
                if user_id not in main_earnings:
                    main_earnings[user_id] = 0
                main_earnings[user_id] += price
                
                # Add referral commission to referrer if exists
                if user and user.get('referred_by'):
                    referrer_id = user['referred_by']
                    referral_amount = (price * REFERRAL_PERCENTAGE) / 100
                    
                    if referrer_id not in referral_earnings:
                        referral_earnings[referrer_id] = 0
                    referral_earnings[referrer_id] += referral_amount
                    
                    print(f"✅ Referral bonus added to {referrer_id}: ৳{referral_amount:.2f}")
            
            # If rejecting account (move back to pending_earnings)
            elif new_status == 'rejected' and old_status == 'pending':
                # Keep in pending_earnings (no change needed)
                pass
            
            # If reverting from approved to pending
            elif new_status == 'pending' and old_status == 'approved':
                # Move back from main_earnings to pending_earnings
                if user_id in main_earnings:
                    main_earnings[user_id] -= price
                    if main_earnings[user_id] < 0:
                        main_earnings[user_id] = 0
                
                # Add back to pending
                if user_id not in pending_earnings:
                    pending_earnings[user_id] = 0
                pending_earnings[user_id] += price
                
                # Remove referral bonus from referrer
                if user and user.get('referred_by'):
                    referrer_id = user['referred_by']
                    referral_amount = (price * REFERRAL_PERCENTAGE) / 100
                    
                    if referrer_id in referral_earnings:
                        referral_earnings[referrer_id] -= referral_amount
                        if referral_earnings[referrer_id] < 0:
                            referral_earnings[referrer_id] = 0
                    
                    print(f"⚠️ Referral bonus removed from {referrer_id}: ৳{referral_amount:.2f}")
            
            print(f"✅ Account {account_id} status changed from {old_status} to {new_status}")
            print(f"   User: {user_id}")
            print(f"   Price: ৳{price:.2f}")
            
            return jsonify({
                'success': True,
                'status': new_status,
                'message': f'Account status changed to {new_status}'
            })
    
    return jsonify({'error': 'Account not found'}), 404

@app.route('/admin/withdrawals')
@admin_required
def admin_view_withdrawals():
    """Admin view all withdrawals"""
    # Get all withdrawals
    all_withdrawals = withdrawals.copy()
    
    # Get filter parameter
    status_filter = request.args.get('status', 'all')
    if status_filter != 'all':
        all_withdrawals = [w for w in all_withdrawals if w['status'] == status_filter]
    
    # Sort by created_at descending
    all_withdrawals.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Count by status
    status_counts = {
        'all': len(withdrawals),
        'pending': len([w for w in withdrawals if w['status'] == 'pending']),
        'completed': len([w for w in withdrawals if w['status'] == 'completed']),
        'rejected': len([w for w in withdrawals if w['status'] == 'rejected'])
    }
    
    return render_template('admin_withdrawals.html', withdrawals=all_withdrawals, 
                         status_filter=status_filter, status_counts=status_counts, users=users)

@app.route('/admin/api/withdrawal/<withdrawal_id>/status', methods=['POST'])
@admin_required
def admin_update_withdrawal_status(withdrawal_id):
    """Admin update withdrawal status"""
    data = request.get_json()
    new_status = data.get('status', 'pending')
    
    for w in withdrawals:
        if w['id'] == withdrawal_id:
            w['status'] = new_status
            return jsonify({'success': True, 'status': new_status})
    
    return jsonify({'error': 'Withdrawal not found'}), 404

@app.route('/admin/export-to-sheets', methods=['POST'])
@admin_required
def admin_export_to_sheets():
    """Admin export approved Gmail accounts to Google Sheets"""
    result = upload_gmail_to_sheets(approved_only=True)
    return jsonify(result)

@app.route('/admin/import-from-sheets', methods=['GET', 'POST'])
@admin_required
def admin_import_from_sheets():
    """Admin import Gmail accounts from Google Sheets"""
    if request.method == 'GET':
        # Show import form
        return render_template('admin_import_sheets.html')
    
    if request.method == 'POST':
        spreadsheet_id = request.form.get('spreadsheet_id', '').strip()
        sheet_name = request.form.get('sheet_name', 'Sheet1').strip()
        
        # Validate spreadsheet ID
        if not spreadsheet_id:
            return render_template('admin_import_sheets.html', 
                                 error='Spreadsheet ID is required')
        
        # Import Gmail accounts
        result = import_gmail_from_sheets(spreadsheet_id, sheet_name, admin_user_id='admin')
        
        if 'error' in result:
            return render_template('admin_import_sheets.html', 
                                 error=result['error'])
        
        return render_template('admin_import_sheets.html', 
                             result=result,
                             success=True)

@app.route('/admin/api/import-sheets', methods=['POST'])
@admin_required
def admin_import_sheets_api():
    """API endpoint to import Gmail accounts from Google Sheets"""
    data = request.get_json()
    spreadsheet_id = data.get('spreadsheet_id', '').strip()
    sheet_name = data.get('sheet_name', 'Sheet1').strip()
    
    if not spreadsheet_id:
        return jsonify({'error': 'Spreadsheet ID is required'}), 400
    
    result = import_gmail_from_sheets(spreadsheet_id, sheet_name, admin_user_id='admin')
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
