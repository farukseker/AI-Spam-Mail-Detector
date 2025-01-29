import streamlit as st
import os
import json
import imaplib
import email
from email.header import decode_header
from ollama import chat, list
from ollama import ChatResponse
from langchain_ollama.llms import OllamaLLM
from langchain_ollama.chat_models import Client
from user import PASSWORD, USERNAME


# Geçmiş model seçimini kaydetmek için dosya yolu
MODEL_CONFIG_FILE = "last_model.json"


# Geçmiş model seçimini yükleme
def load_last_model():
    if os.path.exists(MODEL_CONFIG_FILE):
        with open(MODEL_CONFIG_FILE, "r") as file:
            return json.load(file).get("last_model", None)
    return None


# Model seçimini kaydetme
def save_last_model(model_name):
    with open(MODEL_CONFIG_FILE, "w") as file:
        json.dump({"last_model": model_name}, file)


# Ollama'nın yüklü olup olmadığını kontrol etme
def check_ollama():
    try:
        model_list = Client().list()
        model_list = [n.model for n in [model[1] for model in model_list][0]]
        return True, model_list
    except Exception as e:
        return False, str(e)


# Mailleri alma (IMAP)
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
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    emails.append({"id": mail_id, "subject": subject})
        return emails
    except Exception as e:
        return str(e)


# LLM ile analiz
def analyze_emails(email, model_name):
    try:
        response: ChatResponse = chat(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": f"""Scan this email content and identify it with the headings |spam|good|undefined|fraud|
                    let the information you detected be at the top of the results for example spam:(mail content)
                    now I am entering the email you will analyze
                    mail:: {email['subject']}"""
                }
            ]
        )
        result = response.message.content.lower()
        print(result)
        status = "Spam" if "spam" in result else "Ham" if "ham" in result else "Unknown"
        return {"title": email["subject"], "status": status}
    except Exception as e:
        return {"title": email["subject"], "status": f"Error: {e}"}


def main():
    st.title("Email Spam Classifier")

    st.subheader("Ollama Check")
    ollama_installed, ollama_data = check_ollama()
    if not ollama_installed:
        st.error(f"Ollama is not installed: {ollama_data}")
        return
    st.success("Ollama is installed.")

    st.subheader("Select LLM Model")
    last_model = load_last_model()
    models = ollama_data
    selected_model = st.selectbox("Choose a model", models,
                                  index=models.index(last_model) if last_model in models else 0)
    if selected_model:
        print(selected_model)
        save_last_model(selected_model)

    # SMTP giriş bilgileri
    st.subheader("SMTP Login")
    email_user = st.text_input("Email Address", value=USERNAME)
    email_pass = st.text_input("Email Password", value=PASSWORD, type="password")

    if st.button("Fetch and Analyze Emails"):
        if not email_user or not email_pass:
            st.error("Please provide email credentials.")
            return

        # Mailleri al
        st.info("Fetching emails...")
        emails = fetch_emails(email_user, email_pass)
        if isinstance(emails, str):  # Hata kontrolü
            st.error(f"Error fetching emails: {emails}")
            return

        # Mailleri analiz et
        st.info("Analyzing emails...")

        # Create a placeholder for the table
        table_placeholder = st.empty()
        results = []

        for email in emails[:10]:
            results.append(analyze_emails(email, selected_model))
            table_placeholder.table(results)

        # Sonuçları göster
        st.subheader("Analysis Results")
        st.table(results)


if __name__ == "__main__":
    main()
