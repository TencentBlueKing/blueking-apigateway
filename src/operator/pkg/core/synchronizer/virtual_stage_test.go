// Package synchronizer_test ...
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
	"bytes"
	"os"
	"path/filepath"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/spf13/viper"
	yaml "gopkg.in/yaml.v2"

	"operator/pkg/config"
	"operator/pkg/constant"
	. "operator/pkg/core/synchronizer"
	"operator/pkg/entity"
)

var _ = Describe("VirtualStage", func() {
	var (
		stage            *VirtualStage
		apisixHealthzURI string
		gatewayName      string
		stageName        string
		logPath          string
	)

	JustAfterEach(viper.Reset)

	BeforeEach(func() {
		apisixHealthzURI = "/healthz"
		gatewayName = "virtual-gateway"
		stageName = "virtual-stage"
		logPath = "/logs/access.log"

		Init(&config.Config{
			Apisix: config.Apisix{
				VirtualStage: config.VirtualStage{
					VirtualGateway:    gatewayName,
					VirtualStage:      stageName,
					FileLoggerLogPath: logPath,
				},
			},
		})
	})

	JustBeforeEach(func() {
		stage = NewVirtualStage(apisixHealthzURI)
	})

	checkLabels := func(labels *entity.LabelInfo) {
		Expect(labels.Gateway).To(Equal(gatewayName))
		Expect(labels.Stage).To(Equal(stageName))
	}

	checkMetadata := func(metadata entity.ResourceMetadata) {
		// Name 可能为空，只检查 ID 和 Labels
		Expect(metadata.ID).NotTo(BeEmpty())
		checkLabels(metadata.Labels)
	}

	Context("MakeConfiguration", func() {
		var configuration *entity.ApisixStageResource

		JustBeforeEach(func() {
			configuration = stage.MakeConfiguration()
		})

		Context("Standard Configuration", func() {
			It("should create 404 default route", func() {
				route := configuration.Routes[NotFoundHandling]
				checkMetadata(route.ResourceMetadata)

				Expect(route.URI).To(Equal("/*"))
				Expect(route.Priority).To(Equal(-100))
				Expect(route.Status).To(Equal(entity.Status(1)))

				plugins := route.Plugins
				Expect(plugins).To(HaveKey("bk-error-wrapper"))
				Expect(plugins).To(HaveKey("bk-not-found-handler"))
				Expect(plugins["file-logger"]).To(HaveKeyWithValue("path", logPath))
			})

			It("should create outter healthz route", func() {
				route := configuration.Routes[HealthZRouteIDOuter]
				checkMetadata(route.ResourceMetadata)

				Expect(route.Uris).To(ContainElement(apisixHealthzURI))
				Expect(route.Priority).To(Equal(-100))
				Expect(route.Methods).To(ContainElement("GET"))
				Expect(route.Status).To(Equal(entity.Status(1)))

				plugins := route.Plugins
				Expect(plugins["limit-req"]).To(HaveKeyWithValue("key", "server_addr"))
				Expect(plugins["mocking"]).To(HaveKeyWithValue("response_example", "ok"))
			})
		})

		Context("Extra Configuration", func() {
			var (
				extraPath          string
				extraConfiguration *entity.ApisixStageResource
			)

			BeforeEach(func() {
				extraPath = filepath.Join(os.TempDir(), "extra-config.yaml")
				Init(&config.Config{
					Apisix: config.Apisix{
						VirtualStage: config.VirtualStage{
							VirtualGateway:       gatewayName,
							VirtualStage:         stageName,
							FileLoggerLogPath:    logPath,
							ExtraApisixResources: extraPath,
						},
					},
				})

				extraConfiguration = entity.NewEmptyApisixConfiguration()
				// 重新创建 stage 以使用新的配置
				stage = NewVirtualStage(apisixHealthzURI)
				// 初始化 configuration 用于比较
				configuration = stage.MakeConfiguration()
			})

			AfterEach(func() {
				_ = os.Remove(extraPath)
			})

			writeExtraConfiguration := func() {
				// 将 ApisixStageResource (map) 转换为 ExtraApisixStageResource (slice)
				extraConfig := &entity.ExtraApisixStageResource{
					Routes:   make([]*entity.Route, 0, len(extraConfiguration.Routes)),
					Services: make([]*entity.Service, 0, len(extraConfiguration.Services)),
					SSLs:     make([]*entity.SSL, 0, len(extraConfiguration.SSLs)),
				}
				for _, route := range extraConfiguration.Routes {
					extraConfig.Routes = append(extraConfig.Routes, route)
				}
				for _, service := range extraConfiguration.Services {
					extraConfig.Services = append(extraConfig.Services, service)
				}
				for _, ssl := range extraConfiguration.SSLs {
					extraConfig.SSLs = append(extraConfig.SSLs, ssl)
				}

				buf := &bytes.Buffer{}
				encoder := yaml.NewEncoder(buf)
				Expect(encoder.Encode(extraConfig)).To(BeNil())

				Expect(os.WriteFile(extraPath, buf.Bytes(), 0o644)).To(BeNil())
			}

			It("should skip a not exists file", func() {
				config := stage.MakeConfiguration()
				Expect(len(config.Routes)).To(Equal(len(configuration.Routes)))
			})

			It("should skip a valid yaml", func() {
				Expect(os.WriteFile(extraPath, []byte("not:a:yaml"), 0o644)).To(BeNil())

				config := stage.MakeConfiguration()
				Expect(len(config.Routes)).To(Equal(len(configuration.Routes)))
			})

			It("should not include invalid extra route", func() {
				extraConfiguration.Routes[""] = &entity.Route{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "",
						Kind: constant.Route,
					},
				}
				writeExtraConfiguration()

				config := stage.MakeConfiguration()
				Expect(len(config.Routes)).To(Equal(len(configuration.Routes)))
			})

			It("should include valid extra route", func() {
				extraConfiguration.Routes["not-empty"] = &entity.Route{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "not-empty",
						Kind: constant.Route,
					},
				}
				writeExtraConfiguration()

				config := stage.MakeConfiguration()
				Expect(len(config.Routes)).To(Equal(len(configuration.Routes) + 1))

				for _, route := range config.Routes {
					checkMetadata(route.ResourceMetadata)
				}
			})

			It("should not include invalid extra service", func() {
				extraConfiguration.Services[""] = &entity.Service{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "",
						Kind: constant.Service,
					},
				}
				writeExtraConfiguration()

				config := stage.MakeConfiguration()
				Expect(len(config.Services)).To(Equal(len(configuration.Services)))
			})

			It("should include valid extra service", func() {
				extraConfiguration.Services["not-empty"] = &entity.Service{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "not-empty",
						Kind: constant.Service,
					},
				}
				writeExtraConfiguration()

				config := stage.MakeConfiguration()
				Expect(len(config.Services)).To(Equal(len(configuration.Services) + 1))

				for _, service := range config.Services {
					checkMetadata(service.ResourceMetadata)
				}
			})

			It("should not include invalid extra ssl", func() {
				extraConfiguration.SSLs[""] = &entity.SSL{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "",
						Kind: constant.SSL,
					},
				}
				writeExtraConfiguration()

				config := stage.MakeConfiguration()
				Expect(len(config.SSLs)).To(Equal(len(configuration.SSLs)))
			})

			It("should include valid extra ssl", func() {
				extraConfiguration.SSLs["not-empty"] = &entity.SSL{
					ResourceMetadata: entity.ResourceMetadata{
						ID:   "not-empty",
						Kind: constant.SSL,
					},
				}
				writeExtraConfiguration()

				config := stage.MakeConfiguration()
				Expect(len(config.SSLs)).To(Equal(len(configuration.SSLs) + 1))

				for _, ssl := range config.SSLs {
					checkLabels(ssl.Labels)
				}
			})
		})
	})
})
