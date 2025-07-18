# 🤖 RAG Chatbot - Sistema Otimizado

Sistema RAG (Retrieval-Augmented Generation) avançado para consultas sobre documentação, desenvolvido com LangChain e Google Gemini.

## ✨ Características

- 🚀 **Performance Otimizada**: Sistema de cache inteligente
- 🔒 **Segurança**: Rate limiting e validação robusta
- 📊 **Métricas**: Monitoramento completo de performance
- 🎯 **Feedback**: Sistema de avaliação integrado
- 🔧 **Configurável**: Configuração externa flexível

## 🛠️ Tecnologias

- **Python 3.8+**
- **LangChain** - Framework para aplicações LLM
- **Google Gemini** - Modelo de linguagem
- **ChromaDB** - Banco de dados vetorial
- **dotenv** - Gerenciamento de variáveis de ambiente

## 📦 Instalação

```bash
git clone https://github.com/diegolopesdev9/rag-chatbot-langchain.git
cd rag-chatbot-langchain
pip install -r requirements.txt
cp .env.example .env
```
## ⚙️ Configuração

### 1. Obter API Key do Google (Grátis)

1. **Acesse:** https://aistudio.google.com/
2. **Faça login** com sua conta Google
3. **Clique em "Get API Key"**
4. **Crie uma nova API Key**
5. **Copie a chave** (algo como: `AIzaSyB1234...`)

### 2. Configurar no Projeto

**Opção A: Arquivo .env (Recomendado)**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione sua chave
GOOGLE_API_KEY=sua_chave_aqui

## 🚀 Uso

### Executar o Sistema

1. **Abra o terminal** no PyCharm ou cmd
2. **Navegue para a pasta do projeto:**
   ```bash
   cd caminho/para/rag-chatbot-langchain