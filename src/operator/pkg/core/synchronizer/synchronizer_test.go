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

package synchronizer_test

import (
	"context"
	"encoding/json"
	"os"
	"sync"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/prometheus/client_golang/prometheus"
	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/server/v3/embed"

	"operator/pkg/config"
	"operator/pkg/core/store"
	"operator/pkg/core/synchronizer"
	"operator/pkg/entity"
	"operator/pkg/metric"
	"operator/tests/util"
)

// Helper function to create PluginMetadata with config
func createPluginMetadata(id string, configData map[string]any) *entity.PluginMetadata {
	configData["id"] = id // id is required for PluginMetadataConf
	rawConfig, _ := json.Marshal(configData)
	conf := entity.PluginMetadataConf{id: rawConfig}
	return &entity.PluginMetadata{
		ResourceMetadata: entity.ResourceMetadata{
			ID:   id,
			Name: id,
		},
		PluginMetadataConf: conf,
	}
}

func createReleaseInfo(gateway, stage string) *entity.ReleaseInfo {
	return &entity.ReleaseInfo{
		ResourceMetadata: entity.ResourceMetadata{
			Labels: &entity.LabelInfo{
				Gateway: gateway,
				Stage:   stage,
			},
		},
	}
}

func createStageConfigWithService(gateway, stage string) *entity.ApisixStageResource {
	routeID := gateway + "-route"
	serviceID := gateway + "-service"
	labels := &entity.LabelInfo{Gateway: gateway, Stage: stage}
	return &entity.ApisixStageResource{
		Routes: map[string]*entity.Route{
			routeID: {
				ResourceMetadata: entity.ResourceMetadata{ID: routeID, Labels: labels},
				ServiceID:        serviceID,
				URI:              "/" + gateway + "/*",
				Status:           1,
			},
		},
		Services: map[string]*entity.Service{
			serviceID: {
				ResourceMetadata: entity.ResourceMetadata{ID: serviceID, Labels: labels},
			},
		},
		SSLs: make(map[string]*entity.SSL),
	}
}

var _ = Describe("ApisixConfigSynchronizer", func() {
	var (
		syncer           *synchronizer.ApisixConfigSynchronizer
		mockStore        *store.ApisixEtcdStore
		apisixHealthzURI string
		ctx              context.Context
	)

	BeforeEach(func() {
		ctx = context.Background()
		apisixHealthzURI = "/healthz"

		// Initialize metric with a new registry to avoid duplicate registration
		reg := prometheus.NewRegistry()
		metric.InitMetric(reg)

		// Initialize synchronizer config
		synchronizer.Init(&config.Config{
			Apisix: config.Apisix{
				VirtualStage: config.VirtualStage{
					VirtualGateway:    "virtual-gateway",
					VirtualStage:      "virtual-stage",
					FileLoggerLogPath: "/logs/access.log",
				},
			},
		})

		// Create a mock store (nil for unit testing without etcd)
		mockStore = nil
		syncer = synchronizer.NewSynchronizer(mockStore, apisixHealthzURI, 5)
	})

	Describe("NewSynchronizer", func() {
		It("should create a new synchronizer with initialized fields", func() {
			Expect(syncer).NotTo(BeNil())
		})

		It("should create synchronizer with different healthz URI", func() {
			customURI := "/api/healthz"
			customSyncer := synchronizer.NewSynchronizer(nil, customURI, 5)
			Expect(customSyncer).NotTo(BeNil())
		})

		It("should use the default concurrency when configured with a non-positive value", func() {
			customSyncer := synchronizer.NewSynchronizer(nil, apisixHealthzURI, 0)
			done := make(chan struct{})
			go func() {
				defer close(done)
				defer func() {
					_ = recover()
				}()
				_ = customSyncer.SyncRelease(
					ctx,
					createReleaseInfo("gateway", "stage"),
					entity.NewEmptyApisixConfiguration(),
				)
			}()

			Eventually(done, 200*time.Millisecond).Should(BeClosed())
		})
	})

	Describe("SyncRelease", func() {
		It("should return error when release info is nil", func() {
			config := &entity.ApisixStageResource{
				Routes:   make(map[string]*entity.Route),
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			err := syncer.SyncRelease(ctx, nil, config)
			Expect(err).To(MatchError("releaseInfo is nil"))
		})

		Context("when store is nil", func() {
			It("should panic when store is nil", func() {
				config := &entity.ApisixStageResource{
					Routes:   make(map[string]*entity.Route),
					Services: make(map[string]*entity.Service),
					SSLs:     make(map[string]*entity.SSL),
				}

				// This will panic because store is nil
				Expect(func() {
					_ = syncer.SyncRelease(
						ctx,
						createReleaseInfo("test-gateway", "test-stage"),
						config,
					)
				}).To(Panic())
			})
		})
	})

	Describe("SyncGlobal", func() {
		Context("when store is nil", func() {
			It("should panic when store is nil", func() {
				globalConfig := &entity.ApisixGlobalResource{
					PluginMetadata: make(map[string]*entity.PluginMetadata),
				}

				// This will panic because store is nil
				Expect(func() {
					_ = syncer.SyncGlobal(ctx, globalConfig)
				}).To(Panic())
			})
		})
	})

	Describe("Concurrent Operations", func() {
		It("should handle concurrent Sync calls safely", func() {
			// Test that concurrent calls can enter the gateway synchronization path safely.
			// Since store is nil, we just verify no race conditions occur
			done := make(chan bool, 3)

			for i := 0; i < 3; i++ {
				go func(idx int) {
					defer func() {
						// Recover from panic due to nil store
						recover()
						done <- true
					}()

					config := &entity.ApisixStageResource{
						Routes:   make(map[string]*entity.Route),
						Services: make(map[string]*entity.Service),
						SSLs:     make(map[string]*entity.SSL),
					}
					_ = syncer.SyncRelease(ctx, createReleaseInfo("gateway", "stage"), config)
				}(i)
			}

			// Wait for all goroutines to complete
			for i := 0; i < 3; i++ {
				<-done
			}
		})
	})
})

var _ = Describe("Config Key Generation", func() {
	Describe("GenStagePrimaryKey", func() {
		It("should generate correct stage key", func() {
			key := config.GenStagePrimaryKey("my-gateway", "prod")
			Expect(key).To(ContainSubstring("my-gateway"))
			Expect(key).To(ContainSubstring("prod"))
		})

		It("should generate different keys for different stages", func() {
			key1 := config.GenStagePrimaryKey("gateway", "stage1")
			key2 := config.GenStagePrimaryKey("gateway", "stage2")
			Expect(key1).NotTo(Equal(key2))
		})

		It("should generate different keys for different gateways", func() {
			key1 := config.GenStagePrimaryKey("gateway1", "stage")
			key2 := config.GenStagePrimaryKey("gateway2", "stage")
			Expect(key1).NotTo(Equal(key2))
		})
	})
})

var _ = Describe("ApisixConfigSynchronizer with EmbedEtcd", func() {
	var (
		etcd             *embed.Etcd
		client           *clientv3.Client
		etcdStore        *store.ApisixEtcdStore
		syncer           *synchronizer.ApisixConfigSynchronizer
		ctx              context.Context
		apisixHealthzURI string
	)

	BeforeEach(func() {
		var err error
		ctx = context.Background()
		apisixHealthzURI = "/healthz"

		// Initialize metric with a new registry
		reg := prometheus.NewRegistry()
		metric.InitMetric(reg)

		// Initialize synchronizer config
		synchronizer.Init(&config.Config{
			Apisix: config.Apisix{
				VirtualStage: config.VirtualStage{
					VirtualGateway:    "virtual-gateway",
					VirtualStage:      "virtual-stage",
					FileLoggerLogPath: "/logs/access.log",
				},
			},
		})

		// Start embedded etcd
		client, etcd, err = util.StartEmbedEtcdClient(ctx)
		Expect(err).ShouldNot(HaveOccurred())

		// Create store with embedded etcd
		etcdStore, err = store.NewApisixEtcdStore(
			ctx,
			client,
			"/apisix",
			10*time.Millisecond, // putInterval
			10*time.Millisecond, // delInterval
			5*time.Second,       // syncTimeout
		)
		Expect(err).ShouldNot(HaveOccurred())

		// Create synchronizer with real store
		syncer = synchronizer.NewSynchronizer(etcdStore, apisixHealthzURI, 5)
	})

	AfterEach(func() {
		if etcdStore != nil {
			etcdStore.Close()
		}
		if client != nil {
			client.Close()
		}
		if etcd != nil {
			etcd.Close()
			_ = os.RemoveAll(etcd.Config().Dir)
		}
	})

	Describe("SyncRelease", func() {
		It("should sync new configuration to etcd", func() {
			stageConfig := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route-1": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-1",
							Name: "test-route",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/v1/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			err := syncer.SyncRelease(ctx, createReleaseInfo("test-gateway", "test-stage"), stageConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify data was written to etcd
			resp, err := client.Get(ctx, "/apisix/routes/route-1")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))
		})

		It("should not write to etcd when configuration is unchanged", func() {
			stageConfig := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route-2": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-2",
							Name: "unchanged-route",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/v2/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			// First sync
			err := syncer.SyncRelease(ctx, createReleaseInfo("test-gateway", "test-stage"), stageConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Get the revision after first sync
			resp1, err := client.Get(ctx, "/apisix/routes/route-2")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp1.Kvs).To(HaveLen(1))
			revision1 := resp1.Kvs[0].ModRevision

			// Wait for registry watch to process the events and update cache
			time.Sleep(200 * time.Millisecond)

			// Second sync with same configuration (need to reset create/update time)
			stageConfig2 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route-2": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-2",
							Name: "unchanged-route",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/v2/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}
			err = syncer.SyncRelease(ctx, createReleaseInfo("test-gateway", "test-stage"), stageConfig2)
			Expect(err).ShouldNot(HaveOccurred())

			// Get the revision after second sync
			resp2, err := client.Get(ctx, "/apisix/routes/route-2")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp2.Kvs).To(HaveLen(1))
			revision2 := resp2.Kvs[0].ModRevision

			// Revision should be the same since no actual change was made
			Expect(revision2).To(Equal(revision1))
		})

		It("should update etcd when configuration changes", func() {
			// Initial config
			stageConfig1 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route-3": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-3",
							Name: "changing-route",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/v3/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			err := syncer.SyncRelease(ctx, createReleaseInfo("test-gateway", "test-stage"), stageConfig1)
			Expect(err).ShouldNot(HaveOccurred())

			// Get revision after first sync
			resp1, err := client.Get(ctx, "/apisix/routes/route-3")
			Expect(err).ShouldNot(HaveOccurred())
			revision1 := resp1.Kvs[0].ModRevision

			// Wait a bit
			time.Sleep(50 * time.Millisecond)

			// Changed config - different URI
			stageConfig2 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route-3": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-3",
							Name: "changing-route",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/v3/changed/*", // Changed!
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			err = syncer.SyncRelease(ctx, createReleaseInfo("test-gateway", "test-stage"), stageConfig2)
			Expect(err).ShouldNot(HaveOccurred())

			// Get revision after second sync
			resp2, err := client.Get(ctx, "/apisix/routes/route-3")
			Expect(err).ShouldNot(HaveOccurred())
			revision2 := resp2.Kvs[0].ModRevision

			// Revision should be different since config changed
			Expect(revision2).To(BeNumerically(">", revision1))
		})

		It("should delete resources that no longer exist in new config", func() {
			// Initial config with 2 routes
			stageConfig1 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route-4a": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-4a",
							Name: "route-a",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/a/*",
						Status: 1,
					},
					"route-4b": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-4b",
							Name: "route-b",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/b/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			err := syncer.SyncRelease(ctx, createReleaseInfo("test-gateway", "test-stage"), stageConfig1)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify both routes exist
			resp, err := client.Get(ctx, "/apisix/routes/", clientv3.WithPrefix())
			Expect(err).ShouldNot(HaveOccurred())
			routeCount := 0
			for _, kv := range resp.Kvs {
				if string(kv.Key) == "/apisix/routes/route-4a" ||
					string(kv.Key) == "/apisix/routes/route-4b" {
					routeCount++
				}
			}
			Expect(routeCount).To(Equal(2))

			// Wait for registry watch to process the events and update cache
			time.Sleep(200 * time.Millisecond)

			// New config with only 1 route (route-4b removed)
			stageConfig2 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route-4a": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "route-4a",
							Name: "route-a",
							Labels: &entity.LabelInfo{
								Gateway: "test-gateway",
								Stage:   "test-stage",
							},
						},
						URI:    "/api/a/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			err = syncer.SyncRelease(ctx, createReleaseInfo("test-gateway", "test-stage"), stageConfig2)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify route-4b was deleted
			resp, err = client.Get(ctx, "/apisix/routes/route-4b")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(0))

			// Verify route-4a still exists
			resp, err = client.Get(ctx, "/apisix/routes/route-4a")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))
		})
	})

	Describe("Sync with multiple gateways", func() {
		It("should limit concurrent gateway syncs without serializing every gateway", func() {
			const (
				gatewaySyncConcurrency = 2
				delInterval            = 2 * time.Second
			)

			concurrencyStore, err := store.NewApisixEtcdStore(
				ctx,
				client,
				"/concurrency-apisix",
				10*time.Millisecond,
				delInterval,
				5*time.Second,
			)
			Expect(err).ShouldNot(HaveOccurred())
			DeferCleanup(concurrencyStore.Close)

			concurrencySyncer := synchronizer.NewSynchronizer(
				concurrencyStore,
				apisixHealthzURI,
				gatewaySyncConcurrency,
			)
			gateways := []string{"gateway-1", "gateway-2", "gateway-3"}
			for _, gateway := range gateways {
				err = concurrencySyncer.SyncRelease(
					ctx,
					createReleaseInfo(gateway, "prod"),
					createStageConfigWithService(gateway, "prod"),
				)
				Expect(err).ShouldNot(HaveOccurred())
			}

			Eventually(func() int {
				resourceCount := 0
				for _, gateway := range gateways {
					stageConfig := concurrencyStore.Get(config.GenStagePrimaryKey(gateway, "prod"))
					resourceCount += len(stageConfig.Routes) + len(stageConfig.Services)
				}
				return resourceCount
			}, 2*time.Second, 10*time.Millisecond).Should(Equal(6))

			start := make(chan struct{})
			errCh := make(chan error, len(gateways))
			var wg sync.WaitGroup
			for _, gateway := range gateways {
				gateway := gateway
				wg.Add(1)
				go func() {
					defer wg.Done()
					<-start
					errCh <- concurrencySyncer.SyncRelease(
						ctx,
						createReleaseInfo(gateway, "prod"),
						entity.NewEmptyApisixConfiguration(),
					)
				}()
			}
			close(start)
			defer wg.Wait()

			Eventually(func() int {
				resp, getErr := client.Get(ctx, "/concurrency-apisix/routes/", clientv3.WithPrefix())
				Expect(getErr).ShouldNot(HaveOccurred())
				return len(resp.Kvs)
			}, delInterval/2, 10*time.Millisecond).Should(Equal(1))

			wg.Wait()
			close(errCh)
			for syncErr := range errCh {
				Expect(syncErr).ShouldNot(HaveOccurred())
			}
		})

		It("should keep global synchronization exclusive from gateway synchronization", func() {
			const delInterval = 500 * time.Millisecond
			exclusiveStore, err := store.NewApisixEtcdStore(
				ctx,
				client,
				"/exclusive-apisix",
				10*time.Millisecond,
				delInterval,
				5*time.Second,
			)
			Expect(err).ShouldNot(HaveOccurred())
			DeferCleanup(exclusiveStore.Close)

			exclusiveSyncer := synchronizer.NewSynchronizer(exclusiveStore, apisixHealthzURI, 2)
			gateway := "exclusive-gateway"
			err = exclusiveSyncer.SyncRelease(
				ctx,
				createReleaseInfo(gateway, "prod"),
				createStageConfigWithService(gateway, "prod"),
			)
			Expect(err).ShouldNot(HaveOccurred())
			Eventually(func() int {
				stageConfig := exclusiveStore.Get(config.GenStagePrimaryKey(gateway, "prod"))
				return len(stageConfig.Routes) + len(stageConfig.Services)
			}, 2*time.Second, 10*time.Millisecond).Should(Equal(2))

			stageErrCh := make(chan error, 1)
			globalErrCh := make(chan error, 1)
			globalDone := make(chan struct{})
			var wg sync.WaitGroup
			wg.Add(1)
			go func() {
				defer wg.Done()
				stageErrCh <- exclusiveSyncer.SyncRelease(
					ctx,
					createReleaseInfo(gateway, "prod"),
					entity.NewEmptyApisixConfiguration(),
				)
			}()
			defer wg.Wait()

			Eventually(func() int {
				resp, getErr := client.Get(ctx, "/exclusive-apisix/routes/", clientv3.WithPrefix())
				Expect(getErr).ShouldNot(HaveOccurred())
				return len(resp.Kvs)
			}, 2*time.Second, 10*time.Millisecond).Should(BeZero())

			wg.Add(1)
			go func() {
				defer wg.Done()
				defer close(globalDone)
				globalErrCh <- exclusiveSyncer.SyncGlobal(ctx, entity.NewEmptyApisixGlobalResource())
			}()

			Consistently(globalDone, delInterval/2).ShouldNot(BeClosed())

			wg.Wait()
			Expect(<-stageErrCh).ShouldNot(HaveOccurred())
			Expect(<-globalErrCh).ShouldNot(HaveOccurred())
		})

		It("should handle multiple gateways independently", func() {
			// Config for gateway-1
			config1 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"gw1-route": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "gw1-route",
							Name: "gateway1-route",
							Labels: &entity.LabelInfo{
								Gateway: "gateway-1",
								Stage:   "prod",
							},
						},
						URI:    "/gw1/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			// Config for gateway-2
			config2 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"gw2-route": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "gw2-route",
							Name: "gateway2-route",
							Labels: &entity.LabelInfo{
								Gateway: "gateway-2",
								Stage:   "prod",
							},
						},
						URI:    "/gw2/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			// Sync both gateways
			err := syncer.SyncRelease(ctx, createReleaseInfo("gateway-1", "prod"), config1)
			Expect(err).ShouldNot(HaveOccurred())

			err = syncer.SyncRelease(ctx, createReleaseInfo("gateway-2", "prod"), config2)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify both routes exist
			resp1, err := client.Get(ctx, "/apisix/routes/gw1-route")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp1.Kvs).To(HaveLen(1))

			resp2, err := client.Get(ctx, "/apisix/routes/gw2-route")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp2.Kvs).To(HaveLen(1))
		})
	})

	Describe("RemoveNotExistStage", func() {
		It("should remove stages that no longer exist", func() {
			// Create configs for multiple stages
			stageConfig1 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"stage1-route": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "stage1-route",
							Name: "stage1-route",
							Labels: &entity.LabelInfo{
								Gateway: "gateway",
								Stage:   "stage1",
							},
						},
						URI:    "/stage1/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			stageConfig2 := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"stage2-route": {
						ResourceMetadata: entity.ResourceMetadata{
							ID:   "stage2-route",
							Name: "stage2-route",
							Labels: &entity.LabelInfo{
								Gateway: "gateway",
								Stage:   "stage2",
							},
						},
						URI:    "/stage2/*",
						Status: 1,
					},
				},
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}

			// Sync both stages
			err := syncer.SyncRelease(ctx, createReleaseInfo("gateway", "stage1"), stageConfig1)
			Expect(err).ShouldNot(HaveOccurred())

			err = syncer.SyncRelease(ctx, createReleaseInfo("gateway", "stage2"), stageConfig2)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify both routes exist
			resp, err := client.Get(ctx, "/apisix/routes/stage1-route")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			resp, err = client.Get(ctx, "/apisix/routes/stage2-route")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			// Wait for registry watch to process the events and update cache
			time.Sleep(200 * time.Millisecond)

			// Now sync stage2 with empty config to remove it
			emptyConfig := &entity.ApisixStageResource{
				Routes:   make(map[string]*entity.Route),
				Services: make(map[string]*entity.Service),
				SSLs:     make(map[string]*entity.SSL),
			}
			err = syncer.SyncRelease(ctx, createReleaseInfo("gateway", "stage2"), emptyConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify stage1 route still exists
			resp, err = client.Get(ctx, "/apisix/routes/stage1-route")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			// Verify stage2 route was deleted
			resp, err = client.Get(ctx, "/apisix/routes/stage2-route")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(0))
		})
	})

	Describe("SyncGlobal", func() {
		It("should sync global plugin metadata to etcd", func() {
			globalConfig := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"prometheus": createPluginMetadata("prometheus", map[string]any{
						"prefer_name": true,
					}),
				},
			}

			err := syncer.SyncGlobal(ctx, globalConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify plugin_metadata was written to etcd
			resp, err := client.Get(ctx, "/apisix/plugin_metadata/prometheus")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))
		})

		It("should not write to etcd when global config is unchanged", func() {
			globalConfig := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"file-logger": createPluginMetadata("file-logger", map[string]any{
						"path": "/logs/access.log",
					}),
				},
			}

			// First sync
			err := syncer.SyncGlobal(ctx, globalConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Get revision after first sync
			resp1, err := client.Get(ctx, "/apisix/plugin_metadata/file-logger")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp1.Kvs).To(HaveLen(1))
			revision1 := resp1.Kvs[0].ModRevision

			// Wait for registry watch to process the event and update cache
			// The registry uses async watch to update its internal cache
			time.Sleep(200 * time.Millisecond)

			// Second sync with same config
			globalConfig2 := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"file-logger": createPluginMetadata("file-logger", map[string]any{
						"path": "/logs/access.log",
					}),
				},
			}
			err = syncer.SyncGlobal(ctx, globalConfig2)
			Expect(err).ShouldNot(HaveOccurred())

			// Get revision after second sync
			resp2, err := client.Get(ctx, "/apisix/plugin_metadata/file-logger")
			Expect(err).ShouldNot(HaveOccurred())
			revision2 := resp2.Kvs[0].ModRevision

			// Revision should be the same since no actual change
			Expect(revision2).To(Equal(revision1))
		})

		It("should update etcd when global config changes", func() {
			globalConfig1 := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"limit-count": createPluginMetadata("limit-count", map[string]any{
						"count": 100,
					}),
				},
			}

			err := syncer.SyncGlobal(ctx, globalConfig1)
			Expect(err).ShouldNot(HaveOccurred())

			resp1, err := client.Get(ctx, "/apisix/plugin_metadata/limit-count")
			Expect(err).ShouldNot(HaveOccurred())
			revision1 := resp1.Kvs[0].ModRevision

			time.Sleep(50 * time.Millisecond)

			// Changed config
			globalConfig2 := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"limit-count": createPluginMetadata("limit-count", map[string]any{
						"count": 200, // Changed!
					}),
				},
			}

			err = syncer.SyncGlobal(ctx, globalConfig2)
			Expect(err).ShouldNot(HaveOccurred())

			resp2, err := client.Get(ctx, "/apisix/plugin_metadata/limit-count")
			Expect(err).ShouldNot(HaveOccurred())
			revision2 := resp2.Kvs[0].ModRevision

			// Revision should be different
			Expect(revision2).To(BeNumerically(">", revision1))
		})

		It("should delete global resources that no longer exist", func() {
			// Initial config with 2 plugin metadata
			globalConfig1 := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"plugin-a": createPluginMetadata("plugin-a", map[string]any{}),
					"plugin-b": createPluginMetadata("plugin-b", map[string]any{}),
				},
			}

			err := syncer.SyncGlobal(ctx, globalConfig1)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify both exist
			resp, err := client.Get(ctx, "/apisix/plugin_metadata/plugin-a")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			resp, err = client.Get(ctx, "/apisix/plugin_metadata/plugin-b")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			// Wait for registry watch to process the events and update cache
			time.Sleep(200 * time.Millisecond)

			// New config with only plugin-a
			globalConfig2 := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"plugin-a": createPluginMetadata("plugin-a", map[string]any{}),
				},
			}

			err = syncer.SyncGlobal(ctx, globalConfig2)
			Expect(err).ShouldNot(HaveOccurred())

			// plugin-a should still exist
			resp, err = client.Get(ctx, "/apisix/plugin_metadata/plugin-a")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			// plugin-b should be deleted
			resp, err = client.Get(ctx, "/apisix/plugin_metadata/plugin-b")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(0))
		})

		It("should sync virtual stage along with global config", func() {
			globalConfig := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"test-plugin": createPluginMetadata("test-plugin", map[string]any{}),
				},
			}

			err := syncer.SyncGlobal(ctx, globalConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify virtual stage route was created (from VirtualStage.MakeConfiguration)
			// The virtual stage creates routes for healthz endpoint
			resp, err := client.Get(ctx, "/apisix/routes/", clientv3.WithPrefix())
			Expect(err).ShouldNot(HaveOccurred())
			// Should have at least the virtual stage route
			Expect(len(resp.Kvs)).To(BeNumerically(">=", 1))
		})

		It("should handle multiple global resources", func() {
			globalConfig := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"prometheus": createPluginMetadata("prometheus", map[string]any{
						"prefer_name": true,
					}),
					"zipkin": createPluginMetadata("zipkin", map[string]any{
						"endpoint": "http://zipkin:9411/api/v2/spans",
					}),
					"skywalking": createPluginMetadata("skywalking", map[string]any{
						"service_name": "my-service",
					}),
				},
			}

			err := syncer.SyncGlobal(ctx, globalConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Verify all plugin metadata were written
			for _, name := range []string{"prometheus", "zipkin", "skywalking"} {
				resp, err := client.Get(ctx, "/apisix/plugin_metadata/"+name)
				Expect(err).ShouldNot(HaveOccurred())
				Expect(resp.Kvs).To(HaveLen(1))
			}
		})

		It("should handle empty global config", func() {
			// First add some global resources
			globalConfig1 := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"to-be-removed": createPluginMetadata("to-be-removed", map[string]any{}),
				},
			}

			err := syncer.SyncGlobal(ctx, globalConfig1)
			Expect(err).ShouldNot(HaveOccurred())

			resp, err := client.Get(ctx, "/apisix/plugin_metadata/to-be-removed")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(1))

			// Wait for registry watch to process the events and update cache
			time.Sleep(200 * time.Millisecond)

			// Sync with empty config
			emptyConfig := &entity.ApisixGlobalResource{
				PluginMetadata: make(map[string]*entity.PluginMetadata),
			}

			err = syncer.SyncGlobal(ctx, emptyConfig)
			Expect(err).ShouldNot(HaveOccurred())

			// Resource should be deleted
			resp, err = client.Get(ctx, "/apisix/plugin_metadata/to-be-removed")
			Expect(err).ShouldNot(HaveOccurred())
			Expect(resp.Kvs).To(HaveLen(0))
		})
	})
})
