import json

from django_dynamic_fixture import G

from apigateway.core.admin import BackendConfigAdminForm
from apigateway.core.constants import BackendKindEnum
from apigateway.core.models import Backend, BackendConfig


def test_backend_config_admin_form_displays_decrypted_config(fake_stage):
    config = {
        "timeout": 30000,
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "weight": 1,
                "auth": {"header": {"Authorization": "Bearer secret"}},
                "options": {"model": "gpt-4o"},
            }
        ],
    }
    backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.AI.value)
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=backend,
        stage=fake_stage,
        config=config,
    )

    form = BackendConfigAdminForm(instance=backend_config)

    assert json.loads(form.fields["config_json"].initial) == config
