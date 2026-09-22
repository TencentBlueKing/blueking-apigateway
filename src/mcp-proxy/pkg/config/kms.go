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
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
	"unicode/utf8"

	"github.com/TencentBlueKing/bk-kms-sdk/go/decrypt"
)

var kmsEnvelopePath = "/etc/secrets/bk-apigateway-kms"

func kmsEnabled() bool {
	value := os.Getenv("ENABLE_KMS")
	return value == "true" || value == "True"
}

func loadKMSCredentials() (map[string]any, error) {
	if !kmsEnabled() {
		return nil, nil
	}
	privateKey := strings.TrimSpace(os.Getenv("BK_APIGATEWAY_KMS_PRIVATE_KEY"))
	if privateKey == "" {
		return nil, errors.New("KMS requires BK_APIGATEWAY_KMS_PRIVATE_KEY")
	}
	envelope, err := os.ReadFile(kmsEnvelopePath)
	if err != nil {
		return nil, errors.New("unable to read KMS credential envelope")
	}
	plaintext, err := decryptKMSEnvelope(strings.TrimSpace(string(envelope)), privateKey)
	if err != nil {
		return nil, errors.New("unable to decrypt KMS credential envelope")
	}
	var credentials map[string]any
	if !utf8.ValidString(plaintext) || json.Unmarshal([]byte(plaintext), &credentials) != nil ||
		credentials == nil {
		return nil, errors.New("KMS plaintext must be a JSON object")
	}
	return credentials, nil
}

func decryptKMSEnvelope(envelope, privateKey string) (plaintext string, err error) {
	// The temporary SDK can panic on malformed CBC ciphertext. Convert that
	// boundary failure to a startup error without exposing the panic or input.
	defer func() {
		if recover() != nil {
			plaintext = ""
			err = errors.New("invalid KMS credential envelope")
		}
	}()
	return decrypt.Decrypt(envelope, privateKey)
}

func bindKMSCredentials(credentials map[string]any, bindings map[*string][]string) error {
	for target, path := range bindings {
		var value any = credentials
		for _, part := range path {
			object, _ := value.(map[string]any)
			value = object[part]
		}
		text, ok := value.(string)
		if !ok || strings.TrimSpace(text) == "" {
			return fmt.Errorf("KMS requires a non-empty string at %s", strings.Join(path, "."))
		}
		*target = text
	}
	return nil
}

func (cfg *Config) applyKMS() error {
	credentials, err := loadKMSCredentials()
	if err != nil || credentials == nil {
		return err
	}
	bindings := map[*string][]string{&cfg.McpServer.EncryptKey: {"encryption", "encryptKey"}}
	for i := range cfg.Databases {
		db := &cfg.Databases[i]
		instance := db.ID
		if instance == "apigateway" {
			instance = "apigw"
		}
		bindings[&db.User] = []string{"mysql", instance, "username"}
		bindings[&db.Password] = []string{"mysql", instance, "password"}
	}
	return bindKMSCredentials(credentials, bindings)
}
