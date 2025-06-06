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
	"encoding/base64"
	"encoding/hex"
)

// AESGCMDecrypt decrypts AES-GCM ciphertext using the given key.
func AESGCMDecrypt(key string, nonce string, encryptedText string) ([]byte, error) {
	keyBytes, _ := base64.StdEncoding.DecodeString(key)
	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return nil, err
	}
	toHex, err := hex.DecodeString(encryptedText)
	if err != nil {
		return nil, err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	plaintext, err := aead.Open(nil, []byte(nonce), toHex, nil)
	if err != nil {
		return nil, err
	}
	return plaintext, nil
}
