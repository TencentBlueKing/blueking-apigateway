from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from apigateway.core.constants import AI_BACKEND_BUILTIN_PROVIDERS, AIBackendProviderEnum, BackendKindEnum


def mask_header_value(value: str) -> str:
    return "****" if len(value) < 4 else f"{value[:2]}****{value[-2:]}"


def _validate_object_keys(data: dict[str, Any], *, allowed: set[str], required: set[str], path: str) -> None:
    if missing := required - data.keys():
        raise ValueError(f"{path}: missing required field: {min(missing)}")
    if unknown := data.keys() - allowed:
        raise ValueError(f"{path}: unknown field: {min(unknown)}")


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


class AIBackendConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    timeout: int = Field(default=30000, gt=0)
    instances: list[dict[str, Any]] = Field(min_length=1, max_length=1)

    @field_validator("instances")
    @classmethod
    def validate_instances(cls, instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
        instance = instances[0]
        path = "$.instances[0]"
        _validate_object_keys(
            instance,
            allowed={"name", "provider", "weight", "auth", "options", "override"},
            required={"name", "provider", "weight", "options"},
            path=path,
        )
        if not isinstance(instance["name"], str) or not instance["name"]:
            raise ValueError(f"{path}.name: must be a non-empty string")
        if instance["provider"] not in AIBackendProviderEnum.get_values():
            raise ValueError(f"{path}.provider: unsupported provider")
        if type(instance["weight"]) is not int or instance["weight"] != 1:
            raise ValueError(f"{path}.weight: must be 1")
        cls._validate_auth(instance.get("auth"), provided="auth" in instance)
        cls._validate_options(instance["options"])
        cls._validate_override(instance.get("override"), provided="override" in instance)
        return instances

    @staticmethod
    def _validate_auth(auth: Any, *, provided: bool) -> None:
        path = "$.instances[0].auth"
        if not provided:
            return
        if not isinstance(auth, dict):
            raise ValueError(f"{path}: must be an object")  # noqa: TRY004
        _validate_object_keys(auth, allowed={"header"}, required=set(), path=path)
        if "header" not in auth:
            return
        headers = auth["header"]
        if not isinstance(headers, dict) or any(
            not isinstance(key, str) or not isinstance(value, str) for key, value in headers.items()
        ):
            raise ValueError(f"{path}.header: names and values must be strings")
        normalized: set[str] = set()
        for key in headers:
            normalized_key = key.casefold()
            if normalized_key in normalized:
                raise ValueError(f"{path}.header: duplicate header: {key}")
            normalized.add(normalized_key)

    @staticmethod
    def _validate_options(options: Any) -> None:
        path = "$.instances[0].options"
        if not isinstance(options, dict):
            raise ValueError(f"{path}: must be an object")  # noqa: TRY004
        if "model" not in options:
            raise ValueError(f"{path}: missing required field: model")
        if not isinstance(options["model"], str) or not options["model"]:
            raise ValueError(f"{path}.model: must be a non-empty string")

    @staticmethod
    def _validate_override(override: Any, *, provided: bool) -> None:
        path = "$.instances[0].override"
        if not provided:
            return
        if not isinstance(override, dict):
            raise ValueError(f"{path}: must be an object")  # noqa: TRY004
        _validate_object_keys(override, allowed={"endpoint"}, required={"endpoint"}, path=path)
        if not isinstance(override["endpoint"], str) or not override["endpoint"]:
            raise ValueError(f"{path}.endpoint: must be a non-empty string")

    @model_validator(mode="after")
    def validate_provider_contract(self) -> Self:
        instance = self.instances[0]
        headers = instance.get("auth", {}).get("header", {})
        authorization = next((value for key, value in headers.items() if key.casefold() == "authorization"), "")
        if instance["provider"] in AI_BACKEND_BUILTIN_PROVIDERS:
            if not authorization:
                raise ValueError("$.instances[0].auth.header: Authorization header is required")
            if "override" in instance:
                raise ValueError("$.instances[0].override: override is not allowed")
        elif "override" not in instance:
            raise ValueError("$.instances[0].override: override.endpoint is required")
        return self

    def to_config(self) -> dict[str, Any]:
        data = self.model_dump(exclude_unset=True)
        data["timeout"] = self.timeout
        return data


type BackendConfigType = type[StandardBackendConfig] | type[AIBackendConfig]


BACKEND_CONFIG_TYPES: dict[str, BackendConfigType] = {
    BackendKindEnum.STANDARD.value: StandardBackendConfig,
    BackendKindEnum.AI.value: AIBackendConfig,
}
