from ddf import G

from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage
from apigateway.service.gateway_released_resource import get_gateway_released_resources


def _make_released_resource(gateway, resource_version, *, resource_id, name):
    return G(
        ReleasedResource,
        gateway=gateway,
        resource_version_id=resource_version.id,
        resource_id=resource_id,
        resource_name=name,
        resource_method="GET",
        resource_path=f"/{name}",
        is_public=False,
        oauth2_public_client_enabled=False,
        oauth2_personal_client_enabled=False,
        data={
            "id": resource_id,
            "name": name,
            "description": f"{name} description",
            "description_en": f"{name} description en",
        },
    )


def _release(gateway, resource_version, stage_name):
    return G(
        Release,
        gateway=gateway,
        stage=G(Stage, gateway=gateway, name=stage_name, status=0),
        resource_version=resource_version,
    )


def test_uses_only_current_release_versions():
    gateway = G(Gateway, name="lookup-release-boundary")
    current_version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
    orphan_version = G(ResourceVersion, gateway=gateway, version="2.0.0", _data="[]")
    _release(gateway, current_version, "prod")
    current = _make_released_resource(gateway, current_version, resource_id=1, name="current")
    _make_released_resource(gateway, orphan_version, resource_id=2, name="orphan")

    result = list(get_gateway_released_resources(gateway_id=gateway.id))

    assert [(item.resource_id, item.resource_name) for item in result] == [(current.resource_id, "current")]


def test_merges_versions_and_ignores_visibility_flags():
    gateway = G(Gateway, name="inactive-private-gateway", status=0, is_public=False)
    first_version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
    second_version = G(ResourceVersion, gateway=gateway, version="2.0.0", _data="[]")
    _release(gateway, first_version, "prod")
    _release(gateway, second_version, "test")
    _make_released_resource(gateway, first_version, resource_id=1, name="private_disabled")
    _make_released_resource(gateway, second_version, resource_id=2, name="second_resource")

    result = list(get_gateway_released_resources(gateway_id=gateway.id))

    assert [(item.resource_id, item.resource_name) for item in result] == [
        (1, "private_disabled"),
        (2, "second_resource"),
    ]


def test_deduplicates_by_resource_id_using_latest_matching_snapshot():
    gateway = G(Gateway, name="deduplicate-gateway")
    old_version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
    new_version = G(ResourceVersion, gateway=gateway, version="2.0.0", _data="[]")
    _release(gateway, old_version, "prod")
    _release(gateway, new_version, "test")
    _make_released_resource(gateway, old_version, resource_id=1, name="old_name")
    _make_released_resource(gateway, new_version, resource_id=1, name="new_name")

    unfiltered = list(get_gateway_released_resources(gateway_id=gateway.id))
    old_name_only = list(get_gateway_released_resources(gateway_id=gateway.id, resource_names=["old_name"]))

    assert [(item.resource_id, item.resource_name) for item in unfiltered] == [(1, "new_name")]
    assert [(item.resource_id, item.resource_name) for item in old_name_only] == [(1, "old_name")]


def test_orders_by_name_then_resource_id():
    gateway = G(Gateway, name="ordered-gateway")
    version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
    _release(gateway, version, "prod")
    _make_released_resource(gateway, version, resource_id=3, name="zeta")
    _make_released_resource(gateway, version, resource_id=2, name="alpha")
    _make_released_resource(gateway, version, resource_id=1, name="alpha")

    result = list(get_gateway_released_resources(gateway_id=gateway.id))

    assert [(item.resource_name, item.resource_id) for item in result] == [
        ("alpha", 1),
        ("alpha", 2),
        ("zeta", 3),
    ]


def test_single_version_page_uses_three_queries(django_assert_num_queries):
    gateway = G(Gateway, name="query-budget-gateway")
    version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
    _release(gateway, version, "prod")
    _make_released_resource(gateway, version, resource_id=1, name="resource")

    with django_assert_num_queries(3):
        queryset = get_gateway_released_resources(gateway_id=gateway.id)
        assert queryset.count() == 1
        assert len(list(queryset[:10])) == 1


def test_multiple_version_page_uses_four_queries(django_assert_num_queries):
    gateway = G(Gateway, name="multi-version-query-budget-gateway")
    first_version = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
    second_version = G(ResourceVersion, gateway=gateway, version="2.0.0", _data="[]")
    _release(gateway, first_version, "prod")
    _release(gateway, second_version, "test")
    _make_released_resource(gateway, first_version, resource_id=1, name="old_name")
    _make_released_resource(gateway, second_version, resource_id=1, name="new_name")

    with django_assert_num_queries(4):
        queryset = get_gateway_released_resources(gateway_id=gateway.id)
        assert queryset.count() == 1
        assert [(item.resource_id, item.resource_name) for item in queryset[:10]] == [(1, "new_name")]
