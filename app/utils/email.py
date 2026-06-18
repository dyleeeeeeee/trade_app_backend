import resend
import os
from quart import current_app
from pathlib import Path
from datetime import datetime, timezone

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "emails"

# ---------------------------------------------------------------------------
# Astrid Global — transactional email system.
# Visual language: an institutional private-wealth aesthetic (think a
# JP Morgan investment portal) — a light, confident layout, deep-navy brand
# rule with a thin bronze accent, serif headlines, structured data panels with
# hairline dividers, reference numbers on every transaction, and a formal,
# compliant footer. Every message is proportional to the event it confirms.
# ---------------------------------------------------------------------------

# Palette (institutional)
INK = "#0a1f44"          # deep navy (brand)
NAVY = "#16315c"
BRONZE = "#9a7b4f"       # private-wealth accent (thin rules / eyebrow)
TEXT = "#14223b"         # near-navy body text
MUTED = "#5b6678"        # slate-gray secondary
FAINT = "#8a94a6"        # tertiary / captions
HAIR = "#e3e6ec"         # hairline dividers
PANEL = "#f6f7f9"        # light panel fill
PAGE = "#eef0f3"         # page background
GOOD = "#1f7a54"         # muted deep green
WARN = "#9a6a1b"         # muted amber
BAD = "#a3303a"          # muted crimson
WHITE = "#ffffff"

SERIF = "Georgia, 'Times New Roman', Times, serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

APP_URL = "https://astridgloballtd.pro"
SUPPORT_EMAIL = "support@astridgloballtd.pro"

TONE_COLORS = {
    "pending": WARN,
    "success": GOOD,
    "declined": BAD,
    "info": NAVY,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def _ref(prefix: str, value) -> str:
    return f"{prefix}-{value}"


def _badge(label: str, tone: str = "info") -> str:
    color = TONE_COLORS.get(tone, NAVY)
    return (
        f'<span style="display:inline-block;border:1px solid {color};color:{color};'
        f'font-family:{SANS};font-size:10px;font-weight:700;letter-spacing:1.5px;'
        f'text-transform:uppercase;padding:5px 12px;border-radius:2px;">{label}</span>'
    )


def _amount_hero(amount_html: str, caption: str) -> str:
    return (
        f'<div style="background-color:{PANEL};border:1px solid {HAIR};border-radius:4px;'
        f'padding:24px 28px;margin:0 0 24px;">'
        f'<p style="color:{FAINT};font-family:{SANS};font-size:11px;font-weight:600;'
        f'letter-spacing:1.5px;text-transform:uppercase;margin:0 0 8px;">{caption}</p>'
        f'<p style="color:{INK};font-family:{SANS};font-size:34px;font-weight:600;'
        f'letter-spacing:-0.5px;margin:0;">{amount_html}</p>'
        f'</div>'
    )


def _rows(items) -> str:
    """items: list of (label, value) tuples. Renders a hairline-divided panel."""
    cells = []
    for i, (label, value) in enumerate(items):
        border = "" if i == 0 else f"border-top:1px solid {HAIR};"
        cells.append(
            f'<tr><td style="{border}padding:13px 0;color:{MUTED};font-family:{SANS};'
            f'font-size:12px;letter-spacing:0.3px;">{label}</td>'
            f'<td style="{border}padding:13px 0;color:{TEXT};font-family:{SANS};font-size:13px;'
            f'font-weight:600;text-align:right;">{value}</td></tr>'
        )
    return (
        f'<div style="background-color:{PANEL};border:1px solid {HAIR};border-radius:4px;'
        f'padding:6px 20px;margin:0 0 24px;"><table role="presentation" width="100%" '
        f'style="border-collapse:collapse;">{"".join(cells)}</table></div>'
    )


def _mono(text: str) -> str:
    return f'<span style="font-family:{MONO};font-size:12px;">{text}</span>'


def _button(label: str, href: str) -> str:
    return (
        f'<table role="presentation" cellspacing="0" cellpadding="0" style="margin:8px 0 28px;">'
        f'<tr><td style="background-color:{INK};border-radius:3px;">'
        f'<a href="{href}" style="display:inline-block;color:{WHITE};font-family:{SANS};'
        f'font-size:14px;font-weight:600;letter-spacing:0.3px;padding:13px 30px;'
        f'text-decoration:none;">{label}</a></td></tr></table>'
    )


def _note(html: str, tone: str = "muted") -> str:
    border = {"muted": HAIR, "warn": WARN, "bad": BAD}.get(tone, HAIR)
    color = {"muted": MUTED, "warn": WARN, "bad": BAD}.get(tone, MUTED)
    return (
        f'<div style="border-left:3px solid {border};padding:2px 0 2px 16px;margin:0 0 20px;">'
        f'<p style="color:{color};font-family:{SANS};font-size:13px;line-height:1.6;margin:0;">{html}</p></div>'
    )


def _para(html: str) -> str:
    return f'<p style="color:{TEXT};font-family:{SANS};font-size:15px;line-height:1.65;margin:0 0 20px;">{html}</p>'


def _heading(text: str) -> str:
    return (
        f'<p style="color:{INK};font-family:{SANS};font-size:13px;font-weight:700;'
        f'letter-spacing:0.4px;text-transform:uppercase;margin:28px 0 12px;">{text}</p>'
    )


def _layout(category: str, title: str, content_html: str, recipient: str = None) -> str:
    recipient_line = (
        f'This confirmation was sent to {recipient}. ' if recipient else ''
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light"></head>
<body style="background-color:{PAGE};margin:0;padding:0;-webkit-font-smoothing:antialiased;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:{PAGE};">
<tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%;">

  <!-- Brand bar -->
  <tr><td style="padding:0 0 20px;">
    <table role="presentation" width="100%"><tr>
      <td style="font-family:{SERIF};color:{INK};font-size:22px;font-weight:700;letter-spacing:3px;">ASTRID&nbsp;GLOBAL</td>
      <td align="right" style="font-family:{SANS};color:{BRONZE};font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">Private Wealth</td>
    </tr></table>
    <div style="height:2px;background-color:{INK};margin-top:12px;"></div>
    <div style="height:1px;background-color:{BRONZE};margin-top:2px;width:96px;"></div>
  </td></tr>

  <!-- Card -->
  <tr><td style="background-color:{WHITE};border:1px solid {HAIR};border-radius:6px;padding:40px 36px;">
    <p style="color:{BRONZE};font-family:{SANS};font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin:0 0 10px;">{category}</p>
    <h1 style="color:{INK};font-family:{SERIF};font-size:26px;font-weight:700;line-height:1.25;margin:0 0 22px;">{title}</h1>
    {content_html}
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:28px 8px 0;">
    <div style="height:1px;background-color:{HAIR};margin-bottom:20px;"></div>
    <p style="color:{MUTED};font-family:{SANS};font-size:12px;line-height:1.7;margin:0 0 10px;">
      <strong style="color:{TEXT};">Astrid Global Ltd</strong> &nbsp;|&nbsp; Wealth Management &amp; Digital Asset Services<br>
      Questions? Contact <a href="mailto:{SUPPORT_EMAIL}" style="color:{NAVY};text-decoration:none;">{SUPPORT_EMAIL}</a>
    </p>
    <p style="color:{FAINT};font-family:{SANS};font-size:11px;line-height:1.7;margin:0;">
      {recipient_line}This is an automated message regarding your account; please do not reply.
      This communication is confidential and intended solely for the named recipient.
      Investing involves risk, including the possible loss of principal; past performance and
      target returns are not guarantees of future results. © 2026 Astrid Global Ltd. All rights reserved.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
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
            if not to_email:
                print("Email skipped (no recipient)")
                return
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

    # ---- Onboarding -------------------------------------------------------
    async def send_welcome_email(self, email: str, name: str = None):
        display_name = name or "Investor"
        content = (
            _para(f"Dear {display_name},")
            + _para(
                "Welcome to Astrid Global. Your account has been opened and your portal is "
                "ready. From a single, secure dashboard you can fund your account, invest across "
                "digital assets and equities, and follow our managed strategies."
            )
            + _heading("Your portal at a glance")
            + _rows([
                ("Fund &amp; manage", "Deposit, withdraw and transfer with full transaction records"),
                ("Markets", "Trade crypto and equities on real-time pricing"),
                ("Managed strategies", "Allocate to curated, risk-rated strategies"),
                ("Oversight", "Monitor performance and statements 24/7"),
            ])
            + _button("Enter your portal", f"{APP_URL}/dashboard")
            + _heading("Protecting your account")
            + _note(
                "Astrid Global will never ask for your password or one-time codes by email or "
                "phone. Keep your credentials private and verify the sender on every message."
            )
        )
        html = _layout("Account Opening", "Welcome to Astrid Global", content, email)
        await self.send_email(email, "Welcome to Astrid Global — your account is open", html)

    # ---- Security ---------------------------------------------------------
    async def send_login_notification(self, email: str, ip_address: str = "Unknown", user_agent: str = "Unknown"):
        content = (
            _para("We are writing to confirm a new sign-in to your Astrid Global account.")
            + _rows([
                ("Date &amp; time", _mono(_now_utc())),
                ("IP address", _mono(ip_address)),
                ("Device", user_agent),
            ])
            + _para("If this was you, no action is required.")
            + _note(
                "If you do not recognise this activity, reset your password immediately and "
                f"contact us at {SUPPORT_EMAIL}.",
                tone="warn",
            )
        )
        html = _layout("Security Notice", "New sign-in to your account", content, email)
        await self.send_email(email, "Security notice: new sign-in to your Astrid Global account", html)

    async def send_password_reset_email(self, email: str, reset_token: str):
        reset_link = f"{APP_URL}/reset-password?token={reset_token}"
        content = (
            _para(
                "We received a request to reset the password on your Astrid Global account. "
                "Use the button below to choose a new password."
            )
            + _button("Reset password", reset_link)
            + _note("For your security, this link expires in 60 minutes and can be used once.", tone="warn")
            + _para("If you did not request this, you can safely ignore this message — your password will not change.")
            + _heading("Trouble with the button?")
            + _para(f'Copy and paste this address into your browser:<br>{_mono(reset_link)}')
        )
        html = _layout("Security", "Reset your password", content, email)
        await self.send_email(email, "Reset your Astrid Global password", html)

    # ---- Funding ----------------------------------------------------------
    async def send_deposit_confirmation_email(self, email: str, amount: float, new_balance: float = None):
        content = (
            _badge("Credited", "success")
            + _para("This confirms that the following deposit has been credited to your account.")
            + _amount_hero(f"${amount:,.2f}", "Amount credited")
            + _rows(
                [("Transaction", "Deposit"), ("Value date", _mono(_now_utc()))]
                + ([("Available balance", f"${new_balance:,.2f}")] if new_balance is not None else [])
            )
            + _button("View account", f"{APP_URL}/wallet")
            + _para("Your funds are available to invest immediately.")
        )
        html = _layout("Transaction Confirmation", "Deposit received", content, email)
        await self.send_email(email, f"Deposit confirmation — ${amount:,.2f} credited", html)

    async def send_withdrawal_request_email(self, email: str, amount: float, withdrawal_id: int, network: str = None, wallet_address: str = None):
        content = (
            _badge("Pending review", "pending")
            + _para("We have received your withdrawal instruction. It is now pending review by our operations team.")
            + _amount_hero(f"${amount:,.2f}", "Amount requested")
            + _rows([
                ("Reference", _mono(_ref("WD", withdrawal_id))),
                ("Network", network or "—"),
                ("Destination", _mono(wallet_address or "—")),
                ("Submitted", _mono(_now_utc())),
            ])
            + _heading("What happens next")
            + _rows([
                ("1 · Review", "Our team verifies the request (typically 1–2 business days)"),
                ("2 · Release", "Approved funds are sent to your destination"),
                ("3 · Confirmation", "You receive a confirmation once funds are released"),
            ])
            + _note(f"Keep reference {_ref('WD', withdrawal_id)} for any correspondence about this request.")
        )
        html = _layout("Withdrawal Instruction", "Withdrawal request received", content, email)
        await self.send_email(email, f"Withdrawal request received — ref {_ref('WD', withdrawal_id)}", html)

    async def send_withdrawal_approved_email(self, email: str, amount: float, withdrawal_id: int):
        content = (
            _badge("Approved", "success")
            + _para("Your withdrawal has been approved and the funds are being released to your destination.")
            + _amount_hero(f"${amount:,.2f}", "Amount released")
            + _rows([
                ("Reference", _mono(_ref("WD", withdrawal_id))),
                ("Approved", _mono(_now_utc())),
            ])
            + _heading("Expected settlement")
            + _rows([
                ("Digital asset", "Typically within a few hours"),
                ("Bank transfer", "1–3 business days"),
            ])
            + _note(
                f"If funds do not arrive within the expected window, contact {SUPPORT_EMAIL} "
                f"quoting reference {_ref('WD', withdrawal_id)}."
            )
        )
        html = _layout("Withdrawal Confirmation", "Your withdrawal has been approved", content, email)
        await self.send_email(email, f"Withdrawal approved — ref {_ref('WD', withdrawal_id)}", html)

    async def send_withdrawal_rejected_email(self, email: str, amount: float, withdrawal_id: int, reason: str = None):
        reason_text = reason or "Please contact our support team for further details."
        content = (
            _badge("Declined", "declined")
            + _para("We were unable to process the following withdrawal request, and no funds have left your account.")
            + _rows([
                ("Amount", f"${amount:,.2f}"),
                ("Reference", _mono(_ref("WD", withdrawal_id))),
                ("Reason", reason_text),
            ])
            + _para("If you believe this was made in error, our team is ready to help.")
            + _button("Contact support", f"mailto:{SUPPORT_EMAIL}")
        )
        html = _layout("Withdrawal Update", "Withdrawal could not be processed", content, email)
        await self.send_email(email, f"Withdrawal update — ref {_ref('WD', withdrawal_id)}", html)

    async def send_transfer_sent_email(self, email: str, amount: float, recipient_email: str, new_balance: float = None):
        content = (
            _badge("Debited", "info")
            + _para("This confirms an internal transfer sent from your account.")
            + _amount_hero(f"-${amount:,.2f}", "Amount sent")
            + _rows(
                [("Recipient", recipient_email), ("Date", _mono(_now_utc()))]
                + ([("Available balance", f"${new_balance:,.2f}")] if new_balance is not None else [])
            )
            + _button("View account", f"{APP_URL}/wallet")
        )
        html = _layout("Transfer Confirmation", "Transfer sent", content, email)
        await self.send_email(email, f"Transfer sent — ${amount:,.2f}", html)

    async def send_transfer_received_email(self, email: str, amount: float, sender_email: str = None, new_balance: float = None):
        sender = sender_email or "another Astrid Global account"
        content = (
            _badge("Credited", "success")
            + _para("Good news — you have received an internal transfer.")
            + _amount_hero(f"+${amount:,.2f}", "Amount received")
            + _rows(
                [("From", sender), ("Date", _mono(_now_utc()))]
                + ([("Available balance", f"${new_balance:,.2f}")] if new_balance is not None else [])
            )
            + _button("View account", f"{APP_URL}/wallet")
        )
        html = _layout("Transfer Confirmation", "Funds received", content, email)
        await self.send_email(email, f"Funds received — ${amount:,.2f}", html)

    # ---- Trading ----------------------------------------------------------
    async def send_trade_executed_email(self, email: str, asset: str, side: str, size: float, price: float, total: float):
        side_label = "Buy" if side.lower() == "buy" else "Sell"
        content = (
            _badge(f"{side_label} executed", "info")
            + _para(f"This is a confirmation that your {side_label.lower()} instruction has been executed in full.")
            + _rows([
                ("Instrument", f"<strong>{asset}</strong>"),
                ("Side", side_label),
                ("Quantity", _mono(f"{size}")),
                ("Execution price", _mono(f"${price:,.2f}")),
            ])
            + _amount_hero(f"${total:,.2f}", "Gross consideration")
            + _rows([("Executed", _mono(_now_utc()))])
            + _button("View portfolio", f"{APP_URL}/trading")
            + _note("Please review this confirmation. Market orders fill at the prevailing price at execution.")
        )
        html = _layout("Trade Confirmation", f"{side_label} order executed — {asset}", content, email)
        await self.send_email(email, f"Trade confirmation — {side_label} {asset}", html)

    async def send_strategy_subscription_email(self, email: str, strategy_name: str, invested_amount: float, expected_roi: float, risk_level: str):
        content = (
            _badge("Mandate active", "success")
            + _para(f"This confirms your allocation to the <strong>{strategy_name}</strong> strategy.")
            + _amount_hero(f"${invested_amount:,.2f}", "Amount allocated")
            + _rows([
                ("Strategy", strategy_name),
                ("Target daily return", f"{expected_roi:.2f}%"),
                ("Risk rating", risk_level.title()),
                ("Effective", _mono(_now_utc())),
            ])
            + _heading("How your mandate works")
            + _rows([
                ("Management", "Your allocation is managed actively on your behalf"),
                ("Performance", "Results accrue to your account and are shown in your dashboard"),
                ("Flexibility", "You may unsubscribe at any time to release your allocation"),
            ])
            + _button("View strategy", f"{APP_URL}/strategies")
            + _note(
                "Target returns are objectives, not guarantees. The value of investments can fall "
                "as well as rise, and you may get back less than you invested.",
                tone="warn",
            )
        )
        html = _layout("Advisory Confirmation", "Strategy allocation confirmed", content, email)
        await self.send_email(email, f"Allocation confirmed — {strategy_name}", html)

    async def send_strategy_unsubscribe_email(self, email: str, strategy_name: str, invested_amount: float, earnings: float, returned_amount: float):
        gain = earnings >= 0
        content = (
            _badge("Mandate closed", "info")
            + _para(f"This confirms that your allocation to the <strong>{strategy_name}</strong> strategy has been closed and released to your account.")
            + _amount_hero(f"${returned_amount:,.2f}", "Returned to your balance")
            + _rows([
                ("Strategy", strategy_name),
                ("Principal", f"${invested_amount:,.2f}"),
                ("Earnings", f"{'+' if gain else '-'}${abs(earnings):,.2f}"),
                ("Closed", _mono(_now_utc())),
            ])
            + _button("View account", f"{APP_URL}/wallet")
            + _note(
                "Past performance is not indicative of future results. You may allocate to a "
                "strategy again at any time from your portal."
            )
        )
        html = _layout("Advisory Confirmation", "Strategy allocation released", content, email)
        await self.send_email(email, f"Allocation released — {strategy_name}", html)

    async def send_password_changed_email(self, email: str):
        content = (
            _badge("Updated", "success")
            + _para("This confirms that the password on your Astrid Global account was changed.")
            + _rows([("Changed", _mono(_now_utc()))])
            + _note(
                "If you did not make this change, your account may be at risk. Reset your "
                f"password again immediately and contact us at {SUPPORT_EMAIL}.",
                tone="bad",
            )
        )
        html = _layout("Security", "Your password was changed", content, email)
        await self.send_email(email, "Your Astrid Global password was changed", html)

    async def send_copy_trading_email(self, email: str, trader_name: str, allocation: float):
        content = (
            _badge("Following", "success")
            + _para(
                f"This confirms that you are now copying <strong>{trader_name}</strong>. Eligible trades "
                "from this lead trader will be mirrored to your account in proportion to your allocation."
            )
            + _rows([
                ("Lead trader", trader_name),
                ("Portfolio allocation", f"{allocation:.0f}%"),
                ("Effective", _mono(_now_utc())),
            ])
            + _button("Manage copy trading", f"{APP_URL}/copy-trading")
            + _note(
                "Copy trading carries risk and past performance is not indicative of future results. "
                "You can adjust your allocation or stop copying at any time.",
                tone="warn",
            )
        )
        html = _layout("Copy Trading", "You are now copying a lead trader", content, email)
        await self.send_email(email, f"Copy trading active — {trader_name}", html)


# Global email service instance
email_service = EmailService()
