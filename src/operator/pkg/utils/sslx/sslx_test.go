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
package sslx

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"math/big"
	"net"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

// 生成测试用的自签名证书
func generateTestCert() string {
	priv, _ := rsa.GenerateKey(rand.Reader, 2048)
	notBefore := time.Now()
	notAfter := notBefore.Add(365 * 24 * time.Hour)

	template := x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			Organization: []string{"Test Org"},
		},
		NotBefore: notBefore,
		NotAfter:  notAfter,
		KeyUsage:  x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{
			x509.ExtKeyUsageServerAuth,
		},
		BasicConstraintsValid: true,
	}

	derBytes, _ := x509.CreateCertificate(rand.Reader, &template, &template, &priv.PublicKey, priv)
	certPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "CERTIFICATE",
		Bytes: derBytes,
	})
	return string(certPEM)
}

func TestX509CertValidity(t *testing.T) {
	validCert := generateTestCert()

	tests := []struct {
		name    string
		crt     string
		wantErr bool
	}{
		{
			name:    "valid cert",
			crt:     validCert,
			wantErr: false,
		},
		{
			name:    "empty cert",
			crt:     "",
			wantErr: true,
		},
		{
			name:    "invalid cert",
			crt:     "invalid-cert-data",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := X509CertValidity(tt.crt)
			if tt.wantErr {
				assert.Error(t, err)
				return
			}
			assert.NoError(t, err)
			assert.NotNil(t, got)
			assert.True(t, got.NotBefore > 0)
			assert.True(t, got.NotAfter > got.NotBefore)
		})
	}
}

func TestParseCert(t *testing.T) {
	// 生成测试证书和密钥
	priv, _ := rsa.GenerateKey(rand.Reader, 2048)
	notBefore := time.Now()
	notAfter := notBefore.Add(365 * 24 * time.Hour)

	// 生成带DNSNames的证书
	dnsTemplate := x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			CommonName:   "test.example.com",
			Organization: []string{"Test Org"},
		},
		DNSNames:              []string{"test1.example.com", "test2.example.com"},
		IPAddresses:           []net.IP{net.ParseIP("127.0.0.1"), net.ParseIP("::1")},
		NotBefore:             notBefore,
		NotAfter:              notAfter,
		KeyUsage:              x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid: true,
	}

	// 生成只带IP地址的证书
	ipTemplate := x509.Certificate{
		SerialNumber: big.NewInt(2),
		Subject: pkix.Name{
			Organization: []string{"Test Org"},
		},
		IPAddresses:           []net.IP{net.ParseIP("192.168.1.1"), net.ParseIP("10.0.0.1")},
		NotBefore:             notBefore,
		NotAfter:              notAfter,
		KeyUsage:              x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid: true,
	}

	// 生成只带Subject CN的证书
	cnTemplate := x509.Certificate{
		SerialNumber: big.NewInt(3),
		Subject: pkix.Name{
			CommonName:   "subject.example.com",
			Organization: []string{"Test Org"},
		},
		NotBefore:             notBefore,
		NotAfter:              notAfter,
		KeyUsage:              x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid: true,
	}

	// 生成证书和密钥
	dnsDerBytes, _ := x509.CreateCertificate(rand.Reader, &dnsTemplate, &dnsTemplate, &priv.PublicKey, priv)
	dnsCertPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "CERTIFICATE",
		Bytes: dnsDerBytes,
	})

	ipDerBytes, _ := x509.CreateCertificate(rand.Reader, &ipTemplate, &ipTemplate, &priv.PublicKey, priv)
	ipCertPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "CERTIFICATE",
		Bytes: ipDerBytes,
	})

	cnDerBytes, _ := x509.CreateCertificate(rand.Reader, &cnTemplate, &cnTemplate, &priv.PublicKey, priv)
	cnCertPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "CERTIFICATE",
		Bytes: cnDerBytes,
	})

	keyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(priv),
	})

	// 测试用例
	tests := []struct {
		name    string
		crt     string
		key     string
		want    []string
		wantErr bool
	}{
		{
			name:    "valid cert with DNSNames",
			crt:     string(dnsCertPEM),
			key:     string(keyPEM),
			want:    []string{"test1.example.com", "test2.example.com"},
			wantErr: false,
		},
		{
			name:    "valid cert with IP addresses",
			crt:     string(ipCertPEM),
			key:     string(keyPEM),
			want:    []string{"192.168.1.1", "10.0.0.1"},
			wantErr: false,
		},
		{
			name:    "valid cert with Subject CN",
			crt:     string(cnCertPEM),
			key:     string(keyPEM),
			want:    []string{"subject.example.com"},
			wantErr: false,
		},
		{
			name:    "empty cert",
			crt:     "",
			key:     "",
			want:    nil,
			wantErr: true,
		},
		{
			name:    "invalid cert",
			crt:     "invalid-cert-data",
			key:     "invalid-key-data",
			want:    nil,
			wantErr: true,
		},
		{
			name: "cert and key mismatch",
			crt:  string(dnsCertPEM),
			key: string(pem.EncodeToMemory(&pem.Block{
				Type: "RSA PRIVATE KEY",
				Bytes: func() []byte {
					priv, _ := rsa.GenerateKey(rand.Reader, 2048)
					return x509.MarshalPKCS1PrivateKey(priv)
				}(),
			})),
			want:    nil,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ParseCert(tt.crt, tt.key)
			if tt.wantErr {
				assert.Error(t, err)
				return
			}
			assert.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}
