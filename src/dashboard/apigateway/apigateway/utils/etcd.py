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
from typing import Any, Dict

import etcd3
from django.conf import settings

from .etcd_monkeypatch import Etcd3Client


def client(
    host="localhost",
    port=2379,
    ca_cert=None,
    cert_key=None,
    cert_cert=None,
    timeout=None,
    user=None,
    password=None,
    grpc_options=None,
):
    """Return an instance of an Etcd3Client."""
    return Etcd3Client(
        host=host,
        port=port,
        ca_cert=ca_cert,
        cert_key=cert_key,
        cert_cert=cert_cert,
        timeout=timeout,
        user=user,
        password=password,
        grpc_options=grpc_options,
    )


def new_etcd_client(etcd_config: Dict[str, Any]) -> etcd3.Etcd3Client:
    """
    Create a new ETCD client with the given configuration.

    Args:
        etcd_config: ETCD configuration dictionary with keys:
            - host: ETCD host (required)
            - port: ETCD port (required)
            - user: ETCD user (optional)
            - password: ETCD password (optional)
            - ca_cert: CA certificate path (optional)
            - cert_cert: Client certificate path (optional)
            - cert_key: Client key path (optional)
            - timeout: Connection timeout (optional)
            - grpc_options: gRPC options (optional)

    Returns:
        An Etcd3Client instance
    """
    return client(**etcd_config)


def get_etcd_client() -> etcd3.Etcd3Client:
    """
    Get ETCD client using default settings.ETCD_CONFIG.

    This function is kept for backward compatibility with existing code that doesn't
    specify a data plane. Use new_etcd_client(etcd_config) when working with
    multi-data-plane configurations.
    """
    return new_etcd_client(settings.ETCD_CONFIG)
