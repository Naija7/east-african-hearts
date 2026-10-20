"""Email sending functionality for East African Hearts"""

from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

load_dotenv()

mail = Mail()


def _send_async(msg):
    """Send in a background thread so the request returns immediately.
    Failures are logged, not raised (users can use "resend verification")."""
    import threading
    from flask import current_app
    app = current_app._get_current_object()

    def run():
        try:
            with app.app_context():
                mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")

    threading.Thread(target=run, daemon=True).start()


def init_email(app):
    """Initialize Flask-Mail with app"""
    # Configure email settings
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@eastafricanhearts.com')

    mail.init_app(app)
    return mail


def send_verification_email(email, name, verification_link):
    """
    Send email verification link to user
    """
    subject = "Verify Your Email - East African Hearts"

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h1 style="color: #e91e63; margin-bottom: 20px;">Welcome to East African Hearts! 💕</h1>

                <p style="font-size: 16px; color: #333; line-height: 1.6;">
                    Hi <strong>{name}</strong>,
                </p>

                <p style="font-size: 16px; color: #333; line-height: 1.6;">
                    Thank you for registering with East African Hearts! To complete your signup and start finding your perfect match, please verify your email address by clicking the button below.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" style="background-color: #e91e63; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>

                <p style="font-size: 14px; color: #666; line-height: 1.6;">
                    Or copy and paste this link in your browser:
                </p>
                <p style="font-size: 12px; color: #999; word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                    {verification_link}
                </p>

                <p style="font-size: 14px; color: #999; margin-top: 20px;">
                    <strong>Important:</strong> This link will expire in 24 hours.
                </p>

                <p style="font-size: 14px; color: #999; line-height: 1.6;">
                    If you did not create this account, please ignore this email.
                </p>

                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

                <p style="font-size: 12px; color: #999; text-align: center;">
                    © 2026 East African Hearts. All rights reserved.<br>
                    Connecting Hearts Across East Africa
                </p>
            </div>
        </body>
    </html>
    """

    text_body = f"""
    Welcome to East African Hearts!

    Hi {name},

    Thank you for registering! To complete your signup, please verify your email by visiting:
    {verification_link}

    This link will expire in 24 hours.

    If you did not create this account, please ignore this email.

    © 2026 East African Hearts. All rights reserved.
    """

    try:
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            body=text_body
        )
        _send_async(msg)
        return True, None
    except Exception as e:
        print(f"Error sending email: {e}")
        return False, str(e)


def send_resend_verification_email(email, name, verification_link):
    """
    Send resend verification email to user
    """
    subject = "Resend: Verify Your Email - East African Hearts"

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h1 style="color: #e91e63; margin-bottom: 20px;">Verify Your Email - East African Hearts 💕</h1>

                <p style="font-size: 16px; color: #333; line-height: 1.6;">
                    Hi <strong>{name}</strong>,
                </p>

                <p style="font-size: 16px; color: #333; line-height: 1.6;">
                    Here's a fresh verification link to complete your email verification. Click below to verify your account.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" style="background-color: #e91e63; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>

                <p style="font-size: 14px; color: #999; margin-top: 20px;">
                    <strong>Important:</strong> This link will expire in 24 hours.
                </p>

                <p style="font-size: 12px; color: #999; text-align: center; margin-top: 30px;">
                    © 2026 East African Hearts. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """

    try:
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body
        )
        _send_async(msg)
        return True, None
    except Exception as e:
        print(f"Error sending email: {e}")
        return False, str(e)
