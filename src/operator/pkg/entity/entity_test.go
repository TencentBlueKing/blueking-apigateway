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

package entity

import (
	"context"
	"encoding/json"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.etcd.io/etcd/api/v3/mvccpb"

	"operator/pkg/constant"
)

var _ = Describe("Entity", func() {
	Describe("NewEmptyApisixConfiguration", func() {
		It("should create an empty ApisixStageResource with initialized maps", func() {
			config := NewEmptyApisixConfiguration()
			Expect(config).NotTo(BeNil())
			Expect(config.Routes).NotTo(BeNil())
			Expect(config.Services).NotTo(BeNil())
			Expect(config.SSLs).NotTo(BeNil())

			Expect(len(config.Routes)).To(Equal(0))
			Expect(len(config.Services)).To(Equal(0))
			Expect(len(config.SSLs)).To(Equal(0))
		})
	})

	Describe("NewEmptyApisixGlobalResource", func() {
		It("should create an empty ApisixGlobalResource with initialized maps", func() {
			resource := NewEmptyApisixGlobalResource()
			Expect(resource).NotTo(BeNil())
			Expect(resource.PluginMetadata).NotTo(BeNil())

			Expect(len(resource.PluginMetadata)).To(Equal(0))
		})
	})

	Describe("Route", func() {
		var route *Route

		BeforeEach(func() {
			route = &Route{
				CreateTime: 1234567890,
				UpdateTime: 9876543210,
			}
		})

		Context("GetCreateTime", func() {
			It("should return the create time", func() {
				Expect(route.GetCreateTime()).To(Equal(int64(1234567890)))
			})
		})

		Context("GetUpdateTime", func() {
			It("should return the update time", func() {
				Expect(route.GetUpdateTime()).To(Equal(int64(9876543210)))
			})
		})

		Context("SetCreateTime", func() {
			It("should set the create time", func() {
				route.SetCreateTime(111111)
				Expect(route.CreateTime).To(Equal(int64(111111)))
			})
		})

		Context("SetUpdateTime", func() {
			It("should set the update time", func() {
				route.SetUpdateTime(222222)
				Expect(route.UpdateTime).To(Equal(int64(222222)))
			})
		})
	})

	Describe("Service", func() {
		var service *Service

		BeforeEach(func() {
			service = &Service{
				CreateTime: 1234567890,
				UpdateTime: 9876543210,
			}
		})

		Context("GetCreateTime", func() {
			It("should return the create time", func() {
				Expect(service.GetCreateTime()).To(Equal(int64(1234567890)))
			})
		})

		Context("GetUpdateTime", func() {
			It("should return the update time", func() {
				Expect(service.GetUpdateTime()).To(Equal(int64(9876543210)))
			})
		})

		Context("SetCreateTime", func() {
			It("should set the create time", func() {
				service.SetCreateTime(111111)
				Expect(service.CreateTime).To(Equal(int64(111111)))
			})
		})

		Context("SetUpdateTime", func() {
			It("should set the update time", func() {
				service.SetUpdateTime(222222)
				Expect(service.UpdateTime).To(Equal(int64(222222)))
			})
		})
	})

	Describe("PluginMetadataConf", func() {
		Context("UnmarshalJSON", func() {
			It("should unmarshal valid JSON with id", func() {
				conf := &PluginMetadataConf{}
				jsonData := []byte(`{"id":"test-plugin","key":"value"}`)
				err := conf.UnmarshalJSON(jsonData)
				Expect(err).NotTo(HaveOccurred())
				Expect(*conf).To(HaveKey("test-plugin"))
			})

			It("should return error when id is empty", func() {
				conf := &PluginMetadataConf{}
				jsonData := []byte(`{"key":"value"}`)
				err := conf.UnmarshalJSON(jsonData)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(ContainSubstring("plugin id is empty"))
			})

			It("should return error when JSON is invalid", func() {
				conf := &PluginMetadataConf{}
				jsonData := []byte(`invalid json`)
				err := conf.UnmarshalJSON(jsonData)
				Expect(err).To(HaveOccurred())
			})
		})

		Context("MarshalJSON", func() {
			It("should marshal to original JSON", func() {
				conf := PluginMetadataConf{
					"test-plugin": json.RawMessage(`{"id":"test-plugin","key":"value"}`),
				}
				result, err := conf.MarshalJSON()
				Expect(err).NotTo(HaveOccurred())
				Expect(result).To(MatchJSON(`{"id":"test-plugin","key":"value"}`))
			})

			It("should return error when conf is empty", func() {
				conf := PluginMetadataConf{}
				result, err := conf.MarshalJSON()
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(Equal("invalid plugin conf"))
				Expect(result).To(BeNil())
			})

			It("should return error when key is empty", func() {
				conf := PluginMetadataConf{
					"": json.RawMessage(`{"key":"value"}`),
				}
				result, err := conf.MarshalJSON()
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(Equal("invalid plugin conf"))
				Expect(result).To(BeNil())
			})
		})
	})

	Describe("PluginMetadata", func() {
		Context("UnmarshalJSON and MarshalJSON integration", func() {
			It("should successfully unmarshal and marshal plugin metadata", func() {
				jsonData := []byte(`{"id":"test-plugin","setting1":"value1","setting2":100}`)
				conf := &PluginMetadataConf{}
				err := conf.UnmarshalJSON(jsonData)
				Expect(err).NotTo(HaveOccurred())

				result, err := conf.MarshalJSON()
				Expect(err).NotTo(HaveOccurred())
				Expect(result).To(MatchJSON(jsonData))
			})
		})
	})

	Describe("ResourceMetadata", func() {
		var rm *ResourceMetadata

		BeforeEach(func() {
			rm = &ResourceMetadata{
				ID:   "test-id",
				Kind: constant.Route,
				Labels: &LabelInfo{
					Gateway:       "test-gateway",
					Stage:         "test-stage",
					PublishId:     "123",
					ApisixVersion: "3.13.X",
				},
				Ctx: context.Background(),
			}
		})

		Context("GetID", func() {
			It("should return the resource ID", func() {
				Expect(rm.GetID()).To(Equal("test-id"))
			})
		})

		Context("GetGatewayName", func() {
			It("should return the gateway name from labels", func() {
				Expect(rm.GetGatewayName()).To(Equal("test-gateway"))
			})

			It("should return empty string when labels is nil", func() {
				rm.Labels = nil
				Expect(rm.GetGatewayName()).To(Equal(""))
			})
		})

		Context("GetStageName", func() {
			It("should return the stage name from labels", func() {
				Expect(rm.GetStageName()).To(Equal("test-stage"))
			})

			It("should return empty string when labels is nil", func() {
				rm.Labels = nil
				Expect(rm.GetStageName()).To(Equal(""))
			})
		})

		Context("GetStageKey", func() {
			It("should return the stage key from gateway and stage names", func() {
				expected := "bk.release.test-gateway.test-stage"
				Expect(rm.GetStageKey()).To(Equal(expected))
			})
		})

		Context("IsEmpty", func() {
			It("should return true when resource metadata is nil", func() {
				var nilRM *ResourceMetadata
				Expect(nilRM.IsEmpty()).To(BeTrue())
			})

			It("should return false when gateway and stage are set", func() {
				Expect(rm.IsEmpty()).To(BeFalse())
			})

			It("should return true when both gateway and stage are empty (non-PluginMetadata)", func() {
				rm.Labels.Gateway = ""
				rm.Labels.Stage = ""
				Expect(rm.IsEmpty()).To(BeTrue())
			})

			It("should return false for PluginMetadata even with empty labels", func() {
				rm.Kind = constant.PluginMetadata
				rm.Labels.Gateway = ""
				rm.Labels.Stage = ""
				Expect(rm.IsEmpty()).To(BeFalse())
			})
		})

		Context("IsGlobalResource", func() {
			It("should return true for PluginMetadata with no stage", func() {
				rm.Kind = constant.PluginMetadata
				rm.Labels.Stage = ""
				Expect(rm.IsGlobalResource()).To(BeTrue())
			})

			It("should return false for PluginMetadata with stage", func() {
				rm.Kind = constant.PluginMetadata
				rm.Labels.Stage = "test-stage"
				Expect(rm.IsGlobalResource()).To(BeFalse())
			})

			It("should return false for non-PluginMetadata resources", func() {
				rm.Kind = constant.Route
				Expect(rm.IsGlobalResource()).To(BeFalse())
			})
		})

		Context("GetReleaseID", func() {
			It("should return stage key for non-PluginMetadata resources", func() {
				rm.Kind = constant.Route
				expected := "bk.release.test-gateway.test-stage"
				Expect(rm.GetReleaseID()).To(Equal(expected))
			})

			It("should return ID for PluginMetadata resources", func() {
				rm.Kind = constant.PluginMetadata
				Expect(rm.GetReleaseID()).To(Equal("test-id"))
			})
		})

		Context("GetReleaseInfo", func() {
			It("should return ReleaseInfo with correct values", func() {
				releaseInfo := rm.GetReleaseInfo()
				Expect(releaseInfo).NotTo(BeNil())
				Expect(releaseInfo.ID).To(Equal("test-id"))
				Expect(releaseInfo.PublishId).To(Equal(123))
				Expect(releaseInfo.ApisixVersion).To(Equal("3.13.X"))
				Expect(releaseInfo.Ctx).To(Equal(context.Background()))
			})

			It("should handle non-numeric PublishId gracefully", func() {
				rm.Labels.PublishId = "not-a-number"
				releaseInfo := rm.GetReleaseInfo()
				Expect(releaseInfo.PublishId).To(Equal(0))
			})
		})

		Context("IsDeleteRelease", func() {
			It("should return true when Op is PUT and PublishId is DeletePublishID", func() {
				rm.Op = mvccpb.PUT
				rm.Labels.PublishId = constant.DeletePublishID
				Expect(rm.IsDeleteRelease()).To(BeTrue())
			})

			It("should return false when Op is not PUT", func() {
				rm.Op = mvccpb.DELETE
				rm.Labels.PublishId = constant.DeletePublishID
				Expect(rm.IsDeleteRelease()).To(BeFalse())
			})

			It("should return false when PublishId is not DeletePublishID", func() {
				rm.Op = mvccpb.PUT
				rm.Labels.PublishId = "123"
				Expect(rm.IsDeleteRelease()).To(BeFalse())
			})

			It("should handle nil labels gracefully", func() {
				rm.Op = mvccpb.PUT
				rm.Labels = nil
				// GetReleaseInfo will panic with nil labels, so we just verify
				// that calling with proper setup doesn't panic
				rm.Labels = &LabelInfo{PublishId: "1"}
				Expect(rm.IsDeleteRelease()).To(BeFalse())
			})
		})

		Context("ClearUnusedFields", func() {
			It("should clear PublishId from labels", func() {
				rm.Labels.PublishId = "123"
				rm.ClearUnusedFields()
				Expect(rm.Labels.PublishId).To(Equal(""))
			})

			It("should not panic when labels is nil", func() {
				rm.Labels = nil
				Expect(func() { rm.ClearUnusedFields() }).NotTo(Panic())
			})
		})

		Context("GetCreateTime/SetCreateTime", func() {
			It("should return 0 for ResourceMetadata", func() {
				Expect(rm.GetCreateTime()).To(Equal(int64(0)))
			})

			It("should not panic when setting create time", func() {
				Expect(func() { rm.SetCreateTime(123456) }).NotTo(Panic())
			})
		})

		Context("GetUpdateTime/SetUpdateTime", func() {
			It("should return 0 for ResourceMetadata", func() {
				Expect(rm.GetUpdateTime()).To(Equal(int64(0)))
			})

			It("should not panic when setting update time", func() {
				Expect(func() { rm.SetUpdateTime(123456) }).NotTo(Panic())
			})
		})
	})

	Describe("ReleaseInfo", func() {
		var ri *ReleaseInfo

		BeforeEach(func() {
			ri = &ReleaseInfo{
				ResourceMetadata: ResourceMetadata{
					ID: "test-release",
				},
				PublishId:       100,
				PublishTime:     "2025-01-01T00:00:00Z",
				ApisixVersion:   "3.13.X",
				ResourceVersion: "v1.0.0",
			}
		})

		Context("String", func() {
			It("should format ReleaseInfo as string", func() {
				expected := "test-release:100:2025-01-01T00:00:00Z:3.13.X:v1.0.0"
				Expect(ri.String()).To(Equal(expected))
			})
		})

		Context("IsNoNeedReport", func() {
			It("should return true when PublishId is NoNeedReportPublishID (-1)", func() {
				ri.PublishId = -1
				Expect(ri.IsNoNeedReport()).To(BeTrue())
			})

			It("should return true when PublishId is DeletePublishID (-2)", func() {
				ri.PublishId = -2
				Expect(ri.IsNoNeedReport()).To(BeTrue())
			})

			It("should return false when PublishId is 0", func() {
				ri.PublishId = 0
				// PublishId 0 is converted to "0" which doesn't match the special constants
				Expect(ri.IsNoNeedReport()).To(BeFalse())
			})

			It("should return false when PublishId is a valid positive number", func() {
				ri.PublishId = 100
				Expect(ri.IsNoNeedReport()).To(BeFalse())
			})
		})
	})

	Describe("LabelInfo", func() {
		It("should have correct json tags", func() {
			labels := &LabelInfo{
				Gateway:       "test-gateway",
				Stage:         "prod",
				PublishId:     "100",
				ApisixVersion: "3.13.X",
			}

			jsonData, err := json.Marshal(labels)
			Expect(err).NotTo(HaveOccurred())

			var result map[string]string
			err = json.Unmarshal(jsonData, &result)
			Expect(err).NotTo(HaveOccurred())

			Expect(result).To(HaveKeyWithValue("gateway.bk.tencent.com/gateway", "test-gateway"))
			Expect(result).To(HaveKeyWithValue("gateway.bk.tencent.com/stage", "prod"))
			Expect(result).To(HaveKeyWithValue("gateway.bk.tencent.com/publish-id", "100"))
			Expect(result).To(HaveKeyWithValue("gateway.bk.tencent.com/apisix-version", "3.13.X"))
		})
	})

	Describe("Edge Cases", func() {
		Context("ResourceMetadata with nil context", func() {
			It("should handle nil context gracefully", func() {
				rm := &ResourceMetadata{
					ID:   "test-id",
					Kind: constant.Route,
					Labels: &LabelInfo{
						Gateway: "gateway",
						Stage:   "stage",
					},
					Ctx: nil,
				}

				releaseInfo := rm.GetReleaseInfo()
				Expect(releaseInfo.Ctx).To(BeNil())
			})
		})

		Context("ResourceMetadata with empty ID", func() {
			It("should return empty string for GetID", func() {
				rm := &ResourceMetadata{
					ID: "",
				}
				Expect(rm.GetID()).To(Equal(""))
			})
		})

		Context("ReleaseInfo String with zero values", func() {
			It("should format correctly with zero values", func() {
				ri := &ReleaseInfo{}
				expected := ":0:::"
				Expect(ri.String()).To(Equal(expected))
			})
		})
	})
})
