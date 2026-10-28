from unittest.mock import MagicMock

import pytest
from django.utils.translation import override
from django_dynamic_fixture import G

from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import AppGatewayPermission, AppPermissionRecord
from apigateway.core.models import Release

READ_ROUTES = [
    "openapi.gateway.list",
    "openapi.gateway.retrieve",
    "openapi.v2.open.gateway.list",
    "openapi.v2.open.gateway.lookup",
    "openapi.v2.open.gateway.retrieve",
    "openapi.v2.inner.gateway.list",
    "openapi.v2.inner.gateway.lookup",
    "openapi.v2.inner.gateway.retrieve",
    "docs.gateway.list",
    "docs.gateway.retrieve",
]


@pytest.mark.parametrize("view_name", READ_ROUTES)
@pytest.mark.parametrize(
    "language,english,expected", [("zh-cn", "English", "默认名"), ("en", "English", "English"), ("en", None, "默认名")]
)
def test_gateway_read_routes_localize_display_name(request_view, fake_gateway, view_name, language, english, expected):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = english
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    G(Release, gateway=fake_gateway)
    params = {}
    data = {}
    if view_name.endswith("retrieve"):
        params = (
            {"gateway_id": fake_gateway.pk}
            if view_name == "openapi.gateway.retrieve"
            else {"gateway_name": fake_gateway.name}
        )
    if view_name.endswith("lookup"):
        data = {"names": fake_gateway.name} if ".open." in view_name else {"gateway_names": fake_gateway.name}
    with override(language):
        response = request_view(
            method="GET", view_name=view_name, path_params=params, data=data, app=MagicMock(app_code="test")
        )
    assert response.status_code == 200, response.json()
    result = response.json()["data"]
    if isinstance(result, dict) and "results" in result:
        result = result["results"]
    if isinstance(result, list):
        result = next(item for item in result if item["id"] == fake_gateway.pk)
    assert result["display_name"] == expected


@pytest.mark.parametrize("surface", ["openapi.gateway", "openapi.v2.open.gateway", "openapi.v2.inner.gateway"])
@pytest.mark.parametrize("keyword", ["默认", "English"])
def test_gateway_exact_vs_fuzzy_display_search(request_view, fake_gateway, surface, keyword):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = "English"
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    G(Release, gateway=fake_gateway)
    for fuzzy, expected in [(False, []), (True, [] if keyword == "English" else [fake_gateway.pk])]:
        response = request_view(
            method="GET",
            view_name=f"{surface}.list",
            data={"name": keyword, "fuzzy": fuzzy},
            app=MagicMock(app_code="test"),
        )
        assert response.status_code == 200, response.json()
        assert [item["id"] for item in response.json()["data"]] == expected


def test_inner_lookup_respects_explicit_fields(request_view, fake_gateway):
    for fields, expected in [("id,name", {"id", "name"}), ("id,display_name", {"id", "display_name"})]:
        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.lookup",
            data={"gateway_names": fake_gateway.name, "fields": fields},
            app=MagicMock(app_code="test"),
        )
        assert response.status_code == 200, response.json()
        assert set(response.json()["data"][0]) == expected


@pytest.mark.parametrize(
    "view_name",
    [
        "openapi.permission.app-records",
        "openapi.permission.app-record-detail",
        "openapi.v2.inner.permission.apply-records",
        "openapi.v2.inner.permission.apply-record-detail",
    ],
)
@pytest.mark.parametrize(
    "language,english,expected", [("zh-cn", "English", "默认名"), ("en", "English", "English"), ("en", None, "默认名")]
)
def test_permission_record_list_and_detail_projection(
    request_view, fake_gateway, view_name, language, english, expected
):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = english
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    record = G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code="test",
        applied_by="admin",
        grant_dimension=GrantDimensionEnum.API.value,
        status=ApplyStatusEnum.PENDING.value,
    )
    params = {"record_id": record.pk} if view_name.endswith("detail") else {}
    with override(language):
        response = request_view(
            method="GET",
            view_name=view_name,
            path_params=params,
            data={"target_app_code": "test"},
            app=MagicMock(app_code="test"),
        )
    assert response.status_code == 200, response.json()
    result = response.json()["data"]
    if "results" in result:
        result = result["results"][0]
    assert result["gateway_display_name"] == expected


@pytest.mark.parametrize("keyword", ["默认", "English"])
def test_docs_keyword_search_excludes_english_display_name(request_view, fake_gateway, keyword):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = "English"
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    G(Release, gateway=fake_gateway)
    response = request_view(method="GET", view_name="docs.gateway.list", data={"keyword": keyword, "limit": 1})
    assert response.status_code == 200, response.json()
    assert response.json()["data"]["count"] == (0 if keyword == "English" else 1)
    assert [row["id"] for row in response.json()["data"]["results"]] == (
        [] if keyword == "English" else [fake_gateway.pk]
    )


@pytest.mark.parametrize(
    "view_name",
    [
        "openapi.permission.resource",
        "openapi.permission.app-permissions",
        "openapi.v2.inner.gateway.permission.resource.list",
        "openapi.v2.inner.permission.app-permissions",
    ],
)
@pytest.mark.parametrize(
    "language,english,expected", [("zh-cn", "English", "默认名"), ("en", "English", "English"), ("en", None, "默认名")]
)
def test_permission_dictionary_producer_routes(
    request_view, fake_gateway, fake_resource_version, fake_release, view_name, language, english, expected
):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = english
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    G(AppGatewayPermission, gateway=fake_gateway, bk_app_code="test", expires=None)
    if view_name == "openapi.permission.resource":
        params = {"gateway_id": fake_gateway.pk}
    elif view_name == "openapi.v2.inner.gateway.permission.resource.list":
        params = {"gateway_name": fake_gateway.name}
    else:
        params = {}
    with override(language):
        response = request_view(
            method="GET",
            view_name=view_name,
            path_params=params,
            gateway=fake_gateway,
            data={"target_app_code": "test"},
            app=MagicMock(app_code="test"),
        )
    assert response.status_code == 200, response.json()
    rows = response.json()["data"]
    assert rows
    assert all(row["gateway_display_name"] == expected for row in rows)


@pytest.mark.parametrize("view_name", ["openapi.permission.app-records", "openapi.v2.inner.permission.apply-records"])
@pytest.mark.parametrize("keyword", ["默认", "English"])
def test_permission_record_existing_query_matches_display_names(request_view, fake_gateway, view_name, keyword):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = "English"
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code="test",
        applied_by="admin",
        grant_dimension=GrantDimensionEnum.API.value,
    )
    response = request_view(
        method="GET",
        view_name=view_name,
        data={"target_app_code": "test", "query": keyword},
        app=MagicMock(app_code="test"),
    )
    assert response.status_code == 200, response.json()
    assert response.json()["data"]["count"] == (0 if keyword == "English" else 1)


@pytest.mark.parametrize("view_name", ["openapi.gateway.list", "openapi.v2.open.gateway.list"])
@pytest.mark.parametrize("keyword", ["默认", "English"])
def test_public_gateway_existing_keyword_filters(request_view, fake_gateway, view_name, keyword):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = "English"
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    G(Release, gateway=fake_gateway)
    query = {"query": keyword, "fuzzy": True} if view_name == "openapi.gateway.list" else {"keyword": keyword}
    response = request_view(method="GET", view_name=view_name, data=query, app=MagicMock(app_code="test"))
    assert response.status_code == 200, response.json()
    assert [item["id"] for item in response.json()["data"]] == ([] if keyword == "English" else [fake_gateway.pk])
