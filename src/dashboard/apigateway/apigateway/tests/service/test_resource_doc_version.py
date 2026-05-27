from ddf import G

from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.core.models import Release, ResourceVersion
from apigateway.service.resource_doc_version import clear_unreleased_resource_doc


def test_clear_unreleased_resource_doc_keeps_current_release_docs(fake_gateway, fake_stage, fake_resource_version):
    stale_resource_version = G(ResourceVersion, gateway=fake_gateway, version="0.9.0")
    G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)

    kept_doc = G(
        ReleasedResourceDoc,
        gateway=fake_gateway,
        resource_version_id=fake_resource_version.id,
        resource_id=1,
        data={},
    )
    stale_doc = G(
        ReleasedResourceDoc,
        gateway=fake_gateway,
        resource_version_id=stale_resource_version.id,
        resource_id=2,
        data={},
    )

    clear_unreleased_resource_doc(fake_gateway.id)

    assert ReleasedResourceDoc.objects.filter(id=kept_doc.id).exists()
    assert not ReleasedResourceDoc.objects.filter(id=stale_doc.id).exists()
