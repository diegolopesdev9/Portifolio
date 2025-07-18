import os
import json
import logging
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from time import time
from collections import defaultdict, deque
from functools import lru_cache
from hashlib import md5
from html import escape
from contextlib import contextmanager
import threading

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# Configuração de logging avançada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Exceções customizadas
class RAGException(Exception):
    """Exceção base para erros RAG."""
    pass


class EmbeddingError(RAGException):
    """Erro de embedding."""
    pass


class RetrievalError(RAGException):
    """Erro de recuperação."""
    pass


class ValidationError(RAGException):
    """Erro de validação."""
    pass


class RateLimitError(RAGException):
    """Erro de rate limit."""
    pass


# Configuração robusta
@dataclass
class RAGConfig:
    """Configuração do sistema RAG."""
    embedding_model: str = "models/embedding-001"
    llm_model: str = "gemini-1.5-pro"
    temperature: float = 0.7
    persist_directory: str = "./chroma_db"
    max_results: int = 3
    max_retries: int = 3
    timeout: int = 30
    cache_size: int = 100
    rate_limit_requests: int = 10
    rate_limit_window: int = 60
    min_query_length: int = 3
    max_query_length: int = 1000
    feedback_file: str = "feedback.jsonl"
    metrics_file: str = "metrics.jsonl"

    @classmethod
    def from_file(cls, config_path: str) -> 'RAGConfig':
        """Carrega configuração de arquivo JSON."""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except FileNotFoundError:
            logger.warning(f"Arquivo de configuração {config_path} não encontrado. Usando configuração padrão.")
            return cls()
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            raise ValidationError(f"Erro no arquivo de configuração: {e}")

    def validate(self) -> None:
        """Valida configurações."""
        if not (0 <= self.temperature <= 1):
            raise ValidationError("Temperature deve estar entre 0 e 1")

        if self.max_results < 1:
            raise ValidationError("max_results deve ser maior que 0")

        if self.cache_size < 1:
            raise ValidationError("cache_size deve ser maior que 0")

        if self.min_query_length < 1:
            raise ValidationError("min_query_length deve ser maior que 0")

        if self.max_query_length < self.min_query_length:
            raise ValidationError("max_query_length deve ser maior que min_query_length")


def main():
    """Função principal do programa."""
    try:
        # Carrega configuração
        config = RAGConfig.from_file("config/config.json")

        print("🚀 Sistema RAG Otimizado inicializado com sucesso!")
        print("📊 Configuração carregada")

    except Exception as e:
        logger.error(f"Erro na execução principal: {e}")
        print(f"❌ Erro crítico: {e}")


if __name__ == "__main__":
    main()