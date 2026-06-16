# -*- coding: utf-8 -*-
from apigateway.components.bkpaas import get_paas_apps_by_username


class TestGetPaaSAppsByUsername:
    def test_get_paas_apps_by_username_sends_tenant_header(self, mocker):
        mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
        mocker.patch("apigateway.components.bkpaas.gen_gateway_headers", return_value={"X-Gateway": "1"})
        mock_http_get = mocker.patch(
            "apigateway.components.bkpaas.http_get",
            return_value=(True, [{"code": "app-001", "name": "App 001"}]),
        )

        result = get_paas_apps_by_username("alice", "tenant-a")

        assert result == [{"code": "app-001", "name": "App 001"}]
        mock_http_get.assert_called_once()
        _, data = mock_http_get.call_args.args[:2]
        assert data == {"username": "alice"}
        assert mock_http_get.call_args.kwargs["headers"] == {
            "X-Gateway": "1",
            "X-Bk-Tenant-Id": "tenant-a",
        }
