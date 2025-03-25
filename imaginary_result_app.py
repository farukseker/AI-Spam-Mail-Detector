import streamlit as st
from app import EmailSpamClassifier
from dataclasses import dataclass
import random


@dataclass(frozen=True)
class EmailResult:
    is_spam: bool | None = None
    sentiment: str | None = None
    is_important: bool | None = None
    subject: str = ""
    sender: str = ""
    has_error: bool = False


def create_good_data(row: int) -> list:
    for _ in range(row):
        yield {
            "is_spam": '❌',
            "is_important": '✔️',
            "sentiment": '🌿',
            "subject": 'Good Content Test Mail',
            "sender": 'Good User',
            "has_error": '❌'
        }


def create_bad_data(row: int) -> list:
    for _ in range(row):
        yield {
            "is_spam": '✔️',
            "is_important": '❌',
            "sentiment": '🗑️',
            "subject": 'Bad Content Test Mail',
            "sender": 'Good/Bad User',
            "has_error": '❌'
        }


def do_data() -> list[dict[str, str]]:
    good_results = list(create_good_data(15))
    bad_results = list(create_bad_data(15))

    mixed_results = good_results + bad_results
    random.shuffle(mixed_results)

    return mixed_results


st.set_page_config(layout="wide")
st.title("Email Spam Classifier")

classifier = EmailSpamClassifier()

if llm_list := classifier.local_llm.list_llm():
    st.subheader("SMTP Login")

    email_user = st.text_input("Email Address", value='YOUREMAIL')
    email_pass = st.text_input("Email Password", type="password", value='YOURPASSWORD')

    selected_model = st.selectbox("Choose a model", llm_list)
    row = st.number_input(label='Set a mail limit or 0 unlimited', value=10)

    st.title(f"Model: {selected_model}")

    st.button("Fetch and Analyze Emails")

    st.table([result for result in do_data()])
    st.button(label="Download Results as Excel")
