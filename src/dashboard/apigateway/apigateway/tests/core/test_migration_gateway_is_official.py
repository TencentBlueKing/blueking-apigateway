import importlib

from ddf import G
from django.apps import apps

from apigateway.core.models import Context, Gateway
from apigateway.service.contexts import GatewayAuthContext


def test_gateway_is_official_migration_backfills_from_gateway_auth_context(meta_schemas):
    super_official_gateway = G(Gateway)
    official_gateway = G(Gateway)
    cloud_gateway = G(Gateway)
    missing_type_gateway = G(Gateway)
    invalid_config_gateway = G(Gateway)
    no_context_gateway = G(Gateway)

    GatewayAuthContext().save(super_official_gateway.id, {"api_type": 0})
    GatewayAuthContext().save(official_gateway.id, {"api_type": 1})
    GatewayAuthContext().save(cloud_gateway.id, {"api_type": 10})
    GatewayAuthContext().save(missing_type_gateway.id, {})
    GatewayAuthContext().save(invalid_config_gateway.id, {"api_type": 1})
    Context.objects.filter(scope_type="api", type="api_auth", scope_id=invalid_config_gateway.id).update(
        _config="{invalid"
    )

    migration = importlib.import_module("apigateway.core.migrations.0052_gateway_is_official")
    migration.forwards_func(apps, None)

    super_official_gateway.refresh_from_db()
    official_gateway.refresh_from_db()
    cloud_gateway.refresh_from_db()
    missing_type_gateway.refresh_from_db()
    invalid_config_gateway.refresh_from_db()
    no_context_gateway.refresh_from_db()

    assert super_official_gateway.is_official is True
    assert official_gateway.is_official is True
    assert cloud_gateway.is_official is False
    assert missing_type_gateway.is_official is False
    assert invalid_config_gateway.is_official is False
    assert no_context_gateway.is_official is False


def test_gateway_is_official_migration_reverse_resets_field():
    gateway = G(Gateway, is_official=True)

    migration = importlib.import_module("apigateway.core.migrations.0052_gateway_is_official")
    migration.reverse_func(apps, None)

    gateway.refresh_from_db()
    assert gateway.is_official is False
