/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/hex"
	"encoding/pem"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestAESGCMDecrypt(t *testing.T) {
	// Generate a test key
	keyBytes := make([]byte, 32) // AES-256
	_, err := rand.Read(keyBytes)
	assert.NoError(t, err)
	key := base64.StdEncoding.EncodeToString(keyBytes)

	// Generate a test nonce (12 bytes for GCM)
	nonceBytes := make([]byte, 12)
	_, err = rand.Read(nonceBytes)
	assert.NoError(t, err)
	nonce := string(nonceBytes)

	// Encrypt test data
	plaintext := "Hello, World!"
	block, err := aes.NewCipher(keyBytes)
	assert.NoError(t, err)

	aead, err := cipher.NewGCM(block)
	assert.NoError(t, err)

	ciphertext := aead.Seal(nil, nonceBytes, []byte(plaintext), nil)
	encryptedText := hex.EncodeToString(ciphertext)

	// Test decryption
	result, err := AESGCMDecrypt(key, nonce, encryptedText)
	assert.NoError(t, err)
	assert.Equal(t, plaintext, result)
}

func TestAESGCMDecrypt_InvalidKey(t *testing.T) {
	_, err := AESGCMDecrypt("invalid-base64", "nonce", "encrypted")
	assert.Error(t, err)
}

func TestAESGCMDecrypt_InvalidKeyLength(t *testing.T) {
	// Key too short for AES
	shortKey := base64.StdEncoding.EncodeToString([]byte("short"))
	_, err := AESGCMDecrypt(shortKey, "123456789012", "encrypted")
	assert.Error(t, err)
}

func TestAESGCMDecrypt_InvalidEncryptedText(t *testing.T) {
	keyBytes := make([]byte, 32)
	_, _ = rand.Read(keyBytes)
	key := base64.StdEncoding.EncodeToString(keyBytes)

	_, err := AESGCMDecrypt(key, "123456789012", "invalid-hex")
	assert.Error(t, err)
}

func TestParsePrivateKey_PKCS1(t *testing.T) {
	// Generate RSA key
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	assert.NoError(t, err)

	// Encode as PKCS1
	privateKeyBytes := x509.MarshalPKCS1PrivateKey(privateKey)
	pemBlock := &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: privateKeyBytes,
	}
	pemData := pem.EncodeToMemory(pemBlock)

	// Test parsing
	result, err := ParsePrivateKey(pemData)
	assert.NoError(t, err)
	assert.NotNil(t, result)
}

func TestParsePrivateKey_PKCS8(t *testing.T) {
	// Generate RSA key
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	assert.NoError(t, err)

	// Encode as PKCS8
	privateKeyBytes, err := x509.MarshalPKCS8PrivateKey(privateKey)
	assert.NoError(t, err)

	pemBlock := &pem.Block{
		Type:  "PRIVATE KEY",
		Bytes: privateKeyBytes,
	}
	pemData := pem.EncodeToMemory(pemBlock)

	// Test parsing
	result, err := ParsePrivateKey(pemData)
	assert.NoError(t, err)
	assert.NotNil(t, result)
}

func TestParsePrivateKey_InvalidPEM(t *testing.T) {
	_, err := ParsePrivateKey([]byte("not a pem block"))
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "failed to decode PEM block")
}

func TestParsePrivateKey_UnsupportedType(t *testing.T) {
	pemBlock := &pem.Block{
		Type:  "UNSUPPORTED KEY TYPE",
		Bytes: []byte("some data"),
	}
	pemData := pem.EncodeToMemory(pemBlock)

	_, err := ParsePrivateKey(pemData)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "unsupported PEM block type")
}

func TestParsePrivateKey_InvalidPKCS1Data(t *testing.T) {
	pemBlock := &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: []byte("invalid pkcs1 data"),
	}
	pemData := pem.EncodeToMemory(pemBlock)

	_, err := ParsePrivateKey(pemData)
	assert.Error(t, err)
}

func TestParsePrivateKey_InvalidPKCS8Data(t *testing.T) {
	pemBlock := &pem.Block{
		Type:  "PRIVATE KEY",
		Bytes: []byte("invalid pkcs8 data"),
	}
	pemData := pem.EncodeToMemory(pemBlock)

	_, err := ParsePrivateKey(pemData)
	assert.Error(t, err)
}
