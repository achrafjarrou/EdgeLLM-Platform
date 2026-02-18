# -*- coding: utf-8 -*-
"""
EdgeLLM Platform - Integration Tests
"""
import pytest
import sys
sys.path.append('../..')

from edgellm.core.inference_engine import InferenceEngine, InferenceRequest, ModelProvider

def test_inference_engine_initialization():
    """Test engine can be initialized"""
    engine = InferenceEngine()
    assert engine is not None
    assert engine.router is not None

def test_local_inference():
    """Test local inference works"""
    engine = InferenceEngine()
    
    request = InferenceRequest(
        prompt="What is 2+2? Answer with just the number.",
        max_tokens=10,
        tier="standard"
    )
    
    result = engine.infer(request)
    
    assert result is not None
    assert result.content
    assert result.latency_ms > 0
    assert result.cost_eur == 0.0  # Local should be free
    assert result.data_location == "on-premise"

def test_tier_routing():
    """Test that different tiers route to appropriate models"""
    engine = InferenceEngine()
    
    # Standard tier should prefer local
    std_request = InferenceRequest(
        prompt="Simple question",
        tier="standard"
    )
    std_model = engine.router.route(std_request)
    assert std_model in [ModelProvider.LOCAL_PHI4, ModelProvider.LOCAL_MISTRAL]
    
    # Enterprise tier may use cloud for complex queries
    ent_request = InferenceRequest(
        prompt="Very complex analysis requiring deep reasoning...",
        tier="enterprise"
    )
    ent_model = engine.router.route(ent_request)
    # Just verify it completes without error
    assert ent_model is not None

@pytest.mark.asyncio
async def test_api_health_endpoint():
    """Test API health check"""
    from httpx import AsyncClient
    
    # This would require the API to be running
    # In real tests, you'd use a test client
    pass  # Placeholder

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
