import time
import pandas as pd
from dataclasses import dataclass
import streamlit as st
from ai_service import LocalLLM
from email_service import EmailFetcher
from performance import get_performance_metric


@dataclass(frozen=True)
class EmailResult:
    is_spam: bool | None = None
    sentiment: str | None = None
    themes: list[str] | None = None
    is_important: bool | None = None
    has_error: bool = False
    error_message: str | None = None
    id: str = ""
    subject: str = ""
    is_starred: bool = False
    labels: list[str] = None
    flags: list[str] = None
    sender: str = ""


class EmailSpamClassifier:
    def __init__(self):
        self.email_fetcher = None
        self.local_llm = LocalLLM()

    def fetch_and_analyze_emails(self, limit: int):
        self.email_fetcher.connect()
        results = []

        for mail in self.email_fetcher.fetch_emails(limit):
            analysis = None
            attempts = 0
            while analysis is None and attempts < 2:
                analysis = self.local_llm.analyze_mail(email=mail.body)
                if analysis is None:
                    time.sleep(0.1)
                    attempts += 1

            if analysis:
                results.append(EmailResult(
                    is_spam=analysis.is_spam,
                    is_important=analysis.is_important,
                    sentiment=analysis.sentiment,
                    themes=analysis.themes,
                    id=mail.id,
                    subject=mail.subject,
                    is_starred=mail.is_starred,
                    labels=mail.labels,
                    flags=mail.flags,
                    sender=mail._from
                ))
            else:
                results.append(EmailResult(
                    has_error=True,
                    error_message="Analysis failed after 2 attempts",
                    id=mail.id,
                    subject=mail.subject,
                    sender=mail._from
                ))

        self.email_fetcher.disconnect()
        return results


@get_performance_metric
def main() -> None:
    # Streamlit UI
    st.set_page_config(layout="wide")
    st.title("Email Spam Classifier")
    classifier = EmailSpamClassifier()

    if llm_list := classifier.local_llm.list_llm():
        st.subheader("SMTP Login")
        email_user = st.text_input("Email Address", type='password', value='YOUREMAIL')
        email_pass = st.text_input("Email Password", type="password", value='YOURPASSWORD')

        selected_model = st.selectbox("Choose a model", llm_list)
        classifier.local_llm.selected_model = selected_model

        row = st.number_input(label='Set a mail limit or 0 unlimited', value=10)

        if st.button("Fetch and Analyze Emails"):
            classifier.email_fetcher = EmailFetcher(email_user, email_pass)
            results = classifier.fetch_and_analyze_emails(row)

            st.subheader("Analysis Results")
            st.table([result.__dict__ for result in results])

            if results:
                df = pd.DataFrame([result.__dict__ for result in results])
                import io

                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                excel_buffer.seek(0)

                st.download_button(label="Download Results as Excel", data=excel_buffer, file_name="email_analysis.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error('please start "ollama"')


if __name__ == '__main__':
    main()
