#!/usr/bin/env python3
"""
Test Gmail SMTP connection independently
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_connection():
    """Test Gmail SMTP connection with App Password"""
    
    # Gmail SMTP settings
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    email = "razavcf@gmail.com"
    password = "nbpabpjwzzbaanai"  # App Password from .env
    
    try:
        print("Testing Gmail SMTP connection...")
        print(f"Email: {email}")
        print(f"Server: {smtp_server}:{smtp_port}")
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email  # Send to self for testing
        msg['Subject'] = "QuMail SMTP Test"
        
        body = "This is a test email from QuMail to verify SMTP connection."
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP
        print("Connecting to Gmail SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print("Attempting login...")
        server.login(email, password)
        
        print("Login successful! Sending test email...")
        text = msg.as_string()
        server.sendmail(email, email, text)
        server.quit()
        
        print("✅ SUCCESS: Gmail SMTP test passed!")
        print("✅ App Password is working correctly")
        print("✅ Email sent successfully")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("❌ AUTHENTICATION ERROR:")
        print(f"   {e}")
        print("\n🔧 SOLUTIONS:")
        print("1. Check if 2-Factor Authentication is enabled on Gmail")
        print("2. Generate a new App Password:")
        print("   - Go to https://myaccount.google.com/apppasswords")
        print("   - Select 'Mail' and 'Other (Custom name)'")
        print("   - Enter 'QuMail' as the name")
        print("   - Copy the new 16-character password")
        print("3. Make sure you're using the App Password, not your regular password")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n🔧 SOLUTIONS:")
        print("1. Check your internet connection")
        print("2. Verify Gmail SMTP settings")
        print("3. Check if Gmail is blocking the connection")
        return False

if __name__ == "__main__":
    test_gmail_connection()