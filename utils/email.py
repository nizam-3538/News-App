import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SENDER, EMAIL_PASSWORD

def _send_email(to_email: str, subject: str, html_content: str):
    """
    Core SMTP helper to send secure emails via Gmail.
    """
    try:
        # Create a secure SSL context
        context = ssl.create_default_context()
        
        # Create the MIME message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"PulseNews <{EMAIL_SENDER}>"
        message["To"] = to_email
        
        # Attach HTML content
        part = MIMEText(html_content, "html")
        message.attach(part)
        
        # Connect and Send
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, message.as_string())
            
        print(f"📧 Email successfully sent to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP Error: Authentication failed. Please check your App Password.")
        return False
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def send_verification_email(to_email: str, otp: str):
    """
    Sends a 6-digit OTP verification code using the Gmail SMTP server.
    """
    subject = "Your PulseNews Verification Code"
    html_content = f"""
        <div style="font-family: sans-serif; max-width: 400px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
            <h2 style="color: #2563eb;">PulseNews Verification</h2>
            <p>Welcome! Use the 6-digit code below to verify your account:</p>
            <div style="background: #f1f5f9; padding: 16px; border-radius: 8px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #0f172a;">
                {otp}
            </div>
            <p style="font-size: 12px; color: #64748b; margin-top: 20px;">This code will expire in 10 minutes.</p>
        </div>
    """
    return _send_email(to_email, subject, html_content)

def send_password_reset_email(to_email: str, otp: str):
    """
    Sends a password reset token (reserved for future implementation).
    """
    subject = "Reset Your PulseNews Password"
    html_content = f"""
        <div style="font-family: sans-serif; max-width: 400px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
            <h2 style="color: #ef4444;">Password Reset</h2>
            <p>We received a request to reset your password. Use the following code:</p>
            <div style="background: #fef2f2; padding: 16px; border-radius: 8px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #b91c1c;">
                {otp}
            </div>
            <p style="font-size: 12px; color: #64748b; margin-top: 20px;">If you didn't request this, you can ignore this email.</p>
        </div>
    """
    return _send_email(to_email, subject, html_content)
