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

# for dev env, use username/password to connect etcd
# raise error: "Established channel does not have a sufficient security level to transfer call credential."
# so we need to patch the __init__ method

# reference: https://github.com/kragniz/python-etcd3/issues/2713

import random

import grpc
from etcd3 import etcdrpc
from etcd3.client import Endpoint, EtcdTokenCallCredentials, MultiEndpointEtcd3Client, Transactions


def patched_multiendpointetcd3client__init__(
    self, endpoints=None, timeout=None, user=None, password=None, failover=False, uses_secure_channel=False
):
    self.metadata = None
    self.failover = failover

    # Cache GRPC stubs here
    self._stubs = {}

    # Step 1: setup endpoints
    self.endpoints = {ep.netloc: ep for ep in endpoints}
    self._current_endpoint_label = random.choice(list(self.endpoints.keys()))

    # Step 2: if auth is enabled, call the auth endpoint
    self.timeout = timeout
    self.call_credentials = None
    cred_params = [c is not None for c in (user, password)]

    if all(cred_params):
        auth_request = etcdrpc.AuthenticateRequest(name=user, password=password)

        resp = self.authstub.Authenticate(auth_request, self.timeout)
        self.metadata = (("token", resp.token),)
        # NOTE: only use metadata_call_credentials when using secure channel
        if uses_secure_channel:
            self.call_credentials = grpc.metadata_call_credentials(EtcdTokenCallCredentials(resp.token))

    elif any(cred_params):
        raise Exception("if using authentication credentials both user and password must be specified.")  # noqa: TRY002

    self.transactions = Transactions()


MultiEndpointEtcd3Client.__init__ = patched_multiendpointetcd3client__init__


class Etcd3Client(MultiEndpointEtcd3Client):
    """
    etcd v3 API client.

    :param host: Host to connect to, 'localhost' if not specified
    :type host: str, optional
    :param port: Port to connect to on host, 2379 if not specified
    :type port: int, optional
    :param ca_cert: Filesystem path of etcd CA certificate
    :type ca_cert: str or os.PathLike, optional
    :param cert_key: Filesystem path of client key
    :type cert_key: str or os.PathLike, optional
    :param cert_cert: Filesystem path of client certificate
    :type cert_cert: str or os.PathLike, optional
    :param timeout: Timeout for all RPC in seconds
    :type timeout: int or float, optional
    :param user: Username for authentication
    :type user: str, optional
    :param password: Password for authentication
    :type password: str, optional
    :param dict grpc_options: Additional gRPC options
    :type grpc_options: dict, optional
    """

    def __init__(
        self,
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
        # Step 1: verify credentials
        cert_params = [c is not None for c in (cert_cert, cert_key)]
        if ca_cert is not None:
            if all(cert_params):
                credentials = self.get_secure_creds(ca_cert, cert_key, cert_cert)
                self.uses_secure_channel = True
            elif any(cert_params):
                # some of the cert parameters are set
                raise ValueError(
                    "to use a secure channel ca_cert is required by itself, "
                    "or cert_cert and cert_key must both be specified."
                )
            else:
                credentials = self.get_secure_creds(ca_cert, None, None)
                self.uses_secure_channel = True
        else:
            self.uses_secure_channel = False
            credentials = None

        # Step 2: create Endpoint
        ep = Endpoint(host, port, secure=self.uses_secure_channel, creds=credentials, opts=grpc_options)

        # NOTE: here we pass one more parameter to the super class: uses_secure_channel
        super(Etcd3Client, self).__init__(
            endpoints=[ep], timeout=timeout, user=user, password=password, uses_secure_channel=self.uses_secure_channel
        )
