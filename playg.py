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
from performance import get_performance_metric


def clean_text(text):
    # Unicode özel karakterleri kaldır
    text = re.sub(r'[\u200c\u00a0]', ' ', text)

    # Gereksiz boşlukları temizle
    text = re.sub(r'\s+', ' ', text)

    # Metnin başındaki ve sonundaki boşlukları kırp
    text = text.strip()

    return text


def fetch_emails(email_user, email_pass, limit=100):
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
    themes: list[str] | str
    is_important: bool


# JsonOutputParser
parser = PydanticOutputParser(pydantic_object=EmailAnalysis)

# Prompt template with stricter JSON instructions
prompt_template = PromptTemplate(
    template="""Analyze the following email text and determine the following:
    1. Is the email spam or not?
    2. What is the sentiment of the email (positive, negative, or neutral)?
    3. What are the key themes or aspects discussed in the email?
    4. Should this email be considered important and worth attention?

    You must return the result strictly as a valid JSON object. No extra text, comments, or explanations should be included.
    If the output is not in valid JSON format, the response will be considered invalid.

    The JSON object must strictly follow this structure:
    {{
        "is_spam": true or false,
        "sentiment": "positive" or "negative" or "neutral",
        "themes": ["theme1", "theme2", ...],
        "is_important": true or false
    }}

    Email text: {email_text}
    JSON response:""",
    input_variables=["email_text"],
)


models: dict[int, str] = {
    0: 'llama3.2:1b',
    1: 'llama3.2:3b',  # ok
    2: 'benevolentjoker/nsfwvanessa:latest',
    3: 'llama3.2-vision:11b',
    4: 'deepseek-coder-v2:latest',
    5: 'llava:latest',
    6: 'llama3.1:latest',
    7: 'deepseek-r1:1.5b'  # ok
}

selected_model: str = models[0]
# Ollama Client and model
client = Client()
# llm = OllamaLLM(client=client, model="llama3.1:latest")
# llm = OllamaLLM(client=client, model="llama3.2:3b")
llm = OllamaLLM(client=client, model=selected_model)
mail_count: int = 40
# Chain integration
chain = prompt_template | llm | parser


@get_performance_metric
def task() -> None:
    emails = fetch_emails(TEST_USERNAME, TEST_PASSWORD, limit=mail_count)
    if isinstance(emails, str):  # Hata kontrolü
        print(f"Error fetching emails: {emails}")

    spam_counter: int = 0
    error_counter: int = 0
    for email in emails:
        # print(email)
        try:
            # Spam analysis
            # print(email.get('subject'))
            response = chain.invoke({"email_text": email.get('body')})
            # print(response)
            if response.is_spam:
                spam_counter += 1
            print(f'id({email.get('id')}) - "{email.get('subject')} | {'SPAM' if response.is_spam else 'CLEAN'} | {'IMP' if response.is_important else 'NOT'}"')
        except Exception as e:
            error_counter += 1
            print(f'ERROR: id({email.get('id')}) - "{email.get('subject')}')
            with open('parssed.error.log', 'a+', encoding='utf-8') as df:
                df.write(str(e))
    print(f"""
        {selected_model} -> spam sayısı: {spam_counter},
        model: {selected_model},
        error: {error_counter},
        mail count: {mail_count}"""
    )


if __name__ == '__main__':
    task()


'''
"id": mail_id.decode(),
"subject": subject,
"from": from_,
"body": body.strip(),
"urls": urls
'''