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

package util_test

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/hex"
	"encoding/pem"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/util"
)

var _ = Describe("Cryptography", func() {
	Describe("AESGCMDecrypt", func() {
		It("should decrypt correctly", func() {
			keyBytes := make([]byte, 32) // AES-256
			_, err := rand.Read(keyBytes)
			Expect(err).NotTo(HaveOccurred())
			key := base64.StdEncoding.EncodeToString(keyBytes)

			nonceBytes := make([]byte, 12)
			_, err = rand.Read(nonceBytes)
			Expect(err).NotTo(HaveOccurred())
			nonce := string(nonceBytes)

			plaintext := "Hello, World!"
			block, err := aes.NewCipher(keyBytes)
			Expect(err).NotTo(HaveOccurred())

			aead, err := cipher.NewGCM(block)
			Expect(err).NotTo(HaveOccurred())

			ciphertext := aead.Seal(nil, nonceBytes, []byte(plaintext), nil)
			encryptedText := hex.EncodeToString(ciphertext)

			result, err := util.AESGCMDecrypt(key, nonce, encryptedText)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).To(Equal(plaintext))
		})

		It("should fail with invalid key", func() {
			_, err := util.AESGCMDecrypt("invalid-base64", "nonce", "encrypted")
			Expect(err).To(HaveOccurred())
		})

		It("should fail with invalid key length", func() {
			shortKey := base64.StdEncoding.EncodeToString([]byte("short"))
			_, err := util.AESGCMDecrypt(shortKey, "123456789012", "encrypted")
			Expect(err).To(HaveOccurred())
		})

		It("should fail with invalid encrypted text", func() {
			keyBytes := make([]byte, 32)
			_, _ = rand.Read(keyBytes)
			key := base64.StdEncoding.EncodeToString(keyBytes)

			_, err := util.AESGCMDecrypt(key, "123456789012", "invalid-hex")
			Expect(err).To(HaveOccurred())
		})
	})

	Describe("ParsePrivateKey", func() {
		It("should parse PKCS1 private key", func() {
			privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
			Expect(err).NotTo(HaveOccurred())

			privateKeyBytes := x509.MarshalPKCS1PrivateKey(privateKey)
			pemBlock := &pem.Block{
				Type:  "RSA PRIVATE KEY",
				Bytes: privateKeyBytes,
			}
			pemData := pem.EncodeToMemory(pemBlock)

			result, err := util.ParsePrivateKey(pemData)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
		})

		It("should parse PKCS8 private key", func() {
			privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
			Expect(err).NotTo(HaveOccurred())

			privateKeyBytes, err := x509.MarshalPKCS8PrivateKey(privateKey)
			Expect(err).NotTo(HaveOccurred())

			pemBlock := &pem.Block{
				Type:  "PRIVATE KEY",
				Bytes: privateKeyBytes,
			}
			pemData := pem.EncodeToMemory(pemBlock)

			result, err := util.ParsePrivateKey(pemData)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
		})

		It("should fail with invalid PEM", func() {
			_, err := util.ParsePrivateKey([]byte("not a pem block"))
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("failed to decode PEM block"))
		})

		It("should fail with unsupported type", func() {
			pemBlock := &pem.Block{
				Type:  "UNSUPPORTED KEY TYPE",
				Bytes: []byte("some data"),
			}
			pemData := pem.EncodeToMemory(pemBlock)

			_, err := util.ParsePrivateKey(pemData)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("unsupported PEM block type"))
		})

		It("should fail with invalid PKCS1 data", func() {
			pemBlock := &pem.Block{
				Type:  "RSA PRIVATE KEY",
				Bytes: []byte("invalid pkcs1 data"),
			}
			pemData := pem.EncodeToMemory(pemBlock)

			_, err := util.ParsePrivateKey(pemData)
			Expect(err).To(HaveOccurred())
		})

		It("should fail with invalid PKCS8 data", func() {
			pemBlock := &pem.Block{
				Type:  "PRIVATE KEY",
				Bytes: []byte("invalid pkcs8 data"),
			}
			pemData := pem.EncodeToMemory(pemBlock)

			_, err := util.ParsePrivateKey(pemData)
			Expect(err).To(HaveOccurred())
		})

		It("should fail with PKCS8 non-RSA key (ECDSA)", func() {
			// Generate an ECDSA key (non-RSA)
			ecdsaKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
			Expect(err).NotTo(HaveOccurred())

			privateKeyBytes, err := x509.MarshalPKCS8PrivateKey(ecdsaKey)
			Expect(err).NotTo(HaveOccurred())

			pemBlock := &pem.Block{
				Type:  "PRIVATE KEY",
				Bytes: privateKeyBytes,
			}
			pemData := pem.EncodeToMemory(pemBlock)

			_, err = util.ParsePrivateKey(pemData)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("expected RSA private key"))
		})
	})
})
