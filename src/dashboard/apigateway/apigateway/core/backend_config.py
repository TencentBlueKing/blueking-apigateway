from copy import deepcopy
from typing import Any, Literal, Self
from urllib.parse import urlsplit

from django.utils.translation import gettext as _
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from apigateway.common.error_codes import error_codes
from apigateway.common.security import is_forbidden_host
from apigateway.core.constants import (
    AI_BACKEND_BUILTIN_PROVIDERS,
    STAGE_VAR_PATTERN,
    AIBackendFallbackStrategyEnum,
    BackendKindEnum,
)

_FORBIDDEN_AI_BACKEND_HEADERS = frozenset({"host", "content-length", "transfer-encoding", "connection"})
AI_PRIMARY_PRIORITY = 10
AI_BACKUP_PRIORITY = 0
AI_INSTANCE_WEIGHT = 1
AI_CHASH_HASH_ON = "vars_combinations"
AI_CHASH_KEY = "$bk_app_code"


def mask_header_value(value: str) -> str:
    return "****" if len(value) < 4 else f"{value[:2]}****{value[-2:]}"


def _validate_object_keys(data: dict[str, Any], *, allowed: set[str], required: set[str], path: str) -> None:
    if missing := required - data.keys():
        raise ValueError(f"{path}: missing required field: {min(missing)}")
    if unknown := data.keys() - allowed:
        raise ValueError(f"{path}: unknown field: {min(unknown)}")


def _contains_stage_var(value: Any) -> bool:
    if isinstance(value, str):
        return STAGE_VAR_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(_contains_stage_var(key) or _contains_stage_var(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_stage_var(item) for item in value)
    return False


type AIBackendProvider = Literal["openai", "deepseek", "openai-compatible"]
type AIBackendHashOn = Literal["vars", "header", "cookie", "consumer", "vars_combinations"]
type AIBackendFallbackItem = Literal["rate_limiting", "http_429", "http_5xx"]
type AIBackendFallbackStrategy = (
    Literal["instance_health_and_rate_limiting", "http_429", "http_5xx"] | list[AIBackendFallbackItem]
)


def _validate_ai_endpoint(endpoint: str, path: str) -> str:
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError:
        raise ValueError(f"{path}: port is invalid") from None
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"{path}: scheme must be http or https")
    if not parsed.hostname:
        raise ValueError(f"{path}: hostname is required")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{path}: userinfo is not allowed")
    if is_forbidden_host(parsed.hostname):
        raise ValueError(f"{path}: host is forbidden")
    if port is not None and is_forbidden_host(f"{parsed.hostname}:{port}"):
        raise ValueError(f"{path}: port is forbidden")
    return endpoint


class StandardBackendConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["node"]
    timeout: int = Field(gt=0)
    loadbalance: Literal["roundrobin", "weighted-roundrobin", "chash", "ewma", "least_conn"]
    hash_on: Literal["vars", "header", "cookie", "vars_combinations"] | None = None
    key: str | None = None
    hosts: list[dict[str, Any]] = Field(min_length=1)
    checks: dict[str, Any] | None = None

    @field_validator("hash_on", "key", mode="before")
    @classmethod
    def reject_null_optional_fields(cls, value):
        if value is None:
            raise ValueError("field must not be null")
        return value

    @field_validator("hosts")
    @classmethod
    def validate_hosts(cls, hosts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for index, host in enumerate(hosts):
            path = f"$.hosts[{index}]"
            _validate_object_keys(
                host,
                allowed={"scheme", "host", "weight"},
                required={"scheme", "host"},
                path=path,
            )
            if host["scheme"] not in {"http", "https", "grpc", "grpcs"}:
                raise ValueError(f"{path}.scheme: unsupported scheme")
            if not isinstance(host["host"], str):
                raise ValueError(f"{path}.host: must be a string")  # noqa: TRY004
            if "weight" in host and (type(host["weight"]) is not int or host["weight"] < 1):
                raise ValueError(f"{path}.weight: must be a positive integer")
        return hosts

    def to_config(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class AIBackendAuth(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    header: dict[str, str] = Field(default_factory=dict)

    @field_validator("header")
    @classmethod
    def validate_headers(cls, headers: dict[str, str]) -> dict[str, str]:
        normalized: set[str] = set()
        for key in headers:
            normalized_key = key.casefold()
            if normalized_key in _FORBIDDEN_AI_BACKEND_HEADERS:
                raise ValueError(f"header is forbidden: {key}")
            if normalized_key in normalized:
                raise ValueError(f"duplicate header: {key}")
            normalized.add(normalized_key)
        return headers


class AIBackendOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    endpoint: str

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, endpoint: str) -> str:
        return _validate_ai_endpoint(endpoint, "override.endpoint")


class AIBackendInstance(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1, max_length=100)
    provider: AIBackendProvider
    priority: int = AI_PRIMARY_PRIORITY
    weight: int = Field(default=0, ge=0)
    auth: AIBackendAuth | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    override: AIBackendOverride | None = None
    model_endpoint: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_stage_vars(cls, data: Any) -> Any:
        if _contains_stage_var(data):
            raise ValueError("AI backend config must not contain environment variables")
        return data

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: dict[str, Any]) -> dict[str, Any]:
        if "model" in options and (not isinstance(options["model"], str) or not options["model"]):
            raise ValueError("model must be a non-empty string")
        return options

    @field_validator("model_endpoint")
    @classmethod
    def validate_model_endpoint(cls, endpoint: str | None) -> str | None:
        return _validate_ai_endpoint(endpoint, "model_endpoint") if endpoint is not None else None

    @model_validator(mode="after")
    def validate_provider_contract(self) -> Self:
        headers = self.auth.header if self.auth else {}
        authorization = next((value for key, value in headers.items() if key.casefold() == "authorization"), "")
        if self.provider in AI_BACKEND_BUILTIN_PROVIDERS:
            if not authorization:
                raise ValueError("auth.header: Authorization header is required")
            if self.override is not None:
                raise ValueError("override: override is not allowed")
            if self.model_endpoint is not None:
                raise ValueError("model_endpoint: model_endpoint is not allowed")
        elif self.override is None:
            raise ValueError("override: override.endpoint is required")
        return self


class AIBackendBalancer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    algorithm: Literal["chash", "roundrobin"] = "roundrobin"
    hash_on: AIBackendHashOn | None = None
    key: str | None = None

    @model_validator(mode="after")
    def validate_chash(self) -> Self:
        if self.algorithm == "chash" and self.hash_on is None:
            raise ValueError("hash_on is required for chash")
        if self.algorithm == "chash" and self.hash_on != "consumer" and not self.key:
            raise ValueError("key is required for chash unless hash_on is consumer")
        return self


class AIBackendConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    timeout: int = Field(default=300, ge=1, le=300)
    instances: list[AIBackendInstance] = Field(min_length=1)
    balancer: AIBackendBalancer | None = None
    fallback_strategy: AIBackendFallbackStrategy | None = None

    @classmethod
    def normalize_for_write(cls, data: Any) -> dict[str, Any]:
        # Keep write defaults out of model_validate: reading or republishing old
        # configurations must not enable retries that were never configured.
        if isinstance(data, dict):
            data = deepcopy(data)
            if (
                isinstance(data.get("instances"), list)
                and len(data["instances"]) == 1
                and data.get("fallback_strategy") == []
            ):
                data.pop("fallback_strategy")
            balancer = data.get("balancer")
            if isinstance(balancer, dict) and balancer.get("algorithm") == "chash":
                balancer.setdefault("hash_on", AI_CHASH_HASH_ON)
                balancer.setdefault("key", AI_CHASH_KEY)

        model = cls.model_validate(data)
        config = model.to_config()
        names = [item.name for item in model.instances]
        if len(set(names)) != len(names):
            raise error_codes.INVALID_ARGUMENT.format(_("模型实例名称不能重复。"))
        priorities = [item.priority for item in model.instances]
        if any(value not in (AI_PRIMARY_PRIORITY, AI_BACKUP_PRIORITY) for value in priorities):
            raise error_codes.INVALID_ARGUMENT.format(_("模型实例优先级只能为 10（主实例）或 0（备用实例）。"))
        if AI_PRIMARY_PRIORITY not in priorities or priorities.count(AI_BACKUP_PRIORITY) > 1:
            raise error_codes.INVALID_ARGUMENT.format(_("至少需要一个主实例，且最多只能配置一个备用实例。"))
        if len(model.instances) == 1:
            return config

        if "fallback_strategy" in model.model_fields_set and model.fallback_strategy is None:
            raise error_codes.INVALID_ARGUMENT.format(_("故障重试策略必须为数组。"))
        for item, output in zip(model.instances, config["instances"], strict=True):
            if "weight" in item.model_fields_set and item.weight != AI_INSTANCE_WEIGHT:
                raise error_codes.INVALID_ARGUMENT.format(_("多实例配置的权重必须为 1。"))
            output.update(priority=item.priority, weight=AI_INSTANCE_WEIGHT)
        config["instances"].sort(key=lambda item: (-item["priority"], item["name"]))

        _normalize_ai_pool_routing(config, has_backup=AI_BACKUP_PRIORITY in priorities)
        return config

    @model_validator(mode="before")
    @classmethod
    def reject_stage_vars(cls, data: Any) -> Any:
        global_config = (
            {key: value for key, value in data.items() if key != "instances"} if isinstance(data, dict) else data
        )
        if _contains_stage_var(global_config):
            raise ValueError("AI backend config must not contain environment variables")
        return data

    @model_validator(mode="after")
    def reject_multi_fields_for_one_instance(self) -> Self:
        if len(self.instances) == 1 and (self.balancer is not None or self.fallback_strategy is not None):
            raise ValueError("balancer and fallback_strategy require multiple instances")
        return self

    def to_config(self) -> dict[str, Any]:
        data = self.model_dump(exclude_unset=True, exclude_none=True)
        data["timeout"] = self.timeout
        for output, instance in zip(data["instances"], self.instances, strict=True):
            output["weight"] = instance.weight
        return data


def _normalize_ai_pool_routing(config: dict[str, Any], *, has_backup: bool) -> None:
    balancer = config.get("balancer", {})
    balancer.setdefault("algorithm", "roundrobin")
    config["balancer"] = balancer

    strategy = config.setdefault("fallback_strategy", AIBackendFallbackStrategyEnum.get_values())
    if message := get_ai_pool_routing_error(config):
        raise error_codes.INVALID_ARGUMENT.format(message)
    strategy = [item for item in AIBackendFallbackStrategyEnum.get_values() if item in strategy]
    if has_backup and not strategy:
        raise error_codes.INVALID_ARGUMENT.format(_("配置备用实例时，至少需要启用一项故障重试条件。"))
    config["fallback_strategy"] = strategy


def get_ai_pool_routing_error(config: dict[str, Any]) -> str | None:
    """Return a shared write/Web routing error without changing configuration or raising an API error."""
    balancer = config.get("balancer")
    if (
        balancer
        and balancer.get("algorithm", "roundrobin") != "chash"
        and ("hash_on" in balancer or "key" in balancer)
    ):
        return _("轮询算法不支持配置 hash_on 和 key。")
    if (
        balancer
        and balancer.get("algorithm") == "chash"
        and (balancer.get("hash_on") != AI_CHASH_HASH_ON or balancer.get("key") != AI_CHASH_KEY)
    ):
        return _("一致性哈希仅支持 vars_combinations 和 $bk_app_code。")
    strategy = config.get("fallback_strategy", [])
    if not isinstance(strategy, list) or any(
        item not in AIBackendFallbackStrategyEnum.get_values() for item in strategy
    ):
        return _("故障重试策略仅支持 http_429 和 http_5xx 数组。")

    return None


type BackendConfigType = type[StandardBackendConfig] | type[AIBackendConfig]


BACKEND_CONFIG_TYPES: dict[str, BackendConfigType] = {
    BackendKindEnum.STANDARD.value: StandardBackendConfig,
    BackendKindEnum.AI.value: AIBackendConfig,
}
