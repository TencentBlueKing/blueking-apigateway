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

package schema

import (
	"encoding/json"
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/xeipuuv/gojsonschema"

	"operator/pkg/constant"
	"operator/pkg/entity"
)

var APISIXVersionList = []constant.APISIXVersion{
	constant.APISIXVersion313,
}

func TestNewResourceSchema(t *testing.T) {
	tests := []struct {
		name         string
		version      constant.APISIXVersion
		resourceType constant.APISIXResource
		jsonPath     string
		config       string
		shouldFail   bool
	}{
		{
			name:         "normal case ",
			version:      constant.APISIXVersion313,
			resourceType: constant.Route,
			jsonPath:     "main.route",
			config: `{
			  "id": "bk.r.xxx",
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: false,
		},
		{
			name:         "invalid schema path",
			version:      constant.APISIXVersion313,
			resourceType: constant.Route,
			jsonPath:     "invalid.path",
			shouldFail:   true,
		},
		{
			name:         "invalid version",
			version:      "invalid_version",
			resourceType: constant.Route,
			jsonPath:     "main.route",
			shouldFail:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			schemaDef, schema, err := NewResourceSchema(
				tt.version,
				tt.resourceType,
				tt.jsonPath,
			)

			if tt.shouldFail {
				assert.Error(t, err)
				assert.Nil(t, schema)
				assert.Empty(t, schemaDef)
				return
			}

			assert.NoError(t, err)
			assert.NotNil(t, schema)
			assert.NotEmpty(t, schemaDef)

			result, err := schema.Validate(gojsonschema.NewStringLoader(tt.config))
			assert.NoError(t, err)
			assert.True(t, result.Valid())
		})
	}
}

func TestNewAPISIXJsonSchemaValidator(t *testing.T) {
	type testMap struct {
		name       string
		version    constant.APISIXVersion
		resource   constant.APISIXResource
		jsonPath   string
		shouldFail bool
	}

	tests := []testMap{}
	// 包含所有版本和资源类型
	for _, version := range APISIXVersionList {
		for _, resource := range constant.ResourceTypeList {
			resourceTests := []testMap{
				{
					name:       "Valid Schema",
					version:    version,
					resource:   resource,
					jsonPath:   fmt.Sprintf("main.%s", resource.String()),
					shouldFail: false,
				},
				{
					name:       "Invalid Version",
					version:    "invalid_version",
					resource:   resource,
					jsonPath:   fmt.Sprintf("main.%s", resource.String()),
					shouldFail: true,
				},
				{
					name:       "Invalid Path",
					version:    version,
					resource:   resource,
					jsonPath:   "invalid.path",
					shouldFail: true,
				},
			}
			tests = append(tests, resourceTests...)
		}
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := NewAPISIXJsonSchemaValidator(tt.version, tt.resource, tt.jsonPath)
			if tt.shouldFail {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestAPISIXJsonSchemaValidatorValidate(t *testing.T) {
	tests := []struct {
		name       string
		resource   constant.APISIXResource
		jsonPath   string
		config     string
		shouldFail bool
	}{
		{
			name:     "Valid Route to write to the DATABASE",
			resource: constant.Route,
			jsonPath: "main.route",
			config: `{
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid Route With valid vars",
			resource: constant.Route,
			jsonPath: "main.route",
			config: `{
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
               "vars": [
                 "test"
              ],
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: true,
		},
		{
			name:     "Valid Route With vars",
			resource: constant.Route,
			jsonPath: "main.route",
			config: `{
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
               "vars": [
                 [
                    "http_a",
                    "!",
                    "==",
                    "av"
                ],
                [
                    "arg_b",
                    "~=",
                    "av"
                ],
                [
                    "arg_b",
                    "~=",
                    "av"
                ],
                [
                    "g",
                    "!",
                    "HAS",
                    "gv"
                ]
              ],
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid vars with op",
			resource: constant.Route,
			jsonPath: "main.route",
			config: `{
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
               "vars": [
                 [
                    "http_a",
                    "!",
                    "==",
                    "av"
                ],
                [
                    "arg_b",
                    "~=",
                    "av"
                ],
                [
                    "arg_b",
                    "~=",
                    "av"
                ]
              ],
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid Service to write to the DATABASE",
			resource: constant.Service,
			jsonPath: "main.service",
			config: `{
              "name": "service1",
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid Upstream to write to the DATABASE",
			resource: constant.Upstream,
			jsonPath: "main.upstream",
			config: `{
		      "name": "upstream1",
			  "scheme": "http",
			  "nodes": [
		        {
		            "host": "111",
		            "port": 80,
		            "weight": 1
		        }
		      ],
		      "pass_host": "pass",
		      "type": "roundrobin",
		      "desc": "22"
		    }`,
			shouldFail: false,
		},
		{
			name:     "Valid SSLs to write to the DATABASE",
			resource: constant.SSL,
			jsonPath: "main.ssl",
			config: `{
			  "cert": "-----BEGIN CERTIFICATE-----\nMIIDJzCCAg+gAwIBAgIRAJvCZRh2nejK7+Ss3AgrEa0wDQYJKoZIhvcNAQELBQAw\ngYoxEjAQBgNVBAMMCWxkZGdvLm5ldDEMMAoGA1UECwwDZGV2MQ4wDAYDVQQKDAVs\nZGRnbzELMAkGA1UEBhMCQ04xIzAhBgkqhkiG9w0BCQEWFGxlY2hlbmdhZG1pbkAx\nMjYuY29tMREwDwYDVQQHDAhzaGFuZ2hhaTERMA8GA1UECAwIc2hhbmdoYWkwHhcN\nMjUwMjI2MDE0ODQ0WhcNMjcwMjI2MDE0ODQ0WjATMREwDwYDVQQDDAh0ZXN0LmNv\nbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAIIJ82TMFlWOR7dDkJ0X\nLclmCUDlefEJY2laYPWxaCe3oaIndosUmgm5aovYUTWDRAByn56HPFub5fc2Kt9v\n5+HWVd149JuP43F5NXaUKbE6GuXUWR7WhorzIRbabvvkE4SdpkrGwthi6AxUnvKK\naHKn11hSk+MBUWxjhSJoQy/ds3fKSpq7j+LAMRmQo9a3uW/HBl7FdfWIH5ZTN3Q8\n+ZDMc2zrEqOXFBGFBwzsbcVGNppMkUBuYmxIp7O3slB7rH7oOkdpYReIwWQOOswO\nhbBu5UGqC8nMX0N0jhzMyxrvDOIFSjjKiXuu46qd+t/GxUB9+8ZJ/Fn3WsJ6iQf7\n+cMCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEARSufAXUin/eFxcpojYMZ6F3t6VYp\njiZ+3Sx+UjQ4mq3qq8eQ/r0haxGtw2GeMuyprfxj6YTX6erQlJKkDk8vJXpDbFR4\n4dj1g4VQDZshPH2j2HJ/4l/kAvbDy/Rj9eIdV0Ux+t8s7MYgP7yf35Nb1ejJyWhB\nPS56NWCyj43lJcwnUmH4EAvLiFdgGgiaPQdm2/XlyEd8UVZugihIgjlQ3XKwMwsb\nXFfjJdDgdhFO5jmtU+rdEQWuaJDCEEWQJfMFmWRGApri97T/14QOulTqCXfk8+Wq\nw4WMGMQt3zIALlf7Meknv2qfTxax3JAO8lf7KuN5A4S5SuqAHke9NfGzAA==\n-----END CERTIFICATE-----",
			  "key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCCCfNkzBZVjke3\nQ5CdFy3JZglA5XnxCWNpWmD1sWgnt6GiJ3aLFJoJuWqL2FE1g0QAcp+ehzxbm+X3\nNirfb+fh1lXdePSbj+NxeTV2lCmxOhrl1Fke1oaK8yEW2m775BOEnaZKxsLYYugM\nVJ7yimhyp9dYUpPjAVFsY4UiaEMv3bN3ykqau4/iwDEZkKPWt7lvxwZexXX1iB+W\nUzd0PPmQzHNs6xKjlxQRhQcM7G3FRjaaTJFAbmJsSKezt7JQe6x+6DpHaWEXiMFk\nDjrMDoWwbuVBqgvJzF9DdI4czMsa7wziBUo4yol7ruOqnfrfxsVAffvGSfxZ91rC\neokH+/nDAgMBAAECggEACSzKj4IW0VKInNWXjn3kLSGV5Y5LXEZdTUGjNbKetq6u\nKNK/+nApriX27ocEs9HfKmjr+jNwfsYxI5Ae1kT/B2AoDshJ+e/dDFSRARzTFD4V\nR8IDx7k7JPKikwo2am9dMS4uXXhIpxvTY4tU66f4Vp6hAwpQhOPC6vLaoeLZWrcg\nAjjPTud/1N8D+CMsnsrfLh9XPLvUZIqYm5DCgE6fFle1/X/YrqzzMzflCG3Ns5Gv\nMY0i1xR7baAj8nT9iG+MCvCW8Ak2++pweX2Hli6l5aqk+esDU/zUAdddJdtpufGT\nkobCOKtqNXzEj6UGrsQU/27dc1tQKt4VgRvsgC+aAQKBgQC5zySFCpqtZY/naKnw\nGXf1Pl7r8aTuWVA+8ziRiyPlyI60oMHhu0bSIoRIh7lpa8km/cNsJOMTFWmHUANT\ndu53icmSCO++M1d+nrl3aWYyqbAlFvqMPtiW5/pYRnWJi4GSQTonGY32EhmN1qo5\nJbmj7NVxRnX0g9OTX4+f5MdCUQKBgQCzKXzwim/KxeOeVURVu/LQGK+Or2Ssyzjr\nz8MPQ2OE5DX528hLkE5h0EVhffSrsTfQiiMIhzU/Rywa7khNRqsTmhFEHM5JI+Rl\nGZgGgG4T5Q3idfrx3jXGqMylmoR0pA+4aGpSGg135vuIhJWCn8RI/mgMl0KP6Nax\nSSZkex4B0wKBgFr470FwIrEY068SEHnsjk31fpX4lq7X7bEUdjLUM/wyCKSpPKPf\nhFon6ip0wTO7QR4lCoQtPzw9tJA6fZZk2XaPcLBeTbsK+iCVZ+ruIMpXSFWwfXUi\n4/pmk6yaurtgIU1RQD6ahWXgEMDgRDF8pfp7Xzl5rRDNZk52cCRx55kxAoGAV4/p\nTi56oKHCszl9ImGvNGE8PAIgtArGkQmDjcwjsWlPsAPoinXGuStvHUzP7bG5U6SP\nprVeIsUIG0ll8M6fAf+EfMOPVlPCZl7x3AucwQBrnsiGkvtFUQhirHUuU0tzm278\nt4+gEX/EY15ZK/QlnH8qHy02DNuBQjg8GVPKwJ0CgYATHdUKjNJG0dMkJ8pjjsI1\nXOYqFo7bXeA5iw6gvmhGTt0Oc7QkOt/VWyvGvRn4UPXcaZixEsFj+rKVlCbZG9gJ\nDvC3nKL8jGXiVs0eJot2WHZJlM04YqzSlaqBNW5O+p/IMmJ1q1zehGm1oIHq0RlA\ncO+a+H4tgy7YSbgYm32XKQ==\n-----END RSA PRIVATE KEY-----",
			  "snis": [
			  	"test.com"
			  ],
			  "status": 1,
			  "validity_start": 1740534524,
			  "validity_end": 1803606524
		    }`,
			shouldFail: false,
		},
		{
			name:     "Valid Consumer to write to the DATABASE",
			resource: constant.Consumer,
			jsonPath: "main.consumer",
			config: `{
			  "plugins": {
			    "authz-casbin": {
			  	"model": "path/to/model.conf",
			  	"policy": "path/to/policy.csv",
			  	"username": "admin"
			    }
			  },
			  "username": "consumer1"
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid StreamRoute",
			resource: constant.StreamRoute,
			jsonPath: "main.stream_route",
			config: `{
              "remote_addr": "127.0.0.1",
              "server_addr": "127.0.0.1",
              "server_port": 8000,
              "sni": "test.com",
              "protocol": {
                "name": "test",
                "conf": {}
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "limit-conn": {
                    "burst": 20,
                    "conn": 100,
                    "default_conn_delay": 0.1,
                    "key": "remote_addr"
                }
              }
            }`,
			shouldFail: false,
		},

		{
			name:     "Valid Route to write to the ETCD",
			resource: constant.Route,
			jsonPath: "main.route",
			config: `{
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid Service to write to the ETCD",
			resource: constant.Service,
			jsonPath: "main.service",
			config: `{
              "name": "service1",
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid Upstream to write to the ETCD",
			resource: constant.Upstream,
			jsonPath: "main.upstream",
			config: `{
		      "name": "upstream1",
			  "scheme": "http",
			  "nodes": [
		        {
		            "host": "111",
		            "port": 80,
		            "weight": 1
		        }
		      ],
		      "pass_host": "pass",
		      "type": "roundrobin",
		      "desc": "22"
		    }`,
			shouldFail: false,
		},
		{
			name:     "Valid SSLs to write to the ETCD",
			resource: constant.SSL,
			jsonPath: "main.ssl",
			config: `{
			  "cert": "-----BEGIN CERTIFICATE-----\nMIIDJzCCAg+gAwIBAgIRAJvCZRh2nejK7+Ss3AgrEa0wDQYJKoZIhvcNAQELBQAw\ngYoxEjAQBgNVBAMMCWxkZGdvLm5ldDEMMAoGA1UECwwDZGV2MQ4wDAYDVQQKDAVs\nZGRnbzELMAkGA1UEBhMCQ04xIzAhBgkqhkiG9w0BCQEWFGxlY2hlbmdhZG1pbkAx\nMjYuY29tMREwDwYDVQQHDAhzaGFuZ2hhaTERMA8GA1UECAwIc2hhbmdoYWkwHhcN\nMjUwMjI2MDE0ODQ0WhcNMjcwMjI2MDE0ODQ0WjATMREwDwYDVQQDDAh0ZXN0LmNv\nbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAIIJ82TMFlWOR7dDkJ0X\nLclmCUDlefEJY2laYPWxaCe3oaIndosUmgm5aovYUTWDRAByn56HPFub5fc2Kt9v\n5+HWVd149JuP43F5NXaUKbE6GuXUWR7WhorzIRbabvvkE4SdpkrGwthi6AxUnvKK\naHKn11hSk+MBUWxjhSJoQy/ds3fKSpq7j+LAMRmQo9a3uW/HBl7FdfWIH5ZTN3Q8\n+ZDMc2zrEqOXFBGFBwzsbcVGNppMkUBuYmxIp7O3slB7rH7oOkdpYReIwWQOOswO\nhbBu5UGqC8nMX0N0jhzMyxrvDOIFSjjKiXuu46qd+t/GxUB9+8ZJ/Fn3WsJ6iQf7\n+cMCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEARSufAXUin/eFxcpojYMZ6F3t6VYp\njiZ+3Sx+UjQ4mq3qq8eQ/r0haxGtw2GeMuyprfxj6YTX6erQlJKkDk8vJXpDbFR4\n4dj1g4VQDZshPH2j2HJ/4l/kAvbDy/Rj9eIdV0Ux+t8s7MYgP7yf35Nb1ejJyWhB\nPS56NWCyj43lJcwnUmH4EAvLiFdgGgiaPQdm2/XlyEd8UVZugihIgjlQ3XKwMwsb\nXFfjJdDgdhFO5jmtU+rdEQWuaJDCEEWQJfMFmWRGApri97T/14QOulTqCXfk8+Wq\nw4WMGMQt3zIALlf7Meknv2qfTxax3JAO8lf7KuN5A4S5SuqAHke9NfGzAA==\n-----END CERTIFICATE-----",
			  "key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCCCfNkzBZVjke3\nQ5CdFy3JZglA5XnxCWNpWmD1sWgnt6GiJ3aLFJoJuWqL2FE1g0QAcp+ehzxbm+X3\nNirfb+fh1lXdePSbj+NxeTV2lCmxOhrl1Fke1oaK8yEW2m775BOEnaZKxsLYYugM\nVJ7yimhyp9dYUpPjAVFsY4UiaEMv3bN3ykqau4/iwDEZkKPWt7lvxwZexXX1iB+W\nUzd0PPmQzHNs6xKjlxQRhQcM7G3FRjaaTJFAbmJsSKezt7JQe6x+6DpHaWEXiMFk\nDjrMDoWwbuVBqgvJzF9DdI4czMsa7wziBUo4yol7ruOqnfrfxsVAffvGSfxZ91rC\neokH+/nDAgMBAAECggEACSzKj4IW0VKInNWXjn3kLSGV5Y5LXEZdTUGjNbKetq6u\nKNK/+nApriX27ocEs9HfKmjr+jNwfsYxI5Ae1kT/B2AoDshJ+e/dDFSRARzTFD4V\nR8IDx7k7JPKikwo2am9dMS4uXXhIpxvTY4tU66f4Vp6hAwpQhOPC6vLaoeLZWrcg\nAjjPTud/1N8D+CMsnsrfLh9XPLvUZIqYm5DCgE6fFle1/X/YrqzzMzflCG3Ns5Gv\nMY0i1xR7baAj8nT9iG+MCvCW8Ak2++pweX2Hli6l5aqk+esDU/zUAdddJdtpufGT\nkobCOKtqNXzEj6UGrsQU/27dc1tQKt4VgRvsgC+aAQKBgQC5zySFCpqtZY/naKnw\nGXf1Pl7r8aTuWVA+8ziRiyPlyI60oMHhu0bSIoRIh7lpa8km/cNsJOMTFWmHUANT\ndu53icmSCO++M1d+nrl3aWYyqbAlFvqMPtiW5/pYRnWJi4GSQTonGY32EhmN1qo5\nJbmj7NVxRnX0g9OTX4+f5MdCUQKBgQCzKXzwim/KxeOeVURVu/LQGK+Or2Ssyzjr\nz8MPQ2OE5DX528hLkE5h0EVhffSrsTfQiiMIhzU/Rywa7khNRqsTmhFEHM5JI+Rl\nGZgGgG4T5Q3idfrx3jXGqMylmoR0pA+4aGpSGg135vuIhJWCn8RI/mgMl0KP6Nax\nSSZkex4B0wKBgFr470FwIrEY068SEHnsjk31fpX4lq7X7bEUdjLUM/wyCKSpPKPf\nhFon6ip0wTO7QR4lCoQtPzw9tJA6fZZk2XaPcLBeTbsK+iCVZ+ruIMpXSFWwfXUi\n4/pmk6yaurtgIU1RQD6ahWXgEMDgRDF8pfp7Xzl5rRDNZk52cCRx55kxAoGAV4/p\nTi56oKHCszl9ImGvNGE8PAIgtArGkQmDjcwjsWlPsAPoinXGuStvHUzP7bG5U6SP\nprVeIsUIG0ll8M6fAf+EfMOPVlPCZl7x3AucwQBrnsiGkvtFUQhirHUuU0tzm278\nt4+gEX/EY15ZK/QlnH8qHy02DNuBQjg8GVPKwJ0CgYATHdUKjNJG0dMkJ8pjjsI1\nXOYqFo7bXeA5iw6gvmhGTt0Oc7QkOt/VWyvGvRn4UPXcaZixEsFj+rKVlCbZG9gJ\nDvC3nKL8jGXiVs0eJot2WHZJlM04YqzSlaqBNW5O+p/IMmJ1q1zehGm1oIHq0RlA\ncO+a+H4tgy7YSbgYm32XKQ==\n-----END RSA PRIVATE KEY-----",
			  "snis": [
			  	"test.com"
			  ],
			  "status": 1,
			  "validity_start": 1740534524,
			  "validity_end": 1803606524
		    }`,
			shouldFail: false,
		},
		{
			name:     "Valid Consumer to write to the ETCD",
			resource: constant.Consumer,
			jsonPath: "main.consumer",
			config: `{
			  "plugins": {
			    "authz-casbin": {
			  	"model": "path/to/model.conf",
			  	"policy": "path/to/policy.csv",
			  	"username": "admin"
			    }
			  },
			  "username": "consumer1"
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid ConsumerGroup to write to the ETCD",
			resource: constant.ConsumerGroup,
			jsonPath: "main.consumer_group",
			config: `{
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid PluginConfig to write to the ETCD",
			resource: constant.PluginConfig,
			jsonPath: "main.plugin_config",
			config: `{
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid GlobalRule to write to the ETCD",
			resource: constant.GlobalRule,
			jsonPath: "main.global_rule",
			config: `{
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid PluginMetaData to write to the ETCD",
			resource: constant.PluginMetadata,
			jsonPath: "main.plugin_metadata",
			config: `{
              "id": "authz-casbin",
              "model": "rbac_model.conf",
              "policy": "rbac_policy.csv"
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid StreamRoute to write to the ETCD",
			resource: constant.StreamRoute,
			jsonPath: "main.stream_route",
			config: `{
              "remote_addr": "127.0.0.1",
              "server_addr": "127.0.0.1",
              "server_port": 8000,
              "sni": "test.com",
              "protocol": {
                "name": "test",
                "conf": {}
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "limit-conn": {
                    "burst": 20,
                    "conn": 100,
                    "default_conn_delay": 0.1,
                    "key": "remote_addr"
                }
              }
            }`,
			shouldFail: false,
		},

		{
			name:     "Invalid Route to write to the ETCD",
			resource: constant.Route,
			jsonPath: "main.route",
			config: `{
			  "test_field": "test_value",
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: true,
		},
		{
			name:     "Invalid Service to write to the ETCD",
			resource: constant.Service,
			jsonPath: "main.service",
			config: `{
			  "test_field": "test_value",
              "name": "service1",
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: true,
		},
		{
			name:     "Invalid Upstream to write to the ETCD",
			resource: constant.Upstream,
			jsonPath: "main.upstream",
			config: `{
			  "test_field": "test_value",
		      "name": "upstream1",
			  "scheme": "http",
			  "nodes": [
		        {
		            "host": "111",
		            "port": 80,
		            "weight": 1
		        }
		      ],
		      "pass_host": "pass",
		      "type": "roundrobin",
		      "desc": "22"
		    }`,
			shouldFail: true,
		},
		{
			name:     "Invalid SSLs to write to the ETCD",
			resource: constant.SSL,
			jsonPath: "main.ssl",
			config: `{
			  "test_field": "test_value",
			  "name": "ssl1",
			  "cert": "-----BEGIN CERTIFICATE-----\nMIIDJzCCAg+gAwIBAgIRAJvCZRh2nejK7+Ss3AgrEa0wDQYJKoZIhvcNAQELBQAw\ngYoxEjAQBgNVBAMMCWxkZGdvLm5ldDEMMAoGA1UECwwDZGV2MQ4wDAYDVQQKDAVs\nZGRnbzELMAkGA1UEBhMCQ04xIzAhBgkqhkiG9w0BCQEWFGxlY2hlbmdhZG1pbkAx\nMjYuY29tMREwDwYDVQQHDAhzaGFuZ2hhaTERMA8GA1UECAwIc2hhbmdoYWkwHhcN\nMjUwMjI2MDE0ODQ0WhcNMjcwMjI2MDE0ODQ0WjATMREwDwYDVQQDDAh0ZXN0LmNv\nbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAIIJ82TMFlWOR7dDkJ0X\nLclmCUDlefEJY2laYPWxaCe3oaIndosUmgm5aovYUTWDRAByn56HPFub5fc2Kt9v\n5+HWVd149JuP43F5NXaUKbE6GuXUWR7WhorzIRbabvvkE4SdpkrGwthi6AxUnvKK\naHKn11hSk+MBUWxjhSJoQy/ds3fKSpq7j+LAMRmQo9a3uW/HBl7FdfWIH5ZTN3Q8\n+ZDMc2zrEqOXFBGFBwzsbcVGNppMkUBuYmxIp7O3slB7rH7oOkdpYReIwWQOOswO\nhbBu5UGqC8nMX0N0jhzMyxrvDOIFSjjKiXuu46qd+t/GxUB9+8ZJ/Fn3WsJ6iQf7\n+cMCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEARSufAXUin/eFxcpojYMZ6F3t6VYp\njiZ+3Sx+UjQ4mq3qq8eQ/r0haxGtw2GeMuyprfxj6YTX6erQlJKkDk8vJXpDbFR4\n4dj1g4VQDZshPH2j2HJ/4l/kAvbDy/Rj9eIdV0Ux+t8s7MYgP7yf35Nb1ejJyWhB\nPS56NWCyj43lJcwnUmH4EAvLiFdgGgiaPQdm2/XlyEd8UVZugihIgjlQ3XKwMwsb\nXFfjJdDgdhFO5jmtU+rdEQWuaJDCEEWQJfMFmWRGApri97T/14QOulTqCXfk8+Wq\nw4WMGMQt3zIALlf7Meknv2qfTxax3JAO8lf7KuN5A4S5SuqAHke9NfGzAA==\n-----END CERTIFICATE-----",
			  "key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCCCfNkzBZVjke3\nQ5CdFy3JZglA5XnxCWNpWmD1sWgnt6GiJ3aLFJoJuWqL2FE1g0QAcp+ehzxbm+X3\nNirfb+fh1lXdePSbj+NxeTV2lCmxOhrl1Fke1oaK8yEW2m775BOEnaZKxsLYYugM\nVJ7yimhyp9dYUpPjAVFsY4UiaEMv3bN3ykqau4/iwDEZkKPWt7lvxwZexXX1iB+W\nUzd0PPmQzHNs6xKjlxQRhQcM7G3FRjaaTJFAbmJsSKezt7JQe6x+6DpHaWEXiMFk\nDjrMDoWwbuVBqgvJzF9DdI4czMsa7wziBUo4yol7ruOqnfrfxsVAffvGSfxZ91rC\neokH+/nDAgMBAAECggEACSzKj4IW0VKInNWXjn3kLSGV5Y5LXEZdTUGjNbKetq6u\nKNK/+nApriX27ocEs9HfKmjr+jNwfsYxI5Ae1kT/B2AoDshJ+e/dDFSRARzTFD4V\nR8IDx7k7JPKikwo2am9dMS4uXXhIpxvTY4tU66f4Vp6hAwpQhOPC6vLaoeLZWrcg\nAjjPTud/1N8D+CMsnsrfLh9XPLvUZIqYm5DCgE6fFle1/X/YrqzzMzflCG3Ns5Gv\nMY0i1xR7baAj8nT9iG+MCvCW8Ak2++pweX2Hli6l5aqk+esDU/zUAdddJdtpufGT\nkobCOKtqNXzEj6UGrsQU/27dc1tQKt4VgRvsgC+aAQKBgQC5zySFCpqtZY/naKnw\nGXf1Pl7r8aTuWVA+8ziRiyPlyI60oMHhu0bSIoRIh7lpa8km/cNsJOMTFWmHUANT\ndu53icmSCO++M1d+nrl3aWYyqbAlFvqMPtiW5/pYRnWJi4GSQTonGY32EhmN1qo5\nJbmj7NVxRnX0g9OTX4+f5MdCUQKBgQCzKXzwim/KxeOeVURVu/LQGK+Or2Ssyzjr\nz8MPQ2OE5DX528hLkE5h0EVhffSrsTfQiiMIhzU/Rywa7khNRqsTmhFEHM5JI+Rl\nGZgGgG4T5Q3idfrx3jXGqMylmoR0pA+4aGpSGg135vuIhJWCn8RI/mgMl0KP6Nax\nSSZkex4B0wKBgFr470FwIrEY068SEHnsjk31fpX4lq7X7bEUdjLUM/wyCKSpPKPf\nhFon6ip0wTO7QR4lCoQtPzw9tJA6fZZk2XaPcLBeTbsK+iCVZ+ruIMpXSFWwfXUi\n4/pmk6yaurtgIU1RQD6ahWXgEMDgRDF8pfp7Xzl5rRDNZk52cCRx55kxAoGAV4/p\nTi56oKHCszl9ImGvNGE8PAIgtArGkQmDjcwjsWlPsAPoinXGuStvHUzP7bG5U6SP\nprVeIsUIG0ll8M6fAf+EfMOPVlPCZl7x3AucwQBrnsiGkvtFUQhirHUuU0tzm278\nt4+gEX/EY15ZK/QlnH8qHy02DNuBQjg8GVPKwJ0CgYATHdUKjNJG0dMkJ8pjjsI1\nXOYqFo7bXeA5iw6gvmhGTt0Oc7QkOt/VWyvGvRn4UPXcaZixEsFj+rKVlCbZG9gJ\nDvC3nKL8jGXiVs0eJot2WHZJlM04YqzSlaqBNW5O+p/IMmJ1q1zehGm1oIHq0RlA\ncO+a+H4tgy7YSbgYm32XKQ==\n-----END RSA PRIVATE KEY-----",
			  "snis": [
			  	"test.com"
			  ],
			  "status": 1,
			  "validity_start": 1740534524,
			  "validity_end": 1803606524
		    }`,
			shouldFail: true,
		},
		{
			name:     "Invalid Consumer to write to the ETCD",
			resource: constant.Consumer,
			jsonPath: "main.consumer",
			config: `{
			  "test_field": "test_value",
			  "plugins": {
			    "authz-casbin": {
			  	"model": "path/to/model.conf",
			  	"policy": "path/to/policy.csv",
			  	"username": "admin"
			    }
			  },
			  "username": "consumer1"
            }`,
			shouldFail: true,
		},
		{
			name:     "Invalid ConsumerGroup to write to the ETCD",
			resource: constant.ConsumerGroup,
			jsonPath: "main.consumer_group",
			config: `{
			  "test_field": "test_value",
              "name": "consumer_group1",
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: true,
		},
		{
			name:     "Invalid PluginConfig to write to the ETCD",
			resource: constant.PluginConfig,
			jsonPath: "main.plugin_config",
			config: `{
			  "test_field": "test_value",
              "name": "plugin_config1",
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: true,
		},
		{
			name:     "Invalid GlobalRule to write to the ETCD",
			resource: constant.GlobalRule,
			jsonPath: "main.global_rule",
			config: `{
			  "test_field": "test_value",
              "name": "global_rule1",
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: true,
		},
		{
			name:     "Invalid StreamRoute to write to the ETCD",
			resource: constant.StreamRoute,
			jsonPath: "main.stream_route",
			config: `{
			  "test_field": "test_value",
              "name": "stream1",
              "remote_addr": "127.0.0.1",
              "server_addr": "127.0.0.1",
              "server_port": 8000,
              "sni": "test.com",
              "protocol": {
                "name": "test",
                "conf": {}
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "limit-conn": {
                    "burst": 20,
                    "conn": 100,
                    "default_conn_delay": 0.1,
                    "key": "remote_addr"
                }
              }
            }`,
			shouldFail: true,
		},
	}

	for _, version := range APISIXVersionList {
		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				validator, err := NewAPISIXJsonSchemaValidator(version, tt.resource, tt.jsonPath)
				assert.NoError(t, err)

				err = validator.Validate(json.RawMessage(tt.config))
				if tt.shouldFail {
					assert.Error(t, err)
				} else {
					assert.NoError(t, err)
				}
			})
		}
	}
}

func TestValidateVarItem(t *testing.T) {
	tests := []struct {
		name       string
		item       []any
		shouldFail bool
	}{
		{
			name: "Valid Triple",
			item: []any{
				"arg_id",
				"==",
				"123",
			},
			shouldFail: false,
		},
		{
			name: "Valid Quadruple",
			item: []any{
				"arg_id",
				"!",
				"==",
				"123",
			},
			shouldFail: false,
		},
		{
			name: "Invalid Length",
			item: []any{
				"arg_id",
				"==",
			},
			shouldFail: true,
		},
		{
			name: "Invalid First Element",
			item: []any{
				123,
				"==",
				"123",
			},
			shouldFail: true,
		},
		{
			name: "Invalid Quadruple Second Element",
			item: []any{
				"arg_id",
				"invalid",
				"==",
				"123",
			},
			shouldFail: true,
		},
		{
			name: "Invalid Operator",
			item: []any{
				"arg_id",
				"invalid_op",
				"123",
			},
			shouldFail: true,
		},
		{
			name: "Empty Value",
			item: []any{
				"arg_id",
				"==",
				nil,
			},
			shouldFail: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateVarItem(tt.item)
			if tt.shouldFail {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestCheckVars(t *testing.T) {
	tests := []struct {
		name       string
		vars       []any
		shouldFail bool
	}{
		{
			name: "Valid Vars",
			vars: []any{
				[]any{
					"arg_id",
					"==",
					"123",
				},
				[]any{
					"http_x_header",
					"!",
					"~~",
					"test.*",
				},
			},
			shouldFail: false,
		},
		{
			name:       "Empty Vars",
			vars:       []any{},
			shouldFail: false,
		},
		{
			name: "Invalid Item Type",
			vars: []any{
				"invalid_item",
			},
			shouldFail: true,
		},
		{
			name: "Invalid Var Item",
			vars: []any{
				[]any{
					"arg_id",
					"invalid_op",
					"123",
				},
			},
			shouldFail: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := checkVars(tt.vars)
			if tt.shouldFail {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestAPISIXJsonSchemaValidatorCHashKeySchemaCheck(t *testing.T) {
	tests := []struct {
		name       string
		upstream   *entity.UpstreamDef
		version    constant.APISIXVersion
		shouldFail bool
	}{
		{
			name: "Valid HashOn consumer",
			upstream: &entity.UpstreamDef{
				HashOn: "consumer",
			},
			version:    constant.APISIXVersion313,
			shouldFail: false,
		},
		{
			name: "Valid HashOn vars",
			upstream: &entity.UpstreamDef{
				HashOn: "vars",
				Key:    "arg_id",
			},
			version:    constant.APISIXVersion313,
			shouldFail: false,
		},
		{
			name: "Valid HashOn header",
			upstream: &entity.UpstreamDef{
				HashOn: "header",
				Key:    "X-User-Id",
			},
			version:    constant.APISIXVersion313,
			shouldFail: false,
		},
		{
			name: "Valid HashOn cookie",
			upstream: &entity.UpstreamDef{
				HashOn: "cookie",
				Key:    "session_id",
			},
			version:    constant.APISIXVersion313,
			shouldFail: false,
		},
		{
			name: "Invalid HashOn type",
			upstream: &entity.UpstreamDef{
				HashOn: "invalid",
			},
			version:    constant.APISIXVersion313,
			shouldFail: true,
		},
		{
			name: "Missing schema for vars",
			upstream: &entity.UpstreamDef{
				HashOn: "vars",
				Key:    "arg_id",
			},
			version:    "invalid_version",
			shouldFail: true,
		},
		{
			name: "Invalid key schema",
			upstream: &entity.UpstreamDef{
				HashOn: "vars",
				Key:    "",
			},
			version:    constant.APISIXVersion313,
			shouldFail: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			validator := &APISIXJsonSchemaValidator{
				version: tt.version,
			}
			err := validator.cHashKeySchemaCheck(tt.upstream)
			if tt.shouldFail {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestAPISIXJsonSchemaValidatorCheckUpstream(t *testing.T) {
	tests := []struct {
		name       string
		upstream   *entity.UpstreamDef
		shouldFail bool
	}{
		{
			name: "Valid Upstream",
			upstream: &entity.UpstreamDef{
				PassHost: "node",
				Nodes:    []*entity.Node{{Host: "127.0.0.1", Port: 80, Weight: 1}},
			},
			shouldFail: false,
		},
		{
			name: "Valid Multiple Nodes with PassHost node",
			upstream: &entity.UpstreamDef{
				PassHost: "node",
				Nodes: []*entity.Node{
					{Host: "127.0.0.1", Port: 80, Weight: 1},
					{Host: "127.0.0.2", Port: 80, Weight: 1},
				},
			},
			shouldFail: false,
		},
		{
			name: "Rewrite PassHost with NonEmpty UpstreamHost",
			upstream: &entity.UpstreamDef{
				PassHost:     "rewrite",
				UpstreamHost: "example.com",
			},
			shouldFail: false,
		},
		{
			name: "Rewrite PassHost with Empty UpstreamHost",
			upstream: &entity.UpstreamDef{
				PassHost:     "rewrite",
				UpstreamHost: "",
			},
			shouldFail: true,
		},
		{
			name: "Missing Key",
			upstream: &entity.UpstreamDef{
				PassHost:     "node",
				Type:         "chash",
				UpstreamHost: "example.com",
			},
			shouldFail: true,
		},
		{
			name: "PassHost node with multiple nodes in map format",
			upstream: &entity.UpstreamDef{
				PassHost: "node",
				Scheme:   "https",
				Type:     "roundrobin",
				Nodes: map[string]float64{
					"httpbin.org:443":  1,
					"mock.api7.ai:443": 1,
				},
			},
			shouldFail: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			validator := &APISIXJsonSchemaValidator{}
			err := validator.checkUpstream(tt.upstream)
			if tt.shouldFail {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestCheckRemoteAddr(t *testing.T) {
	tests := []struct {
		name        string
		remoteAddrs []string
		shouldFail  bool
	}{
		{
			name:        "Valid Addresses",
			remoteAddrs: []string{"127.0.0.1", "192.168.1.1"},
			shouldFail:  false,
		},
		{
			name:        "Empty Address",
			remoteAddrs: []string{""},
			shouldFail:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := checkRemoteAddr(tt.remoteAddrs)
			if tt.shouldFail {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestNewAPISIXSchemaValidator(t *testing.T) {
	type testMap struct {
		name       string
		version    constant.APISIXVersion
		jsonPath   string
		shouldFail bool
	}

	tests := []testMap{}
	// 包含所有版本和资源类型
	for _, version := range APISIXVersionList {
		for _, resource := range constant.ResourceTypeList {
			resourceTests := []testMap{
				{
					name:       "Valid Schema",
					version:    version,
					jsonPath:   fmt.Sprintf("main.%s", resource.String()),
					shouldFail: false,
				},
				{
					name:       "Invalid Version",
					version:    "invalid_version",
					jsonPath:   fmt.Sprintf("main.%s", resource.String()),
					shouldFail: true,
				},
				{
					name:       "Invalid Path",
					version:    version,
					jsonPath:   "invalid.path",
					shouldFail: true,
				},
			}
			tests = append(tests, resourceTests...)
		}
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := NewApisixSchemaValidator(tt.version, tt.jsonPath)
			if tt.shouldFail {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestAPISIXSchemaValidatorValidate(t *testing.T) {
	tests := []struct {
		name       string
		resource   constant.APISIXResource
		jsonPath   string
		config     string
		shouldFail bool
	}{
		{
			name:     "Valid Route",
			resource: constant.Route,
			jsonPath: "main.route",
			config: `{
              "name": "route1",
              "methods": [
                "GET",
                "POST"
              ],
              "enable_websocket": false,
              "uris": [
                "/test"
              ],
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid Service",
			resource: constant.Service,
			jsonPath: "main.service",
			config: `{
              "name": "service1",
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid Upstream",
			resource: constant.Upstream,
			jsonPath: "main.upstream",
			config: `{
		      "name": "upstream1",
			  "scheme": "http",
			  "nodes": [
		        {
		            "host": "111",
		            "port": 80,
		            "weight": 1
		        }
		      ],
		      "pass_host": "pass",
		      "type": "roundrobin",
		      "desc": "22"
		    }`,
			shouldFail: false,
		},
		{
			name:     "Valid SSLs",
			resource: constant.SSL,
			jsonPath: "main.ssl",
			config: `{
			  "name": "ssl1",
			  "cert": "-----BEGIN CERTIFICATE-----\nMIIDJzCCAg+gAwIBAgIRAJvCZRh2nejK7+Ss3AgrEa0wDQYJKoZIhvcNAQELBQAw\ngYoxEjAQBgNVBAMMCWxkZGdvLm5ldDEMMAoGA1UECwwDZGV2MQ4wDAYDVQQKDAVs\nZGRnbzELMAkGA1UEBhMCQ04xIzAhBgkqhkiG9w0BCQEWFGxlY2hlbmdhZG1pbkAx\nMjYuY29tMREwDwYDVQQHDAhzaGFuZ2hhaTERMA8GA1UECAwIc2hhbmdoYWkwHhcN\nMjUwMjI2MDE0ODQ0WhcNMjcwMjI2MDE0ODQ0WjATMREwDwYDVQQDDAh0ZXN0LmNv\nbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAIIJ82TMFlWOR7dDkJ0X\nLclmCUDlefEJY2laYPWxaCe3oaIndosUmgm5aovYUTWDRAByn56HPFub5fc2Kt9v\n5+HWVd149JuP43F5NXaUKbE6GuXUWR7WhorzIRbabvvkE4SdpkrGwthi6AxUnvKK\naHKn11hSk+MBUWxjhSJoQy/ds3fKSpq7j+LAMRmQo9a3uW/HBl7FdfWIH5ZTN3Q8\n+ZDMc2zrEqOXFBGFBwzsbcVGNppMkUBuYmxIp7O3slB7rH7oOkdpYReIwWQOOswO\nhbBu5UGqC8nMX0N0jhzMyxrvDOIFSjjKiXuu46qd+t/GxUB9+8ZJ/Fn3WsJ6iQf7\n+cMCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEARSufAXUin/eFxcpojYMZ6F3t6VYp\njiZ+3Sx+UjQ4mq3qq8eQ/r0haxGtw2GeMuyprfxj6YTX6erQlJKkDk8vJXpDbFR4\n4dj1g4VQDZshPH2j2HJ/4l/kAvbDy/Rj9eIdV0Ux+t8s7MYgP7yf35Nb1ejJyWhB\nPS56NWCyj43lJcwnUmH4EAvLiFdgGgiaPQdm2/XlyEd8UVZugihIgjlQ3XKwMwsb\nXFfjJdDgdhFO5jmtU+rdEQWuaJDCEEWQJfMFmWRGApri97T/14QOulTqCXfk8+Wq\nw4WMGMQt3zIALlf7Meknv2qfTxax3JAO8lf7KuN5A4S5SuqAHke9NfGzAA==\n-----END CERTIFICATE-----",
			  "key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCCCfNkzBZVjke3\nQ5CdFy3JZglA5XnxCWNpWmD1sWgnt6GiJ3aLFJoJuWqL2FE1g0QAcp+ehzxbm+X3\nNirfb+fh1lXdePSbj+NxeTV2lCmxOhrl1Fke1oaK8yEW2m775BOEnaZKxsLYYugM\nVJ7yimhyp9dYUpPjAVFsY4UiaEMv3bN3ykqau4/iwDEZkKPWt7lvxwZexXX1iB+W\nUzd0PPmQzHNs6xKjlxQRhQcM7G3FRjaaTJFAbmJsSKezt7JQe6x+6DpHaWEXiMFk\nDjrMDoWwbuVBqgvJzF9DdI4czMsa7wziBUo4yol7ruOqnfrfxsVAffvGSfxZ91rC\neokH+/nDAgMBAAECggEACSzKj4IW0VKInNWXjn3kLSGV5Y5LXEZdTUGjNbKetq6u\nKNK/+nApriX27ocEs9HfKmjr+jNwfsYxI5Ae1kT/B2AoDshJ+e/dDFSRARzTFD4V\nR8IDx7k7JPKikwo2am9dMS4uXXhIpxvTY4tU66f4Vp6hAwpQhOPC6vLaoeLZWrcg\nAjjPTud/1N8D+CMsnsrfLh9XPLvUZIqYm5DCgE6fFle1/X/YrqzzMzflCG3Ns5Gv\nMY0i1xR7baAj8nT9iG+MCvCW8Ak2++pweX2Hli6l5aqk+esDU/zUAdddJdtpufGT\nkobCOKtqNXzEj6UGrsQU/27dc1tQKt4VgRvsgC+aAQKBgQC5zySFCpqtZY/naKnw\nGXf1Pl7r8aTuWVA+8ziRiyPlyI60oMHhu0bSIoRIh7lpa8km/cNsJOMTFWmHUANT\ndu53icmSCO++M1d+nrl3aWYyqbAlFvqMPtiW5/pYRnWJi4GSQTonGY32EhmN1qo5\nJbmj7NVxRnX0g9OTX4+f5MdCUQKBgQCzKXzwim/KxeOeVURVu/LQGK+Or2Ssyzjr\nz8MPQ2OE5DX528hLkE5h0EVhffSrsTfQiiMIhzU/Rywa7khNRqsTmhFEHM5JI+Rl\nGZgGgG4T5Q3idfrx3jXGqMylmoR0pA+4aGpSGg135vuIhJWCn8RI/mgMl0KP6Nax\nSSZkex4B0wKBgFr470FwIrEY068SEHnsjk31fpX4lq7X7bEUdjLUM/wyCKSpPKPf\nhFon6ip0wTO7QR4lCoQtPzw9tJA6fZZk2XaPcLBeTbsK+iCVZ+ruIMpXSFWwfXUi\n4/pmk6yaurtgIU1RQD6ahWXgEMDgRDF8pfp7Xzl5rRDNZk52cCRx55kxAoGAV4/p\nTi56oKHCszl9ImGvNGE8PAIgtArGkQmDjcwjsWlPsAPoinXGuStvHUzP7bG5U6SP\nprVeIsUIG0ll8M6fAf+EfMOPVlPCZl7x3AucwQBrnsiGkvtFUQhirHUuU0tzm278\nt4+gEX/EY15ZK/QlnH8qHy02DNuBQjg8GVPKwJ0CgYATHdUKjNJG0dMkJ8pjjsI1\nXOYqFo7bXeA5iw6gvmhGTt0Oc7QkOt/VWyvGvRn4UPXcaZixEsFj+rKVlCbZG9gJ\nDvC3nKL8jGXiVs0eJot2WHZJlM04YqzSlaqBNW5O+p/IMmJ1q1zehGm1oIHq0RlA\ncO+a+H4tgy7YSbgYm32XKQ==\n-----END RSA PRIVATE KEY-----",
			  "snis": [
			  	"test.com"
			  ],
			  "status": 1,
			  "validity_start": 1740534524,
			  "validity_end": 1803606524
		    }`,
			shouldFail: false,
		},
		{
			name:     "Valid Consumer",
			resource: constant.Consumer,
			jsonPath: "main.consumer",
			config: `{
			  "plugins": {
			    "authz-casbin": {
			  	"model": "path/to/model.conf",
			  	"policy": "path/to/policy.csv",
			  	"username": "admin"
			    }
			  },
			  "username": "consumer1"
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid ConsumerGroup",
			resource: constant.ConsumerGroup,
			jsonPath: "main.consumer_group",
			config: `{
              "name": "consumer_group1",
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid PluginConfig",
			resource: constant.PluginConfig,
			jsonPath: "main.plugin_config",
			config: `{
              "name": "plugin_config1",
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid GlobalRule",
			resource: constant.GlobalRule,
			jsonPath: "main.global_rule",
			config: `{
              "name": "global_rule1",
              "plugins": {
                "authz-casbin": {
                  "model": "path/to/model.conf",
                  "policy": "path/to/policy.csv",
                  "username": "admin"
                }
              }
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid PluginMetaData",
			resource: constant.PluginMetadata,
			jsonPath: "main.plugin_metadata",
			config: `{
              "id": "authz-casbin",
              "name": "authz-casbin",
              "model": "rbac_model.conf",
              "policy": "rbac_policy.csv"
            }`,
			shouldFail: false,
		},
		{
			name:     "Valid StreamRoute",
			resource: constant.StreamRoute,
			jsonPath: "main.stream_route",
			config: `{
              "name": "stream1",
              "remote_addr": "127.0.0.1",
              "server_addr": "127.0.0.1",
              "server_port": 8000,
              "sni": "test.com",
              "protocol": {
                "name": "test",
                "conf": {}
              },
              "upstream": {
                "scheme": "http",
                "nodes": [
                  {
                    "host": "1.1.1.1",
                    "port": 80,
                    "weight": 1
                  }
                ],
                "pass_host": "pass",
                "type": "roundrobin"
              },
              "plugins": {
                "limit-conn": {
                    "burst": 20,
                    "conn": 100,
                    "default_conn_delay": 0.1,
                    "key": "remote_addr"
                }
              }
            }`,
			shouldFail: false,
		},
	}

	for _, version := range APISIXVersionList {
		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				validator, err := NewApisixSchemaValidator(version, tt.jsonPath)
				assert.NoError(t, err)

				err = validator.Validate(json.RawMessage(tt.config))
				if tt.shouldFail {
					assert.Error(t, err)
				} else {
					assert.NoError(t, err)
				}
			})
		}
	}
}

func TestGetResourceIdentification(t *testing.T) {
	tests := []struct {
		name       string
		config     string
		shouldFail string
	}{
		{
			name:       "ID Field",
			config:     `{"id": "test-id"}`,
			shouldFail: "test-id",
		},
		{
			name:       "Name Field",
			config:     `{"name": "test-name"}`,
			shouldFail: "test-name",
		},
		{
			name:       "Username Field",
			config:     `{"username": "test-user"}`,
			shouldFail: "test-user",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GetResourceIdentification(json.RawMessage(tt.config))
			assert.Equal(t, tt.shouldFail, result)
		})
	}
}
