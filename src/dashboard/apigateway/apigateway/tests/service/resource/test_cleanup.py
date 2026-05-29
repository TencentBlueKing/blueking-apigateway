#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#

from ddf import G

from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion, OpenAPIResourceSchemaVersion
from apigateway.apps.support.constants import DocTypeEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.constants import ContextScopeTypeEnum
from apigateway.core.models import Context, Proxy, Release, Resource, ResourceVersion
from apigateway.service.resource import delete_gateway_resource_versions, delete_gateway_resources


def test_delete_gateway_resources_removes_resource_related_rows(fake_resource):
    G(ResourceDoc, gateway=fake_resource.gateway, resource_id=fake_resource.id, type=DocTypeEnum.MARKDOWN.value)

    assert Resource.objects.filter(id=fake_resource.id).exists()
    assert Context.objects.filter(scope_type=ContextScopeTypeEnum.RESOURCE.value, scope_id=fake_resource.id).exists()
    assert Proxy.objects.filter(resource_id=fake_resource.id).exists()
    assert ResourceDoc.objects.filter(resource_id=fake_resource.id).exists()

    delete_gateway_resources(fake_resource.gateway_id)

    assert not Resource.objects.filter(id=fake_resource.id).exists()
    assert not Context.objects.filter(
        scope_type=ContextScopeTypeEnum.RESOURCE.value, scope_id=fake_resource.id
    ).exists()
    assert not Proxy.objects.filter(resource_id=fake_resource.id).exists()
    assert not ResourceDoc.objects.filter(resource_id=fake_resource.id).exists()


def test_delete_gateway_resource_versions_removes_version_related_rows(fake_gateway, fake_stage):
    resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
    G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=resource_version)
    G(OpenAPIResourceSchemaVersion, resource_version=resource_version, schema=[])
    G(OpenAPIFileResourceSchemaVersion, gateway=fake_gateway, resource_version=resource_version, schema="")

    delete_gateway_resource_versions(fake_gateway.id)

    assert not Release.objects.filter(gateway_id=fake_gateway.id).exists()
    assert not OpenAPIResourceSchemaVersion.objects.filter(resource_version_id=resource_version.id).exists()
    assert not OpenAPIFileResourceSchemaVersion.objects.filter(resource_version_id=resource_version.id).exists()
    assert not ResourceVersion.objects.filter(id=resource_version.id).exists()
