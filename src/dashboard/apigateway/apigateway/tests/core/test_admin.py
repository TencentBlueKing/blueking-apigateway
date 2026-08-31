from django_dynamic_fixture import G

from apigateway.core.admin import BackendConfigAdminForm
from apigateway.core.constants import BackendKindEnum
from apigateway.core.models import Backend, BackendConfig


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
