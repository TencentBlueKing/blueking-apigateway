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

package registry

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/prometheus/client_golang/prometheus"
	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/server/v3/embed"

	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/logging"
	"operator/pkg/metric"
)

var _ = Describe("APIGWEtcdRegistry", func() {
	Describe("NewAPIGWEtcdRegistry", func() {
		It("should create a new registry with correct fields", func() {
			registry := NewAPIGWEtcdRegistry(nil, "/bk-gateway", 0)
			Expect(registry).NotTo(BeNil())
			Expect(registry.keyPrefix).To(Equal("/bk-gateway"))
			Expect(registry.logger).NotTo(BeNil())
			// Default buffer size should be 1000 when 0 is passed
			Expect(registry.watchEventChanSize).To(Equal(100))
		})

		It("should use custom buffer size when provided", func() {
			registry := NewAPIGWEtcdRegistry(nil, "/bk-gateway", 500)
			Expect(registry.watchEventChanSize).To(Equal(500))
		})
	})

	Describe("extractResourceMetadata", func() {
		var registry *APIGWEtcdRegistry

		BeforeEach(func() {
			registry = &APIGWEtcdRegistry{
				keyPrefix: "/bk-gateway-apigw",
				logger:    logging.GetLogger().Named("test-registry"),
			}
		})

		Context("when parsing plugin_metadata", func() {
			It("should extract plugin_metadata correctly", func() {
				key := "/bk-gateway-apigw/v2/global/plugin_metadata/bk-concurrency-limit"
				value := []byte(`{
					"id": "bk-concurrency-limit",
					"name": "bk-concurrency-limit",
					"labels": {}
				}`)

				metadata, err := registry.extractResourceMetadata(key, value)
				Expect(err).To(BeNil())
				Expect(metadata.ID).To(Equal("bk-concurrency-limit"))
				Expect(metadata.Kind).To(Equal(constant.PluginMetadata))
				Expect(metadata.APIVersion).To(Equal("v2"))
			})
		})

		Context("when parsing bk_release", func() {
			It("should extract bk_release correctly", func() {
				key := "/bk-gateway-apigw/v2/gateway/bk-default/default/_bk_release/bk.release.bk-default.default"
				value := []byte(`{
					"id": "bk.release.bk-default.default",
					"name": "bk.release.bk-default.default",
					"labels": {
						"gateway.bk.tencent.com/gateway": "bk-default",
						"gateway.bk.tencent.com/stage": "default"
					}
				}`)

				metadata, err := registry.extractResourceMetadata(key, value)
				Expect(err).To(BeNil())
				Expect(metadata.ID).To(Equal("bk.release.bk-default.default"))
				Expect(metadata.Kind).To(Equal(constant.BkRelease))
				Expect(metadata.APIVersion).To(Equal("v2"))
			})
		})

		Context("when parsing route", func() {
			It("should extract route correctly", func() {
				key := "/bk-gateway-apigw/v2/gateway/bk-default/default/route/bk-default.default.test-route"
				value := []byte(`{
					"id": "bk-default.default.test-route",
					"name": "test-route",
					"labels": {
						"gateway.bk.tencent.com/gateway": "bk-default",
						"gateway.bk.tencent.com/stage": "default"
					}
				}`)

				metadata, err := registry.extractResourceMetadata(key, value)
				Expect(err).To(BeNil())
				Expect(metadata.Kind).To(Equal(constant.Route))
				Expect(metadata.APIVersion).To(Equal("v2"))
			})
		})

		Context("when parsing service", func() {
			It("should extract service correctly", func() {
				key := "/bk-gateway-apigw/v2/gateway/bk-default/default/service/bk-default.default.test-service"
				value := []byte(`{
					"id": "bk-default.default.test-service",
					"name": "test-service",
					"labels": {
						"gateway.bk.tencent.com/gateway": "bk-default",
						"gateway.bk.tencent.com/stage": "default"
					}
				}`)

				metadata, err := registry.extractResourceMetadata(key, value)
				Expect(err).To(BeNil())
				Expect(metadata.Kind).To(Equal(constant.Service))
				Expect(metadata.APIVersion).To(Equal("v2"))
			})
		})

		Context("when key is empty", func() {
			It("should return error", func() {
				key := ""
				value := []byte(`{"id": "test"}`)

				_, err := registry.extractResourceMetadata(key, value)
				Expect(err).NotTo(BeNil())
				Expect(err.Error()).To(ContainSubstring("empty key"))
			})
		})

		Context("when value is invalid JSON", func() {
			It("should return error", func() {
				key := "/bk-gateway-apigw/v2/gateway/bk-default/default/route/test"
				value := []byte(`invalid json`)

				_, err := registry.extractResourceMetadata(key, value)
				Expect(err).NotTo(BeNil())
			})
		})

		Context("when resource kind is not supported", func() {
			It("should return error", func() {
				key := "/bk-gateway-apigw/v2/gateway/bk-default/default/unknown/test"
				value := []byte(`{"id": "test", "labels": {}}`)

				_, err := registry.extractResourceMetadata(key, value)
				Expect(err).NotTo(BeNil())
				Expect(err.Error()).To(ContainSubstring("not support"))
			})
		})

		Context("when key segments are insufficient", func() {
			It("should return error for less than 7 segments", func() {
				key := "/bk-gateway-apigw/v2/gateway/test"
				value := []byte(`{"id": "test", "labels": {}}`)

				_, err := registry.extractResourceMetadata(key, value)
				Expect(err).NotTo(BeNil())
			})
		})
	})
})

// Helper function to create ReleaseInfo for tests
func createReleaseInfo(
	ctx context.Context,
	apiVersion, gateway, stage string,
	kind constant.APISIXResource,
) *entity.ReleaseInfo {
	return &entity.ReleaseInfo{
		ResourceMetadata: entity.ResourceMetadata{
			APIVersion: apiVersion,
			Kind:       kind,
			Labels: &entity.LabelInfo{
				Gateway: gateway,
				Stage:   stage,
			},
		},
		Ctx: ctx,
	}
}

var _ = Describe("APIGWEtcdRegistry with EmbedEtcd", func() {
	var (
		etcd     *embed.Etcd
		client   *clientv3.Client
		registry *APIGWEtcdRegistry
		ctx      context.Context
		reg      *prometheus.Registry
	)

	BeforeEach(func() {
		var err error
		ctx = context.Background()

		// Initialize metrics for testing
		reg = prometheus.NewRegistry()
		metric.InitMetric(reg)

		// Start embedded etcd
		etcd, client, err = startTestEtcd()
		Expect(err).ShouldNot(HaveOccurred())

		registry = NewAPIGWEtcdRegistry(client, "/bk-gateway-apigw", 100)
	})

	AfterEach(func() {
		if client != nil {
			client.Close()
		}
		if etcd != nil {
			etcd.Close()
			os.RemoveAll(etcd.Config().Dir)
		}
	})

	Describe("DeleteResourceByKey", func() {
		It("should delete resource successfully", func() {
			// First put a key
			key := "/bk-gateway-apigw/test-key"
			_, err := client.Put(ctx, key, "test-value")
			Expect(err).ShouldNot(HaveOccurred())

			// Verify it exists
			resp, err := client.Get(ctx, key)
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			// Delete it
			err = registry.DeleteResourceByKey(key)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify it's deleted
			resp, err = client.Get(ctx, key)
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(0))
		})

		It("should not error when deleting non-existent key", func() {
			err := registry.DeleteResourceByKey("/non-existent-key")
			Expect(err).ShouldNot(HaveOccurred())
		})
	})

	Describe("ListStageResources", func() {
		It("should return empty resources when no data exists", func() {
			releaseInfo := createReleaseInfo(
				ctx,
				"v2",
				"non-existent-gateway",
				"non-existent-stage",
				constant.Route,
			)

			resources, err := registry.ListStageResources(releaseInfo)
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resources).NotTo(BeNil())
			Expect(resources.Routes).To(HaveLen(0))
			Expect(resources.Services).To(HaveLen(0))
		})
	})

	Describe("ListGlobalResources", func() {
		It("should return empty resources when no data exists", func() {
			releaseInfo := createReleaseInfo(ctx, "v3", "", "", constant.PluginMetadata)

			resources, err := registry.ListGlobalResources(releaseInfo)
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resources).NotTo(BeNil())
			Expect(resources.PluginMetadata).To(HaveLen(0))
		})
	})

	Describe("Count", func() {
		It("should count resources correctly", func() {
			// Prepare test data
			for i := 0; i < 3; i++ {
				routeKey := fmt.Sprintf(
					"/bk-gateway-apigw/v2/gateway/test-gateway/test-stage/route/route%d",
					i,
				)
				routeValue := map[string]any{
					"id":   fmt.Sprintf("route%d", i),
					"name": fmt.Sprintf("route%d", i),
					"labels": map[string]any{
						"gateway.bk.tencent.com/gateway": "test-gateway",
						"gateway.bk.tencent.com/stage":   "test-stage",
					},
				}
				routeBytes, _ := json.Marshal(routeValue)
				_, err := client.Put(ctx, routeKey, string(routeBytes))
				Expect(err).ShouldNot(HaveOccurred())
			}

			releaseInfo := createReleaseInfo(ctx, "v2", "test-gateway", "test-stage", constant.Route)

			count, err := registry.Count(releaseInfo)
			Expect(err).ShouldNot(HaveOccurred())
			Expect(count).To(Equal(int64(3)))
		})

		It("should return 0 when no resources exist", func() {
			releaseInfo := createReleaseInfo(ctx, "v2", "non-existent", "non-existent", constant.Route)

			count, err := registry.Count(releaseInfo)
			Expect(err).ShouldNot(HaveOccurred())
			Expect(count).To(Equal(int64(0)))
		})
	})

	Describe("Watch", func() {
		It("should receive put events", func() {
			watchCtx, cancel := context.WithCancel(ctx)
			defer cancel()

			eventCh := registry.Watch(watchCtx)
			Expect(eventCh).NotTo(BeNil())

			// Wait for watch to be established
			time.Sleep(100 * time.Millisecond)

			// Put a route
			routeKey := "/bk-gateway-apigw/v2/gateway/test-gateway/test-stage/route/watch-route"
			routeValue := map[string]any{
				"id":   "watch-route",
				"name": "watch-route",
				"labels": map[string]any{
					"gateway.bk.tencent.com/gateway": "test-gateway",
					"gateway.bk.tencent.com/stage":   "test-stage",
				},
			}
			routeBytes, _ := json.Marshal(routeValue)
			_, err := client.Put(ctx, routeKey, string(routeBytes))
			Expect(err).ShouldNot(HaveOccurred())

			// Wait for event
			select {
			case event := <-eventCh:
				Expect(event).NotTo(BeNil())
				Expect(event.Kind).To(Equal(constant.Route))
			case <-time.After(2 * time.Second):
				Fail("timeout waiting for watch event")
			}
		})
	})

	Describe("StageReleaseVersion", func() {
		It("should return error when release not found", func() {
			releaseInfo := createReleaseInfo(ctx, "v2", "non-existent", "non-existent", constant.BkRelease)

			_, err := registry.StageReleaseVersion(releaseInfo)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("empty etcd value"))
		})
	})

	Describe("GetStageResourceByID", func() {
		It("should return error when resource not found", func() {
			releaseInfo := createReleaseInfo(ctx, "v2", "test-gateway", "test-stage", constant.Route)

			_, err := registry.GetStageResourceByID("non-existent-id", releaseInfo)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("empty etcd value"))
		})
	})

	Describe("ValueToStageResource", func() {
		It("should skip bk_release resources", func() {
			releaseKey := "/bk-gateway-apigw/v2/gateway/test-gateway/test-stage/_bk_release/test-release"
			releaseValue := map[string]any{
				"id":   "test-release",
				"name": "test-release",
				"labels": map[string]any{
					"gateway.bk.tencent.com/gateway": "test-gateway",
					"gateway.bk.tencent.com/stage":   "test-stage",
				},
			}
			releaseBytes, _ := json.Marshal(releaseValue)
			_, err := client.Put(ctx, releaseKey, string(releaseBytes))
			Expect(err).ShouldNot(HaveOccurred())

			resp, err := client.Get(ctx, releaseKey)
			Expect(err).ShouldNot(HaveOccurred())

			resources, err := registry.ValueToStageResource(resp)
			Expect(err).ShouldNot(HaveOccurred())
			// bk_release should be skipped
			Expect(resources.Routes).To(HaveLen(0))
			Expect(resources.Services).To(HaveLen(0))
			Expect(resources.SSLs).To(HaveLen(0))
		})

		It("should return error for invalid key format", func() {
			// Key with insufficient segments
			invalidKey := "/bk-gateway-apigw/v2/gateway/test"
			_, err := client.Put(ctx, invalidKey, `{"id": "test", "labels": {}}`)
			Expect(err).ShouldNot(HaveOccurred())

			resp, err := client.Get(ctx, invalidKey)
			Expect(err).ShouldNot(HaveOccurred())

			_, err = registry.ValueToStageResource(resp)
			Expect(err).To(HaveOccurred())
		})
	})

	Describe("ValueToGlobalResource", func() {
		It("should return error for invalid key format", func() {
			// Key with wrong number of segments
			invalidKey := "/bk-gateway-apigw/v2/invalid"
			_, err := client.Put(ctx, invalidKey, `{"id": "test"}`)
			Expect(err).ShouldNot(HaveOccurred())

			resp, err := client.Get(ctx, invalidKey)
			Expect(err).ShouldNot(HaveOccurred())

			_, err = registry.ValueToGlobalResource(resp)
			Expect(err).To(HaveOccurred())
		})
	})
})

// startTestEtcd starts an embedded etcd for testing
func startTestEtcd() (*embed.Etcd, *clientv3.Client, error) {
	cfg := embed.NewConfig()
	cfg.Dir, _ = os.MkdirTemp("", "etcd-apigw-test")
	cfg.LogLevel = "error"

	// Use random ports to avoid conflicts
	cfg.ListenClientUrls = []url.URL{{Scheme: "http", Host: "localhost:0"}}
	cfg.ListenPeerUrls = []url.URL{{Scheme: "http", Host: "localhost:0"}}

	etcd, err := embed.StartEtcd(cfg)
	if err != nil {
		return nil, nil, err
	}

	select {
	case <-etcd.Server.ReadyNotify():
		client, err := clientv3.New(clientv3.Config{
			Endpoints:   []string{etcd.Clients[0].Addr().String()},
			DialTimeout: time.Second,
		})
		return etcd, client, err
	case <-time.After(30 * time.Second):
		etcd.Close()
		return nil, nil, fmt.Errorf("etcd server took too long to start")
	}
}
