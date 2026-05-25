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

package registry

import (
	"context"
	"sync"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/logging"
)

var _ = Describe("ApisixEtcdRegistry", func() {
	Describe("parseResource", func() {
		var registry *ApisixEtcdRegistry

		Context("when parsing routes", func() {
			BeforeEach(func() {
				registry = &ApisixEtcdRegistry{
					Prefix:    "/apisix/routes/",
					resources: make(map[string]entity.ApisixResource),
					mux:       sync.RWMutex{},
					logger:    logging.GetLogger().Named("test-registry"),
				}
			})

			It("should parse route resource correctly", func() {
				key := []byte("/apisix/routes/test-route")
				value := []byte(`{
					"id": "test-route",
					"uri": "/test",
					"status": 1,
					"labels": {
						"gateway.bk.tencent.com/gateway": "test-gateway",
						"gateway.bk.tencent.com/stage": "test-stage"
					}
				}`)

				resource, err := registry.parseResource(key, value)
				Expect(err).To(BeNil())
				Expect(resource).NotTo(BeNil())

				route, ok := resource.(*entity.Route)
				Expect(ok).To(BeTrue())
				Expect(route.ID).To(Equal("test-route"))
				Expect(route.URI).To(Equal("/test"))
			})

			It("should return nil for empty value", func() {
				key := []byte("/apisix/routes/")
				value := []byte("")

				resource, err := registry.parseResource(key, value)
				Expect(err).To(BeNil())
				Expect(resource).To(BeNil())
			})

			It("should return nil for init dir value", func() {
				key := []byte("/apisix/routes/test")
				value := []byte(constant.SkippedValueEtcdInitDir)

				resource, err := registry.parseResource(key, value)
				Expect(err).To(BeNil())
				Expect(resource).To(BeNil())
			})

			It("should return nil for empty object value", func() {
				key := []byte("/apisix/routes/test")
				value := []byte(constant.SkippedValueEtcdEmptyObject)

				resource, err := registry.parseResource(key, value)
				Expect(err).To(BeNil())
				Expect(resource).To(BeNil())
			})

			It("should return error for invalid JSON", func() {
				key := []byte("/apisix/routes/test")
				value := []byte("invalid json")

				resource, err := registry.parseResource(key, value)
				Expect(err).NotTo(BeNil())
				Expect(resource).To(BeNil())
			})
		})

		Context("when parsing services", func() {
			BeforeEach(func() {
				registry = &ApisixEtcdRegistry{
					Prefix:    "/apisix/services/",
					resources: make(map[string]entity.ApisixResource),
					mux:       sync.RWMutex{},
					logger:    logging.GetLogger().Named("test-registry"),
				}
			})

			It("should parse service resource correctly", func() {
				key := []byte("/apisix/services/test-service")
				value := []byte(`{
					"id": "test-service",
					"labels": {
						"gateway.bk.tencent.com/gateway": "test-gateway",
						"gateway.bk.tencent.com/stage": "test-stage"
					}
				}`)

				resource, err := registry.parseResource(key, value)
				Expect(err).To(BeNil())
				Expect(resource).NotTo(BeNil())

				service, ok := resource.(*entity.Service)
				Expect(ok).To(BeTrue())
				Expect(service.ID).To(Equal("test-service"))
			})
		})

		Context("when parsing SSL", func() {
			BeforeEach(func() {
				registry = &ApisixEtcdRegistry{
					Prefix:    "/apisix/ssls/",
					resources: make(map[string]entity.ApisixResource),
					mux:       sync.RWMutex{},
					logger:    logging.GetLogger().Named("test-registry"),
				}
			})

			It("should parse SSL resource correctly", func() {
				key := []byte("/apisix/ssls/test-ssl")
				value := []byte(`{
					"id": "test-ssl",
					"sni": "example.com",
					"status": 1,
					"labels": {
						"gateway.bk.tencent.com/gateway": "test-gateway",
						"gateway.bk.tencent.com/stage": "test-stage"
					}
				}`)

				resource, err := registry.parseResource(key, value)
				Expect(err).To(BeNil())
				Expect(resource).NotTo(BeNil())

				ssl, ok := resource.(*entity.SSL)
				Expect(ok).To(BeTrue())
				Expect(ssl.ID).To(Equal("test-ssl"))
				Expect(ssl.Sni).To(Equal("example.com"))
			})
		})

		Context("when parsing plugin_metadata", func() {
			BeforeEach(func() {
				registry = &ApisixEtcdRegistry{
					Prefix:    "/apisix/plugin_metadata/",
					resources: make(map[string]entity.ApisixResource),
					mux:       sync.RWMutex{},
					logger:    logging.GetLogger().Named("test-registry"),
				}
			})

			It("should parse plugin_metadata resource correctly", func() {
				key := []byte("/apisix/plugin_metadata/http-logger")
				value := []byte(`{
					"id": "http-logger",
					"log_format": {"host": "$host"}
				}`)

				resource, err := registry.parseResource(key, value)
				Expect(err).To(BeNil())
				Expect(resource).NotTo(BeNil())

				pm, ok := resource.(*entity.PluginMetadata)
				Expect(ok).To(BeTrue())
				Expect(pm.ID).To(Equal("http-logger"))
			})
		})

		Context("when parsing unknown resource type", func() {
			BeforeEach(func() {
				registry = &ApisixEtcdRegistry{
					Prefix:    "/apisix/unknown/",
					resources: make(map[string]entity.ApisixResource),
					mux:       sync.RWMutex{},
					logger:    logging.GetLogger().Named("test-registry"),
				}
			})

			It("should return error for unknown resource type", func() {
				key := []byte("/apisix/unknown/test")
				value := []byte(`{"id": "test"}`)

				resource, err := registry.parseResource(key, value)
				Expect(err).NotTo(BeNil())
				Expect(resource).To(BeNil())
			})
		})
	})

	Describe("GetStageResources", func() {
		var registry *ApisixEtcdRegistry

		BeforeEach(func() {
			registry = &ApisixEtcdRegistry{
				Prefix:    "/apisix/routes/",
				resources: make(map[string]entity.ApisixResource),
				mux:       sync.RWMutex{},
				logger:    logging.GetLogger().Named("test-registry"),
			}

			// Add test resources - stageKey format is "bk.release.{gateway}.{stage}"
			registry.resources["route1"] = &entity.Route{
				ResourceMetadata: entity.ResourceMetadata{
					ID: "route1",
					Labels: &entity.LabelInfo{
						Gateway: "gateway1",
						Stage:   "stage1",
					},
				},
			}
			registry.resources["route2"] = &entity.Route{
				ResourceMetadata: entity.ResourceMetadata{
					ID: "route2",
					Labels: &entity.LabelInfo{
						Gateway: "gateway1",
						Stage:   "stage2",
					},
				},
			}
			registry.resources["route3"] = &entity.Route{
				ResourceMetadata: entity.ResourceMetadata{
					ID: "route3",
					Labels: &entity.LabelInfo{
						Gateway: "gateway1",
						Stage:   "stage1",
					},
				},
			}
		})

		It("should return resources for specific stage", func() {
			// stageKey format is "bk.release.{gateway}.{stage}"
			resources := registry.GetStageResources("bk.release.gateway1.stage1")
			Expect(resources).To(HaveLen(2))
		})

		It("should return empty map for non-existent stage", func() {
			resources := registry.GetStageResources("bk.release.gateway1.stage3")
			Expect(resources).To(HaveLen(0))
		})
	})

	Describe("GetAllResources", func() {
		var registry *ApisixEtcdRegistry

		BeforeEach(func() {
			registry = &ApisixEtcdRegistry{
				Prefix:    "/apisix/routes/",
				resources: make(map[string]entity.ApisixResource),
				mux:       sync.RWMutex{},
				logger:    logging.GetLogger().Named("test-registry"),
			}

			registry.resources["route1"] = &entity.Route{
				ResourceMetadata: entity.ResourceMetadata{ID: "route1"},
			}
			registry.resources["route2"] = &entity.Route{
				ResourceMetadata: entity.ResourceMetadata{ID: "route2"},
			}
		})

		It("should return all resources", func() {
			resources := registry.GetAllResources()
			Expect(resources).To(HaveLen(2))
			Expect(resources).To(HaveKey("route1"))
			Expect(resources).To(HaveKey("route2"))
		})

		It("should return a copy of resources", func() {
			resources := registry.GetAllResources()
			resources["new-route"] = &entity.Route{}

			// Original should not be modified
			Expect(registry.resources).To(HaveLen(2))
		})
	})

	Describe("Close", func() {
		It("should cancel context when Close is called", func() {
			ctx, cancel := context.WithCancel(context.Background())
			registry := &ApisixEtcdRegistry{
				Prefix:    "/apisix/routes/",
				resources: make(map[string]entity.ApisixResource),
				mux:       sync.RWMutex{},
				ctx:       ctx,
				cancel:    cancel,
				logger:    logging.GetLogger().Named("test-registry"),
			}

			registry.Close()

			// Context should be cancelled
			select {
			case <-registry.ctx.Done():
				// Success
			default:
				Fail("context should be cancelled after Close")
			}
		})

		It("should not panic when cancel is nil", func() {
			registry := &ApisixEtcdRegistry{
				Prefix:    "/apisix/routes/",
				resources: make(map[string]entity.ApisixResource),
				mux:       sync.RWMutex{},
				cancel:    nil,
				logger:    logging.GetLogger().Named("test-registry"),
			}

			Expect(func() {
				registry.Close()
			}).NotTo(Panic())
		})
	})
})
