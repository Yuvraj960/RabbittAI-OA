"""Email delivery service using Gmail SMTP."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException, status

from app.core.config import settings

_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 700px; margin: 30px auto; background: #ffffff; border-radius: 12px;
              box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
             padding: 36px 40px; text-align: center; }}
  .header h1 {{ color: #e94560; margin: 0; font-size: 26px; letter-spacing: 1px; }}
  .header p {{ color: #a0aec0; margin: 8px 0 0; font-size: 14px; }}
  .badge {{ display: inline-block; background: rgba(233,69,96,0.15); color: #e94560;
            border: 1px solid rgba(233,69,96,0.3); border-radius: 20px;
            padding: 4px 14px; font-size: 12px; margin-top: 12px; }}
  .content {{ padding: 36px 40px; color: #2d3748; line-height: 1.7; }}
  .content h2 {{ color: #1a1a2e; border-bottom: 2px solid #e94560; padding-bottom: 8px;
                  margin-top: 28px; font-size: 20px; }}
  .content h3 {{ color: #0f3460; font-size: 16px; margin-top: 20px; }}
  .content ul {{ padding-left: 20px; }}
  .content li {{ margin-bottom: 6px; }}
  .content strong {{ color: #0f3460; }}
  .footer {{ background: #f7fafc; padding: 20px 40px; text-align: center;
             color: #718096; font-size: 12px; border-top: 1px solid #e2e8f0; }}
  .footer a {{ color: #e94560; text-decoration: none; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🐇 Rabbitt AI</h1>
    <p>Sales Insight Automator</p>
    <span class="badge">Executive Brief — {filename}</span>
  </div>
  <div class="content">
    {ai_summary}
  </div>
  <div class="footer">
    <p>Generated automatically by <strong>Rabbitt AI Sales Insight Automator</strong></p>
    <p>This is an AI-generated summary. Please verify key figures against source data.</p>
  </div>
</div>
</body>
</html>"""


def send_summary_email(recipient: str, filename: str, ai_summary: str) -> None:
    """
    Send the AI-generated HTML summary to the recipient via Gmail SMTP.
    Raises HTTPException if sending fails.
    """
    if not settings.gmail_user or not settings.gmail_app_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service not configured on the server.",
        )

    html_body = _EMAIL_TEMPLATE.format(filename=filename, ai_summary=ai_summary)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Sales Insight Report — {filename}"
    msg["From"] = f"Rabbitt AI <{settings.gmail_user}>"
    msg["To"] = recipient

    msg.attach(MIMEText("Please view this email in an HTML-compatible client.", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp-relay.brevo.com", 2525, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, recipient, msg.as_string())
    except smtplib.SMTPAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.",
        ) from exc
    except smtplib.SMTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Email sending failed: {exc}",
        ) from exc
