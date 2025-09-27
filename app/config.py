import os
from dotenv import load_dotenv

class QuartConfig:
    load_dotenv()
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

    # Supabase Database Configuration
    # Use the pooled connection for better performance
    DATABASE_URL = os.getenv('DATABASE_URL')

    # If DATABASE_URL is not provided, construct from individual components
    if not DATABASE_URL:
        db_host = os.getenv('SUPABASE_DB_HOST')
        db_port = os.getenv('SUPABASE_DB_PORT', '6543')
        db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
        db_user = os.getenv('SUPABASE_DB_USER')
        db_password = os.getenv('SUPABASE_DB_PASSWORD')

        if db_host and db_user and db_password:
            DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"

    # Supabase Keys (for future use if needed)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Use 'None' in production with HTTPS
    SESSION_COOKIE_DOMAIN = None  # Allow any domain

    # Email settings (MailerSend API preferred, Railway-compatible)
    # For Railway deployment, use MailerSend API token:
    # MAILERSEND_TOKEN=your_mailersend_api_token_here
    #
    # Get token from: https://app.mailersend.com/api-tokens
    #
    # SMTP fallback for development:
    MAILERSEND_TOKEN = os.getenv('MAILERSEND_TOKEN', '')
    SMTP_SERVER = os.getenv('SMTP_SERVER', '')  # Empty for development (skips emails)
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'admin@astridglobal.com')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Astrid Global Ltd')
