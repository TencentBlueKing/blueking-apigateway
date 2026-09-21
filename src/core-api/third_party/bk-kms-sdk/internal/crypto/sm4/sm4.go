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

package sm4

import (
	"bytes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"io"

	"github.com/emmansun/gmsm/sm4"
)

func sm4PKCS7Padding(data []byte, blockSize int) []byte {
	padding := blockSize - len(data)%blockSize
	padText := bytes.Repeat([]byte{byte(padding)}, padding)
	return append(data, padText...)
}

func sm4PKCS7Unpadding(data []byte) ([]byte, error) {
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

// SM4EncryptCBC encrypt data in sm4 CBC mode.
func SM4EncryptCBC(plaintext, key []byte) (string, error) {
	block, err := sm4.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("sm4 cipher error(%+v)", err)
	}

	paddedText := sm4PKCS7Padding(plaintext, sm4.BlockSize)

	iv := make([]byte, sm4.BlockSize)
	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return "", fmt.Errorf("create rand iv error(%+v)", err)
	}

	mode := cipher.NewCBCEncrypter(block, iv)

	ciphertext := make([]byte, len(paddedText))
	mode.CryptBlocks(ciphertext, paddedText)

	return base64.StdEncoding.EncodeToString(append(iv, ciphertext...)), nil
}

// SM4DecryptCBC decrypt data in sm4 CBC mode.
func SM4DecryptCBC(encodedText string, key []byte) ([]byte, error) {
	encrypted, err := base64.StdEncoding.DecodeString(encodedText)
	if err != nil {
		return nil, fmt.Errorf("base64 error(%+v)", err)
	}

	if len(encrypted) < sm4.BlockSize*2 {
		return nil, errors.New("invalid data length")
	}

	iv := encrypted[:sm4.BlockSize]
	ciphertext := encrypted[sm4.BlockSize:]

	block, err := sm4.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("sm4 cipher error(%+v)", err)
	}

	mode := cipher.NewCBCDecrypter(block, iv)

	plaintext := make([]byte, len(ciphertext))
	mode.CryptBlocks(plaintext, ciphertext)

	return sm4PKCS7Unpadding(plaintext)
}

// SM4EncryptCTR encrypt data in sm4 CTR mode.
func SM4EncryptCTR(plaintext, key []byte) (string, error) {
	block, err := sm4.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("sm4 cipher error(%+v)", err)
	}

	nonce := make([]byte, sm4.BlockSize)
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", fmt.Errorf("create rand nonce error(%+v)", err)
	}

	mode := newSM4CTR(block, nonce)

	ciphertext := make([]byte, len(plaintext))
	mode.XORKeyStream(ciphertext, plaintext)

	return base64.StdEncoding.EncodeToString(append(nonce, ciphertext...)), nil
}

// SM4DecryptCTR decrypt data in sm4 CTR mode.
func SM4DecryptCTR(encodedText string, key []byte) ([]byte, error) {
	encrypted, err := base64.StdEncoding.DecodeString(encodedText)
	if err != nil {
		return nil, fmt.Errorf("base64 error(%+v)", err)
	}

	if len(encrypted) < sm4.BlockSize+1 {
		return nil, errors.New("invalid data length")
	}

	nonce := encrypted[:sm4.BlockSize]
	ciphertext := encrypted[sm4.BlockSize:]

	block, err := sm4.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("sm4 cipher error(%+v)", err)
	}

	mode := newSM4CTR(block, nonce)

	plaintext := make([]byte, len(ciphertext))
	mode.XORKeyStream(plaintext, ciphertext)

	return plaintext, nil
}

// SM4CTR sm4 ctr mode.
type SM4CTR struct {
	block   cipher.Block
	ctr     []byte
	out     []byte
	outUsed int
}

// new sm4 ctr mode for internal.
func newSM4CTR(block cipher.Block, iv []byte) cipher.Stream {
	dupIV := make([]byte, len(iv))
	copy(dupIV, iv)

	return &SM4CTR{
		block:   block,
		ctr:     dupIV,
		out:     make([]byte, block.BlockSize()),
		outUsed: block.BlockSize(),
	}
}

// XORKeyStream XORs each byte in the given slice with a byte from the cipher's key stream.
func (s *SM4CTR) XORKeyStream(dst, src []byte) {
	for i := 0; i < len(src); i++ {

		if s.outUsed == len(s.out) {
			s.block.Encrypt(s.out, s.ctr)
			s.outUsed = 0

			for j := len(s.ctr) - 1; j >= 0; j-- {
				s.ctr[j]++

				if s.ctr[j] != 0 {
					break
				}
			}
		}

		dst[i] = src[i] ^ s.out[s.outUsed]

		s.outUsed++
	}
}
