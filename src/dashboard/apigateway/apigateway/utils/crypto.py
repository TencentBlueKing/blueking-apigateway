# -*- coding: utf-8 -*-
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
import base64
import hashlib
import itertools
from typing import List, Optional, Tuple, Union

from attrs import define
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import ExtensionOID, NameOID
from django.utils.encoding import force_bytes

from apigateway.utils.time import timestamp


class RSAKeyValidationError(Exception):
    """RSA 密钥校验失败"""


def get_public_key_from_private_key(pem_private_key: Union[str, bytes]) -> bytes:
    try:
        private_key = serialization.load_pem_private_key(force_bytes(pem_private_key), password=None)
    except Exception as err:
        raise RSAKeyValidationError(str(err))

    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


class KeyGenerator:
    def generate_rsa_key(self, length=2048) -> Tuple[bytes, bytes]:
        """
        生成一个新的密钥
        """
        # public_exponent: The public exponent of the new key. Either 65537 or 3 (for legacy purposes).
        # Almost everyone should use 65537.
        # more: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#generation
        key = rsa.generate_private_key(public_exponent=65537, key_size=length)

        private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return (private_key.strip(), public_key.strip())


class KeyValidator:
    def validate_rsa_key(self, private_key: bytes, public_key: bytes):
        """
        校验 RSA 密钥

        - https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#key-loading
        """
        expected_public_key = get_public_key_from_private_key(private_key)
        if expected_public_key.strip() != public_key:
            raise RSAKeyValidationError("public key not match")


@define(slots=False)
class CertificateChecker:
    key: str
    cert: str
    ca_cert: Optional[str] = None

    def __attrs_post_init__(self):
        self._x509_cert = self._load_pem_x509_certificate(self.cert, name="cert")
        self._x509_ca_cert = self._load_pem_x509_certificate(self.ca_cert, name="ca_cert")

    def check(self):
        self._check_cert_key_matched()
        self._check_cert_is_issued_by_cacert()
        return self._extract_cert_info()

    def _load_pem_x509_certificate(self, pem_cert: Optional[Union[str, bytes]], name: str) -> x509.Certificate:
        if not pem_cert:
            return None

        try:
            return x509.load_pem_x509_certificate(force_bytes(pem_cert))
        except Exception:
            raise ValueError(f"{name} invalid: unable to load certificate")

    def _check_cert_key_matched(self):
        public_key_for_cert = self._x509_cert.public_key().public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        try:
            public_key_for_key = get_public_key_from_private_key(self.key)
        except RSAKeyValidationError:
            raise ValueError("key invalid: unable to load private key")

        if public_key_for_cert != public_key_for_key:
            raise RSAKeyValidationError("key and cert are not matched")

    def _check_cert_is_issued_by_cacert(self):
        if not self._x509_ca_cert:
            return

        public_key_for_cacert = self._x509_ca_cert.public_key()
        try:
            # https://cryptography.io/en/latest/x509/reference/#cryptography.x509.Certificate.tbs_certificate_bytes
            public_key_for_cacert.verify(
                self._x509_cert.signature,
                self._x509_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                self._x509_cert.signature_hash_algorithm,
            )
        except InvalidSignature:
            raise RSAKeyValidationError("cert maybe not issued by cacert")

    def _extract_cert_info(self):
        return {
            "snis": self._extract_snis(),
            "validity_start": timestamp(self._x509_cert.not_valid_before),
            "validity_end": timestamp(self._x509_cert.not_valid_after),
        }

    def _extract_snis(self):
        # https://support.dnsimple.com/articles/what-is-common-name/
        snis = []

        for name in itertools.chain(
            self._extract_common_names(),
            self._extract_alternative_names(),
        ):
            if name not in snis:
                snis.append(name)  # ruff: noqa: PERF401

        return snis

    def _extract_common_names(self):
        return [attr.value for attr in self._x509_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)]

    def _extract_alternative_names(self) -> List[str]:
        try:
            extensions = self._x509_cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            return extensions.value.get_values_for_type(x509.DNSName)
        except x509.ExtensionNotFound:
            return []


def calculate_fingerprint(content):
    """
    For specification, see RFC4716, section 4
    """
    key = base64.b64decode("".join(content.splitlines()[1:-1]).encode("ascii"))
    fp_plain = hashlib.md5(key).hexdigest()
    return ":".join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2]))
