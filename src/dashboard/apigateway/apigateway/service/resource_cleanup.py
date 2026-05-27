from typing import List

from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion, OpenAPIResourceSchemaVersion
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.constants import ContextScopeTypeEnum
from apigateway.core.models import Context, Proxy, Release, Resource, ResourceVersion


def delete_resources(resource_ids: List[int]):
    if not resource_ids:
        return

    Context.objects.filter(scope_type=ContextScopeTypeEnum.RESOURCE.value, scope_id__in=resource_ids).delete()
    Proxy.objects.filter(resource_id__in=resource_ids).delete()
    PluginBinding.objects.filter(
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id__in=resource_ids,
    ).delete()
    ResourceDoc.objects.filter(resource_id__in=resource_ids).delete()
    Resource.objects.filter(id__in=resource_ids).delete()


def delete_gateway_resources(gateway_id: int):
    resource_ids = list(Resource.objects.filter(gateway_id=gateway_id).values_list("id", flat=True))
    delete_resources(resource_ids)


def delete_gateway_resource_versions(gateway_id: int):
    Release.objects.filter(gateway_id=gateway_id).delete()
    OpenAPIResourceSchemaVersion.objects.filter(resource_version__gateway_id=gateway_id).delete()
    OpenAPIFileResourceSchemaVersion.objects.filter(gateway_id=gateway_id).delete()
    ResourceVersion.objects.filter(gateway_id=gateway_id).delete()
