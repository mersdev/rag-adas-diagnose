"""
Embedding service for ADAS Diagnostics Co-pilot.

This module provides vector embedding generation for semantic search
across automotive documentation using various embedding providers.
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

import httpx
import openai
from openai import AsyncOpenAI

from agent.config import get_settings, EmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Base exception for embedding service errors."""
    pass


class RateLimitError(EmbeddingServiceError):
    """Raised when rate limit is exceeded."""
    pass


class BaseEmbeddingService(ABC):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this service."""
        pass


class OpenAIEmbeddingService(BaseEmbeddingService):
    """OpenAI embedding service implementation."""
    
    def __init__(self, api_key: str, base_url: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding service.
        
        Args:
            api_key: OpenAI API key
            base_url: API base URL
            model: Embedding model to use
        """
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.max_batch_size = 100  # OpenAI limit
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Model dimensions
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
    
    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension for the current model."""
        return self._dimensions.get(self.model, 1536)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        
        # Process in batches to respect API limits
        all_embeddings = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_embeddings = await self._generate_batch_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                
                embeddings = []
                for embedding_data in response.data:
                    embeddings.append(embedding_data.embedding)
                
                return embeddings
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                else:
                    raise RateLimitError(f"Rate limit exceeded after {self.max_retries} attempts") from e
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Embedding generation failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise EmbeddingServiceError(f"Failed to generate embeddings after {self.max_retries} attempts") from e


class OllamaEmbeddingService(BaseEmbeddingService):
    """Ollama embedding service implementation."""
    
    def __init__(self, base_url: str, model: str = "nomic-embed-text"):
        """
        Initialize Ollama embedding service.
        
        Args:
            base_url: Ollama API base URL
            model: Embedding model to use
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.max_batch_size = 50  # Conservative batch size
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Common Ollama embedding model dimensions
        self._dimensions = {
            "nomic-embed-text": 768,
            "all-minilm": 384,
            "mxbai-embed-large": 1024
        }
    
    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension for the current model."""
        return self._dimensions.get(self.model, 768)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        
        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_embeddings = await self._generate_batch_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        embeddings = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                for attempt in range(self.max_retries):
                    try:
                        response = await client.post(
                            f"{self.base_url}/api/embeddings",
                            json={
                                "model": self.model,
                                "prompt": text
                            }
                        )
                        response.raise_for_status()
                        
                        data = response.json()
                        if "embedding" in data:
                            embeddings.append(data["embedding"])
                            break
                        else:
                            raise EmbeddingServiceError("No embedding in response")
                            
                    except Exception as e:
                        if attempt < self.max_retries - 1:
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(f"Ollama embedding failed, retrying in {wait_time}s: {e}")
                            await asyncio.sleep(wait_time)
                        else:
                            raise EmbeddingServiceError(f"Failed to generate embedding for text after {self.max_retries} attempts") from e
        
        return embeddings


class EmbeddingServiceFactory:
    """Factory for creating embedding services."""
    
    @staticmethod
    def create_service() -> BaseEmbeddingService:
        """Create embedding service based on configuration."""
        settings = get_settings()
        
        provider = settings.llm.embedding_provider
        base_url = settings.llm.embedding_base_url
        api_key = settings.llm.embedding_api_key
        model = settings.llm.embedding_model
        
        if provider == EmbeddingProvider.OPENAI:
            return OpenAIEmbeddingService(
                api_key=api_key,
                base_url=base_url,
                model=model
            )
        elif provider == EmbeddingProvider.OLLAMA:
            return OllamaEmbeddingService(
                base_url=base_url,
                model=model
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")


class EmbeddingManager:
    """Manager for embedding operations with caching and batch processing."""
    
    def __init__(self, service: Optional[BaseEmbeddingService] = None):
        """
        Initialize embedding manager.
        
        Args:
            service: Embedding service to use. If None, creates from config.
        """
        self.service = service or EmbeddingServiceFactory.create_service()
        self.cache: Dict[str, List[float]] = {}
        self.batch_size = 50
    
    async def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Get embedding for text with optional caching.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            Embedding vector
        """
        if use_cache and text in self.cache:
            return self.cache[text]
        
        embedding = await self.service.generate_embedding(text)
        
        if use_cache:
            self.cache[text] = embedding
        
        return embedding
    
    async def get_embeddings(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Get embeddings for multiple texts with optional caching.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache for existing embeddings
        for i, text in enumerate(texts):
            if use_cache and text in self.cache:
                embeddings.append(self.cache[text])
            else:
                embeddings.append(None)  # Placeholder
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        # Generate embeddings for uncached texts
        if texts_to_embed:
            new_embeddings = await self.service.generate_embeddings(texts_to_embed)
            
            # Fill in the embeddings and update cache
            for idx, embedding in zip(indices_to_embed, new_embeddings):
                embeddings[idx] = embedding
                if use_cache:
                    self.cache[texts[idx]] = embedding
        
        return embeddings
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self.cache.clear()
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension from the service."""
        return self.service.embedding_dimension


# Global embedding manager instance
_embedding_manager: Optional[EmbeddingManager] = None


def get_embedding_manager() -> EmbeddingManager:
    """Get the global embedding manager instance."""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager


def reset_embedding_manager():
    """Reset the global embedding manager."""
    global _embedding_manager
    _embedding_manager = None
