from performance import get_performance_metric
from user import PASSWORD, USERNAME
import imaplib
import email
from ollama import chat
from ollama import ChatResponse


# IMAP bağlantısı kur
def connect_to_email_server(username, password, server, port=993):
    mail = imaplib.IMAP4_SSL(server, port)
    mail.login(username, password)
    return mail


# Gelen kutusundan e-postaları al
def fetch_emails(mail, folder="INBOX"):
    mail.select(folder)
    _, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    return email_ids


# E-posta içeriğini ayrıştır
def get_email_content(mail, email_id):
    _, data = mail.fetch(email_id, "(RFC822)")
    raw_email = data[0][1]

    if not raw_email:
        print(f"Email ID {email_id} boş!")
        return None

    try:
        msg = email.message_from_bytes(raw_email)
        if msg is None:
            print(f"Email ID {email_id} ayrıştırılamadı!")
            return None
        return msg
    except Exception as e:
        print(f"Error parsing email ID {email_id}: {e}")
        return None


# E-posta analiz fonksiyonu
def analyze_email_content(email_content, llm):
    if email_content is None:
        print("E-posta içeriği alınamadı!")
        return

    # E-posta başlıkları
    subject = email_content.get("Subject", "Bilinmeyen Konu")
    sender = email_content.get("From", "Bilinmeyen Gönderen")

    # E-posta gövdesi
    body = ""
    if email_content.is_multipart():
        for part in email_content.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = email_content.get_payload(decode=True).decode()

    print(f"Gönderen: {sender}")
    print(f"Konu: {subject}")
    # print(f"Body: {body[:100]}...")  # Body'nin sadece ilk 200 karakterini yazdırıyoruz

    # LLM ile dil analizi
    try:
        response: ChatResponse = chat(
            model="deepseek-r1:1.5b",  # Kullanmak istediğiniz model
            # model="llama3.1:latest",  # Kullanmak istediğiniz model
            # model="llama3.2:1b",  # Kullanmak istediğiniz model
            messages=[  # Kullanıcıdan gelen mesajlar
                {
                    'role': 'user',
                    'content': f"""
                                   Scan this email content and identify it with the headings |spam|good|undefined|fraud|
                            
                            let the information you detected be at the top of the results for example spam:(mail content)
                            now I am entering the email you will analyze
                            mail: {body} 
                    """,  # E-posta içeriğini modelle analiz et
                },
            ]
        )
        print(f"E-posta analiz sonucu: {response.message.content}")
    except Exception as e:
        print(f"LLM analizi hatası: {e}")


@get_performance_metric
def main() -> None:
    # Kullanıcı bilgileri ve sunucu detayları
    SERVER = "imap.gmail.com"

    # LLM modeli ile bağlantı kur
    # IMAP bağlantısı
    mail = connect_to_email_server(USERNAME, PASSWORD, SERVER)
    email_ids = fetch_emails(mail)

    # İlk e-postayı analiz et
    for email_id in email_ids[:10]:  # İlk 5 e-posta
        email_content = get_email_content(mail, email_id)
        analyze_email_content(email_content, chat)
        print('=' * 50)
    mail.logout()


# Ana iş akışı
if __name__ == "__main__":
    main()
