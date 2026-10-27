from copy import deepcopy
from urllib.parse import urlsplit

from django.utils.translation import gettext as _
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from apigateway.apis.backend_config import validate_ai_backend_config
from apigateway.common.error_codes import APIError
from apigateway.core.ai_backend import get_ai_backend_provider_config
from apigateway.core.backend_config import (
    AI_BACKUP_PRIORITY,
    AI_INSTANCE_WEIGHT,
    AI_PRIMARY_PRIORITY,
    AIBackendConfig,
    mask_header_value,
    validate_ai_pool_routing,
)

_NOT_RESTORED = object()


class AIBackendWebConfigNotRepresentable(ValueError):
    pass


class AIBackendWebConfigAdapter:
    @classmethod
    def to_internal(cls, data: dict, *, existing_config: dict | None = None) -> dict:
        try:
            old_instances = cls._existing_instances(existing_config)
            instances = []
            for item in data["instances"]:
                instance = cls._instance_to_internal(item, old_instances.get(item["name"]))
                instance.update(
                    name=item["name"],
                    priority=item["priority"],
                    weight=AI_INSTANCE_WEIGHT,
                )
                instances.append(instance)
            config = {"timeout": data.get("timeout", 300), "instances": instances}
            for key in ("balancer", "fallback_strategy"):
                if key in data:
                    config[key] = data[key]
            return validate_ai_backend_config(config)
        except PydanticValidationError, AIBackendWebConfigNotRepresentable:
            raise serializers.ValidationError(_("已有模型服务配置无法通过 Web 接口编辑。")) from None

    @classmethod
    def to_connectivity(cls, data: dict, *, existing_config: dict | None = None) -> dict:
        """Probe an instance independently; its primary/backup role is irrelevant."""
        try:
            old_instances = cls._existing_instances(existing_config)
            instance = cls._instance_to_internal(data, old_instances.get(data["name"]))
            instance["name"] = data["name"]
            return AIBackendConfig.model_validate({"instances": [instance]}).to_config()
        except PydanticValidationError, AIBackendWebConfigNotRepresentable:
            raise serializers.ValidationError(_("已有模型服务配置无法通过 Web 接口编辑。")) from None

    @staticmethod
    def _existing_instances(config: dict | None) -> dict:
        if not config:
            return {}
        existing = AIBackendConfig.model_validate(config).to_config()["instances"]
        return {item["name"]: item for item in existing}

    @classmethod
    def _instance_to_internal(cls, data: dict, existing: dict | None) -> dict:
        restored_auth = cls._restore_masked_auth(data, existing)
        if restored_auth is _NOT_RESTORED and (credential := cls._credential(data)):
            value = credential[2]
            # Only the exact display-mask shapes are reserved in the Web protocol.
            if value == "****" or (len(value) == 8 and value == mask_header_value(value)):
                raise serializers.ValidationError({credential[0]: _("认证凭据掩码无法恢复，请重新输入认证凭据。")})
        options = dict(data.get("model_options", {}))
        if data.get("model") is not None:
            options["model"] = data["model"]
        instance = {"provider": data["provider"], "options": options}
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
        return instance

    @classmethod
    def to_web(cls, config: dict) -> dict:
        normalized = AIBackendConfig.model_validate(config).to_config()
        balancer = normalized.get("balancer")
        try:
            validate_ai_pool_routing(normalized)
        except APIError as err:
            raise AIBackendWebConfigNotRepresentable(str(err.code.message)) from err
        result: dict = {"timeout": normalized["timeout"], "instances": []}
        # Historical reads preserve priorities/weights instead of applying write defaults.
        for item in normalized["instances"]:
            priority = item.get("priority", AI_PRIMARY_PRIORITY)
            if priority not in (AI_PRIMARY_PRIORITY, AI_BACKUP_PRIORITY) or (
                len(normalized["instances"]) > 1 and item["weight"] != AI_INSTANCE_WEIGHT
            ):
                raise AIBackendWebConfigNotRepresentable("Web protocol cannot represent custom weights or priorities")
            result["instances"].append({"name": item["name"], "priority": priority, **cls._instance_to_web(item)})
        if "balancer" in normalized:
            result["balancer"] = {"algorithm": normalized["balancer"]["algorithm"]}
        if "fallback_strategy" in normalized:
            result["fallback_strategy"] = normalized["fallback_strategy"]
        return result

    @staticmethod
    def _instance_to_web(instance: dict) -> dict:
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
    def _restore_masked_auth(cls, data: dict, existing: dict | None):
        if existing is None:
            return _NOT_RESTORED
        existing_web = cls._instance_to_web(existing)
        incoming = cls._credential(data)
        previous = cls._credential(existing_web)
        if incoming is None or previous is None or incoming[2] != previous[2]:
            return _NOT_RESTORED
        if cls._destination_identity(data) != cls._destination_identity(existing_web):
            raise serializers.ValidationError({incoming[0]: _("模型服务地址已变更，请重新输入认证凭据。")})
        if incoming[1].casefold() != previous[1].casefold():
            raise serializers.ValidationError({incoming[0]: _("认证 Header 已变更，请重新输入认证凭据。")})
        return deepcopy(existing.get("auth", {}))

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
