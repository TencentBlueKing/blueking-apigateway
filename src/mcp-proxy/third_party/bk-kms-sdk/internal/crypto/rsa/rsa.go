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

package rsa

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"errors"
	"fmt"
)

// RSAEncrypt encrypt data in rsa mode.
func RSAEncrypt(plaintext, publicKeyBase64 string) (string, error) {
	publicKey, err := base64.StdEncoding.DecodeString(publicKeyBase64)
	if err != nil {
		return "", fmt.Errorf("base64 decode public key error(%+v)", err)
	}

	block, _ := pem.Decode(publicKey)
	if block == nil {
		return "", errors.New("decode pem public key error")
	}

	pubKey, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		pubKey, err = x509.ParsePKCS1PublicKey(block.Bytes)
		if err != nil {
			return "", fmt.Errorf("parse public key error(%+v)", err)
		}
	}

	rsaPubKey, ok := pubKey.(*rsa.PublicKey)
	if !ok {
		return "", errors.New("not rsa public key")
	}

	ciphertext, err := rsa.EncryptOAEP(sha256.New(), rand.Reader, rsaPubKey, []byte(plaintext), nil)
	if err != nil {
		return "", fmt.Errorf("encrypt error(%+v)", err)
	}

	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

// RSADecrypt decrypt data in rsa mode.
func RSADecrypt(encodedText, privateKeyBase64 string) (string, error) {
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
		return "", errors.New("decode pem private key error")
	}

	privKey, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	if err != nil {
		privKey, err = x509.ParsePKCS1PrivateKey(block.Bytes)
		if err != nil {
			return "", fmt.Errorf("parse private key error(%+v)", err)
		}
	}

	rsaPrivKey, ok := privKey.(*rsa.PrivateKey)
	if !ok {
		return "", errors.New("not rsa private key")
	}

	plaintext, err := rsa.DecryptOAEP(sha256.New(), rand.Reader, rsaPrivKey, ciphertext, nil)
	if err != nil {
		return "", fmt.Errorf("decrypt error(%+v)", err)
	}

	return string(plaintext), nil
}
