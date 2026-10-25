from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader
from utils import compress_image, validate_image_file, get_image_size_mb, log_event, log_error, log_info
from validators import (validate_email, validate_password, validate_name,
                       validate_age, validate_location, validate_bio,
                       validate_interests, validate_message)
from rate_limiter import limiter
from email_verification import (create_verification_token, verify_token,
                                generate_verification_token,
                                create_password_reset_token,
                                verify_password_reset_token,
                                complete_password_reset)
from email_sender import (send_verification_email, send_resend_verification_email,
                          send_password_reset_email, send_admin_password_reset_email)
from db import get_db

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

auth = Blueprint('auth', __name__)


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per 15 minutes", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validate email format
        is_valid, error = validate_email(email)
        if not is_valid:
            flash(error, "error")
            return redirect(url_for('auth.login'))

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            # Enforce email verification if enabled in configuration
            verification_enabled = os.getenv('EMAIL_VERIFICATION_ENABLED', 'false').lower() == 'true'
            if verification_enabled and not user.get('email_verified'):
                flash("Please verify your email address before logging in. If needed, request a new link below.", "warning")
                return redirect(url_for('auth.resend_verification'))

            # Prevent session fixation
            session.clear()
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
        is_valid, error = validate_name(name)
        if not is_valid:
            flash(f"Name: {error}", "error")
            return redirect(url_for('auth.register'))

        is_valid, error = validate_email(email)
        if not is_valid:
            flash(f"Email: {error}", "error")
            return redirect(url_for('auth.register'))

        is_valid, error = validate_password(password)
        if not is_valid:
            flash(f"Password: {error}", "error")
            return redirect(url_for('auth.register'))

        if password != password_confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for('auth.register'))

        if gender not in ['Male', 'Female', 'Other']:
            flash("Invalid gender selection", "error")
            return redirect(url_for('auth.register'))

        is_valid, error = validate_age(age)
        if not is_valid:
            flash(f"Age: {error}", "error")
            return redirect(url_for('auth.register'))

        is_valid, error = validate_location(location)
        if not is_valid:
            flash(f"Location: {error}", "error")
            return redirect(url_for('auth.register'))

        is_valid, error = validate_interests(interests)
        if not is_valid:
            flash(f"Interests: {error}", "error")
            return redirect(url_for('auth.register'))

        # Handle photo upload - now handled via edit profile with Cloudinary
        # Registration doesn't store photos anymore, users add them later
        photo_binary = None
        # Cloudinary photos are uploaded via /profile/edit route

        db = get_db()
        cursor = db.cursor()

        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("Email already registered", "error")
            cursor.close()
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)

        try:
            # Atomic transaction: Insert user and profile together
            sql = "INSERT INTO users (full_name, email, password_hash, gender, age) VALUES (%s, %s, %s, %s, %s)"
            values = (name, email, hashed_password, gender, age)
            cursor.execute(sql, values)
            user_id = cursor.lastrowid

            # Insert profile without photo (NULL) - users add photos via edit profile
            profile_sql = "INSERT INTO profiles (user_id, bio, interests, location, profile_picture) VALUES (%s, %s, %s, %s, NULL)"
            profile_values = (user_id, "", interests, location)
            cursor.execute(profile_sql, profile_values)

            # Email verification check
            verification_enabled = os.getenv('EMAIL_VERIFICATION_ENABLED', 'false').lower() == 'true'
            if not verification_enabled:
                cursor.execute("UPDATE users SET email_verified = 1 WHERE id = %s", (user_id,))
                db.commit()
                cursor.close()
                flash("Registration successful! You can now log in.", "success")
                return redirect(url_for('auth.login'))

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
                    print(f"Warning: Verification email could not be queued: {error}")
                    flash("Registration successful! You may need to resend verification if email doesn't arrive.", "warning")
            else:
                flash("Registration successful! Please check your email to verify your account.", "success")

            cursor.close()
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.rollback()
            log_error(f"Registration Error: {e}", exc_info=True, user_id=0)
            flash("Registration failed. Please try again.", "error")
            cursor.close()

    return render_template("register.html")


@auth.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('home.index'))


# ----------------------------------------------------
# USER PASSWORD RESET ROUTES
# ----------------------------------------------------
@auth.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def forgot_password():
    """Request password reset link for user account"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        is_valid, error = validate_email(email)
        if not is_valid:
            flash(f"Email: {error}", "error")
            return redirect(url_for('auth.forgot_password'))

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, full_name, email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        # Send reset email if user exists (generic message to avoid email enumeration)
        if user:
            token = create_password_reset_token(user['id'], db)
            if token:
                app_url = os.getenv('APP_URL', 'http://127.0.0.1:5000').rstrip('/')
                reset_link = f"{app_url}/reset-password/{token}"
                send_password_reset_email(user['email'], user['full_name'], reset_link)
                log_event(user['id'], 'PASSWORD_RESET_REQUESTED', f"Reset requested from {request.remote_addr}")

        flash("If an account exists with that email, we have sent a password reset link.", "info")
        return redirect(url_for('auth.login'))

    return render_template("forgot_password.html")


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def reset_password(token):
    """Set new password using verified reset token"""
    db = get_db()
    is_valid, user_id, error = verify_password_reset_token(token, db)

    if not is_valid:
        flash(error or "Invalid or expired password reset link.", "error")
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        is_valid_pw, error_pw = validate_password(password)
        if not is_valid_pw:
            flash(f"Password: {error_pw}", "error")
            return redirect(url_for('auth.reset_password', token=token))

        if password != password_confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for('auth.reset_password', token=token))

        hashed_password = generate_password_hash(password)
        success = complete_password_reset(user_id, hashed_password, db)

        if success:
            log_event(user_id, 'PASSWORD_RESET_SUCCESS', f"Password reset from {request.remote_addr}")
            flash("Password reset successfully! You can now log in.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Failed to update password. Please try again.", "error")

    return render_template("reset_password.html", token=token)


# ----------------------------------------------------
# ADMIN AUTH & MANAGEMENT
# ----------------------------------------------------
@auth.route("/admin-login", methods=["GET", "POST"])
@limiter.limit("10 per 15 minutes", methods=["POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, password_hash FROM admin_users WHERE username = %s", (username,))
        admin_user = cursor.fetchone()
        cursor.close()

        if admin_user and check_password_hash(admin_user['password_hash'], password):
            session.clear()
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
@limiter.limit("5 per hour", methods=["POST"])
def admin_forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, email FROM admin_users WHERE username = %s", (username,))
        admin_user = cursor.fetchone()
        cursor.close()

        if admin_user:
            reset_token = generate_verification_token(32)
            expires_at = datetime.now() + timedelta(hours=1)

            try:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO admin_password_resets (admin_id, token, expires_at, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (admin_user['id'], reset_token, expires_at, datetime.now()))
                db.commit()
                cursor.close()

                app_url = os.getenv('APP_URL', 'http://127.0.0.1:5000').rstrip('/')
                reset_link = f"{app_url}/admin-reset-password/{reset_token}"
                send_admin_password_reset_email(admin_user['email'], username, reset_link)

                flash(f"Password reset link sent to {admin_user['email']}", "success")
                log_event(admin_user['id'], 'ADMIN_PASSWORD_RESET_REQUESTED', username)
            except Exception as e:
                db.rollback()
                log_error(f"Admin reset request error: {e}", exc_info=True, user_id=admin_user['id'])
                flash("Error processing request. Please try again.", "error")
                print(f"Admin reset request error: {e}")
        else:
            flash("Admin account not found", "error")

    return render_template("admin_forgot_password.html")


@auth.route("/admin-reset-password/<token>", methods=["GET", "POST"])
def admin_reset_password(token):
    db = get_db()
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
            cursor.execute("DELETE FROM admin_password_resets WHERE admin_id = %s", (reset_record['admin_id'],))
            db.commit()
            cursor.close()

            log_event(reset_record['admin_id'], 'ADMIN_PASSWORD_RESET_SUCCESS', "Admin password reset")
            flash("Password reset successfully. Please login.", "success")
            return redirect(url_for('auth.admin_login'))
        except Exception as e:
            db.rollback()
            log_error(f"Error resetting admin password: {e}", exc_info=True, user_id=reset_record['admin_id'])
            flash("Error resetting password", "error")
            print(f"Error resetting admin password: {e}")

    return render_template("admin_reset_password.html", token=token)


@auth.route("/admin-panel")
def admin_panel():
    if not session.get('admin'):
        flash("Please login as admin first", "error")
        return redirect(url_for('auth.admin_login'))

    db = get_db()
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


@auth.route("/admin-approve-testimonial/<int:testimonial_id>", methods=["GET", "POST"])
def approve_testimonial(testimonial_id):
    if not session.get('admin'):
        return redirect(url_for('auth.admin_login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE testimonials SET status = 'approved' WHERE id = %s", (testimonial_id,))
    db.commit()
    cursor.close()

    flash("Testimonial approved", "success")
    return redirect(url_for('auth.admin_panel'))


@auth.route("/admin-reject-testimonial/<int:testimonial_id>", methods=["GET", "POST"])
def reject_testimonial(testimonial_id):
    if not session.get('admin'):
        return redirect(url_for('auth.admin_login'))

    db = get_db()
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
    session.pop('admin_id', None)
    flash("Admin logged out", "success")
    return redirect(url_for('auth.admin_login'))


# ----------------------------------------------------
# EMAIL VERIFICATION
# ----------------------------------------------------
@auth.route("/verify-email/<token>")
def verify_email(token):
    """Verify email with token"""
    if not token:
        flash("Invalid verification link", "error")
        return redirect(url_for('auth.login'))

    db = get_db()
    success, user_id, error = verify_token(token, db)

    if success:
        flash("Email verified successfully! You can now login.", "success")
        return redirect(url_for('auth.login'))
    else:
        flash(f"Verification failed: {error}", "error")
        return redirect(url_for('auth.login'))


@auth.route("/resend-verification", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def resend_verification():
    """Resend verification email"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        is_valid, error = validate_email(email)
        if not is_valid:
            flash(f"Email: {error}", "error")
            return redirect(url_for('auth.resend_verification'))

        db = get_db()
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

        from email_verification import resend_verification_token
        token = resend_verification_token(user['id'], db)

        if token:
            app_url = os.getenv('APP_URL', 'http://127.0.0.1:5000').rstrip('/')
            verification_link = f"{app_url}/verify-email/{token}"
            success, error_msg = send_resend_verification_email(email, user['full_name'], verification_link)

            if success:
                flash("Verification email sent! Please check your inbox.", "success")
            else:
                print(f"Warning: Verification email failed: {error_msg}")
                flash("Error sending email. Please try again later.", "error")
        else:
            flash("Error creating verification token", "error")

        return redirect(url_for('auth.login'))

@auth.route("/profile")
def view_profile():
    if 'user_id' not in session:
        flash("Please login to view your profile", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.id, u.full_name, u.email, u.age, u.gender, p.bio, p.interests, p.location, p.profile_picture
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE u.id = %s
    """, (user_id,))

    user = cursor.fetchone()
    cursor.close()

    if not user:
        flash("User not found", "error")
        return redirect(url_for('home.index'))

    return render_template("profile.html", user=user, lang=session.get('language', 'en'))

@auth.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if 'user_id' not in session:
        flash("Please login to edit your profile", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    db = get_db()

    if request.method == "POST":
        bio = request.form.get("bio", "").strip()
        interests = request.form.get("interests", "").strip()
        location = request.form.get("location", "").strip()
        photo = request.files.get("photo")

        photo_url = None
        if photo and photo.filename:
            is_valid, error = validate_image_file(photo)
            if not is_valid:
                flash(error, "error")
                return redirect(url_for('auth.edit_profile'))

            photo_data = photo.read()
            size_mb = get_image_size_mb(len(photo_data))
            if size_mb > 15:
                flash("Photo must be less than 15MB", "error")
                return redirect(url_for('auth.edit_profile'))

            try:
                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    photo_data,
                    folder="east-african-hearts/profiles",
                    resource_type="auto",
                    quality="auto",  # Auto-optimize
                    width=500,
                    height=500,
                    crop="fill",
                    overwrite=True,
                    unique_filename=False,
                    public_id=f"user_{user_id}"
                )
                photo_url = result['secure_url']
                log_info(f"Photo uploaded to Cloudinary for user {user_id}", user_id=user_id)
            except Exception as e:
                log_error(f"Cloudinary upload error for user {user_id}: {e}", exc_info=True, user_id=user_id)
                flash("Error uploading photo. Please try again.", "error")
                return redirect(url_for('auth.edit_profile'))

        cursor = db.cursor()
        try:
            if photo_url:
                cursor.execute("""
                    UPDATE profiles
                    SET bio = %s, interests = %s, location = %s, profile_picture = %s
                    WHERE user_id = %s
                """, (bio, interests, location, photo_url, user_id))
            else:
                cursor.execute("""
                    UPDATE profiles
                    SET bio = %s, interests = %s, location = %s
                    WHERE user_id = %s
                """, (bio, interests, location, user_id))

            db.commit()
            log_event(user_id, 'PROFILE_UPDATE', 'Profile updated')
            flash("Profile updated successfully!", "success")
            return redirect(url_for('auth.view_profile'))
        except Exception as e:
            log_error(f"Profile update error for user {user_id}: {e}", exc_info=True, user_id=user_id)
            flash("Error updating profile. Please try again.", "error")
        finally:
            cursor.close()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.full_name, u.email, u.age, u.gender, p.bio, p.interests, p.location, p.profile_picture
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE u.id = %s
    """, (user_id,))

    user = cursor.fetchone()
    cursor.close()

    if not user:
        flash("User not found", "error")
        return redirect(url_for('home.index'))

    return render_template("edit_profile.html", user=user, lang=session.get('language', 'en'))

    return render_template("resend_verification.html")
