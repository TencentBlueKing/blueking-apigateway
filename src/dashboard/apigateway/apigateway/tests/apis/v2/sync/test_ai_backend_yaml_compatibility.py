from copy import deepcopy
from functools import cache
from pathlib import Path

import jsonschema
import pytest

from apigateway.core.constants import GatewayKindEnum
from apigateway.core.models import BackendConfig
from apigateway.utils.yaml import yaml_loads


@cache
def _sync_request_schema(operation_id):
    path = Path(__file__).resolve().parents[4] / "data/apigw-definitions/bk-apigateway-resources.yaml"
    definition = yaml_loads(path.read_text())
    return next(
        operation["requestBody"]["content"]["application/json"]["schema"]
        for methods in definition["paths"].values()
        for operation in methods.values()
        if isinstance(operation, dict) and operation.get("operationId") == operation_id
    )


@pytest.mark.parametrize("route", ["openapi.stage.sync", "openapi.v2.sync.gateway.stages.sync"])
@pytest.mark.parametrize("weight", [None, 0, 1, 80])
@pytest.mark.parametrize("provider", ["openai", "openai-compatible"])
def test_existing_single_instance_yaml_can_be_imported_repeatedly(
    request_view, fake_gateway, mocker, route, weight, provider
):
    mocker.patch(
        "apigateway.apis.open.stage.views.OpenAPIGatewayRelatedAppPermission.has_permission", return_value=True
    )
    mocker.patch(
        "apigateway.apis.v2.permissions.OpenAPIV2GatewayRelatedAppPermission.has_permission", return_value=True
    )
    fake_gateway.kind = GatewayKindEnum.AI.value
    fake_gateway.save()
    # This is the pre-feature YAML structure: no priority, balancer or fallback.
    payload = yaml_loads("""
name: prod
description: existing YAML configuration
vars:
  region: old-region
ai_backends:
  - name: existing-model
    config:
      timeout: 120
      instances:
        - name: original-instance
          provider: openai
          auth:
            header:
              Authorization: "Bearer old-key"
              X-Tenant: old-tenant
          options:
            model: original-model
            temperature: 0.7
            metadata:
              tags: [old, null]
""")
    instance = payload["ai_backends"][0]["config"]["instances"][0]
    instance["provider"] = provider
    if provider == "openai-compatible":
        instance["override"] = {"endpoint": "https://existing.example.com/v1/chat/completions"}
        instance["model_endpoint"] = "https://existing.example.com/v1/models"
    if weight is not None:
        instance["weight"] = weight
    expected = deepcopy(payload["ai_backends"][0]["config"])
    expected["instances"][0].setdefault("weight", 0)
    original_payload = deepcopy(payload)
    operation_id = "sync_stage" if route == "openapi.stage.sync" else "v2_sync_stages"
    jsonschema.validate(payload, _sync_request_schema(operation_id))

    for _ in range(2):
        response = request_view(
            "POST", route, gateway=fake_gateway, path_params={"gateway_name": fake_gateway.name}, data=payload
        )
        assert response.status_code == 200, response.json()
        stored = BackendConfig.objects.get(gateway=fake_gateway, backend__name="existing-model", stage__name="prod")
        assert stored.config == expected
        assert "old-key" not in str(stored._config)
        assert "balancer" not in stored.config and "fallback_strategy" not in stored.config
        assert "priority" not in stored.config["instances"][0]
    assert payload == original_payload


@pytest.mark.parametrize("operation_id", ["sync_stage", "v2_sync_stages"])
@pytest.mark.parametrize("algorithm", ["roundrobin", "chash"])
def test_registered_sync_schema_accepts_main_pool_and_backup(operation_id, algorithm):
    schema = _sync_request_schema(operation_id)
    instances = [
        {"name": "primary-a", "priority": 10, "provider": "openai", "weight": 1},
        {"name": "primary-b", "priority": 10, "provider": "deepseek", "weight": 1},
        {
            "name": "backup",
            "priority": 0,
            "provider": "openai-compatible",
            "weight": 1,
            "override": {"endpoint": "https://backup.example.com/v1/chat/completions"},
        },
    ]
    config = {
        "instances": instances,
        "balancer": {"algorithm": algorithm},
        "fallback_strategy": ["http_429", "http_5xx"],
    }
    if algorithm == "chash":
        config["balancer"].update(hash_on="vars_combinations", key="$bk_app_code")
    jsonschema.validate({"name": "prod", "ai_backends": [{"name": "pool", "config": config}]}, schema)
    properties = schema["properties"]["ai_backends"]["items"]["properties"]["config"]["properties"]
    assert "priority" in properties["instances"]["items"]["properties"]
    assert {"balancer", "fallback_strategy"} <= properties.keys()


@pytest.mark.parametrize("route", ["openapi.stage.sync", "openapi.v2.sync.gateway.stages.sync"])
@pytest.mark.parametrize("credential", ["****", "ab****cd", "literal*key"])
def test_automation_keeps_mask_shaped_credentials_literal(request_view, fake_gateway, mocker, route, credential):
    mocker.patch(
        "apigateway.apis.open.stage.views.OpenAPIGatewayRelatedAppPermission.has_permission", return_value=True
    )
    mocker.patch(
        "apigateway.apis.v2.permissions.OpenAPIV2GatewayRelatedAppPermission.has_permission", return_value=True
    )
    fake_gateway.kind = GatewayKindEnum.AI.value
    fake_gateway.save()
    config = {
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "auth": {"header": {"Authorization": f"Bearer {credential}"}},
            }
        ]
    }
    response = request_view(
        "POST",
        route,
        gateway=fake_gateway,
        path_params={"gateway_name": fake_gateway.name},
        data={"name": "prod", "ai_backends": [{"name": "model", "config": config}]},
    )
    assert response.status_code == 200, response.json()
    stored = BackendConfig.objects.get(gateway=fake_gateway, backend__name="model", stage__name="prod")
    assert stored.config["instances"][0]["auth"]["header"]["Authorization"] == f"Bearer {credential}"
