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

package aes

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
)

func aesPKCS7Padding(data []byte, blockSize int) []byte {
	padding := blockSize - len(data)%blockSize
	padText := bytes.Repeat([]byte{byte(padding)}, padding)
	return append(data, padText...)
}

func aesPKCS7Unpadding(data []byte) ([]byte, error) {
	length := len(data)
	if length == 0 {
		return nil, errors.New("invalid pkcs7 data length")
	}

	unpadding := int(data[length-1])
	if unpadding > length {
		return nil, errors.New("invalid pkcs7 padding length")
	}

	return data[:(length - unpadding)], nil
}

// AESEncryptCBC encrypt data in aes CBC mode.
func AESEncryptCBC(plaintext, key []byte) (string, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("aes cipher error(%+v)", err)
	}

	paddedText := aesPKCS7Padding(plaintext, aes.BlockSize)

	iv := make([]byte, aes.BlockSize)
	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return "", fmt.Errorf("create rand iv error(%+v)", err)
	}

	mode := cipher.NewCBCEncrypter(block, iv)

	ciphertext := make([]byte, len(paddedText))
	mode.CryptBlocks(ciphertext, paddedText)

	return base64.StdEncoding.EncodeToString(append(iv, ciphertext...)), nil
}

// AESDecryptCBC decrypt data in aes CBC mode.
func AESDecryptCBC(encodedText string, key []byte) ([]byte, error) {
	encrypted, err := base64.StdEncoding.DecodeString(encodedText)
	if err != nil {
		return nil, fmt.Errorf("base64 error(%+v)", err)
	}

	if len(encrypted) < aes.BlockSize*2 || (len(encrypted)-aes.BlockSize)%aes.BlockSize != 0 {
		return nil, errors.New("invalid data length")
	}

	iv := encrypted[:aes.BlockSize]
	ciphertext := encrypted[aes.BlockSize:]

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("aes cipher error(%+v)", err)
	}

	mode := cipher.NewCBCDecrypter(block, iv)

	plaintext := make([]byte, len(ciphertext))
	mode.CryptBlocks(plaintext, ciphertext)

	return aesPKCS7Unpadding(plaintext)
}

// AESEncryptCTR encrypt data in aes CTR mode.
func AESEncryptCTR(plaintext, key []byte) (string, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("aes cipher error(%+v)", err)
	}

	nonce := make([]byte, aes.BlockSize)
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", fmt.Errorf("create rand nonce error(%+v)", err)
	}

	mode := cipher.NewCTR(block, nonce)

	ciphertext := make([]byte, len(plaintext))
	mode.XORKeyStream(ciphertext, plaintext)

	return base64.StdEncoding.EncodeToString(append(nonce, ciphertext...)), nil
}

// AESDecryptCTR decrypt data in aes CTR mode.
func AESDecryptCTR(encodedText string, key []byte) ([]byte, error) {
	encrypted, err := base64.StdEncoding.DecodeString(encodedText)
	if err != nil {
		return nil, fmt.Errorf("base64 error(%+v)", err)
	}

	if len(encrypted) < aes.BlockSize+1 {
		return nil, errors.New("invalid data length")
	}

	nonce := encrypted[:aes.BlockSize]
	ciphertext := encrypted[aes.BlockSize:]

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("aes cipher error(%+v)", err)
	}

	mode := cipher.NewCTR(block, nonce)

	plaintext := make([]byte, len(ciphertext))
	mode.XORKeyStream(plaintext, ciphertext)

	return plaintext, nil
}
