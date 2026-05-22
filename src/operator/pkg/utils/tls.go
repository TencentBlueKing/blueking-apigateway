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

// Package utils ...
package utils

import (
	"crypto/tls"
	"crypto/x509"
	"os"

	"github.com/rotisserie/eris"
)

// NewClientTLSConfig ...
func NewClientTLSConfig(cafile, certfile, keyfile string) (*tls.Config, error) {
	caPool, err := loadCa(cafile)
	if err != nil {
		return nil, err
	}

	cert, err := loadCertificates(certfile, keyfile)
	if err != nil {
		return nil, err
	}

	conf := &tls.Config{
		InsecureSkipVerify: true, //nolint:gosec
		RootCAs:            caPool,
		Certificates:       []tls.Certificate{*cert},
	}

	return conf, nil
}

func loadCa(caFile string) (*x509.CertPool, error) {
	ca, err := os.ReadFile(caFile)
	if err != nil {
		return nil, err
	}

	caPool := x509.NewCertPool()
	if ok := caPool.AppendCertsFromPEM(ca); !ok {
		return nil, eris.Errorf("append ca cert failed")
	}

	return caPool, nil
}

func loadCertificates(certFile, keyFile string) (*tls.Certificate, error) {
	// key file
	priKey, err := os.ReadFile(keyFile)
	if err != nil {
		return nil, err
	}
	// certificate
	certData, err := os.ReadFile(certFile)
	if err != nil {
		return nil, err
	}

	tlsCert, err := tls.X509KeyPair(certData, priKey)
	if err != nil {
		return nil, err
	}

	return &tlsCert, nil
}
