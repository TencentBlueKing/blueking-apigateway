import pytest
from ddf import G
from rest_framework.serializers import DateTimeField

from apigateway.apis.web.gateway.serializers import (
    GatewayCreateInputSLZ,
    GatewayListOutputSLZ,
    GatewayRetrieveOutputSLZ,
    GatewayUpdateInputSLZ,
    GatewayUpdateStatusInputSLZ,
)
from apigateway.biz.gateway import GatewayHandler
from apigateway.common.contexts import GatewayAuthConfig
from apigateway.core.constants import GatewayTypeEnum
from apigateway.core.models import JWT, Gateway, Resource, Stage
from apigateway.utils.crypto import calculate_fingerprint


class TestGatewayListOutputSLZ:
    def test_to_representation(self):
        gateway_1 = G(Gateway, created_by="admin", status=1, is_public=True)
        gateway_2 = G(Gateway, created_by="admin", status=0, is_public=False)

        stage_1 = G(Stage, api=gateway_1, name="prod")
        stage_2 = G(Stage, api=gateway_1, name="test")

        G(Resource, api=gateway_1)
        G(Resource, api=gateway_1)

        expected = [
            {
                "id": gateway_1.id,
                "name": gateway_1.name,
                "description": gateway_1.description,
                "created_by": gateway_1.created_by,
                "stages": [
                    {
                        "id": stage_1.id,
                        "name": stage_1.name,
                        "released": False,
                    },
                    {
                        "id": stage_2.id,
                        "name": stage_2.name,
                        "released": False,
                    },
                ],
                "resource_count": 2,
                "status": 1,
                "is_public": True,
                "is_official": True,
                "created_time": DateTimeField().to_representation(gateway_1.created_time),
                "updated_time": DateTimeField().to_representation(gateway_1.updated_time),
            },
            {
                "id": gateway_2.id,
                "name": gateway_2.name,
                "description": gateway_2.description,
                "created_by": gateway_2.created_by,
                "stages": [],
                "resource_count": 0,
                "status": 0,
                "is_public": False,
                "is_official": False,
                "created_time": DateTimeField().to_representation(gateway_2.created_time),
                "updated_time": DateTimeField().to_representation(gateway_2.updated_time),
            },
        ]
        gateways = Gateway.objects.filter(id__in=[gateway_1.id, gateway_2.id])
        gateway_ids = [gateway_1.id, gateway_2.id]
        slz = GatewayListOutputSLZ(
            gateways,
            many=True,
            context={
                "resource_count": Resource.objects.get_resource_count(gateway_ids),
                "stages": GatewayHandler.get_stages_with_release_status(gateway_ids),
                "gateway_auth_configs": {
                    gateway_1.id: GatewayAuthConfig(GatewayTypeEnum.OFFICIAL_API.value),
                    gateway_2.id: GatewayAuthConfig(GatewayTypeEnum.CLOUDS_API.value),
                },
            },
        )
        assert slz.data == expected


class TestGatewayCreateInputSLZ:
    @pytest.mark.parametrize(
        "check_reserved_gateway_name, data, expected",
        [
            # ok
            (
                False,
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["guest"],
                    "is_public": True,
                },
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["guest", "admin"],
                    "is_public": True,
                },
            ),
            # name length < 3
            (
                False,
                {
                    "name": "ab",
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                },
                None,
            ),
            # name length > 32
            (
                False,
                {
                    "name": "a" * 50,
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                },
                None,
            ),
            # name contains invalid character
            (
                False,
                {
                    "name": "a_b_c",
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                },
                None,
            ),
            # name exists
            (
                False,
                {
                    "name": "create-test-exists",
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                },
                None,
            ),
            # name startswith bk-
            (
                True,
                {
                    "name": "bk-test",
                    "description": "test",
                    "maintainers": ["admin", "guest"],
                    "status": 1,
                    "is_public": True,
                },
                None,
            ),
        ],
    )
    def test_validate(self, settings, check_reserved_gateway_name, data, expected):
        settings.CHECK_RESERVED_GATEWAY_NAME = check_reserved_gateway_name

        G(Gateway, name="create-test-exists")
        slz = GatewayCreateInputSLZ(data=data, context={"username": "admin"})
        slz.is_valid()
        if expected is None:
            assert slz.errors
            return

        assert slz.validated_data == expected


class TestGatewayRetrieveOutputSLZ:
    def test_to_representation(self, fake_gateway, mocker):
        mocker.patch(
            "apigateway.apis.web.gateway.serializers.GatewayHandler.get_domain", return_value="http://bkapi.demo.com"
        )
        mocker.patch(
            "apigateway.apis.web.gateway.serializers.GatewayHandler.get_docs_url",
            return_value="http://apigw.demo.com/docs/",
        )

        slz = GatewayRetrieveOutputSLZ(
            instance=fake_gateway,
            context={
                "feature_flags": {"FOO": True},
                "auth_config": GatewayAuthConfig(
                    gateway_type=GatewayTypeEnum.CLOUDS_API.value,
                    allow_update_gateway_auth=True,
                ),
            },
        )
        jwt = JWT.objects.create_jwt(fake_gateway)

        expected = {
            "id": fake_gateway.id,
            "name": fake_gateway.name,
            "description": fake_gateway.description,
            "maintainers": fake_gateway.maintainers,
            "status": fake_gateway.status,
            "is_public": fake_gateway.is_public,
            "created_by": fake_gateway.created_by,
            "created_time": DateTimeField().to_representation(fake_gateway.created_time),
            "public_key": jwt.public_key,
            "allow_update_gateway_auth": True,
            "domain": "http://bkapi.demo.com",
            "docs_url": "http://apigw.demo.com/docs/",
            "public_key_fingerprint": calculate_fingerprint(jwt.public_key),
            "feature_flags": {"FOO": True},
            "is_official": False,
        }

        assert slz.data == expected


class TestGatewayUpdateInputSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "maintainers": ["admin"],
                    "description": "test",
                    "is_public": True,
                },
                {
                    "maintainers": ["admin"],
                    "description": "test",
                    "is_public": True,
                },
            ),
            # input include status
            (
                {
                    "maintainers": ["admin"],
                    "description": "test",
                    "is_public": True,
                    "status": 1,
                },
                {
                    "maintainers": ["admin"],
                    "description": "test",
                    "is_public": True,
                },
            ),
        ],
    )
    def test_validate(self, fake_gateway, data, expected):
        slz = GatewayUpdateInputSLZ(instance=fake_gateway, data=data)
        slz.is_valid(raise_exception=True)

        assert slz.validated_data == expected


class TestGatewayUpdateStatusInputSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "status": 0,
                },
                {
                    "status": 0,
                },
            ),
            # input include is_public
            (
                {
                    "status": 1,
                    "is_public": True,
                },
                {
                    "status": 1,
                },
            ),
            # status invalid
            (
                {
                    "status": 100,
                },
                None,
            ),
        ],
    )
    def test_validate(self, data, expected):
        slz = GatewayUpdateStatusInputSLZ(data=data)
        slz.is_valid()

        if expected is None:
            assert slz.errors
            return

        assert slz.validated_data == expected
