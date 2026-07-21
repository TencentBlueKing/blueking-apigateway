from typing import Any, Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from apigateway.common.security import is_forbidden_host
from apigateway.core.constants import (
    AI_BACKEND_BUILTIN_PROVIDERS,
    STAGE_VAR_PATTERN,
    BackendKindEnum,
)

_FORBIDDEN_AI_BACKEND_HEADERS = frozenset({"host", "content-length", "transfer-encoding", "connection"})


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
    weight: int = Field(default=0, ge=0)
    auth: AIBackendAuth | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    override: AIBackendOverride | None = None
    model_endpoint: str | None = None

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

    @model_validator(mode="before")
    @classmethod
    def reject_stage_vars(cls, data: Any) -> Any:
        if _contains_stage_var(data):
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


type BackendConfigType = type[StandardBackendConfig] | type[AIBackendConfig]


BACKEND_CONFIG_TYPES: dict[str, BackendConfigType] = {
    BackendKindEnum.STANDARD.value: StandardBackendConfig,
    BackendKindEnum.AI.value: AIBackendConfig,
}
