/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

package util

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/hex"
	"encoding/pem"
	"errors"
	"fmt"
)

// AESGCMDecrypt decrypts AES-GCM ciphertext using the given key.
func AESGCMDecrypt(key string, nonce string, encryptedText string) (string, error) {
	keyBytes, err := base64.StdEncoding.DecodeString(key)
	if err != nil {
		return "", err
	}
	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return "", err
	}
	toHex, err := hex.DecodeString(encryptedText)
	if err != nil {
		return "", err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}
	plaintext, err := aead.Open(nil, []byte(nonce), toHex, nil)
	if err != nil {
		return "", err
	}
	return string(plaintext), nil
}

// ParsePrivateKey This function parses a private key from a byte slice
func ParsePrivateKey(privateKeyText []byte) (any, error) {
	// Decode the PEM block from the byte slice
	block, _ := pem.Decode(privateKeyText)
	// If the block is nil, return an error
	if block == nil {
		return nil, errors.New("failed to decode PEM block: no PEM data found")
	}
	// Declare a variable to hold the private key
	var privateKey interface{}
	// Declare a variable to hold any error that occurs
	var err error
	// Switch on the type of the PEM block
	switch block.Type {
	// If the type is RSA PRIVATE KEY
	case "RSA PRIVATE KEY":
		// Parse the private key from the bytes
		privateKey, err = x509.ParsePKCS1PrivateKey(block.Bytes)
	// If the type is PRIVATE KEY
	case "PRIVATE KEY":
		// Parse the private key from the bytes
		privateKey, err = x509.ParsePKCS8PrivateKey(block.Bytes)
		// If no error occurred, ensure it's an RSA key
		if err == nil {
			privateKey, _ = privateKey.(*rsa.PrivateKey) // Ensure it's an RSA key
		}
	default:
		return nil, fmt.Errorf("unsupported PEM block type: %s", block.Type)
	}
	if err != nil {
		return nil, err
	}
	return privateKey, nil
}
