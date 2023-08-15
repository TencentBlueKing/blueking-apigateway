from ddf import G

from apigateway.apis.web.gateway.views import GatewayListCreateApi
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import JWT, Gateway, Stage


class TestGatewayListCreateApi:
    def test_list(self, request_view, fake_gateway):
        resp = request_view(
            method="GET",
            view_name="gateways.list_create",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) >= 1

    def test_filter_list_gateways(self):
        G(Gateway, _maintainers="admin1")
        G(Gateway, _maintainers="admin2;admin1")

        view = GatewayListCreateApi()
        gateways = view._filter_list_gateways("admin1")
        assert len(gateways) >= 2

        gateways = view._filter_list_gateways("admin2")
        assert len(gateways) >= 1

        gateways = view._filter_list_gateways("not_exist_user")
        assert len(gateways) == 0

    def test_create(self, request_view, faker, unique_gateway_name):
        data = {
            "name": unique_gateway_name,
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "is_public": False,
        }

        resp = request_view(
            method="POST",
            view_name="gateways.list_create",
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 201

        gateway = Gateway.objects.get(name=unique_gateway_name)
        assert result["data"]["id"] == gateway.id
        assert Stage.objects.filter(api=gateway).exists()
        assert JWT.objects.filter(api=gateway).count() == 1


class TestGatewayRetrieveUpdateDestroyApi:
    def test_retrieve(self, request_view, fake_gateway):
        JWT.objects.create_jwt(fake_gateway)
        GatewayHandler.save_auth_config(fake_gateway.id, "default")

        resp = request_view(
            method="GET",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_gateway.id

    def test_update(self, request_view, faker, fake_gateway):
        data = {
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "is_public": faker.random_element([True, False]),
        }
        resp = request_view(
            method="PUT",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        gateway = Gateway.objects.get(id=fake_gateway.id)

        assert resp.status_code == 200
        assert gateway.description == data["description"]
        assert gateway.is_public is data["is_public"]

    def test_destroy(self, request_view, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()

        resp = request_view(
            method="DELETE",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )

        assert resp.status_code == 200
        assert fake_gateway.id is not None
        assert not Gateway.objects.filter(id=fake_gateway.id).exists()

    def test_destroy__failed(self, request_view, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        resp = request_view(
            method="DELETE",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )

        assert resp.status_code == 400


class TestGatewayUpdateStatusApi:
    def test_update(self, request_view, faker, fake_gateway):
        data = {
            "status": faker.random_element(GatewayStatusEnum.get_values()),
        }
        resp = request_view(
            method="PUT",
            view_name="gateways.update_status",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        gateway = Gateway.objects.get(id=fake_gateway.id)

        assert resp.status_code == 200
        assert gateway.status == data["status"]
