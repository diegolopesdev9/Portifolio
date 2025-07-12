import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações do sistema
CONFIG = {
    "embedding_model": "models/embedding-001",
    "llm_model": "gemini-1.5-pro",
    "temperature": 0.7,
    "persist_directory": "./chroma_db",
    "max_results": 3,
    "max_retries": 3,
    "timeout": 30
}

class RAGChatbot:
    """Sistema RAG (Retrieval-Augmented Generation) para consultas sobre documentação."""

    def __init__(self, config: Dict = None):
        """
        Inicializa o chatbot RAG.

        Args:
            config: Dicionário com configurações personalizadas
        """
        self.config = config or CONFIG
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self.llm = None
        self.qa_chain = None

        self._setup_environment()
        self._initialize_components()

    def _setup_environment(self):
        """Configura as variáveis de ambiente e validações."""
        try:
            load_dotenv()
            self.google_api_key = os.getenv("GOOGLE_API_KEY")

            if not self.google_api_key:
                logger.error("A variável de ambiente GOOGLE_API_KEY não está configurada.")
                raise ValueError("A variável de ambiente GOOGLE_API_KEY não está configurada.")

            logger.info("Variáveis de ambiente carregadas com sucesso.")

        except FileNotFoundError:
            logger.error("O arquivo .env não foi encontrado. Por favor, crie-o com a chave API do Google.")
            raise
        except Exception as e:
            logger.error(f"Erro ao configurar ambiente: {e}")
            raise

    def _initialize_components(self):
        """Inicializa todos os componentes do sistema RAG."""
        try:
            # Inicializa o modelo de embedding
            logger.info("Inicializando modelo de embedding...")
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=self.config["embedding_model"],
                google_api_key=self.google_api_key
            )

            # Carrega o ChromaDB persistido
            logger.info("Carregando banco de dados vetorial ChromaDB...")
            self.vectorstore = Chroma(
                persist_directory=self.config["persist_directory"],
                embedding_function=self.embeddings
            )

            # Configura o retriever com parâmetros otimizados
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": self.config["max_results"]}
            )

            # Inicializa o LLM do Google Gemini
            logger.info("Inicializando modelo de linguagem...")
            self.llm = ChatGoogleGenerativeAI(
                model=self.config["llm_model"],
                google_api_key=self.google_api_key,
                temperature=self.config["temperature"]
            )

            # Cria a cadeia RAG
            self._create_qa_chain()

            logger.info("Sistema RAG inicializado com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao inicializar componentes: {e}")
            raise

    def _create_qa_chain(self):
        """Cria a cadeia de perguntas e respostas com prompt otimizado."""

        prompt_template = """Você é um assistente especializado em documentação da LangChain. Use EXCLUSIVAMENTE as informações de contexto fornecidas para responder à pergunta.

INSTRUÇÕES IMPORTANTES:
- Se você não souber a resposta baseada no contexto, diga: "Não tenho informações suficientes no contexto fornecido para responder a esta pergunta."
- Seja conciso e direto em suas respostas
- Cite exemplos específicos quando disponíveis no contexto
- Mantenha um tom profissional e prestativo

Contexto: {context}

Pergunta: {question}

Resposta baseada no contexto:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )

    def ask_question(self, query: str) -> Dict:
        """
        Processa uma pergunta e retorna a resposta com metadados.

        Args:
            query: Pergunta a ser respondida

        Returns:
            Dict com resposta, fontes e metadados
        """
        if not query or not query.strip():
            return {
                "error": "Pergunta não pode estar vazia",
                "result": None,
                "source_documents": []
            }

        try:
            logger.info(f"Processando pergunta: {query}")

            # Executa a consulta
            result = self.qa_chain.invoke({"query": query})

            # Processa os documentos fonte
            sources = []
            for doc in result.get("source_documents", []):
                source_info = {
                    "source": doc.metadata.get("source", "Fonte não disponível"),
                    "page": doc.metadata.get("page", "N/A"),
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                sources.append(source_info)

            response_data = {
                "query": query,
                "result": result.get("result", "Resposta não disponível"),
                "source_documents": sources,
                "num_sources": len(sources)
            }

            logger.info(f"Pergunta processada com sucesso. Fontes encontradas: {len(sources)}")
            return response_data

        except Exception as e:
            logger.error(f"Erro ao processar pergunta '{query}': {e}")
            return {
                "error": f"Erro ao processar pergunta: {str(e)}",
                "result": None,
                "source_documents": []
            }

    def display_response(self, response_data: Dict):
        """Exibe a resposta de forma formatada."""
        if response_data.get("error"):
            print(f"❌ Erro: {response_data['error']}")
            return

        print(f"\n🤖 Pergunta: {response_data['query']}")
        print(f"📝 Resposta: {response_data['result']}")
        print(f"\n📚 Fontes consultadas ({response_data['num_sources']}):")

        for i, source in enumerate(response_data['source_documents'], 1):
            print(f"  {i}. {source['source']} (Página: {source['page']})")
            if source['content_preview']:
                print(f"     Preview: {source['content_preview']}")
        print("-" * 80)

    def interactive_chat(self):
        """Interface interativa para chat contínuo."""
        print("=" * 80)
        print("🚀 CHATBOT RAG - DOCUMENTAÇÃO LANGCHAIN")
        print("=" * 80)
        print("Comandos disponíveis:")
        print("  • Digite sua pergunta normalmente")
        print("  • 'sair' ou 'quit' para encerrar")
        print("  • 'limpar' para limpar a tela")
        print("  • 'ajuda' para ver este menu")
        print("=" * 80)

        while True:
            try:
                query = input("\n💬 Sua pergunta: ").strip()

                if not query:
                    continue

                if query.lower() in ['sair', 'quit', 'exit']:
                    print("👋 Encerrando chatbot. Até logo!")
                    break

                if query.lower() == 'limpar':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue

                if query.lower() == 'ajuda':
                    print("\n📖 Comandos disponíveis:")
                    print("  • Digite sua pergunta normalmente")
                    print("  • 'sair' ou 'quit' para encerrar")
                    print("  • 'limpar' para limpar a tela")
                    print("  • 'ajuda' para ver este menu")
                    continue

                # Processa a pergunta
                response = self.ask_question(query)
                self.display_response(response)

            except KeyboardInterrupt:
                print("\n\n👋 Chatbot interrompido pelo usuário. Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro inesperado no chat interativo: {e}")
                print(f"❌ Erro inesperado: {e}")

    def get_database_info(self) -> Dict:
        """Retorna informações sobre o banco de dados vetorial."""
        try:
            collection = self.vectorstore._collection
            return {
                "total_documents": collection.count(),
                "persist_directory": self.config["persist_directory"],
                "embedding_model": self.config["embedding_model"]
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações do banco: {e}")
            return {"error": str(e)}

def run_examples(chatbot: RAGChatbot):
    """Executa exemplos de perguntas para demonstração."""
    print("\n🔍 EXECUTANDO EXEMPLOS DE DEMONSTRAÇÃO")
    print("=" * 80)

    example_questions = [
        "O que é LangChain?",
        "Como usar o WebBaseLoader?",
        "Qual a função do RecursiveCharacterTextSplitter?",
        "Como configurar um sistema RAG?",
        "Quais são os tipos de chains disponíveis?"
    ]

    for question in example_questions:
        response = chatbot.ask_question(question)
        chatbot.display_response(response)

def main():
    """Função principal do programa."""
    try:
        # Inicializa o chatbot
        chatbot = RAGChatbot()

        # Mostra informações do banco de dados
        db_info = chatbot.get_database_info()
        if not db_info.get("error"):
            print(f"📊 Banco de dados: {db_info['total_documents']} documentos carregados")

        # Pergunta ao usuário como quer usar o sistema
        print("\n🎯 Como você gostaria de usar o sistema?")
        print("1. Chat interativo")
        print("2. Executar exemplos de demonstração")
        print("3. Fazer uma pergunta específica")

        choice = input("\nEscolha uma opção (1-3): ").strip()

        if choice == "1":
            chatbot.interactive_chat()
        elif choice == "2":
            run_examples(chatbot)
        elif choice == "3":
            question = input("Digite sua pergunta: ").strip()
            if question:
                response = chatbot.ask_question(question)
                chatbot.display_response(response)
        else:
            print("Opção inválida. Iniciando chat interativo...")
            chatbot.interactive_chat()

    except Exception as e:
        logger.error(f"Erro na execução principal: {e}")
        print(f"❌ Erro crítico: {e}")

if __name__ == "__main__":
    main()
