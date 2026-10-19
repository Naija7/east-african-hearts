# Authentication System - Complete Setup

## Admin Credentials
**Default Admin Login:**
- Username: `admin`
- Password: `Admin@123`

Access admin panel at: `/admin-login`

## Features Implemented

### 1. User Registration
- Secure password hashing with bcrypt
- Email validation (no duplicate registrations)
- Auto-create user profile
- Full form validation

### 2. User Login
- Email & password verification
- Session management
- Persistent login state

### 3. User Logout
- Clear session data
- Safe logout

### 4. Admin Dashboard
- View total registered users
- Manage testimonials
- Approve/reject success stories
- View testimonial statistics

### 5. Admin Features
- Approve testimonials for display
- Reject inappropriate testimonials
- View all pending testimonials
- Testimonial management

## How to Use

### For Regular Users:
1. **Register** - Go to `/register`, fill the form
2. **Login** - Go to `/login` with your email & password
3. **Share Story** - Click "Share Your Story" button on homepage
4. **View** - See approved testimonials on the gallery

### For Admin:
1. **Admin Login** - Go to `/admin-login`
2. **Use credentials above**
3. **Manage Testimonials** - Approve or reject pending stories
4. **View Stats** - See dashboard statistics
5. **Logout** - Click Admin Logout button

## Database Tables Used
- `users` - Stores user accounts & profiles
- `profiles` - User profile details
- `testimonials` - Couple success stories

## Security Features
✅ Password hashing (bcrypt)
✅ Session-based authentication
✅ SQL injection protection
✅ Email duplicate prevention
✅ Admin access control

## Test the System:
1. Restart Flask app: `python app.py`
2. Register a new user
3. Login with credentials
4. Submit a testimonial
5. Go to `/admin-login` and approve it
6. See it appear on homepage!

## Important Notes
⚠️ Change the secret key in production (app.py line 8)
⚠️ Use strong admin password in production
⚠️ Never commit credentials to version control
