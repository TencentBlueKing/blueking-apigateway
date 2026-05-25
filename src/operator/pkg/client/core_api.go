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

// Package client ...
package client

import (
	"context"
	"net/http"
	"sync"

	"gopkg.in/h2non/gentleman.v2"
	"gopkg.in/h2non/gentleman.v2/plugins/body"
	"gopkg.in/h2non/gentleman.v2/plugins/url"

	"operator/pkg/config"
)

const (
	reportPublishEventURL = "/api/v1/micro-gateway/:micro_gateway_instance_id/release/:publish_id/events/"
)

var coreAPIClient *CoreAPIClient

var coreOnce sync.Once

// CoreAPIClient core api client
type CoreAPIClient struct {
	baseClient
	microGatewayInstanceID string
}

// InitCoreAPIClient init core api client
func InitCoreAPIClient(cfg *config.Config) {
	coreOnce.Do(func() {
		coreAPIClient = newCoreAPIClient(cfg.EventReporter.CoreAPIHost, cfg.Auth.ID, cfg.Auth.Secret)
	})
}

// GetCoreAPIClient get core api client
func GetCoreAPIClient() *CoreAPIClient {
	return coreAPIClient
}

// NewCoreAPIClient New core_api client with instance_id and instance_secret
func newCoreAPIClient(host, instanceID, instanceSecret string) *CoreAPIClient {
	cli := gentleman.New()
	cli.URL(host)

	// set instance
	cli.SetHeader("X-Bk-Micro-Gateway-Instance-Id", instanceID)
	cli.SetHeader("X-Bk-Micro-Gateway-Instance-Secret", instanceSecret)

	return &CoreAPIClient{
		baseClient: baseClient{
			client: cli,
		},
		microGatewayInstanceID: instanceID,
	}
}

// ReportPublishEvent report event to core_api
func (c *CoreAPIClient) ReportPublishEvent(ctx context.Context, req *ReportEventReq) error {
	request := c.client.Request()
	request.Path(reportPublishEventURL)
	request.Method(http.MethodPost)
	request.Use(url.Param("micro_gateway_instance_id", coreAPIClient.microGatewayInstanceID))
	request.Use(url.Param("publish_id", req.PublishID))
	request.Use(body.JSON(req))
	return c.doHttpRequest(request, sendAndDecodeResp(nil))
}
