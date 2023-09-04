from ddf import G

from apigateway.core.management.commands.migrate_resources import Command
from apigateway.core.models import Proxy


class TestCommand:
    def test_handle(self, fake_resource):
        fake_gateway = fake_resource.gateway
        fake_proxy = Proxy.objects.get(resource_id=fake_resource.id)
        fake_resource.proxy_id = fake_proxy.id
        fake_resource.save()

        command = Command()

        command.handle(fake_gateway.name, dry_run=False)
        assert Proxy.objects.filter(resource_id=fake_resource.id).count() == 1

        G(Proxy, resource=fake_resource, type="mock")
        assert Proxy.objects.filter(resource_id=fake_resource.id).count() == 2

        command.handle(fake_gateway.name, dry_run=False)
        assert list(Proxy.objects.filter(resource_id=fake_resource.id).values_list("id", flat=True)) == [fake_proxy.id]
