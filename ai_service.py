from langchain_ollama.llms import OllamaLLM
from langchain_ollama.chat_models import Client
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel


class EmailAnalysis(BaseModel):
    is_spam: bool | None = None
    sentiment: str | None = None
    themes: list[str] | None = None
    is_important: bool | None = None


class LocalLLM:
    def __init__(self):
        self.parser: PydanticOutputParser = PydanticOutputParser(pydantic_object=EmailAnalysis)
        self.__selected_template: str | None = 'prompt_templates/worked.two.txt'
        self.__selected_model: str | None = None

    @property
    def _prompt_template_text(self) -> str:
        with open(self.__selected_template, 'r', encoding='utf-8') as df:
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

    def analyze_mail(self, email) -> EmailAnalysis | None:
        try:
            return self.chain.invoke({"email_text": email})
        except Exception as e:
            print(e)
            return None


