"""
Sends the "price dropped" email.

USE_MOCK_DATA=True just logs the email instead of sending it, so the
scheduler is fully runnable/testable with no email provider signed up yet.

To go live: pick Postmark or SendGrid (either works fine for transactional
alerts like this), get an API key, and fill in the real call below.
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_alerts")

USE_MOCK_DATA = True
EMAIL_API_KEY = os.environ.get("EMAIL_API_KEY", "")
FROM_ADDRESS = "alerts@yourdomain.com"  # replace with your real sending domain


def send_price_drop_email(to_email: str, product_title: str, new_price: float, seller: str, url: str) -> None:
    subject = f"Price drop: {product_title} is now ${new_price:.2f}"
    body = f"{product_title} dropped to ${new_price:.2f} at {seller}.\n\nView: {url}"

    if USE_MOCK_DATA:
        logger.info("MOCK EMAIL to %s | %s | %s", to_email, subject, body)
        return

    # Live version (Postmark example — swap for SendGrid similarly):
    # import httpx
    # httpx.post(
    #     "https://api.postmarkapp.com/email",
    #     headers={"X-Postmark-Server-Token": EMAIL_API_KEY, "Accept": "application/json"},
    #     json={
    #         "From": FROM_ADDRESS,
    #         "To": to_email,
    #         "Subject": subject,
    #         "TextBody": body,
    #     },
    #     timeout=10,
    # )
