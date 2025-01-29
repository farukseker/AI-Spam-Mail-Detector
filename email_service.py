import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
from log4py import LoggerManager


logger = LoggerManager.get_logger('EmailFetcher')


def clean_text(text) -> str:
    text = re.sub(r'[\u200c\u00a0]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


@dataclass(frozen=True)
class MailType:
    id: int
    subject: str
    _from: str
    body: str
    urls: list
    flags: list
    labels: list
    is_starred: bool


class EmailFetcher:
    def __init__(self, email_user, email_pass):
        self.email_user = email_user
        self.email_pass = email_pass
        self.server = None

    def connect(self) -> None:
        try:
            self.server = imaplib.IMAP4_SSL("imap.gmail.com")
            self.server.login(self.email_user, self.email_pass)
        except Exception as e:
            logger.error(e)
            raise ConnectionError(f"Failed to connect to the email server: {e}")

    def get_mail_boxs(self) -> list[dict]:
        if not self.server:
            logger.error("Not connected to the email server.")
            raise ConnectionError("Not connected to the email server.")

        status, folders = self.server.list()
        for folder in folders:
            print(folder.decode())

        return [{}]

    def fetch_emails(self, limit=100) -> list[MailType]:
        if not self.server:
            logger.error('Not connected to the email server.')
            raise ConnectionError("Not connected to the email server.")
        try:
            self.server.select("inbox")
            status, messages = self.server.search(None, "ALL")
            if limit == 0:
                mail_ids = messages[0].split()
            else:
                mail_ids = messages[0].split()[-limit:]

            emails = []
            for mail_id in mail_ids:
                status, msg_data = self.server.fetch(mail_id, "(RFC822 FLAGS X-GM-LABELS)")

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()

                        from_ = msg.get("From")
                        body, urls = self._parse_email_body(msg)

                        # Bayrakları ve etiketleri kontrol et
                        flags = []
                        labels = []
                        if len(msg_data) > 2:
                            flags = msg_data[1].decode().split()
                            labels = msg_data[2].decode().split()

                        is_starred = "\\Flagged" in flags or "\\Starred" in labels

                        emails.append(
                            MailType(
                                id=mail_id.decode(),
                                subject=subject,
                                _from=from_,
                                body=body.strip(),
                                urls=urls,
                                flags=flags,
                                labels=labels,
                                is_starred=is_starred
                            )
                        )
            return emails
        except Exception as e:
            raise e

    @staticmethod
    def _parse_email_body(msg) -> tuple[str, list[str]]:
        body = ""
        urls = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/html" and "attachment" not in content_disposition:
                    html_content = part.get_payload(decode=True).decode()
                    soup = BeautifulSoup(html_content, "html.parser")
                    body = clean_text(soup.get_text(strip=True))
                    urls = [a['href'] for a in soup.find_all('a', href=True)]
                    break
                elif content_type == "text/plain" and "attachment" not in content_disposition:
                    body = clean_text(part.get_payload(decode=True).decode())
        else:
            body = clean_text(msg.get_payload(decode=True).decode())

        return body, urls

    def disconnect(self) -> None:
        if self.server:
            self.server.logout()
            self.server = None
