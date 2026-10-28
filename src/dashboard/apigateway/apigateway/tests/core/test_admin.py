from django.contrib import admin
from django.forms.models import modelform_factory
from django_dynamic_fixture import G

from apigateway.core.admin import BackendConfigAdminForm, GatewayAdmin, GatewayAdminForm
from apigateway.core.constants import BackendKindEnum
from apigateway.core.models import Backend, BackendConfig, Gateway


def _ai_config(model="gpt-4o"):
    return {
        "timeout": 300,
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "weight": 1,
                "auth": {"header": {"Authorization": "Bearer secret"}},
                "options": {"model": model},
            }
        ],
    }


def test_backend_config_admin_form_displays_decrypted_config(fake_stage):
    config = _ai_config()
    backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.AI.value)
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=backend,
        stage=fake_stage,
        config=config,
    )

    form = BackendConfigAdminForm(instance=backend_config)

    assert form.initial["config"] == config


def test_backend_config_admin_form_saves_through_encrypted_config_property(fake_stage):
    backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.AI.value)
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=backend,
        stage=fake_stage,
        config=_ai_config(),
    )
    updated_config = _ai_config(model="gpt-4o-mini")
    form = BackendConfigAdminForm(
        instance=backend_config,
        data={
            "gateway": fake_stage.gateway_id,
            "backend": backend.id,
            "stage": fake_stage.id,
            "created_by": "admin",
            "updated_by": "admin",
            "config": updated_config,
        },
    )

    assert form.is_valid(), form.errors
    form.save()

    backend_config.refresh_from_db()
    assert backend_config.config == updated_config
    assert set(backend_config._config) == {"encrypted"}


def test_gateway_admin_english_is_readonly():

    gateway_admin = GatewayAdmin(Gateway, admin.site)
    assert "display_name_en" in gateway_admin.get_readonly_fields(None)


def _gateway_form(gateway, **changes):

    form_class = modelform_factory(Gateway, form=GatewayAdminForm, fields=["name", "display_name", "description"])
    return form_class(
        instance=gateway,
        data={
            "name": gateway.name,
            "display_name": gateway.display_name,
            "description": gateway.description,
            **changes,
        },
    )


def test_gateway_admin_default_normalization_preserves_english():

    gateway = G(Gateway, display_name="Before", display_name_en="English")
    form = _gateway_form(gateway, display_name=" New  Default ")
    assert form.is_valid(), form.errors
    form.save()
    gateway.refresh_from_db()
    assert gateway.display_name == "New  Default"
    assert gateway.display_name_en == "English"


def test_gateway_admin_conflict_is_a_form_error():

    G(Gateway, display_name="Existing")
    gateway = G(Gateway)
    form = _gateway_form(gateway, display_name=" EXISTING ")
    assert not form.is_valid()
    assert "display_name" in form.errors


def test_gateway_admin_metadata_preserves_current_english():

    gateway = G(Gateway, display_name_en="Before English")
    stale = Gateway.objects.get(pk=gateway.pk)
    gateway.display_name_en = "Current English"
    gateway.save(update_fields=["display_name_en"])
    form = _gateway_form(stale, description="Updated")
    assert form.is_valid(), form.errors
    form.save()
    gateway.refresh_from_db()
    assert gateway.display_name_en == "Current English"


def test_gateway_admin_ignores_english_write():
    gateway = G(Gateway, display_name_en="English")
    form = _gateway_form(gateway, display_name_en="Attempted Override")
    assert "display_name_en" not in form.fields
    assert form.is_valid(), form.errors
    form.save()
    gateway.refresh_from_db()
    assert gateway.display_name_en == "English"


def test_gateway_admin_name_may_match_another_display_name():
    G(Gateway, display_name="Taken Technical")
    gateway = G(Gateway)
    form = _gateway_form(gateway, name="taken technical")
    assert form.is_valid(), form.errors
    form.save()
    gateway.refresh_from_db()
    assert gateway.name == "taken technical"
