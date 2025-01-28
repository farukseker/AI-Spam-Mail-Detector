import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup


def clean_text(text):
    return " ".join(text.split())


class EmailFetcher:
    def __init__(self, email_user, email_pass):
        self.email_user = email_user
        self.email_pass = email_pass
        self.server = None

    def connect(self):
        try:
            self.server = imaplib.IMAP4_SSL("imap.gmail.com")
            self.server.login(self.email_user, self.email_pass)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to the email server: {e}")

    def fetch_emails(self, limit=100):
        if not self.server:
            raise ConnectionError("Not connected to the email server.")

        try:
            self.server.select("inbox")
            status, messages = self.server.search(None, "ALL")
            mail_ids = messages[0].split()[-limit:]
            emails = []

            for mail_id in mail_ids:
                status, msg_data = self.server.fetch(mail_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()

                        from_ = msg.get("From")

                        body, urls = self._parse_email_body(msg)

                        emails.append({
                            "id": mail_id.decode(),
                            "subject": subject,
                            "from": from_,
                            "body": body.strip(),
                            "urls": urls
                        })
            return emails
        except Exception as e:
            return str(e)

    def _parse_email_body(self, msg):
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
                    body = part.get_payload(decode=True).decode()
        else:
            body = clean_text(msg.get_payload(decode=True).decode())

        return body, urls

    def disconnect(self):
        if self.server:
            self.server.logout()
            self.server = None
