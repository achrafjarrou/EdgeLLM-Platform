# -*- coding: utf-8 -*-
"""
EdgeLLM Inference Engine - Multi-Model Routing
Production-grade inference with cost-aware routing
"""
import time
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Available inference providers"""
    LOCAL_PHI4 = "local_phi4mini"
    LOCAL_MISTRAL = "local_mistral7b"
    GROQ_LLAMA70B = "groq_llama70b"
    GROQ_LLAMA8B = "groq_llama8b"


@dataclass
class InferenceRequest:
    """Standardized inference request"""
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.1
    user_id: str = "anonymous"
    tier: str = "standard"  # standard | premium | enterprise
    


@dataclass
class InferenceResult:
    """Inference result with full telemetry"""
    content: str
    model_used: ModelProvider
    latency_ms: float
    tokens_in: int
    tokens_out: int
    cost_eur: float
    data_location: str  # "on-premise" | "cloud-eu" | "cloud-us"
    request_id: str


class CostAwareRouter:
    """
    Intelligent routing based on:
    - Query complexity
    - System load
    - User tier/budget
    - Quality requirements
    """
    
    def __init__(self):
        self.local_load = 0.0  # 0-1 scale
        
    def analyze_complexity(self, prompt: str) -> float:
        """
        Estimate query complexity (0-1 scale)
        
        Simple heuristics:
        - Token count
        - Technical terms density
        - Question type (yes/no vs analysis)
        """
        tokens = len(prompt.split())
        
        # Simple complexity score
        if tokens < 50:
            return 0.2
        elif tokens < 200:
            return 0.5
        else:
            return 0.8
    
    def route(self, request: InferenceRequest) -> ModelProvider:
        """
        Decision tree for model selection
        
        Optimization goals:
        1. Minimize cost (prefer local)
        2. Meet latency SLA (by tier)
        3. Ensure quality (complexity-aware)
        """
        complexity = self.analyze_complexity(request.prompt)
        
        # Enterprise tier: always best model
        if request.tier == "enterprise":
            if complexity > 0.6:
                return ModelProvider.GROQ_LLAMA70B
            else:
                return ModelProvider.LOCAL_MISTRAL
        
        # Premium tier: balanced
        if request.tier == "premium":
            if complexity > 0.7:
                return ModelProvider.GROQ_LLAMA70B
            elif complexity > 0.4:
                return ModelProvider.LOCAL_MISTRAL
            else:
                return ModelProvider.LOCAL_PHI4
        
        # Standard tier: cost-optimized
        if self.local_load < 0.8:
            if complexity > 0.5:
                return ModelProvider.LOCAL_MISTRAL
            else:
                return ModelProvider.LOCAL_PHI4
        else:
            # Fallback to cloud if local overloaded
            return ModelProvider.GROQ_LLAMA8B


class InferenceEngine:
    """
    Main inference engine with multiple providers
    """
    
    def __init__(self):
        self.router = CostAwareRouter()
        self._init_providers()
        
    def _init_providers(self):
        """Initialize all available providers"""
        try:
            from openai import OpenAI
            import os
            
            # Local Ollama
            self.local_client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )
            
            # Groq (cloud fallback)
            groq_key = os.getenv('GROQ_API_KEY', '')
            if groq_key:
                self.groq_client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key
                )
            else:
                self.groq_client = None
                log.warning("Groq API key not found - cloud fallback disabled")
                
        except Exception as e:
            log.error(f"Provider initialization failed: {e}")
    
    def infer(self, request: InferenceRequest) -> InferenceResult:
        """
        Execute inference with routing & telemetry
        
        Returns:
            InferenceResult with complete metrics
        """
        # Route request
        model_provider = self.router.route(request)
        
        # Execute
        start = time.perf_counter()
        
        try:
            if model_provider in [ModelProvider.LOCAL_PHI4, ModelProvider.LOCAL_MISTRAL]:
                result = self._infer_local(request, model_provider)
            else:
                result = self._infer_cloud(request, model_provider)
                
            result.latency_ms = (time.perf_counter() - start) * 1000
            
            log.info(f"Request {result.request_id}: {model_provider.value} | "
                    f"{result.latency_ms:.0f}ms | �{result.cost_eur:.4f}")
            
            return result
            
        except Exception as e:
            log.error(f"Inference failed: {e}")
            # Fallback logic
            return self._fallback_infer(request)
    
    def _infer_local(
        self, 
        request: InferenceRequest, 
        provider: ModelProvider
    ) -> InferenceResult:
        """Local inference via Ollama"""
        
        model_map = {
            ModelProvider.LOCAL_PHI4: "phi4-mini",
            ModelProvider.LOCAL_MISTRAL: "mistral:7b-instruct-q4_K_M"
        }
        
        model = model_map[provider]
        
        response = self.local_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return InferenceResult(
            content=response.choices[0].message.content,
            model_used=provider,
            latency_ms=0.0,  # Set by caller
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            cost_eur=0.0,  # Local is free
            data_location="on-premise",
            request_id=f"req_{int(time.time() * 1000)}"
        )
    
    def _infer_cloud(
        self, 
        request: InferenceRequest, 
        provider: ModelProvider
    ) -> InferenceResult:
        """Cloud inference via Groq"""
        
        if not self.groq_client:
            raise RuntimeError("Groq client not initialized")
        
        model_map = {
            ModelProvider.GROQ_LLAMA70B: "llama-3.3-70b-versatile",
            ModelProvider.GROQ_LLAMA8B: "llama-3.1-8b-instant"
        }
        
        model = model_map[provider]
        
        response = self.groq_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return InferenceResult(
            content=response.choices[0].message.content,
            model_used=provider,
            latency_ms=0.0,
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            cost_eur=0.0,  # Groq free tier
            data_location="cloud-us",
            request_id=f"req_{int(time.time() * 1000)}"
        )
    
    def _fallback_infer(self, request: InferenceRequest) -> InferenceResult:
        """Fallback when primary methods fail"""
        log.warning("Using fallback inference")
        # Implement graceful degradation
        return InferenceResult(
            content="[Service temporarily unavailable - please retry]",
            model_used=ModelProvider.LOCAL_PHI4,
            latency_ms=0.0,
            tokens_in=0,
            tokens_out=0,
            cost_eur=0.0,
            data_location="on-premise",
            request_id=f"fallback_{int(time.time())}"
        )


# ---------------------------------------------------------------
# USAGE EXAMPLE
# ---------------------------------------------------------------
if __name__ == "__main__":
    engine = InferenceEngine()
    
    # Test different tiers
    requests = [
        InferenceRequest(
            prompt="What is HIPAA compliance?",
            tier="standard"
        ),
        InferenceRequest(
            prompt="Analyze this 500-page contract for regulatory risks...",
            tier="enterprise"
        )
    ]
    
    for req in requests:
        result = engine.infer(req)
        print(f"\nTier: {req.tier}")
        print(f"Model: {result.model_used.value}")
        print(f"Latency: {result.latency_ms:.0f}ms")
        print(f"Cost: �{result.cost_eur:.4f}")
        print(f"Location: {result.data_location}")
        print(f"Response: {result.content[:100]}...")
