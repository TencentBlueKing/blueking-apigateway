from copy import deepcopy
from urllib.parse import urlsplit

from django.utils.translation import gettext as _
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from apigateway.apis.backend_config import validate_ai_backend_config
from apigateway.core.ai_backend import get_ai_backend_provider_config
from apigateway.core.backend_config import AIBackendConfig, mask_header_value

_NOT_RESTORED = object()


class AIBackendWebConfigNotRepresentable(ValueError):
    pass


class AIBackendWebConfigAdapter:
    @classmethod
    def to_internal(cls, data: dict, *, existing_config: dict | None = None) -> dict:
        try:
            restored_auth = cls._restore_masked_auth(data, existing_config)
        except PydanticValidationError, AIBackendWebConfigNotRepresentable:
            raise serializers.ValidationError(_("已有模型服务配置无法通过 Web 接口编辑。")) from None
        options = dict(data.get("model_options", {}))
        if data.get("model") is not None:
            options["model"] = data["model"]
        instance = {
            "name": "primary",
            "provider": data["provider"],
            "weight": 0,
            "options": options,
        }
        provider_config = get_ai_backend_provider_config(data["provider"])
        if restored_auth is not _NOT_RESTORED:
            instance["auth"] = restored_auth
        elif provider_config is not None:
            instance["auth"] = {"header": {"Authorization": f"Bearer {data['api_key']}"}}
        elif auth_header := data.get("auth_header"):
            instance["auth"] = {"header": {auth_header["name"]: auth_header["value"]}}
        if provider_config is None:
            instance["override"] = {"endpoint": data["endpoint"]}
            if data.get("model_endpoint") is not None:
                instance["model_endpoint"] = data["model_endpoint"]
        return validate_ai_backend_config({"timeout": data.get("timeout", 300), "instances": [instance]})

    @classmethod
    def to_web(cls, config: dict) -> dict:
        normalized = AIBackendConfig.model_validate(config).to_config()
        if len(normalized["instances"]) != 1:
            raise AIBackendWebConfigNotRepresentable("Web protocol requires exactly one instance")
        instance = normalized["instances"][0]
        headers = instance.get("auth", {}).get("header", {})
        if len(headers) > 1:
            raise AIBackendWebConfigNotRepresentable("Web protocol cannot represent multiple auth headers")
        options = dict(instance.get("options", {}))
        model = options.pop("model", None)
        provider_config = get_ai_backend_provider_config(instance["provider"])
        result = {
            "provider": instance["provider"],
            "endpoint": provider_config.endpoint if provider_config else instance["override"]["endpoint"],
            "model_endpoint": provider_config.model_endpoint if provider_config else instance.get("model_endpoint"),
            "api_key": None,
            "auth_header": None,
            "model": model,
            "model_options": options,
            "timeout": normalized["timeout"],
        }
        if provider_config is not None:
            authorization = next(value for key, value in headers.items() if key.casefold() == "authorization")
            api_key = authorization[7:] if authorization.startswith("Bearer ") else authorization
            result["api_key"] = mask_header_value(api_key)
        elif headers:
            name, value = next(iter(headers.items()))
            result["auth_header"] = {"name": name, "value": mask_header_value(value)}
        return result

    @classmethod
    def _restore_masked_auth(cls, data: dict, existing_config: dict | None):
        if existing_config is None:
            return _NOT_RESTORED
        existing_web = cls.to_web(existing_config)
        incoming = cls._credential(data)
        existing = cls._credential(existing_web)
        if incoming is None or existing is None or incoming[2] != existing[2]:
            return _NOT_RESTORED
        if cls._destination_identity(data) != cls._destination_identity(existing_web):
            raise serializers.ValidationError({incoming[0]: _("模型服务地址已变更，请重新输入认证凭据。")})
        if incoming[1].casefold() != existing[1].casefold():
            raise serializers.ValidationError({incoming[0]: _("认证 Header 已变更，请重新输入认证凭据。")})
        return deepcopy(existing_config["instances"][0].get("auth", {}))

    @staticmethod
    def _credential(data: dict) -> tuple[str, str, str] | None:
        if data.get("api_key") is not None:
            return "api_key", "Authorization", data["api_key"]
        if auth_header := data.get("auth_header"):
            return "auth_header", auth_header["name"], auth_header["value"]
        return None

    @staticmethod
    def _destination_identity(data: dict) -> tuple:
        provider = data["provider"]
        provider_config = get_ai_backend_provider_config(provider)
        endpoint = provider_config.endpoint if provider_config else data.get("endpoint")
        model_endpoint = provider_config.model_endpoint if provider_config else data.get("model_endpoint")
        return provider, AIBackendWebConfigAdapter._origin(endpoint), AIBackendWebConfigAdapter._origin(model_endpoint)

    @staticmethod
    def _origin(url: str | None) -> tuple | None:
        if url is None:
            return None
        parsed = urlsplit(url)
        return parsed.scheme, parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
