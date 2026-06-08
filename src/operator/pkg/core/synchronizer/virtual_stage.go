// Package synchronizer ...
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

// Package synchronizer ...
package synchronizer

import (
	"net/http"
	"os"

	"go.uber.org/zap"
	"gopkg.in/yaml.v2"

	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/logging"
)

// HealthZRouteIDInner ... 这几个路由都是外部系统需要的，切记不能修改和删除
const (
	HealthZRouteIDOuter = "micro-gateway-operator-healthz-outer"
	NotFoundHandling    = "micro-gateway-not-found-handling"
	HEADRouteIDOuter    = "data-plane-header-liveness"
)

// VirtualStage combine some builtin routes
type VirtualStage struct {
	entity.ResourceMetadata
	apisixHealthzURI string

	logger *zap.SugaredLogger
}

// NewVirtualStage creates a new virtual stage
func NewVirtualStage(apisixHealthzURI string) *VirtualStage {
	metadata := entity.ResourceMetadata{
		Labels: &entity.LabelInfo{
			Gateway: virtualGatewayName,
			Stage:   virtualStageName,
		},
	}

	return &VirtualStage{
		ResourceMetadata: metadata,
		apisixHealthzURI: apisixHealthzURI,
		logger:           logging.GetLogger().Named("virtual-stage"),
	}
}

func (s *VirtualStage) makeRouteMetadata(id string) entity.ResourceMetadata {
	return entity.ResourceMetadata{
		ID:     id,
		Name:   id,
		Labels: s.ResourceMetadata.Labels,
	}
}

func (s *VirtualStage) make404DefaultRoute() *entity.Route {
	return &entity.Route{
		ResourceMetadata: s.makeRouteMetadata(NotFoundHandling),
		URI:              "/*",
		Priority:         -100,
		Plugins: map[string]any{
			"bk-error-wrapper":     map[string]any{},
			"bk-not-found-handler": map[string]any{},
			"file-logger": map[string]any{
				"path": fileLoggerLogPath,
			},
		},
		Status: constant.StatusEnable,
	}
}

func (s *VirtualStage) makeOuterHealthzRoute() *entity.Route {
	plugins := map[string]any{
		"limit-req": map[string]any{
			"rate":  float64(10),
			"burst": float64(10),
			"key":   "server_addr",
		},
		"mocking": map[string]any{
			"content_type":     "text/plain",
			"response_example": "ok",
		},
	}

	return &entity.Route{
		ResourceMetadata: s.makeRouteMetadata(HealthZRouteIDOuter),
		Uris:             []string{s.apisixHealthzURI},
		Priority:         -100,
		Methods:          []string{http.MethodGet},
		Plugins:          plugins,
		Status:           constant.StatusEnable,
	}
}

// makeOuterHEADRoute return the apisix configuration of outer HEAD route
func (s *VirtualStage) makeOuterHEADRoute() *entity.Route {
	plugins := map[string]any{
		"mocking": map[string]any{
			"content_type":     "text/plain",
			"response_example": "ok",
		},
	}
	return &entity.Route{
		ResourceMetadata: s.makeRouteMetadata(HEADRouteIDOuter),
		URI:              "/",
		Priority:         -99,
		Methods:          []string{http.MethodHead},
		Plugins:          plugins,
		Status:           constant.StatusEnable,
	}
}

func (s *VirtualStage) makeExtraConfiguration() *entity.ExtraApisixStageResource {
	var configuration entity.ExtraApisixStageResource

	if extraApisixResourcesPath == "" {
		return &configuration
	}

	file, err := os.Open(extraApisixResourcesPath)
	if err != nil {
		s.logger.Errorw("open resource path", "err", err, "path", extraApisixResourcesPath)
		return &configuration
	}
	defer func() {
		if err := file.Close(); err != nil {
			s.logger.Errorw("failed to close file", "err", err, "path", extraApisixResourcesPath)
		}
	}()
	decoder := yaml.NewDecoder(file)
	err = decoder.Decode(&configuration)
	if err != nil {
		s.logger.Errorf("parse resource path: %v, decode resource failed: %v", extraApisixResourcesPath, err)
		return &configuration
	}
	return &configuration
}

// MakeConfiguration return the apisix configuration of virtual stage
func (s *VirtualStage) MakeConfiguration() *entity.ApisixStageResource {
	ret := entity.NewEmptyApisixConfiguration()
	extraConfiguration := s.makeExtraConfiguration()
	for _, service := range extraConfiguration.Services {
		if service != nil && service.ID != "" {
			service.Labels = s.Labels
			ret.Services[service.ID] = service
		}
	}

	for _, ssl := range extraConfiguration.SSLs {
		if ssl != nil && ssl.ID != "" {
			ssl.Labels = s.Labels
			ret.SSLs[ssl.ID] = ssl
		}
	}

	for _, route := range extraConfiguration.Routes {
		if route != nil && route.ID != "" {
			route.Labels = s.Labels
			ret.Routes[route.ID] = route
		}
	}

	for _, fn := range []func() *entity.Route{
		s.make404DefaultRoute,
		s.makeOuterHealthzRoute,
		s.makeOuterHEADRoute,
	} {
		route := fn()
		ret.Routes[route.ID] = route
	}

	return ret
}
