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

package agent

import (
	"context"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.etcd.io/etcd/api/v3/mvccpb"

	"operator/pkg/constant"
	"operator/pkg/core/agent/timer"
	"operator/pkg/entity"
)

var _ = Describe("EventAgent", func() {
	var (
		agent        *EventAgent
		commitChan   chan []*entity.ReleaseInfo
		releaseTimer *timer.ReleaseTimer
	)

	BeforeEach(func() {
		commitChan = make(chan []*entity.ReleaseInfo, 10)
		releaseTimer = timer.NewReleaseTimer()
		agent = NewEventAgent(nil, commitChan, nil, releaseTimer)
		// Set shorter time window for faster tests
		timer.SetEventsWaitingTimeWindow(100 * time.Millisecond)
	})

	AfterEach(func() {
		// Reset to default
		timer.SetEventsWaitingTimeWindow(2 * time.Second)
	})

	Describe("NewEventAgent", func() {
		It("should create a new event agent with initialized fields", func() {
			Expect(agent).NotTo(BeNil())
			Expect(agent.commitChan).To(Equal(commitChan))
			Expect(agent.resourceTimer).To(Equal(releaseTimer))
			Expect(agent.logger).NotTo(BeNil())
		})
	})

	Describe("SetKeepAliveChan", func() {
		It("should set the keep alive channel", func() {
			keepAliveChan := make(chan struct{})
			agent.SetKeepAliveChan(keepAliveChan)
			Expect(agent.keepAliveChan).NotTo(BeNil())
		})
	})

	Describe("handleEvent", func() {
		Context("when event is empty", func() {
			It("should skip empty event", func() {
				event := &entity.ResourceMetadata{
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
					Kind: constant.Route,
				}

				// Should not panic and should not update timer
				agent.handleEvent(event)
			})
		})

		Context("when event is delete operation", func() {
			It("should skip delete event for non-global resource", func() {
				event := &entity.ResourceMetadata{
					Labels: &entity.LabelInfo{
						Gateway: "test-gateway",
						Stage:   "test-stage",
					},
					Op:   mvccpb.DELETE,
					Kind: constant.Route,
				}

				agent.handleEvent(event)
				// Timer should not be updated for delete events
			})
		})

		Context("when event is valid put operation", func() {
			It("should update timer for valid event", func() {
				event := &entity.ResourceMetadata{
					ID: "test-route",
					Labels: &entity.LabelInfo{
						Gateway:   "test-gateway",
						Stage:     "test-stage",
						PublishId: "1",
					},
					Op:   mvccpb.PUT,
					Kind: constant.Route,
					Ctx:  context.Background(),
				}

				agent.handleEvent(event)
				// Timer should be updated
			})
		})

		Context("when event is global resource", func() {
			It("should handle global resource event", func() {
				event := &entity.ResourceMetadata{
					ID: "plugin-metadata-1",
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
					Op:   mvccpb.PUT,
					Kind: constant.PluginMetadata,
					Ctx:  context.Background(),
				}

				// Global resources should not be skipped even with empty gateway/stage
				agent.handleEvent(event)
			})
		})
	})

	Describe("handleTicker", func() {
		It("should not send to commit channel when timer is empty", func() {
			agent.handleTicker(context.Background())

			select {
			case <-commitChan:
				Fail("should not receive anything when timer is empty")
			default:
				// Success - nothing received
			}
		})

		It("should send to commit channel when timer has expired releases", func() {
			// Add an event to timer
			event := &entity.ResourceMetadata{
				ID: "test-route-1",
				Labels: &entity.LabelInfo{
					Gateway:   "test-gateway",
					Stage:     "test-stage",
					PublishId: "1",
				},
				Op:   mvccpb.PUT,
				Kind: constant.Route,
				Ctx:  context.Background(),
			}
			agent.handleEvent(event)

			// Wait for timer to expire (100ms + buffer)
			time.Sleep(200 * time.Millisecond)

			agent.handleTicker(context.Background())

			select {
			case releases := <-commitChan:
				Expect(releases).To(HaveLen(1))
				Expect(releases[0].GetGatewayName()).To(Equal("test-gateway"))
			case <-time.After(time.Second):
				Fail("should receive releases from commit channel")
			}
		})
	})

	Describe("Multiple Events Handling", func() {
		It("should accumulate multiple events from same stage before timer expires", func() {
			// Send multiple events for the same stage
			for i := 0; i < 5; i++ {
				event := &entity.ResourceMetadata{
					ID: "route-" + string(rune('a'+i)),
					Labels: &entity.LabelInfo{
						Gateway:   "gateway-1",
						Stage:     "stage-1",
						PublishId: "1",
					},
					Op:   mvccpb.PUT,
					Kind: constant.Route,
					Ctx:  context.Background(),
				}
				agent.handleEvent(event)
			}

			// Timer should not have expired yet
			agent.handleTicker(context.Background())

			select {
			case <-commitChan:
				Fail("should not receive anything before timer expires")
			default:
				// Success - events are accumulated
			}
		})

		It("should commit accumulated events when timer expires", func() {
			// Send multiple events for the same stage
			for i := 0; i < 3; i++ {
				event := &entity.ResourceMetadata{
					ID: "route-" + string(rune('a'+i)),
					Labels: &entity.LabelInfo{
						Gateway:   "gateway-1",
						Stage:     "stage-1",
						PublishId: "1",
					},
					Op:   mvccpb.PUT,
					Kind: constant.Route,
					Ctx:  context.Background(),
				}
				agent.handleEvent(event)
			}

			// Wait for timer to expire (100ms + buffer)
			time.Sleep(200 * time.Millisecond)

			agent.handleTicker(context.Background())

			select {
			case releases := <-commitChan:
				// Should only have 1 release (stage-level, not resource-level)
				Expect(releases).To(HaveLen(1))
				Expect(releases[0].GetGatewayName()).To(Equal("gateway-1"))
				Expect(releases[0].GetStageName()).To(Equal("stage-1"))
			case <-time.After(time.Second):
				Fail("should receive releases from commit channel")
			}
		})

		It("should handle events from multiple different stages", func() {
			// Send events for different stages
			stages := []struct {
				gateway string
				stage   string
			}{
				{"gateway-a", "prod"},
				{"gateway-a", "test"},
				{"gateway-b", "prod"},
			}

			for _, s := range stages {
				event := &entity.ResourceMetadata{
					ID: s.gateway + "-" + s.stage + "-route",
					Labels: &entity.LabelInfo{
						Gateway:   s.gateway,
						Stage:     s.stage,
						PublishId: "1",
					},
					Op:   mvccpb.PUT,
					Kind: constant.Route,
					Ctx:  context.Background(),
				}
				agent.handleEvent(event)
			}

			// Wait for timer to expire (100ms + buffer)
			time.Sleep(200 * time.Millisecond)

			agent.handleTicker(context.Background())

			select {
			case releases := <-commitChan:
				// Should have 3 releases (one per stage)
				Expect(releases).To(HaveLen(3))

				// Verify all stages are present
				stageKeys := make(map[string]bool)
				for _, r := range releases {
					key := r.GetGatewayName() + "-" + r.GetStageName()
					stageKeys[key] = true
				}
				Expect(stageKeys).To(HaveKey("gateway-a-prod"))
				Expect(stageKeys).To(HaveKey("gateway-a-test"))
				Expect(stageKeys).To(HaveKey("gateway-b-prod"))
			case <-time.After(time.Second):
				Fail("should receive releases from commit channel")
			}
		})

		It("should update existing stage timer when new event arrives", func() {
			// First event
			event1 := &entity.ResourceMetadata{
				ID: "route-1",
				Labels: &entity.LabelInfo{
					Gateway:   "gateway-1",
					Stage:     "stage-1",
					PublishId: "1",
				},
				Op:   mvccpb.PUT,
				Kind: constant.Route,
				Ctx:  context.Background(),
			}
			agent.handleEvent(event1)

			// Wait a bit but not enough for timer to expire (50ms < 100ms)
			time.Sleep(50 * time.Millisecond)

			// Second event for same stage - should reset timer
			event2 := &entity.ResourceMetadata{
				ID: "route-2",
				Labels: &entity.LabelInfo{
					Gateway:   "gateway-1",
					Stage:     "stage-1",
					PublishId: "2",
				},
				Op:   mvccpb.PUT,
				Kind: constant.Route,
				Ctx:  context.Background(),
			}
			agent.handleEvent(event2)

			// Check timer - should not be ready yet since we just updated
			agent.handleTicker(context.Background())

			select {
			case <-commitChan:
				Fail("should not receive anything - timer was reset")
			default:
				// Success - timer was reset
			}

			// Now wait for timer to expire (100ms + buffer)
			time.Sleep(200 * time.Millisecond)

			agent.handleTicker(context.Background())

			select {
			case releases := <-commitChan:
				Expect(releases).To(HaveLen(1))
				// Should have the latest publishId
				Expect(releases[0].Labels.PublishId).To(Equal("2"))
			case <-time.After(time.Second):
				Fail("should receive releases from commit channel")
			}
		})

		It("should handle mixed global and stage resources", func() {
			// Stage resource event
			stageEvent := &entity.ResourceMetadata{
				ID: "route-1",
				Labels: &entity.LabelInfo{
					Gateway:   "gateway-1",
					Stage:     "stage-1",
					PublishId: "1",
				},
				Op:   mvccpb.PUT,
				Kind: constant.Route,
				Ctx:  context.Background(),
			}
			agent.handleEvent(stageEvent)

			// Global resource event
			globalEvent := &entity.ResourceMetadata{
				ID: "plugin-metadata-1",
				Labels: &entity.LabelInfo{
					Gateway: "",
					Stage:   "",
				},
				Op:   mvccpb.PUT,
				Kind: constant.PluginMetadata,
				Ctx:  context.Background(),
			}
			agent.handleEvent(globalEvent)

			// Wait for timer to expire (100ms + buffer)
			time.Sleep(200 * time.Millisecond)

			agent.handleTicker(context.Background())

			select {
			case releases := <-commitChan:
				// Should have 2 releases (1 stage + 1 global)
				Expect(releases).To(HaveLen(2))
			case <-time.After(time.Second):
				Fail("should receive releases from commit channel")
			}
		})

		It("should skip delete events for non-global resources", func() {
			// PUT event first
			putEvent := &entity.ResourceMetadata{
				ID: "route-1",
				Labels: &entity.LabelInfo{
					Gateway:   "gateway-1",
					Stage:     "stage-1",
					PublishId: "1",
				},
				Op:   mvccpb.PUT,
				Kind: constant.Route,
				Ctx:  context.Background(),
			}
			agent.handleEvent(putEvent)

			// DELETE event for different resource in same stage
			deleteEvent := &entity.ResourceMetadata{
				ID: "route-2",
				Labels: &entity.LabelInfo{
					Gateway:   "gateway-1",
					Stage:     "stage-1",
					PublishId: "1",
				},
				Op:   mvccpb.DELETE,
				Kind: constant.Route,
				Ctx:  context.Background(),
			}
			agent.handleEvent(deleteEvent)

			// Wait for timer to expire (100ms + buffer)
			time.Sleep(200 * time.Millisecond)

			agent.handleTicker(context.Background())

			select {
			case releases := <-commitChan:
				// Should only have 1 release from PUT event
				Expect(releases).To(HaveLen(1))
			case <-time.After(time.Second):
				Fail("should receive releases from commit channel")
			}
		})

		It("should handle global resource delete event", func() {
			// Global resource DELETE event should be processed
			globalDeleteEvent := &entity.ResourceMetadata{
				ID: "plugin-metadata-1",
				Labels: &entity.LabelInfo{
					Gateway: "",
					Stage:   "",
				},
				Op:   mvccpb.DELETE,
				Kind: constant.PluginMetadata,
				Ctx:  context.Background(),
			}
			agent.handleEvent(globalDeleteEvent)

			// Wait for timer to expire (100ms + buffer)
			time.Sleep(200 * time.Millisecond)

			agent.handleTicker(context.Background())

			select {
			case releases := <-commitChan:
				// Global delete should be processed
				Expect(releases).To(HaveLen(1))
			case <-time.After(time.Second):
				Fail("should receive releases from commit channel")
			}
		})
	})
})
