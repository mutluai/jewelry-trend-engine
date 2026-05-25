"""
Alert Service — Email (Resend) and Slack notifications.
Gracefully skips if not configured.
"""
import logging
import httpx
from config import get_settings

logger = logging.getLogger(__name__)


class AlertService:

    def __init__(self):
        self.settings = get_settings()

    async def send_email(self, subject: str, body_html: str, to: str | None = None) -> bool:
        """Send email via Resend API. Returns True on success."""
        if not self.settings.has_email:
            logger.info("Email not configured (RESEND_API_KEY or ALERT_EMAIL_TO missing) — skipping")
            return False

        recipient = to or self.settings.alert_email_to

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.settings.alert_email_from,
                        "to": [recipient],
                        "subject": subject,
                        "html": body_html,
                    },
                )
                if response.status_code in (200, 201):
                    logger.info(f"Email sent to {recipient}: {subject}")
                    return True
                else:
                    logger.error(f"Resend API error {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    async def send_slack(self, message: str, blocks: list | None = None) -> bool:
        """Send message to Slack via incoming webhook. Returns True on success."""
        if not self.settings.has_slack:
            logger.info("Slack not configured (SLACK_WEBHOOK_URL missing) — skipping")
            return False

        payload: dict = {"text": message}
        if blocks:
            payload["blocks"] = blocks

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.settings.slack_webhook_url,
                    json=payload,
                )
                if response.status_code == 200:
                    logger.info("Slack message sent")
                    return True
                else:
                    logger.error(f"Slack webhook error {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False

    async def send_report_notification(
        self,
        report_type: str,
        report_content: str,
        report_url: str | None,
        stats: dict,
    ) -> tuple[bool, bool]:
        """Send report via email and Slack. Returns (email_sent, slack_sent)."""
        subject = self._report_subject(report_type, stats)
        html_body = self._report_html(report_content, report_url, stats)
        slack_summary = self._report_slack_summary(report_type, report_url, stats)

        email_sent = await self.send_email(subject, html_body)
        slack_sent = await self.send_slack(slack_summary)

        return email_sent, slack_sent

    async def send_alert(self, title: str, message: str, severity: str = "info") -> None:
        """Send a system alert via Slack."""
        emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "ℹ️")
        await self.send_slack(f"{emoji} *{title}*\n{message}")

    def _report_subject(self, report_type: str, stats: dict) -> str:
        type_labels = {
            "daily": "Günlük Özet",
            "weekly": "Haftalık Trend Raporu",
            "opportunity": "Fırsat Listesi",
            "competitor": "Rakip Raporu",
        }
        label = type_labels.get(report_type, report_type.title())
        brand = self.settings.brand_name
        from datetime import date
        return f"[{brand}] {label} — {date.today().strftime('%d.%m.%Y')}"

    def _report_html(self, content: str, url: str | None, stats: dict) -> str:
        content_html = content.replace("\n", "<br>").replace("## ", "<h2>").replace("# ", "<h1>")
        url_section = f'<p><a href="{url}">📄 Raporu İndir</a></p>' if url else ""
        return f"""
<html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
<div style="background: #f8f4ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
  <h3>📊 Özet</h3>
  <ul>
    <li>Toplam ürün: <strong>{stats.get('total_products', 0)}</strong></li>
    <li>Yeni sinyal: <strong>{stats.get('new_signals', 0)}</strong></li>
    <li>Yüksek puanlı fırsat: <strong>{stats.get('top_score', 'N/A')}</strong></li>
  </ul>
  {url_section}
</div>
<div>{content_html}</div>
<hr><p style="color: #999; font-size: 12px;">Jewelry Trend Engine tarafından otomatik oluşturulmuştur.</p>
</body></html>"""

    def _report_slack_summary(self, report_type: str, url: str | None, stats: dict) -> str:
        type_labels = {"daily": "Günlük", "weekly": "Haftalık", "opportunity": "Fırsat"}
        label = type_labels.get(report_type, report_type.title())
        lines = [
            f"📊 *{label} Raporu Hazır*",
            f"• Ürün: {stats.get('total_products', 0)} | Sinyal: {stats.get('new_signals', 0)}",
            f"• En yüksek fırsat skoru: {stats.get('top_score', 'N/A')}",
        ]
        if url:
            lines.append(f"• <{url}|Raporu İndir>")
        return "\n".join(lines)
