"""
OTP service module for generating and verifying one-time passwords via email.

Functions:
    generate_otp(email): Generates and sends an OTP to the provided email address.
    verify_otp(email, otp): Verifies the OTP for the provided email address.

Note:
    Any user_id argument is of type uuid.
"""

from email.mime.text import MIMEText
import pyotp
import hmac
import hashlib
import base64
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

general_secret = os.getenv("OTP_SECRET")
password = os.getenv("APP_PASSWORD")

def generate_otp(email):
    """
    Generates and sends an OTP to the provided email address.

    Args:
        email (str): Email address to send OTP.

    Returns:
        tuple: Message and HTTP status code.
    """
    h = hmac.new(general_secret.encode('utf-8'), email.encode('utf-8'), hashlib.sha256)
    digest = h.digest()

    user_secret = base64.b32encode(digest).decode('utf-8')

    totp = pyotp.TOTP(user_secret, interval=180, digits=6)
    otp = totp.now()

    body = f"""This is the otp: {otp} to verify your email please do not share with anyone and it will expire in 3 minutes. 
    If you didn't perform this action please contact us
    """

    message = MIMEText(body)
    message['Subject'] = "Action required to verify email"
    message['From'] = "fabiyipelumi0@gmail.com"
    message['To'] = email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login("fabiyipelumi0@gmail.com", password)
        server.sendmail(message['From'], message['To'], message.as_string())

    return {
        "message": "email sent, check your mail for otp"
    }, 200

def verify_otp(email, otp):
    """
    Verifies the OTP for the provided email address.

    Args:
        email (str): Email address.
        otp (str): One-time password to verify.

    Returns:
        bool: True if OTP is valid, False otherwise.
    """
    h = hmac.new(general_secret.encode('utf-8'), email.encode('utf-8'), hashlib.sha256)
    digest = h.digest()

    user_secret = base64.b32encode(digest).decode('utf-8')

    totp = pyotp.TOTP(user_secret, interval=180, digits=6)
    verified = totp.verify(otp, valid_window=1)

    return verified
