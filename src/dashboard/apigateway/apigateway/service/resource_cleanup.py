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

    # 1. delete auth config context
    Context.objects.filter(scope_type=ContextScopeTypeEnum.RESOURCE.value, scope_id__in=resource_ids).delete()

    # 2. delete proxy
    Proxy.objects.filter(resource_id__in=resource_ids).delete()

    # 3. delete plugin binding
    PluginBinding.objects.filter(
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id__in=resource_ids,
    ).delete()

    # 4. delete resource doc
    ResourceDoc.objects.filter(resource_id__in=resource_ids).delete()

    # 5. delete resource
    Resource.objects.filter(id__in=resource_ids).delete()


def delete_gateway_resources(gateway_id: int):
    resource_ids = list(Resource.objects.filter(gateway_id=gateway_id).values_list("id", flat=True))
    delete_resources(resource_ids)


def delete_gateway_resource_versions(gateway_id: int):
    # delete gateway release
    Release.objects.filter(gateway_id=gateway_id).delete()

    # delete gateway openapi resource schema version
    OpenAPIResourceSchemaVersion.objects.filter(resource_version__gateway_id=gateway_id).delete()

    # delete gateway openapi file resource schema version
    OpenAPIFileResourceSchemaVersion.objects.filter(gateway_id=gateway_id).delete()

    # delete resource version
    ResourceVersion.objects.filter(gateway_id=gateway_id).delete()
