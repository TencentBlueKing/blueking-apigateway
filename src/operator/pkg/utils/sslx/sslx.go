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

// Package sslx ...
package sslx

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/pem"
	"errors"
	"fmt"
)

// Validity ...
type Validity struct {
	NotBefore, NotAfter int64
}

// X509CertValidity 获取证书有效期
func X509CertValidity(crt string) (*Validity, error) {
	if crt == "" {
		return nil, errors.New("无效证书")
	}
	certDERBlock, _ := pem.Decode([]byte(crt))
	if certDERBlock == nil {
		return nil, errors.New("证书解析失败")
	}

	x509Cert, err := x509.ParseCertificate(certDERBlock.Bytes)
	if err != nil {
		return nil, errors.New("证书解析失败")
	}

	val := Validity{}

	val.NotBefore = x509Cert.NotBefore.Unix()
	val.NotAfter = x509Cert.NotAfter.Unix()

	return &val, nil
}

// ParseCert 解析证书
func ParseCert(crt, key string) ([]string, error) {
	certDERBlock, _ := pem.Decode([]byte(crt))
	if certDERBlock == nil {
		return nil, errors.New("证书解析失败")
	}

	// Match key and cert
	_, err := tls.X509KeyPair([]byte(crt), []byte(key))
	if err != nil {
		return nil, fmt.Errorf("密钥和证书不匹配: %w", err)
	}

	x509Cert, err := x509.ParseCertificate(certDERBlock.Bytes)
	if err != nil {
		return nil, errors.New("证书解析失败")
	}
	// Domain
	var snis []string
	switch {
	case len(x509Cert.DNSNames) > 0:
		snis = x509Cert.DNSNames
	case len(x509Cert.IPAddresses) > 0:
		for _, ip := range x509Cert.IPAddresses {
			snis = append(snis, ip.String())
		}
	case len(x509Cert.Subject.Names) > 0:
		attributeTypeNames := map[string]string{
			"2.5.4.6":  "C",
			"2.5.4.10": "O",
			"2.5.4.11": "OU",
			"2.5.4.3":  "CN",
			"2.5.4.5":  "SERIALNUMBER",
			"2.5.4.7":  "L",
			"2.5.4.8":  "ST",
			"2.5.4.9":  "STREET",
			"2.5.4.17": "POSTALCODE",
		}
		for _, tv := range x509Cert.Subject.Names {
			oidString := tv.Type.String()
			if typeName, ok := attributeTypeNames[oidString]; ok && typeName == "CN" {
				valueString := fmt.Sprint(tv.Value)
				snis = append(snis, valueString)
			}
		}
	}
	return snis, nil
}
