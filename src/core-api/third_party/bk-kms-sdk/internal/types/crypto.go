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

package types

import "fmt"

// CryptoType is crypto type.
type CryptoType string

const (
	// CryptoTypeAES aes crypto type.
	CryptoTypeAES CryptoType = "AES"

	// CryptoTypeSM4 sm4 crypto type.
	CryptoTypeSM4 CryptoType = "SM4"

	// CryptoTypeRSA rsa crypto type.
	CryptoTypeRSA CryptoType = "RSA"

	// CryptoTypeSM2 sm2 crypto type.
	CryptoTypeSM2 CryptoType = "SM2"
)

// String returns the string representation of the crypto type.
func (c CryptoType) String() string {
	return string(c)
}

// ValidateAsymmetric validates asymmetric crypto type.
func (c CryptoType) ValidateAsymmetric() error {
	switch c {
	case CryptoTypeRSA, CryptoTypeSM2:
		return nil

	default:
		return fmt.Errorf("invalid asymmetric crypto type(%s)", c)
	}
}

// ValidateSymmetric validates symmetric crypto type.
func (c CryptoType) ValidateSymmetric() error {
	switch c {
	case CryptoTypeAES, CryptoTypeSM4:
		return nil

	default:
		return fmt.Errorf("invalid symmetric crypto type(%s)", c)
	}
}

// CryptoMode is symmetric crypto mode.
type CryptoMode string

const (
	// CryptoModeCBC cbc crypto mode.
	CryptoModeCBC CryptoMode = "CBC"

	// CryptoModeCTR ctr crypto mode.
	CryptoModeCTR CryptoMode = "CTR"
)

// String returns the string representation of the crypto mode.
func (m CryptoMode) String() string {
	return string(m)
}

// Validate validates symmetric crypto mode.
func (m CryptoMode) Validate() error {
	switch m {
	case CryptoModeCBC, CryptoModeCTR:
		return nil

	default:
		return fmt.Errorf("invalid crypto mode(%s)", m)
	}
}

const (
	// CryptoKeyLength crypto key length.
	CryptoKeyLength = 16
)
