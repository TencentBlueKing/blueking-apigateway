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

package integration_test

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	clientv3 "go.etcd.io/etcd/client/v3"

	"operator/pkg/client"
	"operator/pkg/config"
	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/metric"
	"operator/tests/integration"
)

const (
	testGateway           = "bk-default"
	testStage             = "default"
	testDataServiceAmount = 1
	testDataRoutesAmount  = 3
	operatorURL           = "http://127.0.0.1:6004"
	publishID             = 1
	delPublishID          = 2
	delRouteKey           = "/bk-gateway-apigw/v2/gateway/bk-default/default/route/bk-default.default.2"
	versionProbeRouteKey  = "/bk-gateway-apigw/v2/gateway/bk-default/default/route/bk-default.default.-1"
)

var stageKey = config.GenStagePrimaryKey(testGateway, testStage)

var _ = Describe("Operator Integration", func() {
	// Wait for operator to be ready before running tests
	time.Sleep(time.Second * 10)
	var etcdCli *clientv3.Client
	var resourceCli *client.ResourceClient
	BeforeEach(func() {
		cfg := clientv3.Config{
			Endpoints:   []string{"localhost:2479"},
			DialTimeout: 5 * time.Second,
		}
		var err error
		etcdCli, err = clientv3.New(cfg)
		Expect(err).NotTo(HaveOccurred())
		resourceCli = client.NewResourceClient(operatorURL, "xxxxx")
	})

	AfterEach(func() {
		_, err := etcdCli.Delete(context.Background(), "/", clientv3.WithPrefix())
		Expect(err).NotTo(HaveOccurred())
		_ = etcdCli.Close()
	})

	Describe("test publish and update default resource", func() {
		Context("test new apigateway publish", func() {
			It("should not error and the value should be equal to what was put", func() {
				// load resources
				resources := integration.GetBkDefaultResource()
				// put route
				for key, route := range resources.Routes {
					rawConfig, _ := json.Marshal(route)
					_, err := etcdCli.Put(context.Background(), key, string(rawConfig))
					Expect(err).NotTo(HaveOccurred())
				}

				// put service
				for key, service := range resources.Services {
					rawConfig, _ := json.Marshal(service)
					_, err := etcdCli.Put(context.Background(), key, string(rawConfig))
					Expect(err).NotTo(HaveOccurred())
				}

				// put global rule
				globalResource := integration.GetBkDefaultGlobalResource()
				for key, pluginMetadata := range globalResource.PluginMetadata {
					rawConfig, _ := json.Marshal(pluginMetadata)
					_, err := etcdCli.Put(context.Background(), key, string(rawConfig))
					Expect(err).NotTo(HaveOccurred())
				}
				// put stage release
				stageRelease := integration.GetBkDefaultStageRelease()
				for key, release := range stageRelease {
					rawConfig, _ := json.Marshal(release)
					_, err := etcdCli.Put(context.Background(), key, string(rawConfig))
					Expect(err).NotTo(HaveOccurred())
				}

				time.Sleep(time.Second * 30)

				metricsAdapter, err := integration.NewMetricsAdapter(operatorURL)

				Expect(err).NotTo(HaveOccurred())

				// assert resource_event_triggered_count
				Expect(metricsAdapter.GetResourceEventTriggeredCountMetric(
					testGateway, testStage, constant.Route.String()),
				).To(Equal(testDataRoutesAmount))

				Expect(metricsAdapter.GetResourceEventTriggeredCountMetric(
					testGateway, testStage, constant.Service.String()),
				).To(Equal(testDataServiceAmount))

				// assert resource convert
				Expect(metricsAdapter.GetResourceConvertedCountMetric(
					testGateway, testStage, constant.ApisixResourceTypeRoutes),
				).To(Equal(testDataRoutesAmount))

				Expect(metricsAdapter.GetResourceConvertedCountMetric(
					testGateway, testStage, constant.ApisixResourceTypeServices),
				).To(Equal(testDataServiceAmount))

				// assert apisix operation count
				Expect(metricsAdapter.GetApisixOperationCountMetric(
					metric.ActionPut, metric.ResultSuccess, constant.ApisixResourceTypeRoutes),
				// 2 micro-gateway-not-found-handling and healthz-outer and head-outer
				).To(Equal(testDataRoutesAmount + 3))

				Expect(metricsAdapter.GetApisixOperationCountMetric(
					metric.ActionPut, metric.ResultSuccess, constant.ApisixResourceTypeServices),
				).To(Equal(testDataServiceAmount))

				// assert apisix resource
				apisixGatewayResourcesMap, err := resourceCli.ApisixList(&client.ApisixListRequest{
					GatewayName: testGateway,
					StageName:   testStage,
				})
				Expect(err).NotTo(HaveOccurred())

				resourceInfo, ok := apisixGatewayResourcesMap[stageKey]

				Expect(ok).To(BeTrue())

				Expect(len(resourceInfo.Routes)).To(Equal(testDataRoutesAmount))
				Expect(len(resourceInfo.Services)).To(Equal(testDataServiceAmount))

				// assert apigw resource count
				apisixGatewayResourceCount, err := resourceCli.ApisixStageResourceCount(
					&client.ApisixListRequest{
						GatewayName: testGateway,
						StageName:   testStage,
					},
				)
				Expect(err).NotTo(HaveOccurred())
				Expect(apisixGatewayResourceCount.Count).To(Equal(int64(testDataRoutesAmount)))

				// assert apisix current-version publish_id
				apisixResourceVersion, err := resourceCli.ApisixStageCurrentVersion(
					&client.ApisixListRequest{
						GatewayName: testGateway,
						StageName:   testStage,
					},
				)
				Expect(err).NotTo(HaveOccurred())
				Expect(apisixResourceVersion["publish_id"]).To(Equal(float64(publishID)))

				// diff apigw config and apisix config
				apigwResourceListMap, err := resourceCli.ApigwList(&client.ApigwListRequest{
					GatewayName: testGateway,
					StageName:   testStage,
				})
				Expect(err).NotTo(HaveOccurred())
				Expect(len(apigwResourceListMap)).To(Equal(len(apisixGatewayResourcesMap)))

				// 创建过滤选项，忽略时间戳和 publish-id 字段
				ignoreTimeFields := cmpopts.IgnoreFields(entity.Route{}, "CreateTime", "UpdateTime")
				ignoreServiceTimeFields := cmpopts.IgnoreFields(
					entity.Service{},
					"CreateTime",
					"UpdateTime",
				)

				for key, resource := range apigwResourceListMap {
					for routeKey, resourceInfo := range resource.Routes {
						diff := cmp.Diff(
							resourceInfo,
							apisixGatewayResourcesMap[key].Routes[routeKey],
							ignoreTimeFields,
						)
						Expect(diff).To(BeEmpty())
					}
					for serviceKey, resourceInfo := range resource.Services {
						diff := cmp.Diff(
							resourceInfo,
							apisixGatewayResourcesMap[key].Services[serviceKey],
							ignoreServiceTimeFields,
							cmpopts.IgnoreFields(entity.LabelInfo{}, "PublishId"),
						)
						Expect(diff).To(BeEmpty())
					}
				}

				// del route
				_, err = etcdCli.Delete(context.Background(), delRouteKey)
				Expect(err).NotTo(HaveOccurred())
				// put route
				for key, route := range resources.Routes {
					if key == delRouteKey {
						continue
					}
					if key == versionProbeRouteKey {
						route.Plugins["bk-mock"] = map[string]any{
							"response_status": 200,
							"response_example": fmt.Sprintf(
								"{\"publish_id\": %d, \"start_time\": \"2025-10-22 15:24:57+0800\"}",
								delPublishID,
							),
							"response_headers": map[string]string{
								"Content-Type": "application/json",
							},
						}
					}
					route.Labels.PublishId = fmt.Sprintf("%d", delPublishID)
					rawConfig, _ := json.Marshal(route)
					_, err := etcdCli.Put(context.Background(), key, string(rawConfig))
					Expect(err).NotTo(HaveOccurred())
				}

				// put service
				for key, service := range resources.Services {
					service.Labels.PublishId = fmt.Sprintf("%d", delPublishID)
					rawConfig, _ := json.Marshal(service)
					_, err := etcdCli.Put(context.Background(), key, string(rawConfig))
					Expect(err).NotTo(HaveOccurred())
				}

				// add del route release
				// put stage release
				for key, release := range stageRelease {
					release.PublishId = delPublishID
					release.Labels.PublishId = fmt.Sprintf("%d", delPublishID)
					rawConfig, _ := json.Marshal(release)
					_, err := etcdCli.Put(context.Background(), key, string(rawConfig))
					Expect(err).NotTo(HaveOccurred())
				}

				time.Sleep(time.Second * 40)

				// assert apisix current-version publish_id
				apisixResourceVersion, err = resourceCli.ApisixStageCurrentVersion(
					&client.ApisixListRequest{
						GatewayName: testGateway,
						StageName:   testStage,
					},
				)
				Expect(err).NotTo(HaveOccurred())
				Expect(apisixResourceVersion["publish_id"]).To(Equal(float64(delPublishID)))

				apisixResourceListMap, err := resourceCli.ApisixList(&client.ApisixListRequest{
					GatewayName: testGateway,
					StageName:   testStage,
				})
				Expect(err).NotTo(HaveOccurred())
				for _, resource := range apisixResourceListMap {
					Expect(len(resource.Routes)).To(Equal(testDataRoutesAmount - 1))
					Expect(len(resource.Services)).To(Equal(testDataServiceAmount))
				}
			})
		})
	})
})
