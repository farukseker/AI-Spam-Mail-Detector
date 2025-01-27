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
from langchain_ollama.llms import OllamaLLM
from langchain_ollama.chat_models import Client
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel


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
llm = OllamaLLM(client=client, model="llama3.1:latest")

# Chain integration
chain = prompt_template | llm | parser

for _ in range(10):
    # Email example
    email_text = """
    Congratulations! You've won a $1000 gift card. Click here to claim your prize.
    This is a limited-time offer, so act fast!
    """

    try:
        # Spam analysis
        response = chain.invoke({"email_text": email_text})
        print(response)
    except Exception as e:
        print(f"Error: {e}")
