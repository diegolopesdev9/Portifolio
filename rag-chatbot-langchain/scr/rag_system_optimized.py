import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()


class RAGChatbotFinal:
    """Sistema RAG Completo com Google Gemini - Versão Final."""

    def __init__(self):
        """Inicializa o sistema RAG."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.config = self._get_config()
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.session_stats = {
            "queries_made": 0,
            "total_tokens": 0,
            "start_time": datetime.now()
        }

        print("🚀 Sistema RAG inicializado com sucesso!")

    def _get_config(self) -> Dict:
        """Configuração otimizada (sem dependência de arquivo externo)."""
        return {
            "llm_model": "gemini-1.5-flash",
            "temperature": 0.7,
            "max_results": 3,
            "cache_size": 100,
            "rate_limit_requests": 10,
            "rate_limit_window": 60,
            "min_query_length": 3,
            "max_query_length": 1000,
            "timeout": 30
        }

    def validate_setup(self) -> bool:
        """Valida se tudo está configurado corretamente."""
        if not self.api_key:
            print("❌ API Key não encontrada!")
            print("📝 Configure no arquivo .env: GOOGLE_API_KEY=sua_chave")
            print("🔗 Obtenha sua chave em: https://aistudio.google.com/")
            return False

        print("✅ API Key configurada!")
        print("✅ Sistema pronto para uso!")
        return True

    def _validate_query(self, query: str) -> tuple[bool, str]:
        """Valida a query de entrada."""
        if not query or not query.strip():
            return False, "Pergunta não pode estar vazia"

        query = query.strip()

        if len(query) < self.config["min_query_length"]:
            return False, f"Pergunta muito curta (mínimo {self.config['min_query_length']} caracteres)"

        if len(query) > self.config["max_query_length"]:
            return False, f"Pergunta muito longa (máximo {self.config['max_query_length']} caracteres)"

        return True, query

    def _create_optimized_prompt(self, query: str) -> str:
        """Cria um prompt otimizado para o Gemini."""
        return f"""Você é um assistente inteligente e prestativo. Responda à seguinte pergunta de forma clara, precisa e educativa.

INSTRUÇÕES:
- Seja direto e objetivo
- Use exemplos práticos quando apropriado
- Se não souber algo, seja honesto sobre isso
- Mantenha um tom profissional e amigável
- Estruture sua resposta de forma clara

PERGUNTA: {query}

RESPOSTA:"""

    def call_gemini_api(self, query: str) -> Dict:
        """Chama a API do Google Gemini."""
        try:
            # Valida a query
            is_valid, processed_query = self._validate_query(query)
            if not is_valid:
                return self._create_error_response(query, processed_query)

            # Prepara headers e payload
            headers = {"Content-Type": "application/json"}

            prompt = self._create_optimized_prompt(processed_query)

            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": self.config["temperature"],
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                    "stopSequences": []
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }

            url = f"{self.base_url}?key={self.api_key}"

            print("🔄 Consultando Google Gemini...")

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config["timeout"]
            )

            if response.status_code == 200:
                result = response.json()
                return self._process_gemini_response(processed_query, result)
            else:
                error_msg = f"Erro HTTP {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                return self._create_fallback_response(processed_query, error_msg)

        except requests.exceptions.Timeout:
            error_msg = "Timeout na consulta ao Gemini"
            logger.error(error_msg)
            return self._create_fallback_response(query, error_msg)

        except requests.exceptions.ConnectionError:
            error_msg = "Erro de conexão. Verifique sua internet"
            logger.error(error_msg)
            return self._create_fallback_response(query, error_msg)

        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            logger.error(error_msg)
            return self._create_fallback_response(query, error_msg)

    def _process_gemini_response(self, query: str, result: Dict) -> Dict:
        """Processa a resposta do Gemini."""
        try:
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                content = candidate['content']['parts'][0]['text']

                # Atualiza estatísticas
                self.session_stats["queries_made"] += 1

                return {
                    "query": query,
                    "result": content.strip(),
                    "model": self.config["llm_model"],
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "source": "Google Gemini",
                    "real_api": True,
                    "session_query_count": self.session_stats["queries_made"]
                }
            else:
                raise Exception("Resposta vazia ou inválida do Gemini")

        except Exception as e:
            logger.error(f"Erro ao processar resposta: {e}")
            return self._create_fallback_response(query, str(e))

    def _create_error_response(self, query: str, error: str) -> Dict:
        """Cria resposta de erro."""
        return {
            "query": query,
            "result": f"Erro: {error}",
            "model": "sistema",
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "source": "Sistema Local",
            "real_api": False
        }

    def _create_fallback_response(self, query: str, error: str) -> Dict:
        """Cria resposta de fallback em caso de erro."""
        fallback_text = f"""Desculpe, não foi possível processar sua pergunta no momento devido a: {error}

Como alternativa, aqui está uma resposta básica sobre sua pergunta: "{query}"

Esta é uma resposta simulada. Para obter respostas mais precisas, verifique sua conexão com a internet e tente novamente."""

        return {
            "query": query,
            "result": fallback_text,
            "model": "fallback",
            "timestamp": datetime.now().isoformat(),
            "status": "fallback",
            "source": "Sistema Local",
            "real_api": False,
            "error": error
        }

    def display_response(self, response: Dict):
        """Exibe resposta formatada."""
        print(f"\n🤖 Pergunta: {response['query']}")
        print(f"📝 Resposta: {response['result']}")
        print(f"🔧 Modelo: {response['model']}")

        if response.get('real_api'):
            print("✅ Resposta real do Google Gemini!")
        elif response['status'] == 'error':
            print("❌ Erro na consulta!")
        else:
            print("⚠️  Resposta simulada (modo fallback)")

        print(f"📊 Status: {response['status']}")
        print(f"⏰ Timestamp: {response['timestamp']}")

        if response.get('session_query_count'):
            print(f"📈 Consultas na sessão: {response['session_query_count']}")

        print("-" * 80)

    def interactive_chat(self):
        """Chat interativo avançado."""
        print("=" * 80)
        print("🤖 CHAT RAG COM GOOGLE GEMINI - VERSÃO AVANÇADA")
        print("=" * 80)
        print("Comandos especiais:")
        print("  • 'sair' ou 'quit' - Encerra o chat")
        print("  • 'ajuda' - Mostra comandos disponíveis")
        print("  • 'stats' - Mostra estatísticas da sessão")
        print("  • 'limpar' - Limpa a tela")
        print("  • 'teste' - Testa conexão com Gemini")
        print("=" * 80)
        print("💡 Dica: Seja específico em suas perguntas para obter melhores respostas!")
        print("=" * 80)

        while True:
            try:
                query = input("\n💬 Sua pergunta: ").strip()

                if not query:
                    print("⚠️  Digite uma pergunta ou comando.")
                    continue

                # Comandos especiais
                if query.lower() in ['sair', 'quit', 'exit']:
                    self._show_session_summary()
                    print("👋 Obrigado por usar o sistema RAG! Até logo!")
                    break

                elif query.lower() == 'ajuda':
                    self._show_help()
                    continue

                elif query.lower() == 'stats':
                    self._show_statistics()
                    continue

                elif query.lower() == 'limpar':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("🧹 Tela limpa!")
                    continue

                elif query.lower() == 'teste':
                    print("🔄 Testando conexão com Google Gemini...")
                    test_response = self.call_gemini_api("Olá! Você está funcionando?")
                    self.display_response(test_response)
                    continue

                # Processa pergunta normal
                response = self.call_gemini_api(query)
                self.display_response(response)

            except KeyboardInterrupt:
                print("\n\n👋 Chat interrompido pelo usuário. Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro no chat: {e}")
                print(f"❌ Erro inesperado: {e}")

    def _show_help(self):
        """Mostra ajuda detalhada."""
        print("\n📖 AJUDA - COMANDOS DISPONÍVEIS")
        print("-" * 50)
        print("🗣️  PERGUNTAS NORMAIS:")
        print("   • Digite qualquer pergunta e pressione Enter")
        print("   • Exemplos: 'O que é IA?', 'Como funciona Python?'")
        print("\n⚙️  COMANDOS ESPECIAIS:")
        print("   • 'sair' / 'quit' - Encerra o programa")
        print("   • 'ajuda' - Mostra esta ajuda")
        print("   • 'stats' - Estatísticas da sessão")
        print("   • 'limpar' - Limpa a tela")
        print("   • 'teste' - Testa conexão com Gemini")
        print("\n💡 DICAS:")
        print("   • Seja específico em suas perguntas")
        print("   • Use português ou inglês")
        print("   • Evite perguntas muito longas")

    def _show_statistics(self):
        """Mostra estatísticas da sessão."""
        duration = datetime.now() - self.session_stats["start_time"]

        print(f"\n📊 ESTATÍSTICAS DA SESSÃO")
        print("-" * 40)
        print(f"🕒 Tempo de sessão: {duration}")
        print(f"📈 Consultas realizadas: {self.session_stats['queries_made']}")
        print(f"🤖 Modelo em uso: {self.config['llm_model']}")
        print(f"🌡️  Temperature: {self.config['temperature']}")
        print(f"⏱️  Timeout: {self.config['timeout']}s")

    def _show_session_summary(self):
        """Mostra resumo da sessão."""
        duration = datetime.now() - self.session_stats["start_time"]

        print("\n" + "=" * 60)
        print("📊 RESUMO DA SESSÃO")
        print("=" * 60)
        print(f"⏰ Duração total: {duration}")
        print(f"🔢 Total de consultas: {self.session_stats['queries_made']}")
        print(f"🤖 Modelo utilizado: {self.config['llm_model']}")
        print("=" * 60)

    def quick_query(self, question: str) -> Dict:
        """Consulta rápida para uso programático."""
        return self.call_gemini_api(question)


def main():
    """Função principal do programa."""
    print("🚀 Sistema RAG com Google Gemini - Versão Final")
    print("=" * 55)

    try:
        # Inicializa o sistema
        rag_system = RAGChatbotFinal()

        # Valida configuração
        if not rag_system.validate_setup():
            print("\n❌ Sistema não pode continuar sem API Key válida.")
            input("Pressione Enter para sair...")
            return

        print(f"\n🎯 Escolha como usar o sistema:")
        print("1. 💬 Chat interativo completo")
        print("2. ❓ Pergunta única")
        print("3. 🧪 Teste de conexão")
        print("4. 📊 Apenas informações do sistema")

        choice = input("\nSua escolha (1-4): ").strip()

        if choice == "1":
            rag_system.interactive_chat()

        elif choice == "2":
            question = input("\n💭 Digite sua pergunta: ").strip()
            if question:
                print("\n🔄 Processando pergunta...")
                response = rag_system.call_gemini_api(question)
                rag_system.display_response(response)
            else:
                print("❌ Pergunta não pode estar vazia!")

        elif choice == "3":
            print("\n🔬 Executando teste de conexão...")
            test_response = rag_system.call_gemini_api("Teste de conexão: você está funcionando?")
            rag_system.display_response(test_response)

        elif choice == "4":
            rag_system._show_statistics()

        else:
            print("❌ Opção inválida! Iniciando chat interativo...")
            rag_system.interactive_chat()

    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido. Até logo!")
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        print(f"❌ Erro crítico: {e}")

    print("\n🎉 Obrigado por usar o Sistema RAG!")
    input("Pressione Enter para sair...")


if __name__ == "__main__":
    main()