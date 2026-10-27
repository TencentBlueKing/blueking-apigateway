from copy import deepcopy

import pytest
from django_dynamic_fixture import G

from apigateway.apis.web.ai_backend import AIBackendWebConfigAdapter
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum
from apigateway.core.models import Backend, BackendConfig, Stage


@pytest.fixture
def pool_backend(fake_stage):
    fake_stage.gateway.kind = GatewayKindEnum.AI.value
    fake_stage.gateway.save()
    backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.AI.value, name="model-pool", type="http")
    config = AIBackendWebConfigAdapter.to_internal(
        {
            "timeout": 60,
            "instances": [
                {"name": "a", "provider": "openai", "api_key": "alpha-secret"},
                {"name": "b", "provider": "openai", "api_key": "beta-secret"},
                {"name": "backup", "priority": 0, "provider": "openai", "api_key": "backup-secret"},
            ],
        }
    )
    return BackendConfig.objects.create(gateway=fake_stage.gateway, stage=fake_stage, backend=backend, config=config)


def test_create_pool_and_read_explicit_array(request_view, fake_stage):
    fake_stage.gateway.kind = GatewayKindEnum.AI.value
    fake_stage.gateway.save()
    response = request_view(
        "POST",
        "backend.list-create",
        path_params={"gateway_id": fake_stage.gateway_id},
        gateway=fake_stage.gateway,
        data={
            "name": "pool",
            "kind": "ai",
            "type": "http",
            "configs": [
                {
                    "stage_id": fake_stage.id,
                    "balancer": {"algorithm": "chash"},
                    "instances": [
                        {"name": "a", "provider": "openai", "api_key": "alpha-secret"},
                        {"name": "b", "priority": 0, "provider": "openai", "api_key": "beta-secret"},
                    ],
                }
            ],
        },
    )
    assert response.status_code == 201, response.json()
    stored = BackendConfig.objects.get(backend__name="pool", gateway=fake_stage.gateway)
    assert "alpha-secret" not in str(stored._config)
    assert stored.config["balancer"]["key"] == "$bk_app_code"
    output = request_view(
        "GET",
        "backend.retrieve-update-destroy",
        gateway=fake_stage.gateway,
        path_params={"gateway_id": fake_stage.gateway_id, "id": stored.backend_id},
        data={"config_format": "instances"},
    )
    assert output.status_code == 200, output.json()
    config = output.json()["data"]["configs"][0]
    assert [item["name"] for item in config["instances"]] == ["a", "b"]
    assert config["instances"][0]["api_key"] == "al****et"
    assert config["balancer"] == {"algorithm": "chash"}


@pytest.mark.parametrize(
    "route", ["backend.retrieve-update-destroy", "stage.backend-list", "stage.backend-retrieve-update"]
)
def test_pool_queries_require_new_format(request_view, pool_backend, route):
    params = {"gateway_id": pool_backend.gateway_id, "id": pool_backend.stage_id}
    if route.startswith("backend."):
        params["id"] = pool_backend.backend_id
    elif route.endswith("retrieve-update"):
        params["backend_id"] = pool_backend.backend_id
    for fmt, expected in [(None, 400), ("invalid", 400), ("instances", 200)]:
        response = request_view(
            "GET",
            route,
            path_params=params,
            gateway=pool_backend.gateway,
            data={} if fmt is None else {"config_format": fmt},
        )
        assert response.status_code == expected, response.json()
        if expected == 200:
            assert "alpha-secret" not in str(response.json())


@pytest.mark.parametrize("route", ["backend.retrieve-update-destroy", "stage.backend-retrieve-update"])
def test_remove_and_reorder_instances_preserves_credentials_and_publication(request_view, mocker, pool_backend, route):
    publish_stage = mocker.patch("apigateway.apis.web.stage.views.trigger_gateway_publish")
    publish_backend = mocker.patch("apigateway.biz.backend.backend.trigger_gateway_publish")
    data = AIBackendWebConfigAdapter.to_web(pool_backend.config, config_format="instances")
    data["instances"].reverse()
    data["instances"] = [item for item in data["instances"] if item["name"] != "b"]
    params = {
        "gateway_id": pool_backend.gateway_id,
        "id": pool_backend.stage_id,
        "backend_id": pool_backend.backend_id,
    }
    if route.startswith("backend."):
        params = {"gateway_id": pool_backend.gateway_id, "id": pool_backend.backend_id}
        data = {
            "name": pool_backend.backend.name,
            "type": "http",
            "configs": [{"stage_id": pool_backend.stage_id, **data}],
        }
    response = request_view("PUT", route, path_params=params, gateway=pool_backend.gateway, data=data)
    assert response.status_code in (200, 204), response.json()
    pool_backend.refresh_from_db()
    assert [item["name"] for item in pool_backend.config["instances"]] == ["a", "backup"]
    assert pool_backend.config["instances"][0]["auth"]["header"]["Authorization"] == "Bearer alpha-secret"
    assert pool_backend.config["instances"][1]["auth"]["header"]["Authorization"] == "Bearer backup-secret"
    if route.startswith("stage."):
        publish_stage.assert_called_once()
        # Reordering an otherwise unchanged pool should not republish.
        unchanged = AIBackendWebConfigAdapter.to_web(pool_backend.config, config_format="instances")
        unchanged["instances"].reverse()
        publish_stage.reset_mock()
        response = request_view("PUT", route, path_params=params, gateway=pool_backend.gateway, data=unchanged)
        assert response.status_code == 204
        publish_stage.assert_not_called()
    else:
        publish_backend.assert_not_called()  # No published resource references this backend.


def test_invalid_update_does_not_change_storage_or_publish(request_view, mocker, pool_backend):
    publish = mocker.patch("apigateway.apis.web.stage.views.trigger_gateway_publish")
    original = deepcopy(pool_backend.config)
    data = AIBackendWebConfigAdapter.to_web(original, config_format="instances")
    data["fallback_strategy"] = []
    response = request_view(
        "PUT",
        "stage.backend-retrieve-update",
        gateway=pool_backend.gateway,
        path_params={
            "gateway_id": pool_backend.gateway_id,
            "id": pool_backend.stage_id,
            "backend_id": pool_backend.backend_id,
        },
        data=data,
    )
    assert response.status_code == 400
    pool_backend.refresh_from_db()
    assert pool_backend.config == original
    publish.assert_not_called()


def test_stage_create_with_pool_and_connectivity_remains_single_instance(request_view, mocker, pool_backend):
    data = AIBackendWebConfigAdapter.to_web(pool_backend.config, config_format="instances")
    response = request_view(
        "POST",
        "stage.list-create",
        path_params={"gateway_id": pool_backend.gateway_id},
        gateway=pool_backend.gateway,
        data={"name": "new-stage", "description": "", "backends": [{"id": pool_backend.backend_id, "config": data}]},
    )
    # Masks are not portable to a different Stage: no existing credentials are restored.
    assert response.status_code == 201, response.json()
    new_stage = Stage.objects.get(gateway=pool_backend.gateway, name="new-stage")
    stored = BackendConfig.objects.get(stage=new_stage, backend_id=pool_backend.backend_id)
    assert stored.config["instances"][0]["auth"]["header"]["Authorization"] == "Bearer al****et"
    fetch_models = mocker.patch("apigateway.apis.web.backend.views.get_ai_backend_model_ids")
    response = request_view(
        "POST",
        "backend.test-connection",
        path_params={"gateway_id": pool_backend.gateway_id},
        gateway=pool_backend.gateway,
        data={"config": {"stage_id": pool_backend.stage_id, **data}},
    )
    assert response.status_code == 400
    fetch_models.assert_not_called()
