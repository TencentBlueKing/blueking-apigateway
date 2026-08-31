from apigateway.core.ai_backend import AI_BACKEND_PROVIDER_REGISTRY, get_ai_backend_provider_config


def test_builtin_ai_backend_provider_registry_is_complete():
    assert set(AI_BACKEND_PROVIDER_REGISTRY) == {"openai", "deepseek"}
    assert get_ai_backend_provider_config("openai").endpoint == "https://api.openai.com/v1/chat/completions"
    assert get_ai_backend_provider_config("openai").model_endpoint == "https://api.openai.com/v1/models"
    assert get_ai_backend_provider_config("deepseek").endpoint == "https://api.deepseek.com/chat/completions"
    assert get_ai_backend_provider_config("deepseek").model_endpoint == "https://api.deepseek.com/models"
    assert get_ai_backend_provider_config("openai-compatible") is None
