from apigateway.biz.gateway import GatewayHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.core.constants import GatewayTypeEnum


class TestGatewayAuthContext:
    def test_get_gateway_id_to_auth_config(self, fake_gateway):
        GatewayHandler.save_auth_config(fake_gateway.id, "default")

        result = GatewayAuthContext().get_gateway_id_to_auth_config([fake_gateway.id])
        assert fake_gateway.id in result
        assert result[fake_gateway.id].gateway_type == GatewayTypeEnum.CLOUDS_API.value
        assert result[fake_gateway.id].allow_update_gateway_auth is True

    def test_get_auth_config(self, fake_gateway):
        GatewayHandler.save_auth_config(fake_gateway.id, "default")

        result = GatewayAuthContext().get_auth_config(fake_gateway.id)
        assert result.gateway_type == GatewayTypeEnum.CLOUDS_API.value
        assert result.allow_update_gateway_auth is True
