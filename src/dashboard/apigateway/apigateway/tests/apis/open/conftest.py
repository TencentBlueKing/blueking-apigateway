import pytest


@pytest.fixture()
def ignore_related_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.open.permission.views.GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )
