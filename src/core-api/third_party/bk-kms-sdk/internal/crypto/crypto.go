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

package crypto

import (
	"encoding/base64"
	"encoding/json"
	"fmt"

	"github.com/TencentBlueKing/bk-kms-sdk/go/internal/crypto/aes"
	"github.com/TencentBlueKing/bk-kms-sdk/go/internal/crypto/rsa"
	"github.com/TencentBlueKing/bk-kms-sdk/go/internal/crypto/sm2"
	"github.com/TencentBlueKing/bk-kms-sdk/go/internal/crypto/sm4"
	"github.com/TencentBlueKing/bk-kms-sdk/go/internal/types"
)

// SymmetricDecrypt decrypt in symmetric algorithm.
func SymmetricDecrypt(encodedText string, cryptoType types.CryptoType, cryptoMode types.CryptoMode, cryptoKey string) (string, error) {
	if encodedText == "" {
		return "", nil
	}

	if err := cryptoType.ValidateSymmetric(); err != nil {
		return "", err
	}

	if err := cryptoMode.Validate(); err != nil {
		return "", err
	}

	if len(cryptoKey) != types.CryptoKeyLength {
		return "", fmt.Errorf("invalid crypto key length(%d)", len(cryptoKey))
	}

	var err error
	var decrypted []byte

	if cryptoType == types.CryptoTypeAES {
		if cryptoMode == types.CryptoModeCBC {
			decrypted, err = aes.AESDecryptCBC(encodedText, []byte(cryptoKey))
		}

		if cryptoMode == types.CryptoModeCTR {
			decrypted, err = aes.AESDecryptCTR(encodedText, []byte(cryptoKey))
		}
	}

	if cryptoType == types.CryptoTypeSM4 {
		if cryptoMode == types.CryptoModeCBC {
			decrypted, err = sm4.SM4DecryptCBC(encodedText, []byte(cryptoKey))
		}

		if cryptoMode == types.CryptoModeCTR {
			decrypted, err = sm4.SM4DecryptCTR(encodedText, []byte(cryptoKey))
		}
	}

	if err != nil {
		return "", fmt.Errorf("decrypt error(%+v)", err)
	}

	return string(decrypted), nil
}

// AsymmetricDecrypt decrypt in asymmetric algorithm.
func AsymmetricDecrypt(encodedText string, cryptoType types.CryptoType, cryptoPrivateKeyBase64 string) (string, error) {
	if encodedText == "" {
		return "", nil
	}

	if err := cryptoType.ValidateAsymmetric(); err != nil {
		return "", err
	}

	var err error
	var decrypted string

	if cryptoType == types.CryptoTypeRSA {
		decrypted, err = rsa.RSADecrypt(encodedText, cryptoPrivateKeyBase64)
	}

	if cryptoType == types.CryptoTypeSM2 {
		decrypted, err = sm2.SM2Decrypt(encodedText, cryptoPrivateKeyBase64)
	}

	if err != nil {
		return "", fmt.Errorf("decrypt error(%+v)", err)
	}

	return decrypted, nil
}

// HybridEnvelope carries a hybrid encrypted payload.
type HybridEnvelope struct {
	AsymmetricType types.CryptoType `json:"asymmetric_type"`
	SymmetricType  types.CryptoType `json:"symmetric_type"`
	SymmetricMode  types.CryptoMode `json:"symmetric_mode"`
	EncryptedKey   string           `json:"encrypted_key"`
	Ciphertext     string           `json:"ciphertext"`
}

// HybridDecrypt decrypt in hybrid algorithm.
func HybridDecrypt(encodedText string, cryptoPrivateKeyBase64 string) (string, error) {
	if encodedText == "" {
		return "", nil
	}

	raw, err := base64.StdEncoding.DecodeString(encodedText)
	if err != nil {
		return "", fmt.Errorf("decode hybrid envelope error(%+v)", err)
	}

	var envelope HybridEnvelope
	if err := json.Unmarshal(raw, &envelope); err != nil {
		return "", fmt.Errorf("unmarshal hybrid envelope error(%+v)", err)
	}

	if err := envelope.AsymmetricType.ValidateAsymmetric(); err != nil {
		return "", err
	}

	if err := envelope.SymmetricType.ValidateSymmetric(); err != nil {
		return "", err
	}

	if err := envelope.SymmetricMode.Validate(); err != nil {
		return "", err
	}

	symmetricKey, err := AsymmetricDecrypt(envelope.EncryptedKey, envelope.AsymmetricType, cryptoPrivateKeyBase64)
	if err != nil {
		return "", fmt.Errorf("decrypt symmetric key error(%+v)", err)
	}

	if len(symmetricKey) != types.CryptoKeyLength {
		return "", fmt.Errorf("invalid symmetric key length(%d)", len(symmetricKey))
	}

	plaintext, err := SymmetricDecrypt(envelope.Ciphertext, envelope.SymmetricType, envelope.SymmetricMode, symmetricKey)
	if err != nil {
		return "", fmt.Errorf("decrypt data error(%+v)", err)
	}

	return plaintext, nil
}
