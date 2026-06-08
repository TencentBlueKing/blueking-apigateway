/*
 *  TencentBlueKing is pleased to support the open source community by making
 *  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 *  Copyright (C) Tencent. All rights reserved.
 *  Licensed under the MIT License (the "License"); you may not use this file except
 *  in compliance with the License. You may obtain a copy of the License at
 *
 *      http://opensource.org/licenses/MIT
 *
 *  Unless required by applicable law or agreed to in writing, software distributed under
 *  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 *  either express or implied. See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 *   We undertake not to change the open source license (MIT license) applicable
 *   to the current version of the project delivered to anyone in the future.
 */

// Package integration provides utilities for integration testing.
package integration

import (
	"context"
	"encoding/json"
	"net/http"
	"os"

	dto "github.com/prometheus/client_model/go"
	"github.com/prometheus/common/expfmt"

	"operator/pkg/entity"
)

const (
	ResourceEventTriggeredCountMetric = "resource_event_triggered_count"
	ResourceConvertedCountMetric      = "resource_converted_count"
	ResourceSyncCmpCount              = "sync_cmp_count"
	ResourceSyncCmpDiffCount          = "sync_cmp_diff_count"
	ApisixOperationCountMetric        = "apisix_operation_count"
)

// EtcdConfig is the config for the etcd
type EtcdConfig struct {
	Key   string `yaml:"key"`
	Value string `yaml:"value"`
}

// MetricsAdapter is the adapter for the metrics
type MetricsAdapter struct {
	Metrics map[string]*dto.MetricFamily
}

// GetBkDefaultResource retrieves the default API gateway stage resources from a JSON file.
// It reads the configuration from "bk_apigw_gateway_default_stage_resources.json"
// and unmarshals it into an ApisixStageResource struct.
// Returns: entity.ApisixStageResource - the default resources configuration
func GetBkDefaultResource() entity.ApisixStageResource {
	var resources entity.ApisixStageResource
	// Read the JSON file containing default stage resources
	data, err := os.ReadFile("bk_apigw_gateway_default_stage_resources.json")
	if err != nil {
		panic(err) // Panic if file reading fails
	}
	err = json.Unmarshal(data, &resources)
	if err != nil {
		panic(err) // Panic if YAML unmarshaling fails
	}
	return resources // Return the unmarshaled resources
}

// GetBkDefaultGlobalResource retrieves the default API gateway global resources from a JSON file.
// It reads the configuration from "bk_apigw_gateway_default_global_resources.json"
// and unmarshals it into an ApisixGlobalResource struct.
// Returns: entity.ApisixGlobalResource - the default global resources configuration
func GetBkDefaultGlobalResource() entity.ApisixGlobalResource {
	var resources entity.ApisixGlobalResource
	// Read the JSON file containing default stage resources
	data, err := os.ReadFile("bk_apigw_global_resources.json")
	if err != nil {
		panic(err) // Panic if file reading fails
	}
	err = json.Unmarshal(data, &resources)
	if err != nil {
		panic(err) // Panic if YAML unmarshaling fails
	}
	return resources // Return the unmarshaled resources
}

// GetBkDefaultStageRelease retrieves the default API gateway stage release from a JSON file.
// It reads the configuration from "bk_apigw_gateway_default_stage_release.json"
// and unmarshals it into a map[string]entity.ReleaseInfo struct.
// Returns: map[string]entity.ReleaseInfo - the default stage release configuration
func GetBkDefaultStageRelease() map[string]entity.ReleaseInfo {
	var resources map[string]entity.ReleaseInfo
	// Read the JSON file containing default stage resources
	data, err := os.ReadFile("bk_apigw_gateway_default_stage_release.json")
	if err != nil {
		panic(err) // Panic if file reading fails
	}
	err = json.Unmarshal(data, &resources)
	if err != nil {
		panic(err) // Panic if YAML unmarshaling fails
	}
	return resources // Return the unmarshaled resources
}

// NewMetricsAdapter creates a new MetricsAdapter
func NewMetricsAdapter(host string) (*MetricsAdapter, error) {
	req, err := http.NewRequestWithContext(context.Background(), http.MethodGet, host+"/metrics", nil)
	if err != nil {
		return nil, err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer func() { _ = resp.Body.Close() }()
	// 创建一个解析器
	parser := expfmt.TextParser{}
	// 使用解析器解析metrics 数据
	metrics, err := parser.TextToMetricFamilies(resp.Body)
	if err != nil {
		return nil, err
	}
	return &MetricsAdapter{
		Metrics: metrics,
	}, nil
}

// GetResourceMetrics returns the resource metrics by metricsType and labels
func (m *MetricsAdapter) GetResourceMetrics(metricsType string, labels []string) int {
	resourceEventTriggeredCountMetric := m.Metrics[metricsType]
	if resourceEventTriggeredCountMetric == nil {
		return 0
	}
	for _, metric := range resourceEventTriggeredCountMetric.Metric {
		if len(labels) != len(metric.Label) {
			continue
		}
		marched := true
		for i, lab := range metric.Label {
			if labels[i] != lab.GetValue() {
				marched = false
				break
			}
		}
		if marched {
			return int(metric.Counter.GetValue())
		}
	}
	return 0
}

// GetResourceEventTriggeredCountMetric ResourceEventTriggeredCountMetric returns the resource event triggered
// count metric
func (m *MetricsAdapter) GetResourceEventTriggeredCountMetric(gateway, stage, resourceType string) int {
	return m.GetResourceMetrics(ResourceEventTriggeredCountMetric, []string{gateway, stage, resourceType})
}

// GetResourceConvertedCountMetric ResourceConvertedCountMetric returns the resource event triggered count metric
func (m *MetricsAdapter) GetResourceConvertedCountMetric(gateway, stage, resourceType string) int {
	return m.GetResourceMetrics(ResourceConvertedCountMetric, []string{gateway, stage, resourceType})
}

// GetResourceSyncCmpCountMetric ResourceSyncCmpCount returns the resource event triggered count metric
func (m *MetricsAdapter) GetResourceSyncCmpCountMetric(gateway, stage, resourceType string) int {
	return m.GetResourceMetrics(ResourceSyncCmpCount, []string{gateway, stage, resourceType})
}

// GetResourceSyncCmpDiffCountMetric ResourceSyncCmpDiffCount returns the resource event triggered count metric
func (m *MetricsAdapter) GetResourceSyncCmpDiffCountMetric(gateway, stage, resourceType string) int {
	return m.GetResourceMetrics(ResourceSyncCmpDiffCount, []string{gateway, stage, resourceType})
}

// GetApisixOperationCountMetric ApisixOperationCountMetric returns the resource event triggered count metric
func (m *MetricsAdapter) GetApisixOperationCountMetric(action, result, resourceType string) int {
	return m.GetResourceMetrics(ApisixOperationCountMetric, []string{action, result, resourceType})
}
