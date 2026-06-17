import resend
import os
from quart import current_app
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "emails"


def _base_template(title: str, tagline_color: str, tagline_text: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="background-color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:0;">
<div style="max-width:600px;margin:0 auto;padding:40px 20px;">
  <div style="text-align:center;padding:32px 0;">
    <h1 style="color:#60a5fa;font-size:28px;font-weight:700;letter-spacing:4px;margin:0;">ASTRID GLOBAL</h1>
    <p style="color:{tagline_color};font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:4px 0 0;">{tagline_text}</p>
  </div>
  <div style="background-color:#1e293b;border-radius:12px;padding:40px 32px;border:1px solid #334155;">
    <h2 style="color:#f1f5f9;font-size:24px;font-weight:600;margin:0 0 12px;">{title}</h2>
    {body_html}
  </div>
  <div style="text-align:center;padding:24px 0;">
    <p style="color:#64748b;font-size:12px;margin:0;">Astrid Global Ltd | Professional Trading Platform</p>
    <p style="color:#60a5fa;font-size:12px;margin:4px 0 0;">support@astridgloballtd.pro</p>
  </div>
</div>
</body>
</html>"""


class EmailService:
    def __init__(self):
        pass

    def _configure(self):
        api_key = current_app.config.get('RESEND_API_KEY', os.getenv('RESEND_API_KEY', ''))
        if api_key:
            resend.api_key = api_key
            return True
        return False

    def _get_from(self):
        email_from = current_app.config.get('EMAIL_FROM', 'notifications@astridgloballtd.pro')
        email_from_name = current_app.config.get('EMAIL_FROM_NAME', 'Astrid Global Ltd')
        return f"{email_from_name} <{email_from}>"

    async def send_email(self, to_email: str, subject: str, html: str):
        try:
            if not self._configure():
                print(f"Email skipped (no RESEND_API_KEY): {to_email} - {subject}")
                return

            params = {
                "from": self._get_from(),
                "to": [to_email],
                "subject": subject,
                "html": html,
            }

            import asyncio
            response = await asyncio.to_thread(resend.Emails.send, params)
            print(f"Email sent via Resend to {to_email}: {response.get('id', 'ok')}")
            return True

        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")

    async def send_welcome_email(self, email: str, name: str = None):
        display_name = name or "Trader"
        body = f"""
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:0 0 16px;">
      Welcome aboard, {display_name}! Your account has been successfully created.
    </p>
    <div style="background-color:#0f172a;border-radius:8px;padding:20px;margin:24px 0;">
      <p style="color:#a5f3fc;font-size:14px;margin:8px 0;">&#x2713; Deposit funds &amp; start trading</p>
      <p style="color:#a5f3fc;font-size:14px;margin:8px 0;">&#x2713; Buy/sell crypto &amp; stocks in real-time</p>
      <p style="color:#a5f3fc;font-size:14px;margin:8px 0;">&#x2713; Subscribe to copy trading strategies</p>
      <p style="color:#a5f3fc;font-size:14px;margin:8px 0;">&#x2713; Monitor your portfolio 24/7</p>
    </div>
    <div style="text-align:center;margin:32px 0 24px;">
      <a href="https://astridgloballtd.pro/dashboard" style="background-color:#3b82f6;border-radius:8px;color:#ffffff;display:inline-block;font-size:15px;font-weight:600;padding:14px 32px;text-decoration:none;">Open Dashboard</a>
    </div>
    <hr style="border-color:#334155;margin:24px 0;">
    <h3 style="color:#e2e8f0;font-size:16px;font-weight:600;margin:24px 0 8px;">Security Recommendations</h3>
    <p style="color:#cbd5e1;font-size:14px;line-height:1.8;margin:0;">
      &#x2022; Never share your login credentials<br>
      &#x2022; Enable two-factor authentication<br>
      &#x2022; Keep your account information up to date
    </p>"""

        html = _base_template(f"Welcome aboard, {display_name}!", "#94a3b8", "Trading Platform", body)
        await self.send_email(email, "Welcome to Astrid Global Ltd Trading Platform!", html)

    async def send_login_notification(self, email: str, ip_address: str = "Unknown", user_agent: str = "Unknown"):
        from datetime import datetime, timezone
        login_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        body = f"""
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:0 0 16px;">
      We detected a new sign-in to your account.
    </p>
    <div style="background-color:#0f172a;border-radius:8px;padding:20px;margin:20px 0;">
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:12px 0 2px;">Time</p>
      <p style="color:#e2e8f0;font-size:14px;font-family:monospace;margin:0 0 8px;">{login_time}</p>
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:12px 0 2px;">IP Address</p>
      <p style="color:#e2e8f0;font-size:14px;font-family:monospace;margin:0 0 8px;">{ip_address}</p>
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:12px 0 2px;">Device</p>
      <p style="color:#e2e8f0;font-size:14px;font-family:monospace;margin:0;">{user_agent}</p>
    </div>
    <p style="color:#cbd5e1;font-size:15px;margin:0 0 16px;">If this was you, no action is needed.</p>
    <div style="background-color:#7c2d1220;border:1px solid #dc262640;border-radius:8px;padding:16px;margin:20px 0 0;">
      <p style="color:#fca5a5;font-size:13px;margin:0;line-height:1.5;">
        If you don't recognize this activity, change your password immediately and contact support.
      </p>
    </div>"""

        html = _base_template("New Login Detected", "#fbbf24", "Security Alert", body)
        await self.send_email(email, "New Login to Your Astrid Global Account", html)

    async def send_withdrawal_request_email(self, email: str, amount: float, withdrawal_id: int, network: str = None, wallet_address: str = None):
        body = f"""
    <div style="background-color:#92400e20;border:1px solid #f59e0b;border-radius:20px;padding:4px 16px;display:inline-block;margin-bottom:16px;">
      <p style="color:#fbbf24;font-size:11px;font-weight:700;letter-spacing:1px;margin:0;">PENDING REVIEW</p>
    </div>
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:12px 0 20px;">
      Your withdrawal request has been received and is pending review.
    </p>
    <div style="background-color:#0f172a;border-radius:10px;padding:24px;margin:0 0 20px;">
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 2px;">Amount</p>
      <p style="color:#f1f5f9;font-size:24px;font-weight:700;margin:0 0 16px;">${amount:,.2f}</p>
      <hr style="border-color:#334155;margin:16px 0;">
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 2px;">Request ID</p>
      <p style="color:#e2e8f0;font-size:14px;margin:0 0 10px;">#{withdrawal_id}</p>
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 2px;">Network</p>
      <p style="color:#e2e8f0;font-size:14px;margin:0 0 10px;">{network or 'N/A'}</p>
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 2px;">Wallet</p>
      <p style="color:#e2e8f0;font-size:13px;font-family:monospace;margin:0;">{wallet_address or 'N/A'}</p>
    </div>
    <h3 style="color:#e2e8f0;font-size:16px;font-weight:600;margin:24px 0 12px;">What happens next</h3>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">1. Our team reviews your request (1-2 business days)</p>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">2. Funds are processed to your wallet</p>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">3. You'll receive a confirmation email</p>"""

        html = _base_template("Withdrawal Submitted", "#94a3b8", "Withdrawal Confirmation", body)
        await self.send_email(email, f"Withdrawal Request Submitted - Astrid Global Ltd", html)

    async def send_withdrawal_approved_email(self, email: str, amount: float, withdrawal_id: int):
        body = f"""
    <div style="background-color:#065f4620;border:1px solid #10b981;border-radius:20px;padding:4px 16px;display:inline-block;margin-bottom:16px;">
      <p style="color:#34d399;font-size:11px;font-weight:700;letter-spacing:1px;margin:0;">&#x2713; APPROVED</p>
    </div>
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:12px 0 24px;">
      Great news! Your withdrawal has been approved and funds are being sent.
    </p>
    <div style="background-color:#065f4615;border:1px solid #10b98140;border-radius:10px;padding:24px;text-align:center;margin:0 0 24px;">
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">Amount Sent</p>
      <p style="color:#34d399;font-size:32px;font-weight:700;margin:0;">${amount:,.2f}</p>
      <p style="color:#94a3b8;font-size:12px;margin:8px 0 0;">Request #{withdrawal_id}</p>
    </div>
    <h3 style="color:#e2e8f0;font-size:16px;font-weight:600;margin:24px 0 12px;">Processing Times</h3>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">Bank Transfer: 1-3 business days</p>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">Crypto Wallet: Usually instant to a few hours</p>
    <hr style="border-color:#334155;margin:24px 0;">
    <p style="color:#94a3b8;font-size:13px;margin:0;line-height:1.5;">
      If you don't receive funds within the expected timeframe, contact support with your request ID.
    </p>"""

        html = _base_template("Withdrawal Processed", "#94a3b8", "Withdrawal Update", body)
        await self.send_email(email, "Withdrawal Approved - Astrid Global Ltd", html)

    async def send_withdrawal_rejected_email(self, email: str, amount: float, withdrawal_id: int, reason: str = None):
        reason_text = reason or "Please contact support for more details."
        body = f"""
    <div style="background-color:#7c2d1220;border:1px solid #ef4444;border-radius:20px;padding:4px 16px;display:inline-block;margin-bottom:16px;">
      <p style="color:#f87171;font-size:11px;font-weight:700;letter-spacing:1px;margin:0;">DECLINED</p>
    </div>
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:12px 0 20px;">
      We were unable to process your withdrawal request.
    </p>
    <div style="background-color:#0f172a;border-radius:10px;padding:24px;margin:0 0 20px;">
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 2px;">Amount</p>
      <p style="color:#e2e8f0;font-size:14px;margin:0 0 10px;">${amount:,.2f}</p>
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 2px;">Request ID</p>
      <p style="color:#e2e8f0;font-size:14px;margin:0 0 10px;">#{withdrawal_id}</p>
      <hr style="border-color:#334155;margin:16px 0;">
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 4px;">Reason</p>
      <p style="color:#fca5a5;font-size:14px;margin:0;line-height:1.5;">{reason_text}</p>
    </div>
    <p style="color:#cbd5e1;font-size:15px;margin:0 0 20px;">
      If you believe this is an error, please contact support with your request ID.
    </p>
    <div style="text-align:center;margin:24px 0 0;">
      <a href="mailto:support@astridgloballtd.pro" style="background-color:#3b82f6;border-radius:8px;color:#ffffff;display:inline-block;font-size:14px;font-weight:600;padding:12px 28px;text-decoration:none;">Contact Support</a>
    </div>"""

        html = _base_template("Withdrawal Not Processed", "#94a3b8", "Withdrawal Update", body)
        await self.send_email(email, "Withdrawal Request Update - Astrid Global Ltd", html)

    async def send_trade_executed_email(self, email: str, asset: str, side: str, size: float, price: float, total: float):
        is_buy = side.lower() == 'buy'
        badge_bg = "#065f4620" if is_buy else "#7c2d1220"
        badge_border = "#10b981" if is_buy else "#ef4444"
        side_color = "#34d399" if is_buy else "#f87171"

        body = f"""
    <div style="background-color:{badge_bg};border:1px solid {badge_border};border-radius:20px;padding:4px 16px;display:inline-block;margin-bottom:16px;">
      <p style="color:#f1f5f9;font-size:11px;font-weight:700;letter-spacing:1px;margin:0;">{side.upper()}</p>
    </div>
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:12px 0 24px;">
      Your {side.lower()} order has been successfully filled.
    </p>
    <div style="background-color:#0f172a;border-radius:10px;padding:24px;margin:0 0 20px;">
      <p style="color:#f1f5f9;font-size:20px;font-weight:700;margin:0 0 12px;">{asset}</p>
      <hr style="border-color:#334155;margin:12px 0;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding:8px 0;">Side</td><td style="color:{side_color};font-size:14px;font-weight:500;text-align:right;padding:8px 0;">{side.upper()}</td></tr>
        <tr><td style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding:8px 0;">Quantity</td><td style="color:#e2e8f0;font-size:14px;text-align:right;padding:8px 0;">{size}</td></tr>
        <tr><td style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding:8px 0;">Price</td><td style="color:#e2e8f0;font-size:14px;text-align:right;padding:8px 0;">${price:,.2f}</td></tr>
      </table>
      <hr style="border-color:#334155;margin:12px 0;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding:8px 0;">Total Value</td><td style="color:#60a5fa;font-size:18px;font-weight:700;text-align:right;padding:8px 0;">${total:,.2f}</td></tr>
      </table>
    </div>
    <p style="color:#94a3b8;font-size:13px;margin:0;">
      View this trade and your updated portfolio in your dashboard.
    </p>"""

        html = _base_template("Trade Executed", "#94a3b8", "Trade Confirmation", body)
        await self.send_email(email, f"Trade Executed - {side.upper()} {asset}", html)

    async def send_strategy_subscription_email(self, email: str, strategy_name: str, invested_amount: float, expected_roi: float, risk_level: str):
        body = f"""
    <div style="background-color:#065f4620;border:1px solid #10b981;border-radius:20px;padding:4px 16px;display:inline-block;margin-bottom:16px;">
      <p style="color:#34d399;font-size:11px;font-weight:700;letter-spacing:1px;margin:0;">&#x2713; ACTIVE</p>
    </div>
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:12px 0 24px;">
      You've successfully subscribed to the <strong style="color:#f1f5f9;">{strategy_name}</strong> strategy.
    </p>
    <div style="background-color:#0f172a;border-radius:10px;padding:24px;margin:0 0 24px;">
      <p style="color:#f1f5f9;font-size:18px;font-weight:700;margin:0 0 16px;">{strategy_name}</p>
      <hr style="border-color:#334155;margin:0 0 16px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding:8px 0;">Investment</td><td style="color:#e2e8f0;font-size:14px;font-weight:500;text-align:right;padding:8px 0;">${invested_amount:,.2f}</td></tr>
        <tr><td style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding:8px 0;">Expected Daily ROI</td><td style="color:#34d399;font-size:14px;font-weight:700;text-align:right;padding:8px 0;">{expected_roi:.2f}%</td></tr>
        <tr><td style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding:8px 0;">Risk Level</td><td style="color:#e2e8f0;font-size:14px;text-align:right;padding:8px 0;">{risk_level.title()}</td></tr>
      </table>
    </div>
    <h3 style="color:#e2e8f0;font-size:16px;font-weight:600;margin:0 0 12px;">How it works</h3>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">&#x2022; AI algorithms manage your investment actively</p>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">&#x2022; Daily earnings added to your account automatically</p>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">&#x2022; Monitor real-time performance in your dashboard</p>
    <p style="color:#cbd5e1;font-size:14px;margin:6px 0;">&#x2022; Unsubscribe at any time to withdraw</p>
    <div style="text-align:center;margin:28px 0 0;">
      <a href="https://astridgloballtd.pro/strategies" style="background-color:#3b82f6;border-radius:8px;color:#ffffff;display:inline-block;font-size:14px;font-weight:600;padding:12px 28px;text-decoration:none;">View Strategy</a>
    </div>"""

        html = _base_template("Strategy Subscribed", "#94a3b8", "Strategy Confirmation", body)
        await self.send_email(email, f"Strategy Subscription Confirmed - {strategy_name}", html)

    async def send_password_reset_email(self, email: str, reset_token: str):
        reset_link = f"https://astridgloballtd.pro/reset-password?token={reset_token}"

        body = f"""
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:0 0 16px;">
      You requested a password reset for your Astrid Global Ltd account.
      Click the button below to set a new password.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{reset_link}" style="background-color:#3b82f6;border-radius:8px;color:#ffffff;display:inline-block;font-size:15px;font-weight:600;padding:14px 32px;text-decoration:none;">Reset Password</a>
    </div>
    <p style="color:#f59e0b;font-size:13px;text-align:center;margin:0 0 16px;">
      This link expires in 1 hour for security reasons.
    </p>
    <hr style="border-color:#334155;margin:24px 0;">
    <p style="color:#cbd5e1;font-size:15px;line-height:1.6;margin:0 0 16px;">
      If you didn't request this reset, you can safely ignore this email.
    </p>
    <div style="background-color:#0f172a;border-radius:8px;padding:16px;margin:16px 0 0;">
      <p style="color:#64748b;font-size:12px;margin:0 0 8px;">If the button doesn't work, copy this URL:</p>
      <p style="color:#60a5fa;font-size:12px;word-break:break-all;margin:0;font-family:monospace;">{reset_link}</p>
    </div>"""

        html = _base_template("Reset Your Password", "#94a3b8", "Password Reset", body)
        await self.send_email(email, "Password Reset Request - Astrid Global Ltd", html)


# Global email service instance
email_service = EmailService()
