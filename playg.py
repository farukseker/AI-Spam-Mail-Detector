# import ollama
#
#
# # Ollama modelini kullanarak spam analizi yapacak bir fonksiyon oluşturuyoruz
# def analyze_email_spam(email_text):
#     # Ollama'ya e-posta metnini gönderiyoruz ve spam olup olmadığını soruyoruz
#     prompt = f"""
#     Analyze the following email and determine if it is spam or not.
#     Return a JSON response with the following fields:
#     - is_spam: True if the email is spam, False if not.
#     - sentiment: Positive, Negative, or Neutral.
#     - themes: List of key themes discussed in the email.
#
#     Email text: {email_text}
#     """
#
#     # Ollama API'sini kullanarak analizi yapıyoruz
#     response = ollama.chat(model='llama3.2:3b', messages=[{"role": "user", "content": prompt}])
#     # Çıktıyı alıyoruz
#     result = response['message']
#
#     return result
#
#
# # E-posta örneği
# email_text = """
# Congratulations! You've won a $1000 gift card. Click here to claim your prize.
# This is a limited-time offer, so act fast!
# """
#
# # Spam analizi yapıyoruz
# response = analyze_email_spam(email_text)
#
# # Sonuçları yazdırıyoruz
# print(response.content)
import email
from langchain_ollama.llms import OllamaLLM
from langchain_ollama.chat_models import Client
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
import imaplib
from email.header import decode_header
from config import TEST_PASSWORD, TEST_USERNAME
from bs4 import BeautifulSoup
import re


def clean_text(text):
    # Unicode özel karakterleri kaldır
    text = re.sub(r'[\u200c\u00a0]', ' ', text)

    # Gereksiz boşlukları temizle
    text = re.sub(r'\s+', ' ', text)

    # Metnin başındaki ve sonundaki boşlukları kırp
    text = text.strip()

    return text


def fetch_emails(email_user, email_pass, limit=10):
    try:
        # Gmail IMAP sunucusuna bağlan
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Gelen kutusundaki mailleri al
        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()[-limit:]  # Son `limit` kadar mail al
        emails = []

        for mail_id in mail_ids:
            status, msg_data = mail.fetch(mail_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # E-posta mesajını çözümle
                    msg = email.message_from_bytes(response_part[1])

                    # Başlıkları çözümle
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()

                    from_ = msg.get("From")

                    # Mesaj gövdesini çözümle
                    body = ""
                    urls = []
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/html" and "attachment" not in content_disposition:
                                html_content = part.get_payload(decode=True).decode()

                                # HTML içeriğinden metin ve URL'leri çıkar
                                soup = BeautifulSoup(html_content, "html.parser")
                                body = clean_text(soup.get_text(strip=True))
                                urls = [a['href'] for a in soup.find_all('a', href=True)]
                                break
                            elif content_type == "text/plain" and "attachment" not in content_disposition:
                                body = part.get_payload(decode=True).decode()
                    else:
                        body = clean_text(msg.get_payload(decode=True).decode())
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


class EmailAnalysis(BaseModel):
    is_spam: bool
    sentiment: str
    themes: list[str]


# JsonOutputParser
parser = PydanticOutputParser(pydantic_object=EmailAnalysis)

# Prompt template with stricter JSON instructions
prompt_template = PromptTemplate(
    template="""Analyze the following email text and determine if it is spam or not.
    Return the result strictly in JSON format. The JSON object should have the following fields:
    - is_spam (True/False): Whether the email is spam or not.
    - sentiment (string): Sentiment of the email (positive, negative, or neutral).
    - themes (list of strings): Key themes or aspects discussed in the email.

    Email text: {email_text}
    JSON response:""",
    input_variables=["email_text"],
)

# Ollama Client and model
client = Client()
# llm = OllamaLLM(client=client, model="llama3.1:latest")
# llm = OllamaLLM(client=client, model="llama3.2:3b")
llm = OllamaLLM(client=client, model="deepseek-r1:1.5b")

# Chain integration
chain = prompt_template | llm | parser

emails = fetch_emails(TEST_USERNAME, TEST_PASSWORD, limit=20)
if isinstance(emails, str):  # Hata kontrolü
    print(f"Error fetching emails: {emails}")

for email in emails:
    # print(email)
    try:
        # Spam analysis
        response = chain.invoke({"email_text": email.get('body')})
        print(response)
    except Exception as e:
        print(f"Error: {e}")
