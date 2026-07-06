"""
Groq API Client Wrapper using LangChain
Provides LangChain ChatOpenAI interface pointing to Groq API
"""

import os
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import httpx


class GroqClient:
    """Wrapper for Groq API using LangChain's ChatOpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
    
    def get_llm(self, temperature: float = 0.3, max_tokens: int = 2000) -> ChatOpenAI:
        """
        Get a LangChain ChatOpenAI instance configured for Groq.
        
        Args:
            temperature: 0.0-1.0, lower = more deterministic
            max_tokens: Maximum response length
            
        Returns:
            ChatOpenAI: LangChain chat model
        """
        return ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=30
        )
    
    async def chat_completion(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        max_retries: int = 3
    ) -> str:
        """
        Simple chat completion using LangChain with retry logic for rate limits.
        
        Args:
            system_prompt: System instructions for the agent
            user_message: User's message
            temperature: 0.0-1.0, lower = more deterministic
            max_tokens: Maximum response length
            max_retries: Maximum number of retries for 429 errors
            
        Returns:
            str: AI response content
        """
        llm = self.get_llm(temperature=temperature, max_tokens=max_tokens)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        # Retry logic for rate limiting
        for attempt in range(max_retries):
            try:
                response = await llm.ainvoke(messages)
                return response.content
            except Exception as e:
                # Check if it's a rate limit error
                error_str = str(e)
                is_rate_limit = "429" in error_str or "Too Many Requests" in error_str
                
                if is_rate_limit and attempt < max_retries - 1:
                    # Exponential backoff: 2, 4, 8 seconds
                    wait_time = 2 ** (attempt + 1)
                    print(f"[GROQ CLIENT] Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    # Not a rate limit error, or out of retries
                    raise
    
    async def structured_output(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> str:
        """
        Chat completion for structured JSON output.
        Uses lower temperature for more consistent JSON formatting.
        
        Returns:
            str: Raw JSON string (caller must parse)
        """
        full_system = f"""{system_prompt}

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanation, no text outside the JSON object.
"""
        
        return await self.chat_completion(
            system_prompt=full_system,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens
        )


# Global instance
_groq_client = None


def get_groq_client() -> GroqClient:
    """Get singleton Groq client instance"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
