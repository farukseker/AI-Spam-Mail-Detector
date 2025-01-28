from langchain_ollama.llms import OllamaLLM
from langchain_ollama.chat_models import Client
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel


class EmailAnalysis(BaseModel):
    is_spam: bool
    sentiment: str
    themes: list[str]
    is_important: bool


class LocalLLM:
    def __init__(self, selected_template: str):
        self.parser: PydanticOutputParser = PydanticOutputParser(pydantic_object=EmailAnalysis)
        self.selected_template: str = selected_template
        self.__selected_model: str | None = None

    @property
    def _prompt_template_text(self) -> str:
        with open(self.selected_template, 'r', encoding='utf-8') as df:
            return df.read()

    @property
    def load_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(template=self._prompt_template_text, input_variables=["email_text"])

    @property
    def client(self) -> Client:
        return Client()

    def list_llm(self) -> list | None:
        try:
            model_list = self.client.list()
            return [n.model for n in [model[1] for model in model_list][0]]
        except Exception as e:
            # log ekle
            return None

    @property
    def selected_model(self) -> str:
        return self.__selected_model

    @selected_model.setter
    def selected_model(self, _llm: str):
        if _llm in self.list_llm():
            self.__selected_model = _llm
        else:
            raise ValueError("The selected llm model is does not in LocalLLM's list")

    @property
    def chain(self):
        if self.__selected_model is None:
            raise ValueError('The selected_model is does not None')

        return self.load_prompt_template | OllamaLLM(client=self.client, model=self.selected_model) | self.parser

    def analyze_mail(self, email):
        response = self.chain.invoke({"email_text": email})
        print(response)


from email_service import EmailFetcher
from config import TEST_USERNAME, TEST_PASSWORD


email_fetcher: EmailFetcher = EmailFetcher(TEST_USERNAME, TEST_PASSWORD)

try:
    email_fetcher.connect()

    llm = LocalLLM(selected_template='prompt_templates/worked.two.txt')
    if llms := llm.list_llm():
        print(llms)

    llm.selected_model = llms[1]
    print('mail')

    for mail in email_fetcher.fetch_emails(10):
        print(mail.subject)
        llm.analyze_mail(email=mail.body)
except Exception as e:
    print(f'ERROR: {str(e)}')
finally:
    email_fetcher.disconnect()

