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

import pytest
from ddf import G
from django.utils.encoding import smart_bytes

from apigateway.biz.gateway_jwt import BkCrypto, CustomCrypto, GatewayJWTHandler, get_jwt_crypto
from apigateway.core.models import JWT, Gateway

private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpQIBAAKCAQEA2zPAhhBfsTKXxMLzXSg8kHCDzWgox38JpcivdPwabSswdJow\nZO4PC9z/6qSfEApkh15v3nZCqJWETQ5SADyepYT2RaqqB3Vb3a/g1s9C4ehZF4Fl\nWesQ9N0jgfPDruvvmlanb+nb2jSFjUB9cenLF1GLyl+COc4iad7rpgTqert+18PW\nZhlfS72x+sApW8rryDwBUgryjWygyg1Cv63If9+SntwRrKsc9PSwMmjPFClePX/b\nRyEbZvmOonKdkXlzSy5ovdba3ph5XaJhYxWZGTIuL8K7zQpNfHXa8+PJQM6LKw4e\nri6lT46MCKWvMPulcPOjLZGB4SZcEEZGs4PdbQIDAQABAoIBAQCiWwGFCsmluGBa\n9z5DyJKbNQsab8SMhpaBuVPjpPp501xvcOjZSM3SLp1KkSXTPq9Y6GSZdCRJM30r\niajIzh1/YSz7Sr3nClDBsQwqbpcONgcO9uM3p3kGtGghT4innc75FKetp5wUUYR9\nq79+SPkIy3hrqzQMVpZ8rgUCEXAO+EK4WVls+HmGJIpREyCUCeJNNwzfHk3yTnrA\n+rgYFLGfDE+FbpfGvfsQ98Fp6brUF8RqWRCChnE9OqtCp91ro5gTGlYAVU8iIXGr\nw67HQawGvf4xzErTNFBh/Emqhe4lLAhHipLxU76fuZwdLZXr0v+S8xrKvba0hHvv\nHwlKsUjNAoGBAP+8Sri9uzgw2uog4mw/45VA70RBf+VJlkmMTG8AedFg8oyMHJZZ\n5KtUlTUzXmP2iFgmqe1Jqfj0E0CHQubmxMtNDjlTHQFPBdrAg7IiOZZgv4w22457\njARf67fNEHrrk3CmEsB6iqCNrlQQDESfVNJ/AD++IVzJ72pkkHjXbCIXAoGBANtt\nyaOJ/Z3oH9LT+mjPa1NupdHDhbbcDizXjEhwJgHDzyeYb22gEhPnhiQvOONXHzA8\nz3hKHyQTLdEGCZPfTrKUN/GM9QlJiEtajQm0yalInWNzji1DUlXMg+p8FHuE492i\ndrdrsXpSCVWyJERMp1wejGgPssyb/+tL88feugMbAoGBALvihW9HDcaRtjQvJsrr\nAXRFecRG7wTw1HaCmiEvU1BuDqUNx2766lKp2Nl2PRHqLW++MDgCV9tszrwo5BEq\nWEkY+qtJEdVFToLRz6/PD0oZGIGWSCZdRJhuNIscINB+RRuNF9fL8A9XKE3gYHMG\nMFZaMj+im3ZFch1TdwUhF/PPAoGAHmJ2gHnUL7B776LA0xCdyQDSX1iWxHp2UAlM\n+J7m9Gmb3tzB2UlIF4+AyLPtSbW/sNtK01pYM5OgTYhrfRl3+UyC7qTZLX8MK3sP\nep+ZKSLQAHx43JWs6gqW3bpuz6fYMdGUZNO50LlZZ49ybC69Igls4eACn0ieyINM\n74lM8q8CgYEA5NDOGMs4l474Womj4lYX0O0agQwCOaaZCPpambuiXgndbeFSQTj/\nwCnUQQCxsIeLuxXRuHCsaEeg/VEWYJ91du5ftVqZsSG0VFUvCOk84e9pacVl3rZL\nviC9uUwpwnmKWxOF7FmR8sjNTR91q6shzQWuaOw0WcmymaL+MySzvWo=\n-----END RSA PRIVATE KEY-----"
custom_crypted_private_key = "fb635e8543dde12366bfa92ef24fbf82957b0610faabeb4ad5e55e1168177f30340739a37e657f671519df5cdf222f2d7749b3f54aeacc5dd2636128bef17e469d37df47c2f5fc068fbd22e020c8d024bc6459a63257b8fded58e84a046050693ac0fa74632292a696c0a38dc3e186af76c2941a01b5469256b0bf25745572dc75f9a871269a4420763ac8eb1a7fe1875d66d8047b8a8b355702b7dd81a999a1a7dada12fc31615416db163580e687bc40a9af61994a506ca75ea719dc0c53d48582bc62d44008d7d3d24871294d1d2b75330c4cba6878efaadcc3c55a79b83cb9430eea089ec402ba574535b397cb755d98e8443783f20e76a6786f083169169072a58158092dd03ea923f552c680620e44050475abcfc0ac443b2956895a86daa888a0f965a29364e31ef616b37afc6f6fcb42963c3e25fc8b4bf874e76534d4eee6364aea98a86f9516ca70c16439175e33d58e603077ffcdc7359c537aa5fa4177e1293f1ac9e981c8c4ced8f142ede7ef14a60b0a248cee8a789ffd2aeb0235eb583da8e2ca340e95b6b42ba295ac956ca091f804d1d3bcc310df13689951a86a3cf2a788b15c56f8bda0b6530da9c4e18a3c3f6ed22bddc2a79694ad7766b76224e73749d99fdaaf611825fa78b92c12f7c9d03daafcd23c1be193c0d3e5d2850d9ee4db9f82713337077e2668041ff3420a55683ef28cdb8e8316bea108407fd87210ff97fa4a1b4c3c2eaa45f58b06a420c2833f3b991c634142a2bc48af8df393bac4eff01e11ba2d8b484f4e36b90a98e1e191b9f60d195787cb1149f34360929149121c1ae0660b3bb943c5f3e689c3d6419225eb3f4bb5d21a8ca83f76035fc71b5ef1e6b69729d019ce48c2c88da604911522b1f78ddc9b1b9385eaf90abb62fd0ae90dbb20917e74456098e2b5cb5d37d97086cc67ead23deb15a1b201f6c57a570e41852cd54ef36506c599b7aa1f69a93482307e6388cb343790c32eafcb4149dccb2cc1ff32e2c61064a11d44ac1f6f65c750d8a41c66cd207881aa0c26e9b7dff6d3c62eeb025379803a733e7dff9b20832fad54fe8b020ab9c9d3ac30917c11b355658d360d001b9fd3b007ffb2372b7679c6b4a083caa42748aa41bb688f0e772196a7fb1a1089470bbd320aa326e2dbc135bf50ecba9a95004a534e99a6c56becbb9c570284b2bf6747a3c8212b3f2c2ac484218ec0f745545b4c2f9301157bcdb1c54718698ceb03c3fa19b522d45ad2278bf6feaf327a17cc4d0d3a08a8353e963505fa906f61fa7d69f1187d679e23d292f1c2c51e52ad2b23719d664b1a9b2fd8e2ada3d859a355f18bd7d335b71c2845eb65b9a77cf76f577035b7a0424ef1cf420d3d610b431108124cbe244194a492e9a1ab2c6c3f8e80992fc3c652cb90e00c5b9e1b460dc1ad13397cdee232ca762ecaba7fd1997e405c090b5b40a676181b3d4e0a6bd74f500039cb65b677d6a5352b2797e01afd10d549ff448ec374fd48aec497284fb49a4d42ac9dbbce2a614135cdbecc08bb226dadd1cf1eef97d8ed5e2ed7923a61b15a67e0ac34ad3c41769edbc944b7ce71edf994082cd7d45080384cc08f064654ff808a550c2355e227d577030ea824142beba18d5b1ed1368480bc77fd189492d38417f0d778b0c97c07679ebfb20866a0db5f80cb78e4c0fc0d72558f349f797a8864792c041ba9c8c9a0e91e53a90378191a31352494721022fe2f819efa19a1b44ac01c48c906ebd2d4bbff770579e38f14fd2a64ae537619ccf4b900d5074cb03481067ef05c43244fd131b0654658bf6fb788852812887703baf94901b35f3bcac33dd804fd9c918509fc2e8dcaca0e306dc5b7f6a51fdf5a3f458ab99fcb8d21e2a254d2799729d831b138e35d29d74969b4017e5e634cdab59271f021d1fa6a3bef3f12a309fd77dcaee24a3f9d5da1ad5afbc96c4bc044179b495556ddde706358c6931d3cc0ddca4254585d3b5e411beebdd3adc6fb49a10abce80c171595046268c1027b3c2b7222891d829f17dec06c792f582e7ae7cc66e9e7128f45a106cb3065bbefac78bbf747fd681c1f9f8c47de9c4776ba580bfe0c719a37092189b976ea4e6e0f796ebaed826470e0721ac2e6572583253705ed70d09e63afb4ab47f15beaee5c81fd9d77557effb08ba208b4d64ca03a79f798e3a0e469d015cc339e1f9c18834cda88b86a7f07c253d423f0650ea9de58d8d75e98a445e7f0513beb421a5b7133f7e8e7c45306ce39924a69165c9e5036266c7c4530d2563d07247d2b72b43ab142240a5bab3cc75bdf8a046bdb21053a4fab2b297c426acc91dea9bd3fd6a0d38ea3377c2276131f5a891adc777a0374a2e218ffc16253a2eb2b3663ba7d"
custom_jwt_crypto_key = "OWtSMTM0MG4zVDA1dnNpRGpGa1B6SnExYzFjQ2ZXMTM="
custom_crypto_nonce = "q76rE8srRuYM"


class TestCustomCrypto:
    def test_encrypt(self, settings):
        settings.JWT_CRYPTO_KEY = custom_jwt_crypto_key
        settings.CRYPTO_NONCE = custom_crypto_nonce

        crypto = CustomCrypto()
        encrypted_text = crypto.encrypt(private_key)
        assert encrypted_text == custom_crypted_private_key

    def test_decrypt(self, settings):
        settings.JWT_CRYPTO_KEY = custom_jwt_crypto_key
        settings.CRYPTO_NONCE = custom_crypto_nonce

        crypto = CustomCrypto()
        plaintext = crypto.decrypt(custom_crypted_private_key)
        assert plaintext == private_key


bk_crypto_type_classic = "CLASSIC"
bk_crypto_type_shangmi = "SHANGMI"
bk_krill_encrypt_secret_key = "PIMCuSRiVqBg5eSzQqZZrOhGFSUtrlS-8_JlIpjHt0A="

bk_crypto_classic_encrypted_private_key = "bkcrypt$gAAAAABlXxCuBB9mZrduIpc6ZRsaHHTjtlOfN5v7vMfP6e7-3Jc_ythnrJ15fOtFzqUZi507yJEatQTgah4oTYBPvI9n9slLQuN7kpznTRbVYq0uHR-6PEwteQSt5_6p-NdkgClviuydWH_07TyY5GBuUzy9fkff2LYGPRLP2373wVJ2fS84qsYpTU-3LVxlye_r5FXl0mdhcfs8HQVYQlwbzM6_SeLT1x-WilF4VozgKbsQT3SUpyBH6rVBw4wwJdxlTQzcHFfO1iKO_TZxXnExiHqNbZ2uC2z3jqiIxPBXND2Eoii8lhFcxMeTXJyoIWqQy7_FhCoz-YrPA6kK5_FfM7MwpTmtKOixoZOv1Xj-ZYYZsNoIXepvKyiKsnC-pB1iPa_-4tAwrYUqFDJXQnsvgn__uuAN4hxVS4XkXzL4832GjAISiW-sVoE6yymkhtR-DJYb2zTzfZCWPlCwmu9yXtU_hpnGmRNtgXC3hPDHtLFZPCh8g-JCaOJBl5MZa0206IQYclIYibaDXT93026sn_krMIsluNombat2PRh8sG5sTZoD4elTIIy8adT48TjYnwwweI1Uyc7bw_Zvv93DSu7Mn40gr17U5PqAdY2iO8aXVZ-G1UycxWO-15vThLLm1GQk7Q3Md1vMxaJQYsasQ4QggoZQ7eYqemHIkg_-0BOjvDA0LFMBWNslLw5ulyBeIhArR9mrWbuSfWX9LjFon1iY0JT6PgBfSgF-jnGGJdEBwbbBgQSssCnK5RF19uciJGMwhO0cl5PdrAGcwcKnAdPlm6bfbqnKj8B7QDl6QjUJ_IWnkh4oKLC_FgG_DZQWWNtSkA6SyEAkFjWuXl7u6kxS_INqL0RHcxnNvtoTAiKHTIQaULezJGGh_kg8LzMZ4kDxRE8R2Lm_aIfj3GsFvp8ZoYVPIpekyHle2lEAY23qnSrg6bWKvRik-CTes7Nhz_QssKYf62pkSIBRP6UyGkjwNUi_wNaPbmgS3JSb75T_8yGxF8_Ond4XsVc1fOhubTkO2vSmYYrXyirL4WjBO4KBoVdvha6qxmxnVsujp5atBS_otVFUhQbfGT5OrSClclDacmm5AWLaWEWAII2fG7GdRKVgHg1MgYcHlGrFaZlsagFBiv_lKmLTkP_t4LZ45Uoj4KpJLAonBEMpoVIT-qzfbj4QbnGnKaLq-jJAFyuSoD-srrTvfvJ_PHZ8zr5M_XBtl-goIxdoA_o0qCh5TGIBI_fL7OsN05sev9nzZ3nVBPUT3vkGnaezfdWTVAMs2kRtzv_c5kyHcAor4tISdPW30Cko6GvABlfR7MjwujcnL47ZdEj6w7VpYylW59m0KcDMR859o0ndpA-T2HJW3QLfLlav5eri4ItyBgTDXB4wQMsOZGMAFXNOpP99ell5ZUv_Lo7gfJsovU2gtEcDxhZ4ZiIHs1i_SJDn1j9jqWP02QE0VrXe7IZA_J895S3aAxI05kHqGbXgULi5ezuL22N_-B7j-jhKg6BR1KZo9Va_FfnxoTbS6-Wq1se8ln5p7w_4vI7y9HDII450qZhbzKvVUxZksYqCkTEMcnfFwudElCwGbUob0OvUTYpQl3FoGByT6SRmK-gFXUiXDJhpVBS_CiZX5Eu3BGClY7Z1GTrCQBZhdUlXCeIhgnbhOc2wsVwilcAk7bBqfcE4rCo2iI4B9u1dhkg4mkWiFTkqPRa9ymLyLaHLHlGjmInrKNpNebAfDPJk2WvUE20O0xI4PnAmu3OQhm0YjMgX2RvJ8FNzWU-aGor_IzSTKWJH60GxmX0lYMLHmHS8lqpgHcKaUwNE_vjoKXsywCUc8Vp2UeMY-tC8fgsThgd6WmSXNPOJ0LE1XXbkF0m98M23xZhGRrGdGyHFEWy-J-HoHFmAz6YybiZHM88MYnwjp8D43K2ZEu0Voh0tdPP-pYi_K40SCHTG07YIPk1m0NXqnpy65V4wiLTvXOA8coK-kt6BxR-1FioQzoCltFBeLnq3zgyZVqDl_2DfspG8_MmQeOe3gZGkoWEiHZqh8iOH8zt-tRR1M2OMP5oIqZaezWE6viKFSyjvPoMzddli8ws-Et6soF4xJ4CGz48oJ90kuzdfTNaLEefNROS2WZSpyMb4vaw21nXxNtQCDKFcRxMD47cTa64qxmD_yXDgBE2AfjlT1QVQb-9tiht9TyI_DXO_Q-sF_YehFBdttpZgaGAKIBdR1DhOFT7LhHb8BX2QDFl5PDDVpVsTJOxIxB9USzXC_i1nd3Xqi9CHlY_bai2sVALgPcUx3DeEiyFaYHywhCLBaDVWZ-Yui1N2"
bk_crypto_shangmi_encrypted_private_key = "sm4ctr$BU6CddeSPU0vbSC4rv+pP+koYrM9n8QaWMCAsw+8mN/QLhCS4SgAcBqZUKyuMMyKQoW+ZS7wBNKSBnLith0RZv9RRNvcqdAyEnV/6wonf5ATISnQsQFPbg+G1nHBmzB5usVVgS1/T0OnQN8HUEHJTSK3kcVnEtAr9nFGYMyFEBHih9Kqy3Q04V+UVGv0brR0RJuFjTR/RTiJLkhcyBzVpSl/Ge3GdLdgm1r2mYlcE0iB470uth3djfF9vBROiO5DWtdnTu6+teMjaS0p+jTajgFPIAD8ReIj0aRD8+UL8+TZyTa6BnAJuol3bpoISID6+UsXMKGsu2INt6APz1WWeHfnZG8jOy99MdK+r6d4ZGFYp2nxf0FaN1SL0eR7jA/PIIWQPKJWWF86/1fxvDIb0tbUKXjIWd4Uepystv+FNtAWwR5RuwqaOu9lNKihAKq3nw/4TXVrKI0RVGi0vwt+nY0qWZXX0hCE3rFI2P4hSCcCjqpn22A9b5wewtyFCE22S5SVqSHOOYgL46SN0BtNx074JQ8diFETMxwRmADh4wCdIfAWKUn75zs3MjAWU5bHpZqmsnSl6TTpqyw2D+1MH7ulMqZlEWbQaBvJRPIb30cu1NJMv+CxnabbbWIn+6vaQOHQ+8m3HOjW+AEoTEQ3ytIidh0LrhAR5O+Nv1Y8S1rPO8VAIAVjTxAYM/NOPRkMHvKhE+kHZuWILn0ARPMhH/d3bBW2IXt1SRfaM/XF23f84K3CJi32a047ZI+NINy3PumsPVeL049ERwkZO+GHuANWpaixb2X41Gomcy2/QNc/yFZ98KWhCfLnm8NHco+kkNaWAS5yLeuoiVhI7wAPoBKtJo78lQMQcTSX1b7L0rW8y6UR5YkjWViFu+18BfuJ5HsYgD65nBzfZCRBBEjb3dnkeqQFm+AEC2xfUJR+lpUhbQHIOHPColveMi2n8rh/k4brXlsRlmfsk65gXRabVXlV1DReOvxLeZwWKiqet3N9khLAW4UnpbmC7cR3qdVpjHcjq6yAFuZ51W24OSbKV+sgUW8flSkXsjV5ihR+SCKzQ9m/Ve8MI0tz2HQfxVAlHKWwr1KBox+XD7cCNvBHNbHjSWVg/jD3FoVmGb9wdlcyyV+iToW+eZEkcDIug5WL7CChvlQE8CsjMSafKOH8sz7VwVDUOp8iflTBROwg7FIllha+ZH2brp0dR0r1ttkE9NYHcCsTaSAV+YZKpDo9RJnYKXA7aVemfN5ZYaozB5MRleoHENgo7EGqXogDvjYY4yMpi840tfvfsOB4pnxesEVZDfNFYp7ExQwFxQM6gMAA0szIBfaTEJQ3R/GQvzm78ZXhrhvHJFVfRLZDMRKSS+mOx4A9AtawVObIyptCT0YxsP43HTDifHQ//aotKPpaMqSb+LOZ2Inocb8DsfZQdVvRxpBfRa/zW/49mItyXBVtCi+em0RkT6PypHm+S9VxpakOCu7etacVQHbhxYXmU9AVg+5R2ugikTJgSrFleOSidELizowt3Ng/ZQdCQz9jullzCjBlT1/1dkR3IfCh2M/IuH/xkQws41b/CdPuZgzIlZQvvomqXm+fXuYDv8FM9g4HnoRSTpa/DStxRcr6NhS7OPmKBznzMhoxhW2KtD4uQaU/2JCSIdC7cz9UkX2EDfak0ZalKLQuGEt/mKbHZ4lPADzp425NUCMRanoh/yWYiYmoPMLd/OSNL+JtySJG6G2G+m4XU4I7CEBGdXqHGwVsI0U6eKDrFxtEIvqqoJErfDRFAttmLVg0mTJkCwBJGRcVpnT3ENEzzPRcw2PBrikb+JH749LlkxM1erEknFko6Q8WQHvshNdRaRPUV9a7fZ6dSr0WkkZaA3VZRYpX55toYu1dYrSBGkTysEKXajbqfdrZq+Y11LV3XsZaQCuwBqTQ5suC1pu+n8YEBAD/bGuGhKOGzEu5I3sD7jbPt/+dP7VdLMMBu3GXhZijNEAJ1/vdus/E9alAdKNZXp3gDIE7BgxS6aNOgatlGdeMalufI+M3jQtXjFE5gkj/JHJgMdu5vhZhUsDJalYmXm3J5EZ5diZWi0fbte1xQPIpwYPvacVmva59pnD92QUoWc5hLbI2hQcr8zPZJc+LdSLOn/XLIT2NBi02c+W4s7G7MzJFCVikFh1rcMMWz8o2yb25OV/aj55d/WjgM5fhQvyqaER5uWGxxBMTxvbje78BHcSnLYfaCR0qbRyEkPXdGXNQkKgCf7IYEuYOYHZaum4="


class TestBkCrypto:
    def test_encrypt(self, settings):
        settings.BK_CRYPTO_TYPE = bk_crypto_type_classic
        settings.BKKRILL_ENCRYPT_SECRET_KEY = bk_krill_encrypt_secret_key

        crypto = BkCrypto()
        encrypted_text = crypto.encrypt(private_key)
        # each time the encrypted text is different, only prefix and length are fixed
        assert encrypted_text.startswith("bkcrypt$")
        assert len(encrypted_text) == len(bk_crypto_classic_encrypted_private_key)

    def test_decrypt(self, settings):
        settings.BK_CRYPTO_TYPE = bk_crypto_type_classic
        settings.BKKRILL_ENCRYPT_SECRET_KEY = bk_krill_encrypt_secret_key

        crypto = BkCrypto()
        plaintext = crypto.decrypt(bk_crypto_classic_encrypted_private_key)
        assert plaintext == private_key


class TestBkCryptoGM:
    def test_encrypt(self, settings):
        settings.BK_CRYPTO_TYPE = bk_crypto_type_shangmi
        settings.ENCRYPT_CIPHER_TYPE = "SM4CTR"
        settings.BKKRILL_ENCRYPT_SECRET_KEY = bk_krill_encrypt_secret_key

        crypto = BkCrypto()
        encrypted_text = crypto.encrypt(private_key)
        # each time the encrypted text is different, only prefix and length are fixed
        assert encrypted_text.startswith("sm4ctr$")
        assert len(encrypted_text) == len(bk_crypto_shangmi_encrypted_private_key)

    def test_decrypt(self, settings):
        settings.BK_CRYPTO_TYPE = bk_crypto_type_shangmi
        settings.ENCRYPT_CIPHER_TYPE = "SM4CTR"
        settings.BKKRILL_ENCRYPT_SECRET_KEY = bk_krill_encrypt_secret_key

        crypto = BkCrypto()
        plaintext = crypto.decrypt(bk_crypto_shangmi_encrypted_private_key)
        assert plaintext == private_key


class TestGetJWTCrypto:
    def test_get_jwt_crypto_default(self, settings):
        crypto = get_jwt_crypto()
        assert isinstance(crypto, CustomCrypto)

    def test_get_jwt_crypto_not_default(self, settings):
        settings.BK_CRYPTO_TYPE = "CLASSIC"

        crypto = get_jwt_crypto()
        assert isinstance(crypto, BkCrypto)

    def test_get_jwt_crypto_unknown(self, settings):
        settings.BK_CRYPTO_TYPE = "UNKNOWN"

        with pytest.raises(ValueError):
            get_jwt_crypto()


class TestGatewayJWTHandler:
    def test_create_jwt(self):
        gateway = G(Gateway)

        result = GatewayJWTHandler.create_jwt(gateway)
        assert result.gateway == gateway
        assert result.private_key == ""
        assert "BEGIN PUBLIC KEY" in result.public_key
        assert result.encrypted_private_key

    def test_update_jwt_key(self, faker):
        gateway = G(Gateway)
        jwt = G(JWT, gateway=gateway, private_key=faker.pystr(), public_key=faker.pystr())

        GatewayJWTHandler.update_jwt_key(gateway, "test", "test")
        jwt = JWT.objects.get(gateway=gateway)

        crypto = get_jwt_crypto()
        assert jwt.public_key == "test"
        assert crypto.decrypt(jwt.encrypted_private_key) == "test"

    def test_get_private_key(self):
        gateway = G(Gateway)
        G(JWT, gateway=gateway)
        GatewayJWTHandler.update_jwt_key(gateway, "test", "test")
        assert GatewayJWTHandler.get_private_key(gateway.id) == "test"

    def test_is_jwt_key_changed(self, faker):
        gateway = G(Gateway)
        jwt = GatewayJWTHandler.create_jwt(gateway)

        assert GatewayJWTHandler.is_jwt_key_changed(
            gateway,
            smart_bytes(faker.pystr()),
            smart_bytes(faker.pystr()),
        )

        crypto = get_jwt_crypto()
        assert not GatewayJWTHandler.is_jwt_key_changed(
            gateway,
            crypto.decrypt(jwt.encrypted_private_key),
            smart_bytes(jwt.public_key),
        )
