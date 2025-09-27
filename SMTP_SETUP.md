# Astrid Global Ltd Trading Platform - Email Setup Guide

## 🚀 Recommended: MailerSend API (Railway Compatible)

**MailerSend API is the best option for Railway deployment** - it uses HTTP requests instead of SMTP connections, avoiding Railway's network restrictions.

### Setup MailerSend:
1. Sign up at [MailerSend](https://mailersend.com)
2. Create an API token at [API Tokens](https://app.mailersend.com/api-tokens)
3. Set this environment variable in Railway:

```bash
MAILERSEND_TOKEN=your_actual_api_token_here
```

### Optional: Configure From Email
```bash
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Astrid Global Ltd
```

## 📧 How It Works:
- ✅ **MailerSend API first** - Fast, reliable HTTP requests
- ✅ **SMTP fallback** - If MailerSend fails or isn't configured
- ✅ **No timeouts** - HTTP requests work perfectly on Railway
- ✅ **Development mode** - Skips emails if no configuration

## 🔧 Legacy SMTP Setup (Not Recommended for Railway)

If you prefer SMTP, use one of these Railway-compatible services:

### SendGrid SMTP:
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.your_sendgrid_api_key_here
```

### Mailgun SMTP:
```bash
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=postmaster@yourdomain.mailgun.org
SMTP_PASSWORD=your_mailgun_password
```

## 🚀 Deployment

After setting up `MAILERSEND_TOKEN` in Railway environment variables, redeploy your service. Email sending will work without any timeouts!

## 📧 Email Types

The platform sends these emails:
- Welcome emails after signup
- Login notifications
- Withdrawal requests/approvals
- Trade execution confirmations
- Strategy subscription confirmations
- Password reset emails
