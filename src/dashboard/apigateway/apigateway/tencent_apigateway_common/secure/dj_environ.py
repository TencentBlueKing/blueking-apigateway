# -*- coding: utf-8 -*-
from functools import partial

from blue_krill.secure.dj_environ import EncryptedEnviron
from blue_krill.secure.dj_environ import SecureEnv as BaseSecureEnv

from apigateway.tencent_apigateway_common.encrypt.cipher import decrypt_with_random_nonce_from_base64


class SecureEnv(BaseSecureEnv):
    ENVIRON_CLS = partial(EncryptedEnviron, decryptor=decrypt_with_random_nonce_from_base64)
