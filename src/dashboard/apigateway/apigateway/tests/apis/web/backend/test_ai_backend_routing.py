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
                {"name": "a", "priority": 10, "provider": "openai", "api_key": "alpha-secret"},
                {"name": "b", "priority": 10, "provider": "openai", "api_key": "beta-secret"},
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
                        {"name": "a", "priority": 10, "provider": "openai", "api_key": "alpha-secret"},
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
    )
    assert output.status_code == 200, output.json()
    config = output.json()["data"]["configs"][0]
    assert [item["name"] for item in config["instances"]] == ["a", "b"]
    assert config["instances"][0]["api_key"] == "al****et"
    assert config["balancer"] == {"algorithm": "chash"}


@pytest.mark.parametrize(
    "route", ["backend.retrieve-update-destroy", "stage.backend-list", "stage.backend-retrieve-update"]
)
def test_pool_queries_return_arrays_by_default(request_view, pool_backend, route):
    params = {"gateway_id": pool_backend.gateway_id, "id": pool_backend.stage_id}
    if route.startswith("backend."):
        params["id"] = pool_backend.backend_id
    elif route.endswith("retrieve-update"):
        params["backend_id"] = pool_backend.backend_id
    response = request_view("GET", route, path_params=params, gateway=pool_backend.gateway)
    assert response.status_code == 200, response.json()
    assert "alpha-secret" not in str(response.json())
    result = response.json()["data"]
    if route.startswith("backend."):
        config = result["configs"][0]
    elif route.endswith("retrieve-update"):
        config = result["config"]
    else:
        config = next(item["config"] for item in result if item["id"] == pool_backend.backend_id)
    assert [item["name"] for item in config["instances"]] == ["a", "b", "backup"]


@pytest.mark.parametrize("route", ["backend.retrieve-update-destroy", "stage.backend-retrieve-update"])
def test_remove_and_reorder_instances_preserves_credentials_and_publication(request_view, mocker, pool_backend, route):
    publish_stage = mocker.patch("apigateway.apis.web.stage.views.trigger_gateway_publish")
    publish_backend = mocker.patch("apigateway.biz.backend.backend.trigger_gateway_publish")
    data = AIBackendWebConfigAdapter.to_web(pool_backend.config)
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
        unchanged = AIBackendWebConfigAdapter.to_web(pool_backend.config)
        unchanged["instances"].reverse()
        publish_stage.reset_mock()
        response = request_view("PUT", route, path_params=params, gateway=pool_backend.gateway, data=unchanged)
        assert response.status_code == 204
        publish_stage.assert_not_called()
    else:
        publish_backend.assert_not_called()  # No published resource references this backend.


@pytest.mark.parametrize("invalid", ["empty_strategy", "duplicate_name"])
def test_invalid_update_does_not_change_storage_or_publish(request_view, mocker, pool_backend, invalid):
    publish = mocker.patch("apigateway.apis.web.stage.views.trigger_gateway_publish")
    original = deepcopy(pool_backend.config)
    data = AIBackendWebConfigAdapter.to_web(original)
    if invalid == "empty_strategy":
        data["fallback_strategy"] = []
    else:
        data["instances"][1].update(name=data["instances"][0]["name"], api_key="new-key")
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
    assert response.json()["error"]["code"] == "INVALID_ARGUMENT"
    if invalid == "duplicate_name":
        assert "模型实例名称不能重复" in response.json()["error"]["message"]
    pool_backend.refresh_from_db()
    assert pool_backend.config == original
    publish.assert_not_called()


def test_stage_create_with_pool_and_connectivity_remains_single_instance(request_view, mocker, pool_backend):
    data = AIBackendWebConfigAdapter.to_web(pool_backend.config)
    response = request_view(
        "POST",
        "stage.list-create",
        path_params={"gateway_id": pool_backend.gateway_id},
        gateway=pool_backend.gateway,
        data={"name": "new-stage", "description": "", "backends": [{"id": pool_backend.backend_id, "config": data}]},
    )
    assert response.status_code == 400, response.json()
    assert "重新输入" in str(response.json())
    assert not Stage.objects.filter(gateway=pool_backend.gateway, name="new-stage").exists()
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


@pytest.mark.parametrize("route", ["backend.retrieve-update-destroy", "stage.backend-retrieve-update"])
def test_web_rejects_flat_configuration(request_view, pool_backend, route):
    flat = {"provider": "openai", "api_key": "secret", "timeout": 60}
    params = {
        "gateway_id": pool_backend.gateway_id,
        "id": pool_backend.stage_id,
        "backend_id": pool_backend.backend_id,
    }
    if route.startswith("backend."):
        params = {"gateway_id": pool_backend.gateway_id, "id": pool_backend.backend_id}
        flat = {
            "name": pool_backend.backend.name,
            "type": "http",
            "configs": [{"stage_id": pool_backend.stage_id, **flat}],
        }
    response = request_view("PUT", route, path_params=params, gateway=pool_backend.gateway, data=flat)
    assert response.status_code == 400, response.json()


@pytest.mark.parametrize("priority", [10, 0])
@pytest.mark.parametrize("success, expected_status", [(True, 200), (False, 500)])
def test_each_unsaved_instance_is_probed_without_persisting(
    request_view, mocker, fake_stage, priority, success, expected_status
):
    fake_stage.gateway.kind = GatewayKindEnum.AI.value
    fake_stage.gateway.save()
    mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    http_get = mocker.patch(
        "apigateway.biz.backend.connectivity.http_get", return_value=(success, {"data": [{"id": "available-model"}]})
    )
    before = BackendConfig.objects.filter(gateway=fake_stage.gateway).count()
    response = request_view(
        "POST",
        "backend.test-connection",
        path_params={"gateway_id": fake_stage.gateway_id},
        gateway=fake_stage.gateway,
        data={
            "config": {
                "stage_id": fake_stage.id,
                "instance": {
                    "name": "pending-instance",
                    "priority": priority,
                    "provider": "openai",
                    "api_key": "new-key",
                },
            }
        },
    )
    assert response.status_code == expected_status, response.json()
    if success:
        assert response.json()["data"]["models"] == ["available-model"]
    assert BackendConfig.objects.filter(gateway=fake_stage.gateway).count() == before
    assert not Backend.objects.filter(gateway=fake_stage.gateway, kind=BackendKindEnum.AI.value).exists()
    assert http_get.call_args.kwargs["headers"] == {"Authorization": "Bearer new-key"}


def test_existing_backup_is_probed_by_name_without_changing_pool(request_view, mocker, pool_backend):
    mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    http_get = mocker.patch("apigateway.biz.backend.connectivity.http_get", return_value=(True, {"data": []}))
    before = deepcopy(pool_backend.config)
    backup = AIBackendWebConfigAdapter.to_web(before)["instances"][-1]
    response = request_view(
        "POST",
        "backend.test-connection",
        path_params={"gateway_id": pool_backend.gateway_id},
        gateway=pool_backend.gateway,
        data={
            "backend_id": pool_backend.backend_id,
            "config": {"stage_id": pool_backend.stage_id, "instance": backup},
        },
    )
    assert response.status_code == 200, response.json()
    assert http_get.call_args.kwargs["headers"] == {"Authorization": "Bearer backup-secret"}
    pool_backend.refresh_from_db()
    assert pool_backend.config == before


@pytest.mark.parametrize("route", ["backend.retrieve-update-destroy", "stage.backend-retrieve-update"])
def test_renamed_masked_instance_is_rejected_without_saving_or_publishing(request_view, mocker, pool_backend, route):
    publish_stage = mocker.patch("apigateway.apis.web.stage.views.trigger_gateway_publish")
    publish_backend = mocker.patch("apigateway.biz.backend.backend.trigger_gateway_publish")
    before = deepcopy(pool_backend.config)
    data = AIBackendWebConfigAdapter.to_web(before)
    data["instances"][0]["name"] = "renamed"
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
    assert response.status_code == 400, response.json()
    assert "重新输入" in str(response.json())
    pool_backend.refresh_from_db()
    assert pool_backend.config == before
    publish_stage.assert_not_called()
    publish_backend.assert_not_called()


@pytest.mark.parametrize("route", ["backend.retrieve-update-destroy", "stage.backend-retrieve-update"])
def test_pool_reduced_to_single_primary_saves_without_pool_fields(request_view, mocker, pool_backend, route):
    publish_stage = mocker.patch("apigateway.apis.web.stage.views.trigger_gateway_publish")
    data = AIBackendWebConfigAdapter.to_web(pool_backend.config)
    data["instances"] = [data["instances"][0]]
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
    assert len(pool_backend.config["instances"]) == 1
    assert pool_backend.config["instances"][0]["auth"]["header"]["Authorization"] == "Bearer alpha-secret"
    assert "balancer" not in pool_backend.config and "fallback_strategy" not in pool_backend.config
    output = request_view(
        "GET",
        "stage.backend-retrieve-update",
        gateway=pool_backend.gateway,
        path_params={
            "gateway_id": pool_backend.gateway_id,
            "id": pool_backend.stage_id,
            "backend_id": pool_backend.backend_id,
        },
    )
    assert output.status_code == 200, output.json()
    config = output.json()["data"]["config"]
    assert len(config["instances"]) == 1
    assert "balancer" not in config and "fallback_strategy" not in config
    if route.startswith("stage."):
        publish_stage.assert_called_once()
