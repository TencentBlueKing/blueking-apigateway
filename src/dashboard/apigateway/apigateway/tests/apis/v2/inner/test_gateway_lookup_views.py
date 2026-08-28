from unittest import mock

import pytest
from ddf import G
from django.urls import reverse
from django.utils import translation

from apigateway.apis.v2.inner import serializers as inner_serializers
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage


def _release_version(gateway, resource_version, stage_name, *, stage_status=StageStatusEnum.ACTIVE.value):
    return G(
        Release,
        gateway=gateway,
        stage=G(Stage, gateway=gateway, name=stage_name, status=stage_status),
        resource_version=resource_version,
    )


def _make_snapshot(
    gateway,
    resource_version,
    *,
    resource_id,
    name,
    is_public=False,
    oauth2_public_client_enabled=False,
    oauth2_personal_client_enabled=False,
):
    return G(
        ReleasedResource,
        gateway=gateway,
        resource_version_id=resource_version.id,
        resource_id=resource_id,
        resource_name=name,
        resource_method="GET",
        resource_path=f"/{name}",
        is_public=is_public,
        oauth2_public_client_enabled=oauth2_public_client_enabled,
        oauth2_personal_client_enabled=oauth2_personal_client_enabled,
        data={
            "id": resource_id,
            "name": name,
            "description": f"{name} description",
            "description_en": f"{name} description en",
        },
    )


def test_gateway_lookup_and_retrieve_urls_do_not_collide():
    assert reverse("openapi.v2.inner.gateway.lookup") == "/backend/api/v2/inner/gateways/-/lookup/"
    assert (
        reverse(
            "openapi.v2.inner.gateway.retrieve",
            kwargs={"gateway_name": "lookup"},
        )
        == "/backend/api/v2/inner/gateways/lookup/"
    )


def test_gateway_released_resource_url():
    assert (
        reverse(
            "openapi.v2.inner.gateway.released_resource.list",
            kwargs={"gateway_name": "gateway-a"},
        )
        == "/backend/api/v2/inner/gateways/gateway-a/released-resources/"
    )
    assert (
        reverse(
            "openapi.v2.inner.gateway.released_resource.lookup",
            kwargs={"gateway_name": "gateway-a"},
        )
        == "/backend/api/v2/inner/gateways/gateway-a/released-resources/-/lookup/"
    )


@pytest.mark.parametrize("data", [{}, {"gateway_names": ""}, {"gateway_names": ", ,"}])
def test_gateway_lookup_input_rejects_missing_or_empty_names(data):
    slz = inner_serializers.GatewayLookupInputSLZ(data=data)
    assert slz.is_valid() is False


@pytest.mark.parametrize("data", [{}, {"names": ""}, {"names": ", ,"}])
def test_released_resource_lookup_input_rejects_missing_or_empty_names(data):
    slz = inner_serializers.GatewayReleasedResourceLookupInputSLZ(data=data)
    assert slz.is_valid() is False


def test_lookup_inputs_normalize_names_and_fields():
    gateway_slz = inner_serializers.GatewayLookupInputSLZ(
        data={"gateway_names": " gateway-b,gateway-a,gateway-b ", "fields": "id,name,id"}
    )
    resource_slz = inner_serializers.GatewayReleasedResourceLookupInputSLZ(
        data={"names": " resource-b,resource-a,resource-b ", "fields": ""}
    )

    gateway_slz.is_valid(raise_exception=True)
    resource_slz.is_valid(raise_exception=True)

    assert gateway_slz.validated_data == {
        "gateway_names": ["gateway-b", "gateway-a"],
        "fields": {"id", "name"},
    }
    assert resource_slz.validated_data == {
        "names": ["resource-b", "resource-a"],
        "fields": None,
    }


@pytest.mark.parametrize(
    ("serializer_class", "data"),
    [
        (inner_serializers.GatewayLookupInputSLZ, {"gateway_names": "g1", "fields": "unknown"}),
        (inner_serializers.GatewayReleasedResourceLookupInputSLZ, {"names": "r1", "fields": "unknown"}),
    ],
)
def test_lookup_inputs_reject_invalid_values(serializer_class, data):
    assert serializer_class(data=data).is_valid() is False


@pytest.mark.parametrize(
    ("serializer_class", "field_name", "required_data"),
    [
        (inner_serializers.GatewayLookupInputSLZ, "gateway_names", {}),
        (inner_serializers.GatewayReleasedResourceLookupInputSLZ, "names", {}),
    ],
)
def test_lookup_inputs_limit_names_to_50(serializer_class, field_name, required_data):
    accepted = serializer_class(data={**required_data, field_name: ",".join(f"name-{i}" for i in range(50))})
    rejected = serializer_class(data={**required_data, field_name: ",".join(f"name-{i}" for i in range(51))})

    assert accepted.is_valid() is True
    assert rejected.is_valid() is False


class TestGatewayLookupApi:
    @mock.patch(
        "apigateway.apis.v2.inner.serializers.ResourcePermissionHandler.convert_gateway_maintainers_to_display_names"
    )
    def test_returns_requested_gateways_without_availability_filters(
        self,
        mock_convert_maintainers,
        request_view,
    ):
        private = G(
            Gateway,
            name="private",
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=False,
            is_official=True,
        )
        inactive = G(Gateway, name="inactive", status=GatewayStatusEnum.INACTIVE.value, is_public=True)

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.lookup",
            app=mock.MagicMock(app_code="bk_auth"),
            data={"gateway_names": "private,inactive,missing", "fields": "id,name,is_official"},
        )

        assert response.status_code == 200
        assert response.json()["data"] == [
            {"id": inactive.id, "name": "inactive", "is_official": False},
            {"id": private.id, "name": "private", "is_official": True},
        ]
        mock_convert_maintainers.assert_not_called()

    def test_returns_default_fields_without_maintainers(self, request_view):
        gateway = G(Gateway, name="all-fields", _maintainers="admin", is_official=True)

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.lookup",
            app=mock.MagicMock(app_code="bk_auth"),
            data={"gateway_names": gateway.name},
        )

        assert response.status_code == 200
        assert set(response.json()["data"][0]) == {
            "id",
            "name",
            "description",
            "doc_maintainers",
            "kind",
            "is_official",
        }
        assert response.json()["data"][0]["is_official"] is True

    @mock.patch(
        "apigateway.apis.v2.inner.serializers.ResourcePermissionHandler.convert_gateway_maintainers_to_display_names"
    )
    def test_default_fields_do_not_query_bk_user(self, mock_convert_maintainers, request_view):
        G(Gateway, name="gateway-a", _maintainers="admin")
        G(Gateway, name="gateway-b", _maintainers="admin")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.lookup",
            app=mock.MagicMock(app_code="bk_auth"),
            data={"gateway_names": "gateway-a,gateway-b"},
        )

        assert response.status_code == 200
        mock_convert_maintainers.assert_not_called()

    @mock.patch(
        "apigateway.apis.v2.inner.serializers.ResourcePermissionHandler.convert_gateway_maintainers_to_display_names"
    )
    def test_maintainers_requires_explicit_fields(self, mock_convert_maintainers, request_view):
        mock_convert_maintainers.return_value = ["Admin User"]
        gateway = G(Gateway, name="with-maintainers", _maintainers="admin")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.lookup",
            app=mock.MagicMock(app_code="bk_auth"),
            data={"gateway_names": gateway.name, "fields": "id,name,maintainers"},
        )

        assert response.status_code == 200
        assert response.json()["data"] == [
            {"id": gateway.id, "name": "with-maintainers", "maintainers": ["Admin User"]},
        ]
        mock_convert_maintainers.assert_called_once()

    def test_preserves_tenant_visibility(self, request_view, settings):
        settings.ENABLE_MULTI_TENANT_MODE = True
        global_gateway = G(
            Gateway,
            name="global-gateway",
            tenant_mode=TenantModeEnum.GLOBAL.value,
            tenant_id="",
        )
        tenant_a = G(
            Gateway,
            name="tenant-a-gateway",
            tenant_mode=TenantModeEnum.SINGLE.value,
            tenant_id="tenant-a",
        )
        G(
            Gateway,
            name="tenant-b-gateway",
            tenant_mode=TenantModeEnum.SINGLE.value,
            tenant_id="tenant-b",
        )

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.lookup",
            app=mock.MagicMock(app_code="bk_auth"),
            data={"gateway_names": "global-gateway,tenant-a-gateway,tenant-b-gateway", "fields": "id,name"},
            HTTP_X_BK_TENANT_ID="tenant-a",
        )

        assert response.status_code == 200
        assert response.json()["data"] == [
            {"id": global_gateway.id, "name": "global-gateway"},
            {"id": tenant_a.id, "name": "tenant-a-gateway"},
        ]

        missing_tenant = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.lookup",
            app=mock.MagicMock(app_code="bk_auth"),
            data={"gateway_names": "global-gateway"},
        )
        assert missing_tenant.status_code == 400


class TestGatewayReleasedResourceApi:
    def test_returns_active_stage_release_union_without_gateway_visibility_filters(self, request_view):
        gateway = G(
            Gateway,
            name="released-resource-gateway",
            status=GatewayStatusEnum.INACTIVE.value,
            is_public=False,
        )
        old_version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
        new_version = G(ResourceVersion, gateway=gateway, version="2.0.0", _data="[]")
        _release_version(gateway, old_version, "prod")
        _release_version(gateway, new_version, "test")
        first = _make_snapshot(
            gateway,
            old_version,
            resource_id=1,
            name="first_resource",
            is_public=True,
            oauth2_public_client_enabled=True,
            oauth2_personal_client_enabled=True,
        )
        _make_snapshot(gateway, old_version, resource_id=2, name="shared_old")
        latest = _make_snapshot(gateway, new_version, resource_id=2, name="shared_new")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
        )

        assert response.status_code == 200
        assert response.json() == {
            "data": {
                "count": 2,
                "results": [
                    {
                        "id": first.resource_id,
                        "name": "first_resource",
                        "description": "first_resource description",
                        "is_public": True,
                        "oauth2_public_client_enabled": True,
                        "oauth2_personal_client_enabled": True,
                    },
                    {
                        "id": latest.resource_id,
                        "name": "shared_new",
                        "description": "shared_new description",
                        "is_public": False,
                        "oauth2_public_client_enabled": False,
                        "oauth2_personal_client_enabled": False,
                    },
                ],
            }
        }

    def test_names_are_exact_and_results_are_unpaginated(self, request_view):
        gateway = G(Gateway, name="released-resource-filter")
        old_version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
        new_version = G(ResourceVersion, gateway=gateway, version="2.0.0", _data="[]")
        _release_version(gateway, old_version, "prod")
        _release_version(gateway, new_version, "test")
        old = _make_snapshot(gateway, old_version, resource_id=1, name="exact_name")
        _make_snapshot(gateway, new_version, resource_id=1, name="renamed")
        _make_snapshot(gateway, new_version, resource_id=2, name="exact_name_suffix")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.lookup",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
            data={
                "names": " exact_name,missing,exact_name ",
                "fields": "id,name,is_public,oauth2_public_client_enabled,oauth2_personal_client_enabled",
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "data": [
                {
                    "id": old.resource_id,
                    "name": "exact_name",
                    "is_public": False,
                    "oauth2_public_client_enabled": False,
                    "oauth2_personal_client_enabled": False,
                }
            ]
        }

    def test_excludes_inactive_stage_releases(self, request_view):
        gateway = G(Gateway, name="inactive-stage-released-resource")
        active_version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
        offline_version = G(ResourceVersion, gateway=gateway, version="2.0.0", _data="[]")
        _release_version(gateway, active_version, "prod")
        _release_version(gateway, offline_version, "offline", stage_status=StageStatusEnum.INACTIVE.value)
        active = _make_snapshot(gateway, active_version, resource_id=1, name="active_resource")
        _make_snapshot(gateway, offline_version, resource_id=2, name="offline_resource")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
        )

        assert response.status_code == 200
        assert response.json() == {
            "data": {
                "count": 1,
                "results": [
                    {
                        "id": active.resource_id,
                        "name": "active_resource",
                        "description": "active_resource description",
                        "is_public": False,
                        "oauth2_public_client_enabled": False,
                        "oauth2_personal_client_enabled": False,
                    },
                ],
            }
        }

    def test_translates_description_from_snapshot_data(self, request_view):
        gateway = G(Gateway, name="translated-released-resource")
        version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
        _release_version(gateway, version, "prod")
        snapshot = _make_snapshot(gateway, version, resource_id=1, name="translated")

        with translation.override("en"):
            response = request_view(
                method="GET",
                view_name="openapi.v2.inner.gateway.released_resource.list",
                path_params={"gateway_name": gateway.name},
                app=mock.MagicMock(app_code="bk_auth"),
            )

        assert response.status_code == 200
        assert response.json()["data"]["results"] == [
            {
                "id": snapshot.resource_id,
                "name": "translated",
                "description": "translated description en",
                "is_public": False,
                "oauth2_public_client_enabled": False,
                "oauth2_personal_client_enabled": False,
            }
        ]

    def test_returns_empty_page_without_current_release(self, request_view):
        gateway = G(Gateway, name="no-current-release")
        version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
        _make_snapshot(gateway, version, resource_id=1, name="orphan")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
        )

        assert response.status_code == 200
        assert response.json() == {"data": {"count": 0, "results": []}}

    def test_returns_404_for_missing_gateway(self, request_view):
        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": "missing"},
            app=mock.MagicMock(app_code="bk_auth"),
        )

        assert response.status_code == 404

    def test_returns_404_for_cross_tenant_gateway(self, request_view, settings):
        settings.ENABLE_MULTI_TENANT_MODE = True
        gateway = G(
            Gateway,
            name="tenant-b-resource-gateway",
            tenant_mode=TenantModeEnum.SINGLE.value,
            tenant_id="tenant-b",
        )
        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
            HTTP_X_BK_TENANT_ID="tenant-a",
        )

        assert response.status_code == 404

    def test_requires_tenant_header_in_multi_tenant_mode(self, request_view, settings):
        settings.ENABLE_MULTI_TENANT_MODE = True
        gateway = G(
            Gateway,
            name="tenant-header-resource-gateway",
            tenant_mode=TenantModeEnum.SINGLE.value,
            tenant_id="tenant-b",
        )
        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "query",
        [
            {"limit": 0},
            {"limit": 1001},
            {"limit": "invalid"},
            {"offset": -1},
            {"offset": "invalid"},
        ],
    )
    def test_rejects_invalid_pagination(self, request_view, query):
        gateway = G(Gateway, name="released-resource-pagination-validation")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
            data=query,
        )

        assert response.status_code == 400

    def test_paginates_after_deduplication(self, request_view):
        gateway = G(Gateway, name="released-resource-pagination")
        version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
        _release_version(gateway, version, "prod")
        for resource_id in range(1, 22):
            _make_snapshot(gateway, version, resource_id=resource_id, name=f"resource-{resource_id:02d}")

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.released_resource.list",
            path_params={"gateway_name": gateway.name},
            app=mock.MagicMock(app_code="bk_auth"),
            data={"fields": "id,name", "limit": 1000, "offset": 10},
        )

        assert response.status_code == 200
        assert response.json()["data"]["count"] == 21
        assert len(response.json()["data"]["results"]) == 11
        assert response.json()["data"]["results"][0] == {"id": 11, "name": "resource-11"}
