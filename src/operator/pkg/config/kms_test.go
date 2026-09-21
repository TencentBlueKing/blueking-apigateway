/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

package config

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/spf13/viper"
)

func testKMSConfig() *viper.Viper {
	v := viper.New()
	v.Set("auth.id", "legacy-instance")
	v.Set("auth.secret", "legacy-secret")
	v.Set("databases", []map[string]any{
		{
			"id":       "apigateway",
			"user":     "old-user",
			"password": "old-password",
			"host":     "mysql.example",
			"name":     "gateway",
		},
		{"id": "audit", "user": "old-audit", "password": "old-audit-password"},
	})
	v.Set("dashboard.etcd.username", "old-etcd")
	v.Set("dashboard.etcd.password", "old-etcd-password")
	v.Set("apisix.etcd.username", "old-apisix")
	v.Set("apisix.etcd.password", "old-apisix-password")
	v.Set("mcpServer.encryptKey", "old-key")
	v.Set("mcpServer.cryptoNonce", "existing-nonce")
	v.Set("pprof.password", "untouched-pprof")
	return v
}

func testKMSPayload() map[string]any {
	return map[string]any{
		"bkapp_id_secret": map[string]any{
			"default": map[string]any{"app_code": "not-an-instance-id", "app_secret": "$app-secret"},
		},
		"mysql": map[string]any{
			"apigw": map[string]any{"username": "new-user", "password": "$p@ss:/?#%密码"},
			"audit": map[string]any{"username": "audit-user", "password": "audit-password"},
		},
		"etcd": map[string]any{
			"default": map[string]any{"username": "control-user", "password": "control-password"},
			"apisix":  map[string]any{"username": "data-user", "password": "data-password"},
		},
		"encryption": map[string]any{"encryptKey": "$new-encryption-key"},
		"unused":     map[string]any{"other-component": "ignored"},
	}
}

func writeTestKMS(t *testing.T, payload any) string {
	t.Helper()
	raw, err := json.Marshal(payload)
	if err != nil {
		t.Fatal(err)
	}
	return writeTestKMSPlaintext(t, raw)
}

func writeTestKMSPlaintext(t *testing.T, plaintext []byte) string {
	t.Helper()
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	pemKey := pem.EncodeToMemory(
		&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(privateKey)},
	)
	key := make([]byte, 16)
	iv := make([]byte, aes.BlockSize)
	if _, err = rand.Read(key); err != nil {
		t.Fatal(err)
	}
	if _, err = rand.Read(iv); err != nil {
		t.Fatal(err)
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		t.Fatal(err)
	}
	ciphertext := make([]byte, len(plaintext))
	cipher.NewCTR(block, iv).XORKeyStream(ciphertext, plaintext)
	encryptedKey, err := rsa.EncryptOAEP(sha256.New(), rand.Reader, &privateKey.PublicKey, key, nil)
	if err != nil {
		t.Fatal(err)
	}
	envelope, err := json.Marshal(map[string]string{
		"asymmetric_type": "RSA", "symmetric_type": "AES", "symmetric_mode": "CTR",
		"encrypted_key": base64.StdEncoding.EncodeToString(encryptedKey),
		"ciphertext":    base64.StdEncoding.EncodeToString(append(iv, ciphertext...)),
	})
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "envelope")
	if err = os.WriteFile(path, []byte(base64.StdEncoding.EncodeToString(envelope)+"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	oldPath := kmsEnvelopePath
	kmsEnvelopePath = path
	t.Cleanup(func() { kmsEnvelopePath = oldPath })
	t.Setenv("ENABLE_KMS", "True")
	t.Setenv("BK_APIGATEWAY_KMS_PRIVATE_KEY", "\n"+base64.StdEncoding.EncodeToString(pemKey)+"\n")
	return path
}

func TestLoadKMSRejectsMissingPrivateKey(t *testing.T) {
	t.Setenv("ENABLE_KMS", "True")
	t.Setenv("BK_APIGATEWAY_KMS_PRIVATE_KEY", "")
	cfg, err := Load(testKMSConfig())
	if err == nil || cfg != nil {
		t.Fatal("KMS accepted legacy credentials without a private key")
	}
}

func TestLoadKMSInvalidInputs(t *testing.T) {
	for _, kind := range []string{"missing-file", "bad-envelope", "wrong-key", "malformed-cbc", "bad-json", "bad-utf8", "non-object"} {
		t.Run(kind, func(t *testing.T) {
			path := writeTestKMS(t, testKMSPayload())
			switch kind {
			case "missing-file":
				if err := os.Remove(path); err != nil {
					t.Fatal(err)
				}
			case "bad-envelope":
				if err := os.WriteFile(path, []byte("sensitive-invalid-envelope"), 0o600); err != nil {
					t.Fatal(err)
				}
			case "wrong-key":
				t.Setenv("BK_APIGATEWAY_KMS_PRIVATE_KEY", "sensitive-invalid-key")
			case "bad-json":
				writeTestKMSPlaintext(t, []byte("sensitive-invalid-json"))
			case "bad-utf8":
				writeTestKMSPlaintext(t, []byte{'{', '"', 'x', '"', ':', '"', 0xff, '"', '}'})
			case "non-object":
				writeTestKMS(t, []string{"sensitive-json-array"})
			case "malformed-cbc":
				raw, err := os.ReadFile(path)
				if err != nil {
					t.Fatal(err)
				}
				decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(raw)))
				if err != nil {
					t.Fatal(err)
				}
				var payload map[string]string
				if err = json.Unmarshal(decoded, &payload); err != nil {
					t.Fatal(err)
				}
				payload["symmetric_mode"] = "CBC"
				payload["ciphertext"] = base64.StdEncoding.EncodeToString(make([]byte, aes.BlockSize+1))
				encoded, err := json.Marshal(payload)
				if err != nil {
					t.Fatal(err)
				}
				if err = os.WriteFile(
					path,
					[]byte(base64.StdEncoding.EncodeToString(encoded)),
					0o600,
				); err != nil {
					t.Fatal(err)
				}
			}
			cfg, err := Load(testKMSConfig())
			if err == nil || cfg != nil {
				t.Fatal("invalid KMS input must prevent startup")
			}
			if strings.Contains(err.Error(), "sensitive-") {
				t.Fatal("KMS error exposed input")
			}
		})
	}
}

func TestLoadKMSDisabled(t *testing.T) {
	for _, flag := range []string{"", "false", "False", "0"} {
		t.Run(flag, func(t *testing.T) {
			t.Setenv("ENABLE_KMS", flag)
			t.Setenv("BK_APIGATEWAY_KMS_PRIVATE_KEY", "")
			cfg, err := Load(testKMSConfig())
			if err != nil {
				t.Fatal(err)
			}
			if cfg.Auth.Secret != "legacy-secret" || cfg.Dashboard.Etcd.Password != "old-etcd-password" {
				t.Fatal("disabled KMS changed config")
			}
		})
	}
}

func TestLoadKMSRequiredFields(t *testing.T) {
	paths := [][]string{
		{"bkapp_id_secret", "default", "app_secret"},
		{"etcd", "default", "username"},
		{"etcd", "default", "password"},
		{"etcd", "apisix", "username"},
		{"etcd", "apisix", "password"},
	}
	for _, path := range paths {
		for _, bad := range []any{nil, "", "   ", 42, []string{}, map[string]string{}} {
			t.Run(strings.Join(path, "."), func(t *testing.T) {
				payload := testKMSPayload()
				node := payload
				for _, part := range path[:len(path)-1] {
					node = node[part].(map[string]any)
				}
				node[path[len(path)-1]] = bad
				writeTestKMS(t, payload)
				cfg, err := Load(testKMSConfig())
				if err == nil || cfg != nil {
					t.Fatal("invalid credential fell back to legacy settings")
				}
				if !strings.Contains(err.Error(), strings.Join(path, ".")) {
					t.Fatalf("missing field path: %v", err)
				}
			})
		}
	}
}

func TestLoadKMSCredentials(t *testing.T) {
	writeTestKMS(t, testKMSPayload())
	t.Setenv("ENCRYPT_KEY", "old-env-key")
	t.Setenv("BK_APP_SECRET", "old-env-secret")
	cfg, err := Load(testKMSConfig())
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Auth.ID != "legacy-instance" || cfg.Auth.Secret != "$app-secret" {
		t.Fatal("wrong instance auth mapping")
	}
	if cfg.Dashboard.Etcd.Username != "control-user" || cfg.Dashboard.Etcd.Password != "control-password" ||
		cfg.Apisix.Etcd.Username != "data-user" ||
		cfg.Apisix.Etcd.Password != "data-password" {
		t.Fatal("control-plane and data-plane etcd credentials must remain independent")
	}
	if os.Getenv("ENCRYPT_KEY") != "old-env-key" || os.Getenv("BK_APP_SECRET") != "old-env-secret" {
		t.Fatal("KMS mutated environment")
	}
}

func TestLoadKMSWithoutEtcdAuth(t *testing.T) {
	payload := testKMSPayload()
	delete(payload, "etcd")
	writeTestKMS(t, payload)
	v := testKMSConfig()
	v.Set("dashboard.etcd.withoutAuth", true)
	v.Set("apisix.etcd.withoutAuth", true)
	if _, err := Load(v); err != nil {
		t.Fatal(err)
	}
}

func TestLoadKMSDebugDoesNotDumpCredentials(t *testing.T) {
	writeTestKMS(t, testKMSPayload())
	v := testKMSConfig()
	v.Set("debug", true)
	reader, writer, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	old := os.Stdout
	os.Stdout = writer
	t.Cleanup(func() { os.Stdout = old; reader.Close(); writer.Close() })
	if _, err = Load(v); err != nil {
		t.Fatal(err)
	}
	if err = writer.Close(); err != nil {
		t.Fatal(err)
	}
	output, err := io.ReadAll(reader)
	if err != nil {
		t.Fatal(err)
	}
	if len(output) != 0 {
		t.Fatal("KMS debug configuration must not be printed")
	}
}
