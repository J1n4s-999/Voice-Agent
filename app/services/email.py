from datetime import datetime

from postmarker.core import PostmarkClient

from app.config import settings


def format_dt(dt: datetime) -> str:
    return dt.astimezone().strftime("%d.%m.%Y um %H:%M Uhr")


def send_confirmation_email(
    *,
    to_email: str,
    name: str,
    requested_start: datetime,
    duration_minutes: int,
    confirm_link: str,
) -> dict:
    client = PostmarkClient(server_token=settings.postmark_server_token)

    subject = "Bitte bestätige deinen Termin"

    html_body = f"""
    <html>
      <body style="font-family: Arial, Helvetica, sans-serif; color: #1f2937; line-height: 1.6;">
        <h2>Bitte bestätige deinen Termin</h2>

        <p>Hallo {name},</p>

        <p>
          bitte bestätige deinen Termin über den Button unten.
        </p>

        <p><strong>Datum:</strong> {format_dt(requested_start)}<br>
        <strong>Dauer:</strong> {duration_minutes} Minuten</p>

        <p style="margin: 24px 0;">
          <a href="{confirm_link}"
             style="background: #111827; color: #ffffff; text-decoration: none; padding: 12px 20px; border-radius: 8px; display: inline-block;">
            Termin bestätigen
          </a>
        </p>

        <p>Falls der Button nicht funktioniert, nutze diesen Link:</p>
        <p><a href="{confirm_link}">{confirm_link}</a></p>

        <p>Viele Grüße<br>Voice Agent</p>
      </body>
    </html>
    """

    text_body = (
        f"Hallo {name},\n\n"
        f"bitte bestätige deinen Termin.\n\n"
        f"Datum: {format_dt(requested_start)}\n"
        f"Dauer: {duration_minutes} Minuten\n\n"
        f"Bestätigungslink:\n{confirm_link}\n\n"
        f"Viele Grüße\n"
        f"Voice Agent"
    )

    response = client.emails.send(
        From=settings.email_from,
        To=to_email,
        Subject=subject,
        HtmlBody=html_body,
        TextBody=text_body,
        MessageStream="outbound",
    )

    return response