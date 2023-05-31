#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from pprint import pprint

from django.core.management.base import BaseCommand, CommandError

from apigateway.controller.crds.v1beta1 import custom_resources
from apigateway.controller.distributor.key_prefix import KeyPrefixHandler
from apigateway.controller.registry.etcd import EtcdRegistry
from apigateway.core import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-g", "--micro-gateway-name", default=None, type=str, help="micro-gateway name")
        parser.add_argument("-a", "--api-name", required=True, type=str, help="api gateway name")
        parser.add_argument("-s", "--stage-name", required=True, type=str, help="stage name")
        parser.add_argument("-n", "--name", default="", type=str, help="Name of the resource")
        parser.add_argument("-k", "--kind", required=True, type=str, help="Kind of the resource")

    def get_resource_type_by_kind(self, kind: str):
        for type_ in custom_resources:
            if type_.kind == kind:
                return type_

        raise CommandError("Resource kind not found")

    def handle(self, micro_gateway_name: str, api_name: str, stage_name: str, name: str, kind: str, *args, **kwargs):
        gateway = models.Gateway.objects.get(name=api_name)
        stage = models.Stage.objects.get(name=stage_name, api=gateway)
        micro_gateway = self._get_micro_gateway(micro_gateway_name)

        key_prefix = KeyPrefixHandler().get_release_key_prefix(micro_gateway.name, gateway.name, stage.name)
        resource_type = self.get_resource_type_by_kind(kind)

        registry = EtcdRegistry(key_prefix)
        resources = []
        for resource in registry.iter_by_type(resource_type):
            if name in resource.metadata.name:
                resources.append(resource.dict())

        pprint(resources)

    def _get_micro_gateway(self, micro_gateway_name):
        if micro_gateway_name:
            return models.MicroGateway.objects.get(name=micro_gateway_name)

        return models.MicroGateway.objects.get_default_shared_gateway()
