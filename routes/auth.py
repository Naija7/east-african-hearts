from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from utils import compress_image, validate_image_file, get_image_size_mb, log_event
from validators import (validate_email, validate_password, validate_name,
                       validate_age, validate_location, validate_bio,
                       validate_interests, validate_message)
from rate_limiter import limiter
from email_verification import create_verification_token, verify_token
from email_sender import send_verification_email, send_resend_verification_email

# Load environment variables
load_dotenv()

auth = Blueprint('auth', __name__)

# Database connection
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validate email format
        is_valid, error = validate_email(email)
        if not is_valid:
            flash(error, "error")
            return redirect(url_for('auth.login'))

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['name'] = user.get('full_name', 'User')
            log_event(user['id'], 'USER_LOGIN', f"Logged in from {request.remote_addr}")
            flash("Welcome back!", "success")
            return redirect(url_for('home.index'))
        else:
            flash("Invalid email or password", "error")

    return render_template("login.html")

@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        gender = request.form.get("gender", "")
        age = request.form.get("age", "")
        location = request.form.get("location", "").strip()
        interests = request.form.get("interests", "").strip()

        # VALIDATION CHECKS
        # Validate name
        is_valid, error = validate_name(name)
        if not is_valid:
            flash(f"Name: {error}", "error")
            return redirect(url_for('auth.register'))

        # Validate email
        is_valid, error = validate_email(email)
        if not is_valid:
            flash(f"Email: {error}", "error")
            return redirect(url_for('auth.register'))

        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            flash(f"Password: {error}", "error")
            return redirect(url_for('auth.register'))

        # Check password confirmation
        if password != password_confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for('auth.register'))

        # Validate gender
        if gender not in ['Male', 'Female', 'Other']:
            flash("Invalid gender selection", "error")
            return redirect(url_for('auth.register'))

        # Validate age
        is_valid, error = validate_age(age)
        if not is_valid:
            flash(f"Age: {error}", "error")
            return redirect(url_for('auth.register'))

        # Validate location
        is_valid, error = validate_location(location)
        if not is_valid:
            flash(f"Location: {error}", "error")
            return redirect(url_for('auth.register'))

        # Validate interests
        is_valid, error = validate_interests(interests)
        if not is_valid:
            flash(f"Interests: {error}", "error")
            return redirect(url_for('auth.register'))

        # Handle photo upload with compression
        photo_binary = None
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file.filename != '':
                # Validate image
                is_valid, error_msg = validate_image_file(photo_file, max_size_mb=15)
                if not is_valid:
                    flash(error_msg, "error")
                    return redirect(url_for('auth.register'))

                # Compress image
                photo_binary = compress_image(photo_file, max_width=600, max_height=600, quality=80)
                if photo_binary is None:
                    flash("Error processing image. Please try again.", "error")
                    return redirect(url_for('auth.register'))

                size_mb = get_image_size_mb(photo_binary)
                print(f"Image compressed: {size_mb:.2f}MB")

        cursor = db.cursor()

        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("Email already registered", "error")
            cursor.close()
            return redirect(url_for('auth.register'))

        # Hash password
        hashed_password = generate_password_hash(password)

        try:
            # Insert user
            sql = "INSERT INTO users (full_name, email, password_hash, gender, age) VALUES (%s, %s, %s, %s, %s)"
            values = (name, email, hashed_password, gender, age)
            cursor.execute(sql, values)
            db.commit()

            user_id = cursor.lastrowid

            # Create profile with compressed photo
            profile_sql = "INSERT INTO profiles (user_id, bio, interests, location, profile_picture) VALUES (%s, %s, %s, %s, %s)"
            profile_values = (user_id, "", interests, location, photo_binary)
            cursor.execute(profile_sql, profile_values)
            db.commit()

            # Create verification token and send email
            token = create_verification_token(user_id, db)
            if token:
                app_url = os.getenv('APP_URL', 'http://127.0.0.1:5000')
                verification_link = f"{app_url}/verify-email/{token}"
                success, error = send_verification_email(email, name, verification_link)

                if success:
                    flash("Registration successful! Please check your email to verify your account.", "success")
                else:
                    print(f"Warning: Email not sent: {error}")
                    flash("Registration successful! Note: We couldn't send verification email. Try resending later.", "warning")
            else:
                flash("Registration successful! Please check your email to verify your account.", "success")

            cursor.close()
            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"Registration Error: {e}")
            flash("Registration failed. Please try again.", "error")
            cursor.close()

    return render_template("register.html")

@auth.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('home.index'))

@auth.route("/admin-login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, password_hash FROM admin_users WHERE username = %s", (username,))
        admin_user = cursor.fetchone()
        cursor.close()

        if admin_user and check_password_hash(admin_user['password_hash'], password):
            session['admin'] = True
            session['admin_id'] = admin_user['id']
            session['admin_name'] = username
            log_event(admin_user['id'], 'ADMIN_LOGIN', f"Admin login from {request.remote_addr}")
            flash("Admin login successful", "success")
            return redirect(url_for('auth.admin_panel'))
        else:
            log_event(0, 'ADMIN_LOGIN_FAILED', f"Failed login attempt for {username}")
            flash("Invalid admin credentials", "error")

    return render_template("admin_login.html")

@auth.route("/admin-forgot-password", methods=["GET", "POST"])
def admin_forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, email FROM admin_users WHERE username = %s", (username,))
        admin_user = cursor.fetchone()
        cursor.close()

        if admin_user:
            reset_token = create_verification_token(length=32)
            expires_at = datetime.now() + timedelta(hours=1)

            try:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO admin_password_resets (admin_id, token, expires_at, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (admin_user['id'], reset_token, expires_at, datetime.now()))
                db.commit()
                cursor.close()

                reset_link = f"https://yoursite.com/admin-reset-password/{reset_token}"
                flash(f"Password reset link sent to {admin_user['email']}", "success")
                log_event(admin_user['id'], 'ADMIN_PASSWORD_RESET_REQUESTED', username)
            except Exception as e:
                flash("Error processing request. Please try again.", "error")
                print(f"Error: {e}")
        else:
            flash("Admin account not found", "error")

    return render_template("admin_forgot_password.html")

@auth.route("/admin-reset-password/<token>", methods=["GET", "POST"])
def admin_reset_password(token):
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT admin_id FROM admin_password_resets
        WHERE token = %s AND expires_at > %s
    """, (token, datetime.now()))
    reset_record = cursor.fetchone()
    cursor.close()

    if not reset_record:
        flash("Invalid or expired reset link", "error")
        return redirect(url_for('auth.admin_login'))

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        is_valid, error = validate_password(password)
        if not is_valid:
            flash(f"Password: {error}", "error")
            return redirect(url_for('auth.admin_reset_password', token=token))

        if password != password_confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for('auth.admin_reset_password', token=token))

        hashed_password = generate_password_hash(password)

        try:
            cursor = db.cursor()
            cursor.execute("UPDATE admin_users SET password_hash = %s WHERE id = %s",
                          (hashed_password, reset_record['admin_id']))
            cursor.execute("DELETE FROM admin_password_resets WHERE token = %s", (token,))
            db.commit()
            cursor.close()

            log_event(reset_record['admin_id'], 'ADMIN_PASSWORD_RESET_SUCCESS', "Password reset")
            flash("Password reset successfully. Please login.", "success")
            return redirect(url_for('auth.admin_login'))
        except Exception as e:
            flash("Error resetting password", "error")
            print(f"Error: {e}")

    return render_template("admin_reset_password.html", token=token)

@auth.route("/admin-panel")
def admin_panel():
    if 'admin' not in session:
        flash("Please login as admin first", "error")
        return redirect(url_for('auth.admin_login'))

    cursor = db.cursor(dictionary=True)

    # Get stats
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM testimonials WHERE status = 'pending'")
    pending_testimonials = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM testimonials WHERE status = 'approved'")
    approved_testimonials = cursor.fetchone()['count']

    # Get pending testimonials
    cursor.execute("SELECT * FROM testimonials WHERE status = 'pending' ORDER BY created_at DESC")
    testimonials = cursor.fetchall()

    cursor.close()

    return render_template("admin_panel.html",
                         user_count=user_count,
                         pending_testimonials=pending_testimonials,
                         approved_testimonials=approved_testimonials,
                         testimonials=testimonials)

@auth.route("/admin-approve-testimonial/<int:testimonial_id>")
def approve_testimonial(testimonial_id):
    if 'admin' not in session:
        return redirect(url_for('auth.admin_login'))

    cursor = db.cursor()
    cursor.execute("UPDATE testimonials SET status = 'approved' WHERE id = %s", (testimonial_id,))
    db.commit()
    cursor.close()

    flash("Testimonial approved", "success")
    return redirect(url_for('auth.admin_panel'))

@auth.route("/admin-reject-testimonial/<int:testimonial_id>")
def reject_testimonial(testimonial_id):
    if 'admin' not in session:
        return redirect(url_for('auth.admin_login'))

    cursor = db.cursor()
    cursor.execute("UPDATE testimonials SET status = 'rejected' WHERE id = %s", (testimonial_id,))
    db.commit()
    cursor.close()

    flash("Testimonial rejected", "success")
    return redirect(url_for('auth.admin_panel'))

@auth.route("/admin-logout")
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_name', None)
    flash("Admin logged out", "success")
    return redirect(url_for('auth.admin_login'))


@auth.route("/verify-email/<token>")
def verify_email(token):
    """Verify email with token"""
    if not token:
        flash("Invalid verification link", "error")
        return redirect(url_for('auth.login'))

    success, user_id, error = verify_token(token, db)

    if success:
        flash("Email verified successfully! You can now login.", "success")
        return redirect(url_for('auth.login'))
    else:
        flash(f"Verification failed: {error}", "error")
        return redirect(url_for('auth.login'))


@auth.route("/resend-verification", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def resend_verification():
    """Resend verification email"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        # Validate email
        is_valid, error = validate_email(email)
        if not is_valid:
            flash(f"Email: {error}", "error")
            return redirect(url_for('auth.resend_verification'))

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, full_name, email_verified FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            flash("Email not found", "error")
            return redirect(url_for('auth.resend_verification'))

        if user['email_verified']:
            flash("This email is already verified", "info")
            return redirect(url_for('auth.login'))

        # Create new verification token
        from email_verification import resend_verification_token
        token = resend_verification_token(user['id'], db)

        if token:
            app_url = os.getenv('APP_URL', 'http://127.0.0.1:5000')
            verification_link = f"{app_url}/verify-email/{token}"
            success, error_msg = send_resend_verification_email(email, user['full_name'], verification_link)

            if success:
                flash("Verification email sent! Please check your inbox.", "success")
            else:
                print(f"Warning: Email not sent: {error_msg}")
                flash("Error sending email. Please try again later.", "error")
        else:
            flash("Error creating verification token", "error")

        return redirect(url_for('auth.login'))

    return render_template("resend_verification.html")
