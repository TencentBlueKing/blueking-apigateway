/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - 凭证管理服务(BlueKing - Key Management Service) available.
 * Copyright (C) 2022 THL A29 Limited, a Tencent company. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * http://opensource.org/licenses/MIT
 * Unless required by applicable law or agreed to in writing, software distributed
 * under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 * language governing permissions and limitations under the License.We undertake not
 * to change the open source license (MIT license) applicable to the current version
 * of the project delivered to anyone in the future.
 */

package sm2

import (
	"crypto/ecdsa"
	"crypto/rand"
	"encoding/base64"
	"encoding/pem"
	"fmt"

	"github.com/emmansun/gmsm/pkcs8"
	"github.com/emmansun/gmsm/sm2"
	"github.com/emmansun/gmsm/smx509"
)

// SM2Encrypt encrypt data in sm2 mode.
func SM2Encrypt(plaintext, publicKeyBase64 string) (string, error) {
	publicKey, err := base64.StdEncoding.DecodeString(publicKeyBase64)
	if err != nil {
		return "", fmt.Errorf("base64 decode public key error(%+v)", err)
	}

	block, _ := pem.Decode(publicKey)
	if block == nil {
		return "", fmt.Errorf("decode public key pem error")
	}

	pubKey, err := smx509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		return "", fmt.Errorf("parse public key error(%+v)", err)
	}

	sm2PubKey, ok := pubKey.(*ecdsa.PublicKey)
	if !ok {
		return "", fmt.Errorf("public key is not a sm2 public key")
	}

	ciphertext, err := sm2.EncryptASN1(rand.Reader, sm2PubKey, []byte(plaintext))
	if err != nil {
		return "", fmt.Errorf("encrypt error(%+v)", err)
	}

	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

// SM2Decrypt decrypt data in sm2 mode.
func SM2Decrypt(encodedText, privateKeyBase64 string) (string, error) {
	ciphertext, err := base64.StdEncoding.DecodeString(encodedText)
	if err != nil {
		return "", fmt.Errorf("base64 error(%+v)", err)
	}

	privateKey, err := base64.StdEncoding.DecodeString(privateKeyBase64)
	if err != nil {
		return "", fmt.Errorf("base64 decode private key error(%+v)", err)
	}

	block, _ := pem.Decode(privateKey)
	if block == nil {
		return "", fmt.Errorf("decode private key pem error")
	}

	privKey, err := pkcs8.ParsePKCS8PrivateKeySM2(block.Bytes)
	if err != nil {
		return "", fmt.Errorf("parse private key error(%+v)", err)
	}

	plaintext, err := privKey.Decrypt(rand.Reader, ciphertext, sm2.ASN1DecrypterOpts)
	if err != nil {
		return "", fmt.Errorf("decrypt error(%+v)", err)
	}

	return string(plaintext), nil
}
