from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.core.models import Release


def clear_unreleased_resource_doc(gateway_id: int) -> None:
    resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
    ReleasedResourceDoc.objects.filter(gateway_id=gateway_id).exclude(
        resource_version_id__in=resource_version_ids
    ).delete()
