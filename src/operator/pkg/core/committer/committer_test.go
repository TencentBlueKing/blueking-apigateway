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

package committer

import (
	"context"
	"io"
	"log"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"operator/pkg/constant"
	"operator/pkg/core/agent/timer"
	"operator/pkg/entity"
)

var _ = Describe("Committer", func() {
	var (
		committer    *Committer
		releaseTimer *timer.ReleaseTimer
	)

	BeforeEach(func() {
		releaseTimer = timer.NewReleaseTimer()
		committer = NewCommitter(nil, nil, releaseTimer, 100)
	})

	Describe("NewCommitter", func() {
		It("should create a new committer with initialized fields", func() {
			Expect(committer).NotTo(BeNil())
			Expect(committer.commitResourceChan).NotTo(BeNil())
			Expect(committer.gatewayStageChanMap).NotTo(BeNil())
			Expect(committer.gatewayStageChanMapLock).NotTo(BeNil())
			Expect(committer.releaseTimer).To(Equal(releaseTimer))
		})
	})

	Describe("GetCommitChan", func() {
		It("should return the commit channel", func() {
			ch := committer.GetCommitChan()
			Expect(ch).NotTo(BeNil())
			Expect(ch).To(Equal(committer.commitResourceChan))
		})
	})

	Describe("ForceCommit", func() {
		It("should send release info to commit channel", func() {
			releaseInfo := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID: "test-release",
					Labels: &entity.LabelInfo{
						Gateway: "test-gateway",
						Stage:   "test-stage",
					},
				},
			}

			go func() {
				committer.ForceCommit(context.Background(), []*entity.ReleaseInfo{releaseInfo})
			}()

			select {
			case received := <-committer.GetCommitChan():
				Expect(received).To(HaveLen(1))
				Expect(received[0].ID).To(Equal("test-release"))
			case <-time.After(time.Second):
				Fail("timeout waiting for commit channel")
			}
		})
	})

	Describe("CleanupGatewayChannel", func() {
		It("should cleanup gateway channel when exists", func() {
			gatewayName := "test-gateway"

			// Create a gateway channel
			committer.gatewayStageChanMapLock.Lock()
			committer.gatewayStageChanMap[gatewayName] = make(chan struct{}, 1)
			committer.gatewayStageChanMapLock.Unlock()

			// Verify it exists
			committer.gatewayStageChanMapLock.RLock()
			_, exists := committer.gatewayStageChanMap[gatewayName]
			committer.gatewayStageChanMapLock.RUnlock()
			Expect(exists).To(BeTrue())

			// Cleanup
			committer.CleanupGatewayChannel(gatewayName)

			// Verify it's removed
			committer.gatewayStageChanMapLock.RLock()
			_, exists = committer.gatewayStageChanMap[gatewayName]
			committer.gatewayStageChanMapLock.RUnlock()
			Expect(exists).To(BeFalse())
		})

		It("should not panic when gateway channel does not exist", func() {
			Expect(func() {
				committer.CleanupGatewayChannel("non-existent-gateway")
			}).NotTo(Panic())
		})

		It("should drain channel before deleting", func() {
			gatewayName := "test-gateway-with-data"

			// Create a gateway channel with data
			ch := make(chan struct{}, 1)
			ch <- struct{}{}

			committer.gatewayStageChanMapLock.Lock()
			committer.gatewayStageChanMap[gatewayName] = ch
			committer.gatewayStageChanMapLock.Unlock()

			// Cleanup should not block
			done := make(chan bool)
			go func() {
				committer.CleanupGatewayChannel(gatewayName)
				done <- true
			}()

			select {
			case <-done:
				// Success
			case <-time.After(time.Second):
				Fail("CleanupGatewayChannel blocked")
			}
		})
	})

	Describe("retryStage", func() {
		It("should increment retry count and update timer", func() {
			releaseInfo := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID: "test-release",
					Labels: &entity.LabelInfo{
						Gateway: "test-gateway",
						Stage:   "test-stage",
					},
					RetryCount: 0,
				},
			}

			committer.retryStage(releaseInfo)
			Expect(releaseInfo.RetryCount).To(Equal(int64(1)))
		})

		It("should not retry when max retry count is reached", func() {
			releaseInfo := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID: "test-release",
					Labels: &entity.LabelInfo{
						Gateway: "test-gateway",
						Stage:   "test-stage",
					},
					RetryCount: maxStageRetryCount,
				},
			}

			committer.retryStage(releaseInfo)
			// RetryCount should not increase beyond max
			Expect(releaseInfo.RetryCount).To(Equal(int64(maxStageRetryCount)))
		})
	})

	Describe("Run", func() {
		It("should stop when context is cancelled", func() {
			ctx, cancel := context.WithCancel(context.Background())

			done := make(chan bool)
			go func() {
				committer.Run(ctx)
				done <- true
			}()

			// Cancel context
			cancel()

			select {
			case <-done:
				// Success - Run exited
			case <-time.After(time.Second):
				Fail("Run did not exit after context cancellation")
			}
		})
	})

	Describe("Multiple Gateways and Stages", func() {
		It("should handle multiple stages from same gateway", func() {
			gateway := "gateway-1"
			releases := []*entity.ReleaseInfo{
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gateway-1-stage-1",
						Labels: &entity.LabelInfo{
							Gateway: gateway,
							Stage:   "stage-1",
						},
					},
					PublishId: 1,
				},
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gateway-1-stage-2",
						Labels: &entity.LabelInfo{
							Gateway: gateway,
							Stage:   "stage-2",
						},
					},
					PublishId: 2,
				},
			}

			go func() {
				committer.ForceCommit(context.Background(), releases)
			}()

			select {
			case received := <-committer.GetCommitChan():
				Expect(received).To(HaveLen(2))
				// Both stages should belong to the same gateway
				Expect(received[0].GetGatewayName()).To(Equal(gateway))
				Expect(received[1].GetGatewayName()).To(Equal(gateway))
				// Different stages
				Expect(received[0].GetStageName()).To(Equal("stage-1"))
				Expect(received[1].GetStageName()).To(Equal("stage-2"))
			case <-time.After(time.Second):
				Fail("timeout waiting for commit channel")
			}
		})

		It("should handle multiple stages from different gateways", func() {
			releases := []*entity.ReleaseInfo{
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gateway-a-stage-prod",
						Labels: &entity.LabelInfo{
							Gateway: "gateway-a",
							Stage:   "prod",
						},
					},
					PublishId: 1,
				},
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gateway-b-stage-prod",
						Labels: &entity.LabelInfo{
							Gateway: "gateway-b",
							Stage:   "prod",
						},
					},
					PublishId: 2,
				},
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gateway-a-stage-test",
						Labels: &entity.LabelInfo{
							Gateway: "gateway-a",
							Stage:   "test",
						},
					},
					PublishId: 3,
				},
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gateway-c-stage-dev",
						Labels: &entity.LabelInfo{
							Gateway: "gateway-c",
							Stage:   "dev",
						},
					},
					PublishId: 4,
				},
			}

			go func() {
				committer.ForceCommit(context.Background(), releases)
			}()

			select {
			case received := <-committer.GetCommitChan():
				Expect(received).To(HaveLen(4))

				// Verify all gateways are present
				gateways := make(map[string][]string)
				for _, r := range received {
					gateways[r.GetGatewayName()] = append(
						gateways[r.GetGatewayName()],
						r.GetStageName(),
					)
				}

				Expect(gateways).To(HaveKey("gateway-a"))
				Expect(gateways).To(HaveKey("gateway-b"))
				Expect(gateways).To(HaveKey("gateway-c"))

				// gateway-a should have 2 stages
				Expect(gateways["gateway-a"]).To(HaveLen(2))
				Expect(gateways["gateway-a"]).To(ContainElements("prod", "test"))

				// gateway-b and gateway-c should have 1 stage each
				Expect(gateways["gateway-b"]).To(HaveLen(1))
				Expect(gateways["gateway-c"]).To(HaveLen(1))
			case <-time.After(time.Second):
				Fail("timeout waiting for commit channel")
			}
		})

		It("should create separate channels for different gateways", func() {
			releases := []*entity.ReleaseInfo{
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gw1-stage1",
						Labels: &entity.LabelInfo{
							Gateway: "gateway-1",
							Stage:   "stage-1",
						},
					},
				},
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "gw2-stage1",
						Labels: &entity.LabelInfo{
							Gateway: "gateway-2",
							Stage:   "stage-1",
						},
					},
				},
			}

			// Manually create gateway channels to simulate commitGatewayStage behavior
			for _, r := range releases {
				committer.gatewayStageChanMapLock.Lock()
				if _, ok := committer.gatewayStageChanMap[r.GetGatewayName()]; !ok {
					committer.gatewayStageChanMap[r.GetGatewayName()] = make(chan struct{}, 1)
				}
				committer.gatewayStageChanMapLock.Unlock()
			}

			// Verify separate channels exist for each gateway
			committer.gatewayStageChanMapLock.RLock()
			_, hasGw1 := committer.gatewayStageChanMap["gateway-1"]
			_, hasGw2 := committer.gatewayStageChanMap["gateway-2"]
			channelCount := len(committer.gatewayStageChanMap)
			committer.gatewayStageChanMapLock.RUnlock()

			Expect(hasGw1).To(BeTrue())
			Expect(hasGw2).To(BeTrue())
			Expect(channelCount).To(Equal(2))
		})

		It("should handle batch commits with more than segment length", func() {
			// Create more than 10 releases (segment length is 10)
			releases := make([]*entity.ReleaseInfo, 15)
			for i := 0; i < 15; i++ {
				releases[i] = &entity.ReleaseInfo{
					ResourceMetadata: entity.ResourceMetadata{
						ID: "release-" + string(rune('a'+i)),
						Labels: &entity.LabelInfo{
							Gateway: "gateway-" + string(rune('a'+i%3)),
							Stage:   "stage-" + string(rune('1'+i%5)),
						},
					},
					PublishId: i + 1,
				}
			}

			go func() {
				committer.ForceCommit(context.Background(), releases)
			}()

			select {
			case received := <-committer.GetCommitChan():
				Expect(received).To(HaveLen(15))
			case <-time.After(time.Second):
				Fail("timeout waiting for commit channel")
			}
		})

		It("should cleanup multiple gateway channels correctly", func() {
			gateways := []string{"gateway-x", "gateway-y", "gateway-z"}

			// Create channels for multiple gateways
			for _, gw := range gateways {
				committer.gatewayStageChanMapLock.Lock()
				committer.gatewayStageChanMap[gw] = make(chan struct{}, 1)
				committer.gatewayStageChanMapLock.Unlock()
			}

			// Verify all channels exist
			committer.gatewayStageChanMapLock.RLock()
			Expect(committer.gatewayStageChanMap).To(HaveLen(3))
			committer.gatewayStageChanMapLock.RUnlock()

			// Cleanup one gateway
			committer.CleanupGatewayChannel("gateway-y")

			// Verify only gateway-y is removed
			committer.gatewayStageChanMapLock.RLock()
			_, hasX := committer.gatewayStageChanMap["gateway-x"]
			_, hasY := committer.gatewayStageChanMap["gateway-y"]
			_, hasZ := committer.gatewayStageChanMap["gateway-z"]
			committer.gatewayStageChanMapLock.RUnlock()

			Expect(hasX).To(BeTrue())
			Expect(hasY).To(BeFalse())
			Expect(hasZ).To(BeTrue())

			// Cleanup remaining gateways
			committer.CleanupGatewayChannel("gateway-x")
			committer.CleanupGatewayChannel("gateway-z")

			committer.gatewayStageChanMapLock.RLock()
			Expect(committer.gatewayStageChanMap).To(HaveLen(0))
			committer.gatewayStageChanMapLock.RUnlock()
		})

		It("should handle concurrent ForceCommit from multiple gateways", func() {
			ctx := context.Background()
			receivedCount := 0
			done := make(chan bool)

			// Start a goroutine to consume from commit channel
			go func() {
				for i := 0; i < 3; i++ {
					select {
					case releases := <-committer.GetCommitChan():
						receivedCount += len(releases)
					case <-time.After(2 * time.Second):
						break
					}
				}
				done <- true
			}()

			// Concurrently submit from multiple "gateways"
			go committer.ForceCommit(ctx, []*entity.ReleaseInfo{
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:     "concurrent-gw1-stage1",
						Labels: &entity.LabelInfo{Gateway: "concurrent-gw1", Stage: "stage1"},
					},
				},
			})

			go committer.ForceCommit(ctx, []*entity.ReleaseInfo{
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:     "concurrent-gw2-stage1",
						Labels: &entity.LabelInfo{Gateway: "concurrent-gw2", Stage: "stage1"},
					},
				},
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:     "concurrent-gw2-stage2",
						Labels: &entity.LabelInfo{Gateway: "concurrent-gw2", Stage: "stage2"},
					},
				},
			})

			go committer.ForceCommit(ctx, []*entity.ReleaseInfo{
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:     "concurrent-gw3-stage1",
						Labels: &entity.LabelInfo{Gateway: "concurrent-gw3", Stage: "stage1"},
					},
				},
			})

			select {
			case <-done:
				Expect(receivedCount).To(Equal(4))
			case <-time.After(3 * time.Second):
				Fail("timeout waiting for concurrent commits")
			}
		})

		It("should reuse existing gateway channel for same gateway", func() {
			gatewayName := "reuse-gateway"

			// Create initial channel
			committer.gatewayStageChanMapLock.Lock()
			originalChan := make(chan struct{}, 1)
			committer.gatewayStageChanMap[gatewayName] = originalChan
			committer.gatewayStageChanMapLock.Unlock()

			// Simulate getting channel again (like in commitGatewayStage)
			committer.gatewayStageChanMapLock.Lock()
			stageChan, ok := committer.gatewayStageChanMap[gatewayName]
			if !ok {
				stageChan = make(chan struct{}, 1)
				committer.gatewayStageChanMap[gatewayName] = stageChan
			}
			committer.gatewayStageChanMapLock.Unlock()

			// Should be the same channel
			Expect(ok).To(BeTrue())
			// Channels should be the same (pointer comparison)
			committer.gatewayStageChanMapLock.RLock()
			currentChan := committer.gatewayStageChanMap[gatewayName]
			committer.gatewayStageChanMapLock.RUnlock()

			// Verify it's still the original channel by checking capacity
			Expect(cap(currentChan)).To(Equal(cap(originalChan)))
		})
	})

	Describe("Global Resource", func() {
		It("should identify global resource correctly", func() {
			// Global resource: Kind is PluginMetadata and Stage is empty
			globalRelease := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID:   "global-plugin-metadata",
					Kind: constant.PluginMetadata,
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
				},
			}
			Expect(globalRelease.IsGlobalResource()).To(BeTrue())

			// Non-global resource: has Stage
			stageRelease := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID:   "stage-resource",
					Kind: constant.PluginMetadata,
					Labels: &entity.LabelInfo{
						Gateway: "gateway",
						Stage:   "prod",
					},
				},
			}
			Expect(stageRelease.IsGlobalResource()).To(BeFalse())

			// Non-global resource: Kind is not PluginMetadata
			routeRelease := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID:   "route-resource",
					Kind: constant.Route,
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
				},
			}
			Expect(routeRelease.IsGlobalResource()).To(BeFalse())
		})

		It("should send global resource to commit channel", func() {
			globalRelease := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID:   "global-plugin-metadata-1",
					Kind: constant.PluginMetadata,
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
				},
			}

			go func() {
				committer.ForceCommit(context.Background(), []*entity.ReleaseInfo{globalRelease})
			}()

			select {
			case received := <-committer.GetCommitChan():
				Expect(received).To(HaveLen(1))
				Expect(received[0].IsGlobalResource()).To(BeTrue())
				Expect(received[0].ID).To(Equal("global-plugin-metadata-1"))
			case <-time.After(time.Second):
				Fail("timeout waiting for commit channel")
			}
		})

		It("should handle mixed global and stage resources", func() {
			releases := []*entity.ReleaseInfo{
				// Global resource
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "global-plugin-1",
						Kind: constant.PluginMetadata,
						Labels: &entity.LabelInfo{
							Gateway: "",
							Stage:   "",
						},
					},
				},
				// Stage resource
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "gateway-a-stage-prod",
						Kind: constant.Route,
						Labels: &entity.LabelInfo{
							Gateway: "gateway-a",
							Stage:   "prod",
						},
					},
					PublishId: 1,
				},
				// Another global resource
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "global-plugin-2",
						Kind: constant.PluginMetadata,
						Labels: &entity.LabelInfo{
							Gateway: "",
							Stage:   "",
						},
					},
				},
				// Another stage resource
				{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "gateway-b-stage-test",
						Kind: constant.Route,
						Labels: &entity.LabelInfo{
							Gateway: "gateway-b",
							Stage:   "test",
						},
					},
					PublishId: 2,
				},
			}

			go func() {
				committer.ForceCommit(context.Background(), releases)
			}()

			select {
			case received := <-committer.GetCommitChan():
				Expect(received).To(HaveLen(4))

				// Count global vs stage resources
				globalCount := 0
				stageCount := 0
				for _, r := range received {
					if r.IsGlobalResource() {
						globalCount++
					} else {
						stageCount++
					}
				}
				Expect(globalCount).To(Equal(2))
				Expect(stageCount).To(Equal(2))
			case <-time.After(time.Second):
				Fail("timeout waiting for commit channel")
			}
		})

		It("should not create gateway channel for global resource", func() {
			// Global resources should not create gateway channels
			globalRelease := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID:   "global-only-plugin",
					Kind: constant.PluginMetadata,
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
				},
			}

			// Before ForceCommit, no gateway channels should exist for empty gateway name
			committer.gatewayStageChanMapLock.RLock()
			_, hasEmptyGateway := committer.gatewayStageChanMap[""]
			initialLen := len(committer.gatewayStageChanMap)
			committer.gatewayStageChanMapLock.RUnlock()
			Expect(hasEmptyGateway).To(BeFalse())

			go func() {
				committer.ForceCommit(context.Background(), []*entity.ReleaseInfo{globalRelease})
			}()

			// Consume from channel
			select {
			case <-committer.GetCommitChan():
				// After ForceCommit, still no gateway channel for empty gateway
				// (because global resources use commitGlobalResource, not commitGatewayStage)
				committer.gatewayStageChanMapLock.RLock()
				_, hasEmptyGatewayAfter := committer.gatewayStageChanMap[""]
				finalLen := len(committer.gatewayStageChanMap)
				committer.gatewayStageChanMapLock.RUnlock()
				Expect(hasEmptyGatewayAfter).To(BeFalse())
				Expect(finalLen).To(Equal(initialLen))
			case <-time.After(time.Second):
				Fail("timeout waiting for commit channel")
			}
		})

		It("should handle retryStage for global resource", func() {
			globalRelease := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID:   "global-retry-plugin",
					Kind: constant.PluginMetadata,
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
					RetryCount: 0,
				},
			}

			// retryStage should work for global resources too
			committer.retryStage(globalRelease)
			Expect(globalRelease.RetryCount).To(Equal(int64(1)))

			// Should respect max retry count
			globalRelease.RetryCount = maxStageRetryCount
			committer.retryStage(globalRelease)
			Expect(globalRelease.RetryCount).To(Equal(int64(maxStageRetryCount)))
		})

		It("should finish commit group when global resource commit panics", func() {
			previousLogWriter := log.Writer()
			log.SetOutput(io.Discard)
			DeferCleanup(func() {
				log.SetOutput(previousLogWriter)
			})

			globalRelease := &entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					ID:   "global-panic-plugin",
					Kind: constant.PluginMetadata,
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
				},
			}

			done := make(chan struct{})
			go func() {
				committer.commitGroup(context.Background(), []*entity.ReleaseInfo{globalRelease})
				close(done)
			}()

			select {
			case <-done:
			case <-time.After(time.Second):
				Fail("commitGroup blocked after a global resource panic")
			}
		})
	})
})
