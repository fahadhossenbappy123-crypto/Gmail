# Admin Panel Documentation

## 🔐 Admin Access

### Login Page
**URL:** `http://localhost:5000/admin/login`

**Demo Credentials:**
- Email: `admin@gmail.com`
- Password: `admin123`

**⚠️ IMPORTANT FOR PRODUCTION:**
Change the admin credentials in [app.py](app.py):
```python
ADMIN_EMAIL = 'your-admin-email@gmail.com'
ADMIN_PASSWORD_HASH = generate_password_hash('your-strong-password')
```

---

## 📊 Admin Dashboard Features

### 1. **Dashboard** (`/admin/dashboard`)
**Purpose:** Get a complete overview of your system

**What You See:**
- 📍 **Total Users** - Number of registered users
- 📧 **Gmail Accounts** - Total Gmail accounts submitted
- ⏳ **Pending Balance** - Total money awaiting approval
- 💰 **Referral Earnings** - Total earned through referrals
- 📈 **Account Status Breakdown** - Approved, Pending, Rejected counts
- 🔗 **Quick Action Links** - Direct access to manage users, accounts, and settings

**Use Cases:**
- Monitor system growth
- Track pending payouts
- See overall referral program performance

---

### 2. **Manage Users** (`/admin/users`)
**Purpose:** View and manage all registered users

**Features:**
- 🔍 **Search** - Find users by email
- 📌 **Sort Options**:
  - Latest First
  - Email (A-Z)
  - Most Referrals

**User Table Shows:**
| Column | Details |
|--------|---------|
| Email | User's email address |
| Accounts | Number of Gmail accounts submitted |
| Pending | Pending balance for this user |
| Referral | Referral earnings |
| Referrals | Number of successful referrals |
| Joined | Registration date |
| Action | View button to see details |

**Use Cases:**
- Find and manage specific users
- Identify top referrers
- Monitor user activity

---

### 3. **User Details** (`/admin/user/<user_id>`)
**Purpose:** View and manage individual user accounts

#### A. User Profile Section
Shows basic user information:
- Email address
- Unique User ID
- Referral Code (share with others)
- Join Date
- Who referred them (if applicable)

#### B. Statistics Section
At a glance view of:
- Total Gmail Accounts
- Pending Balance
- Referral Balance
- Active Referrals Count

#### C. ⭐ **Edit Balances** (MAIN FEATURE)

##### Edit Pending Balance
**What it does:** Manually adjust how much money the user has earned from Gmail account submissions

**How to use:**
1. See current balance displayed
2. Enter new amount in the input field
3. Click "Update Balance"
4. Balance updates immediately

**Example:**
```
Current: $0.00
User submits 5 accounts @ ৳5 each = ৳25.00
If you want to approve only 3 = Set to ৳15.00
```

##### Edit Referral Balance
**What it does:** Manually adjust referral earnings (money earned when others sign up with referral code)

**How to use:**
1. See current balance displayed
2. Enter new amount
3. Click "Update Balance"
4. Balance updates immediately

**Example:**
```
Current: $0.00
Set to ৳50.00 (if they referred 50 people @ ৳1 each but you want to adjust)
```

#### D. Gmail Accounts Table
Shows all accounts submitted by this user:
- Account holder's name
- Gmail username
- Price per account
- Status (Approved/Pending/Rejected)
- Creation date

#### E. Referrals List
Shows all users who signed up using this user's referral code:
- Referred user's email
- Their referral code
- When they joined
- How many accounts they've submitted

**Use Cases:**
- Approve or reject earnings
- Bonus users for good performance
- Investigate suspicious activity
- View referral network

---

### 4. **Review Gmail Accounts** (`/admin/accounts`)
**Purpose:** Review and approve submitted Gmail accounts

**Filter & Search:**
- **Status Filter**: All, Pending, Approved, Rejected
- **Search**: Find by username or name

**Account Card Shows:**
- Account holder's name
- Username/Email
- Price
- Status (with color coding)
- User's email (clickable - goes to user details)
- Action buttons

**Actions:**
- **For Pending Accounts**: 
  - ✅ **Approve** - Mark as approved (adds to pending earnings)
  - ❌ **Reject** - Mark as rejected
  
- **For Approved/Rejected Accounts**:
  - Edit status to another state

**Use Cases:**
- Verify account quality
- Approve legitimate submissions
- Reject fake or suspicious accounts
- Manage batch approvals

---

### 5. **Referral Commission Settings** (`/admin/referral-commission`)
**Purpose:** Control how much users earn per referral

**What You Can Do:**

#### Set Commission Amount
1. Enter the dollar amount users earn per referral
2. Click "Save Commission Settings"
3. Changes apply to **NEW referrals** only

**Example Scenarios:**
```
Current: ৳1.00 per referral
Change to: ৳2.00 - More attractive, costs more
Change to: ৳0.50 - Less attractive, saves money
```

**Visible Calculations:**
- Shows example: "If 10 users sign up: 10 × ৳1.00 = ৳10.00"
- Predicted impact if you increase/decrease

**⚠️ Important Notes:**
- Only applies to NEW referrals
- Existing referral balances are NOT recalculated
- Recommended range: ৳0.50 - ৳2.00 per referral

**Use Cases:**
- Incentivize users to refer more
- Control marketing costs
- Test different commission rates
- Seasonal promotions

---

## 🔄 Complete User Management Workflow

### Scenario: New User Submits 5 Accounts

1. **User registers** → Shows in `/admin/users`
2. **User creates 5 Gmail accounts** → Appear in `/admin/accounts` as "Pending"
3. **Review accounts**:
   - Check quality in `/admin/accounts`
   - Approve good ones, reject bad ones
4. **Balance updates**:
   - If 5 approved @ ৳5 = ৳25 pending
   - Shows in `/admin/users` and `/admin/user/details`
5. **Edit balance if needed**:
   - Go to user details
   - Adjust pending balance
   - Save changes
6. **User sees updated balance** in their dashboard

---

## 🎯 Referral Program Management

### Setting Up Referrals

1. **Set Commission** (`/admin/referral-commission`)
   - Example: ৳1.00 per referral

2. **User gets referral code** 
   - Unique code shown in their dashboard
   - Can share with friends

3. **Friend signs up** with code
   - Referral automatically linked
   - User gets ৳1.00 added

4. **Monitor referrals**
   - `/admin/user/<id>` shows all referrals
   - Track performance
   - Edit balance if needed

### Example Commission Scenarios

| Scenario | Commission | Cost for 100 referrals |
|----------|-----------|----------------------|
| Aggressive Growth | ৳2.00 | ৳200 |
| Balanced | ৳1.00 | ৳100 |
| Conservative | ৳0.50 | ৳50 |

---

## 📱 API Reference for Integration

### Balance Update APIs

#### Update Pending Balance
```
POST /admin/api/user/<user_id>/balance
Content-Type: application/json

{
  "balance": 150.00
}

Response: { "success": true, "balance": 150.00 }
```

#### Update Referral Balance
```
POST /admin/api/user/<user_id>/referral-balance
Content-Type: application/json

{
  "balance": 75.50
}

Response: { "success": true, "balance": 75.50 }
```

#### Update Account Status
```
POST /admin/api/account/<account_id>/status
Content-Type: application/json

{
  "status": "approved"  // "pending", "approved", "rejected"
}

Response: { "success": true, "status": "approved" }
```

---

## 🔒 Security Notes

**Current State (Development):**
- ✅ Admin login works
- ✅ Session-based authentication
- ⚠️ In-memory data (lost on restart)
- ⚠️ Default credentials visible in code

**For Production:**
1. **Change admin credentials**
2. **Use database** instead of lists
3. **Add encryption** for sensitive data
4. **Use HTTPS** only
5. **Implement role-based access** (e.g., moderators, accountants)
6. **Add audit logging** for all changes
7. **Enable 2FA** for admin login
8. **Add password reset** functionality
9. **Rate limit** admin API endpoints
10. **Regular backups** of data

---

## 🐛 Troubleshooting

### Admin Won't Login
- Check email: `admin@gmail.com`
- Check password: `admin123`
- Make sure you're at `/admin/login` not `/login`
- Check browser console for errors
- Restart Flask server

### Balance Changes Don't Show
- Check network tab for API errors
- Try page refresh
- Check Flask console for 404 errors
- Verify user ID is correct

### Commission Changes Not Working
- Make sure you clicked "Save Commission Settings"
- Changes only apply to NEW referrals
- Existing balances won't update automatically

### No Users Appear
- Users only show after registering in app
- Try creating test user first at `/register`
- Check if app.py is running (`python app.py`)

---

## 💡 Best Practices

### User Management
- ✅ Review all accounts before approval
- ✅ Communicate with users about rejections
- ✅ Monitor for spam/fake accounts
- ✅ Regular audit of balances

### Referral Program
- ✅ Test different commission rates
- ✅ Promote top referrers
- ✅ Monitor fraud attempts
- ✅ Regular payouts for credibility

### Account Management
- ✅ Set clear quality standards
- ✅ Communicate approval criteria
- ✅ Quick turnaround on reviews
- ✅ Consistent pricing

---

## 📞 Support

For issues or feature requests, check:
1. [Flask Documentation](https://flask.palletsprojects.com/)
2. [Werkzeug Security](https://werkzeug.palletsprojects.com/security/)
3. [Template Syntax](https://jinja.palletsprojects.com/)

---

**Last Updated:** April 24, 2026
**Version:** 1.0
**Status:** ✅ Complete
