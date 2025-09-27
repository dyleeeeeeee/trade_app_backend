import aiosmtplib
from email.message import EmailMessage
from quart import current_app
import asyncio
from mailersend import MailerSendClient, EmailBuilder

# RAILWAY SMTP SETUP GUIDE:
#
# Railway blocks traditional SMTP. Use MailerSend API instead:
#
# Set this environment variable in Railway:
# MAILERSEND_TOKEN=your_mailersend_api_token_here
#
# Get your token from: https://app.mailersend.com/api-tokens
#
# The app will automatically use MailerSend API if MAILERSEND_TOKEN is set,
# otherwise falls back to SMTP (for development).

class EmailService:
    def __init__(self):
        # Don't access current_app here - it will be done when needed
        pass

    def _get_config(self):
        """Get email configuration from current app context"""
        return {
            'mailersend_token': current_app.config.get('MAILERSEND_TOKEN', ''),
            'smtp_server': current_app.config['SMTP_SERVER'],
            'smtp_port': current_app.config['SMTP_PORT'],
            'smtp_username': current_app.config['SMTP_USERNAME'],
            'smtp_password': current_app.config['SMTP_PASSWORD'],
            'email_from': current_app.config['EMAIL_FROM'],
            'email_from_name': current_app.config['EMAIL_FROM_NAME']
        }

    async def send_email(self, to_email: str, subject: str, body: str):
        """Send an email asynchronously using MailerSend API or SMTP fallback"""
        try:
            config = self._get_config()

            # Try MailerSend API first if token is available
            if config['mailersend_token']:
                try:
                    return await self._send_via_mailersend(config, to_email, subject, body)
                except Exception as e:
                    print(f"MailerSend API failed, falling back to SMTP: {str(e)}")
                    # Fall back to SMTP if MailerSend fails

            # Fall back to SMTP or skip if not configured
            if not config['smtp_server'] or config['smtp_server'] == 'smtp.gmail.com':
                print(f"Email sending skipped (SMTP not configured or using Gmail): {to_email}")
                return

            # Use SMTP as fallback
            return await self._send_via_smtp(config, to_email, subject, body)

        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            # Don't raise exception - email failure shouldn't break the app

    async def _send_via_mailersend(self, config, to_email: str, subject: str, body: str):
        """Send email using MailerSend SDK"""
        try:
            # Initialize MailerSend client
            ms = MailerSendClient(api_key=config['mailersend_token'])

            # Build email using the official SDK
            email = (EmailBuilder()
                     .from_email(config['email_from'], config['email_from_name'])
                     .to_many([{"email": to_email}])
                     .subject(subject)
                     .html(f"<div style='font-family: Arial, sans-serif; white-space: pre-line;'>{body}</div>")
                     .text(body)
                     .build())

            # Send email using asyncio.to_thread since SDK is synchronous
            response = await asyncio.to_thread(ms.emails.send, email)

            # Check response
            if response.success:
                # Extract message ID if available
                message_id = getattr(response, 'headers', {}).get('x-message-id', 'unknown')
                print(f"Email sent successfully via MailerSend SDK to {to_email} (ID: {message_id})")
                return True
            else:
                error_msg = getattr(response, 'data', {}).get('message', 'Unknown error')
                status_code = getattr(response, 'status_code', 'unknown')
                print(f"MailerSend SDK error for {to_email} (status {status_code}): {error_msg}")
                raise Exception(f"API error ({status_code}): {error_msg}")

        except Exception as e:
            print(f"MailerSend SDK failed for {to_email}: {str(e)}")
            raise

    async def _send_via_smtp(self, config, to_email: str, subject: str, body: str):
        """Send email using SMTP as fallback"""
        try:
            # Handle different SMTP providers
            use_tls = True
            starttls_needed = False

            # SendGrid SMTP settings (Railway-compatible)
            if 'smtp.sendgrid.net' in config['smtp_server']:
                use_tls = True
                starttls_needed = False
            # Mailgun SMTP settings
            elif 'smtp.mailgun.org' in config['smtp_server']:
                use_tls = True
                starttls_needed = False
            # Amazon SES
            elif 'email-smtp' in config['smtp_server']:
                use_tls = True
                starttls_needed = False

            # Create message
            msg = EmailMessage()
            msg['From'] = f"{config['email_from_name']} <{config['email_from']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.set_content(body)

            # Send email with timeout
            timeout = 30  # 30 second timeout for email sending
            try:
                async with asyncio.timeout(timeout):
                    async with aiosmtplib.SMTP(
                        hostname=config['smtp_server'],
                        port=config['smtp_port'],
                        use_tls=use_tls,
                        timeout=10  # Connection timeout
                    ) as smtp:
                        if starttls_needed:
                            await smtp.starttls()
                        if config['smtp_username'] and config['smtp_password']:
                            await smtp.login(config['smtp_username'], config['smtp_password'])
                        await smtp.send_message(msg)

                print(f"Email sent successfully via SMTP to {to_email}")

            except asyncio.TimeoutError:
                print(f"SMTP sending timed out for {to_email}")
            except aiosmtplib.SMTPException as e:
                print(f"SMTP error sending email to {to_email}: {str(e)}")
            except Exception as e:
                print(f"Unexpected SMTP error sending email to {to_email}: {str(e)}")

        except Exception as e:
            print(f"SMTP fallback failed for {to_email}: {str(e)}")
            raise

    async def send_welcome_email(self, email: str, name: str = None):
        """Send welcome email after signup"""
        subject = "Welcome to Astrid Global Ltd Trading Platform!"
        if name:
            greeting = f"Hello {name},"
        else:
            greeting = "Hello,"

        body = f"""{greeting}

Welcome to Astrid Global Ltd Trading Platform! Your account has been successfully created.

You can now:
- Deposit funds to start trading
- Place buy/sell orders on various assets
- Subscribe to copy trading strategies
- Monitor your portfolio in real-time

For security reasons, we recommend:
- Never share your login credentials
- Enable two-factor authentication when available
- Keep your account information up to date

If you have any questions, please don't hesitate to contact our support team.

Happy trading!

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

    async def send_login_notification(self, email: str, ip_address: str = "Unknown", user_agent: str = "Unknown"):
        """Send login notification email"""
        subject = "New Login to Your Astrid Global Ltd Account"

        body = f"""Hello,

We detected a new login to your Astrid Global Ltd Trading account.

Login Details:
- Time: {asyncio.get_event_loop().time()}  # This would be better with proper datetime
- IP Address: {ip_address}
- Device/Browser: {user_agent}

If this was you, no action is needed.

If you don't recognize this activity, please:
1. Change your password immediately
2. Contact our support team
3. Review your account activity

For your security, we recommend enabling additional security measures.

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

    async def send_withdrawal_request_email(self, email: str, amount: float, withdrawal_id: int):
        """Send withdrawal request confirmation"""
        subject = "Withdrawal Request Submitted - Astrid Global Ltd"

        body = f"""Hello,

Your withdrawal request has been successfully submitted.

Withdrawal Details:
- Amount: ${amount:.2f}
- Request ID: {withdrawal_id}
- Status: Pending Review

What happens next:
1. Our team will review your withdrawal request (usually within 1-2 business days)
2. Once approved, funds will be processed to your designated withdrawal method
3. You will receive another email confirming the completion

Please note:
- All withdrawals are subject to security verification
- Large amounts may require additional documentation
- Processing times may vary depending on your location and withdrawal method

If you have any questions about this withdrawal, please contact support with the request ID.

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

    async def send_withdrawal_approved_email(self, email: str, amount: float, withdrawal_id: int):
        """Send withdrawal approval notification"""
        subject = "Withdrawal Approved - Astrid Global Ltd"

        body = f"""Hello,

Great news! Your withdrawal request has been approved and processed.

Withdrawal Details:
- Amount: ${amount:.2f}
- Request ID: {withdrawal_id}
- Status: Completed

The funds have been sent to your designated withdrawal method. Processing times vary by method:
- Bank Transfer: 1-3 business days
- Crypto Wallet: Usually instant to a few hours
- Other methods: Check the processing time for your specific method

Please check your account/balance to confirm receipt of funds.

If you don't receive the funds within the expected timeframe, please contact support with the withdrawal ID.

Thank you for using Astrid Global Ltd!

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

    async def send_withdrawal_rejected_email(self, email: str, amount: float, withdrawal_id: int, reason: str = None):
        """Send withdrawal rejection notification"""
        subject = "Withdrawal Request Update - Astrid Global Ltd"

        body = f"""Hello,

We regret to inform you that your withdrawal request has been declined.

Withdrawal Details:
- Amount: ${amount:.2f}
- Request ID: {withdrawal_id}
- Status: Rejected

{f"Reason for rejection: {reason}" if reason else "Please contact support for more details about why this withdrawal was declined."}

If you believe this is an error or need assistance, please contact our support team with the withdrawal ID.

We apologize for any inconvenience this may cause.

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

    async def send_trade_executed_email(self, email: str, asset: str, side: str, size: float, price: float, total: float):
        """Send trade execution notification"""
        subject = f"Trade Executed - {side.upper()} {asset}"

        body = f"""Hello,

Your trade order has been successfully executed.

Trade Details:
- Asset: {asset}
- Side: {side.upper()}
- Size: {size}
- Price: ${price:.2f}
- Total Value: ${total:.2f}

You can view this trade and your updated portfolio in your dashboard.

Happy trading!

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

    async def send_strategy_subscription_email(self, email: str, strategy_name: str, invested_amount: float, expected_roi: float, risk_level: str):
        """Send strategy subscription confirmation email"""
        subject = f"Strategy Subscription Confirmed - {strategy_name}"

        body = f"""Hello,

Great news! You have successfully subscribed to the {strategy_name} strategy.

Subscription Details:
- Strategy: {strategy_name}
- Investment Amount: ${invested_amount:.2f}
- Expected Daily ROI: {expected_roi:.2f}%
- Risk Level: {risk_level.title()}

What happens next:
1. Your strategy will start generating earnings immediately based on market conditions
2. You can monitor your earnings in your dashboard anytime
3. Earnings are calculated daily and can vary slightly due to market volatility
4. You can unsubscribe at any time to withdraw your investment plus accumulated earnings

Strategy Performance:
- Your investment is actively managed by our AI-powered algorithms
- Daily earnings will be added to your account automatically
- You can view real-time performance in your strategy dashboard

Important Notes:
- Minimum earnings guarantee: 0.01% of your investment per day
- Earnings may vary ±20% due to market conditions
- All investments carry risk, including the potential loss of principal

If you have any questions about your strategy subscription, please don't hesitate to contact our support team.

Happy investing!

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

    async def send_password_reset_email(self, email: str, reset_token: str):
        """Send password reset email"""
        subject = "Password Reset Request - Astrid Global Ltd"

        reset_link = f"http://localhost:8080/reset-password?token={reset_token}"  # Adjust URL as needed

        body = f"""Hello,

You have requested to reset your password for your Astrid Global Ltd account.

To reset your password, please click the link below:
{reset_link}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email. Your password will remain unchanged.

If the link doesn't work, copy and paste the URL into your browser.

Best regards,
The Astrid Global Ltd Team
support@astridglobal.com"""

        await self.send_email(email, subject, body)

# Global email service instance
email_service = EmailService()
