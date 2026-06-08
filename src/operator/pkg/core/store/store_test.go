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

package store

import (
	"context"
	"sync"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/prometheus/client_golang/prometheus"

	"operator/pkg/constant"
	"operator/pkg/core/differ"
	"operator/pkg/core/registry"
	"operator/pkg/entity"
	"operator/pkg/logging"
	"operator/pkg/metric"
)

var metricInitialized = false

var _ = Describe("ApisixEtcdStore", func() {
	// Initialize metrics once before all tests
	BeforeEach(func() {
		if !metricInitialized {
			metric.InitMetric(prometheus.NewRegistry())
			metricInitialized = true
		}
	})

	Describe("differ", func() {
		var d *differ.ConfigDiffer

		BeforeEach(func() {
			d = differ.NewConfigDiffer()
		})

		It("should diff routes correctly", func() {
			oldRoutes := map[string]*entity.Route{
				"route1": {
					ResourceMetadata: entity.ResourceMetadata{
						ID: "route1",
						Labels: &entity.LabelInfo{
							Gateway: "gateway1",
							Stage:   "stage1",
						},
					},
				},
			}
			newRoutes := map[string]*entity.Route{
				"route1": {
					ResourceMetadata: entity.ResourceMetadata{
						ID: "route1",
						Labels: &entity.LabelInfo{
							Gateway: "gateway1",
							Stage:   "stage1",
						},
					},
					URI: "/changed",
				},
				"route2": {
					ResourceMetadata: entity.ResourceMetadata{
						ID: "route2",
						Labels: &entity.LabelInfo{
							Gateway: "gateway1",
							Stage:   "stage1",
						},
					},
				},
			}

			put, del := d.DiffRoutes(oldRoutes, newRoutes)
			Expect(put).To(HaveLen(2)) // route1 changed, route2 added
			Expect(del).To(HaveLen(0))
		})

		It("should diff services correctly", func() {
			oldServices := map[string]*entity.Service{
				"svc1": {
					ResourceMetadata: entity.ResourceMetadata{
						ID: "svc1",
						Labels: &entity.LabelInfo{
							Gateway: "gateway1",
							Stage:   "stage1",
						},
					},
				},
				"svc2": {
					ResourceMetadata: entity.ResourceMetadata{
						ID: "svc2",
						Labels: &entity.LabelInfo{
							Gateway: "gateway1",
							Stage:   "stage1",
						},
					},
				},
			}
			newServices := map[string]*entity.Service{
				"svc1": {
					ResourceMetadata: entity.ResourceMetadata{
						ID: "svc1",
						Labels: &entity.LabelInfo{
							Gateway: "gateway1",
							Stage:   "stage1",
						},
					},
				},
			}

			put, del := d.DiffServices(oldServices, newServices)
			Expect(put).To(HaveLen(0))
			Expect(del).To(HaveLen(1)) // svc2 deleted
		})

		It("should diff SSLs correctly", func() {
			oldSSLs := map[string]*entity.SSL{}
			newSSLs := map[string]*entity.SSL{
				"ssl1": {
					ResourceMetadata: entity.ResourceMetadata{
						ID: "ssl1",
						Labels: &entity.LabelInfo{
							Gateway: "gateway1",
							Stage:   "stage1",
						},
					},
				},
			}

			put, del := d.DiffSSLs(oldSSLs, newSSLs)
			Expect(put).To(HaveLen(1)) // ssl1 added
			Expect(del).To(HaveLen(0))
		})

		It("should diff global resources correctly", func() {
			oldGlobal := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"pm1": {
						ResourceMetadata: entity.ResourceMetadata{
							ID: "pm1",
						},
					},
				},
			}
			newGlobal := &entity.ApisixGlobalResource{
				PluginMetadata: map[string]*entity.PluginMetadata{
					"pm2": {
						ResourceMetadata: entity.ResourceMetadata{
							ID: "pm2",
						},
					},
				},
			}

			put, del := d.DiffGlobal(oldGlobal, newGlobal)
			Expect(put.PluginMetadata).To(HaveLen(1)) // pm2 added
			Expect(del.PluginMetadata).To(HaveLen(1)) // pm1 deleted
		})

		It("should handle nil old config", func() {
			newConfig := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route1": {
						ResourceMetadata: entity.ResourceMetadata{ID: "route1"},
					},
				},
				Services: map[string]*entity.Service{},
				SSLs:     map[string]*entity.SSL{},
			}

			put, del := d.Diff(nil, newConfig)
			Expect(put).To(Equal(newConfig))
			Expect(del).To(BeNil())
		})

		It("should handle nil new config", func() {
			oldConfig := &entity.ApisixStageResource{
				Routes: map[string]*entity.Route{
					"route1": {
						ResourceMetadata: entity.ResourceMetadata{ID: "route1"},
					},
				},
				Services: map[string]*entity.Service{},
				SSLs:     map[string]*entity.SSL{},
			}

			put, del := d.Diff(oldConfig, nil)
			Expect(put).To(BeNil())
			Expect(del).To(Equal(oldConfig))
		})
	})

	Describe("Close", func() {
		It("should cancel context when Close is called", func() {
			ctx, cancel := context.WithCancel(context.Background())
			store := &ApisixEtcdStore{
				prefix:   "/apisix",
				registry: make(map[string]*registry.ApisixEtcdRegistry),
				differ:   differ.NewConfigDiffer(),
				lock:     &sync.RWMutex{},
				ctx:      ctx,
				cancel:   cancel,
				logger:   logging.GetLogger().Named("test-store"),
			}

			store.Close()

			// Context should be cancelled
			select {
			case <-ctx.Done():
				// Success
			default:
				Fail("context should be cancelled after Close")
			}
		})

		It("should not panic when cancel is nil", func() {
			store := &ApisixEtcdStore{
				prefix:   "/apisix",
				registry: make(map[string]*registry.ApisixEtcdRegistry),
				differ:   differ.NewConfigDiffer(),
				lock:     &sync.RWMutex{},
				cancel:   nil,
				logger:   logging.GetLogger().Named("test-store"),
			}

			Expect(func() {
				store.Close()
			}).NotTo(Panic())
		})
	})

	Describe("entity helpers", func() {
		It("should create empty apisix configuration", func() {
			config := entity.NewEmptyApisixConfiguration()

			Expect(config).NotTo(BeNil())
			Expect(config.Routes).NotTo(BeNil())
			Expect(config.Services).NotTo(BeNil())
			Expect(config.SSLs).NotTo(BeNil())
			Expect(config.Routes).To(HaveLen(0))
			Expect(config.Services).To(HaveLen(0))
			Expect(config.SSLs).To(HaveLen(0))
		})

		It("should create empty global resource", func() {
			global := entity.NewEmptyApisixGlobalResource()

			Expect(global).NotTo(BeNil())
			Expect(global.PluginMetadata).NotTo(BeNil())
			Expect(global.PluginMetadata).To(HaveLen(0))
		})
	})

	Describe("apisixResourceTypes", func() {
		It("should contain all required resource types", func() {
			Expect(apisixResourceTypes).To(ContainElement(constant.ApisixResourceTypeRoutes))
			Expect(apisixResourceTypes).To(ContainElement(constant.ApisixResourceTypeServices))
			Expect(apisixResourceTypes).To(ContainElement(constant.ApisixResourceTypeSSL))
			Expect(apisixResourceTypes).To(ContainElement(constant.ApisixResourceTypePluginMetadata))
			Expect(apisixResourceTypes).To(HaveLen(4))
		})
	})
})
