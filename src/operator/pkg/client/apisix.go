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

// Package client  ...
package client

import (
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	json "github.com/json-iterator/go"
	"github.com/spf13/cast"
	"gopkg.in/eapache/go-resiliency.v1/retrier"
	"gopkg.in/h2non/gentleman.v2"
	"gopkg.in/h2non/gentleman.v2/plugins/transport"
	"gopkg.in/h2non/gentleman.v2/plugins/url"

	"operator/pkg/config"
	"operator/pkg/logging"
	"operator/pkg/utils"
)

const (
	getPublishVersionURL = "/api/:gateway/:stage/__apigw_version"
)

var apisixClient *ApisixClient

var apisxiOnce sync.Once

// ApisixClient is client for apisix
type ApisixClient struct {
	baseClient
	// apisix版本探测次数
	versionProbeCount int
	// apisix版本探测间隔
	versionProbeInterval time.Duration
}

// InitApisixClient init apisix cli
func InitApisixClient(cfg *config.Config) {
	apisxiOnce.Do(func() {
		cli := gentleman.New()
		// disable keep alive
		tr := gentleman.NewDefaultTransport(gentleman.DefaultDialer)
		tr.DisableKeepAlives = true
		cli.Use(transport.Set(tr))

		cli.URL(cfg.EventReporter.ApisixHost)
		apisixClient = &ApisixClient{
			baseClient:           baseClient{client: cli},
			versionProbeCount:    cfg.EventReporter.VersionProbe.Retry.Count,
			versionProbeInterval: cfg.EventReporter.VersionProbe.Retry.Interval,
		}
	})
}

// GetApisixClient get apisix client
func GetApisixClient() *ApisixClient {
	return apisixClient
}

// GetReleaseVersion get apisix release info
func (a *ApisixClient) GetReleaseVersion(gatewayName, stageName string,
	publishID string,
) (*VersionRouteResp, error) {
	retryStrategy := retrier.New(retrier.ConstantBackoff(
		a.versionProbeCount, a.versionProbeInterval), nil)
	var resp VersionRouteResp
	err := retryStrategy.Run(func() error {
		request := a.newReleaseVersionRequest(gatewayName, stageName)
		httpResp, sendErr := request.Send()
		if sendErr != nil {
			if httpResp != nil {
				_ = httpResp.Close()
			}
			return sendErr
		}

		return evaluateReleaseVersionResponse(
			gatewayName,
			stageName,
			cast.ToInt64(publishID),
			&resp,
			httpResp.RawResponse,
		)
	})
	if err != nil {
		return &resp, err
	}

	return &resp, nil
}

func (a *ApisixClient) newReleaseVersionRequest(gatewayName, stageName string) *gentleman.Request {
	request := a.client.Request()
	request.Path(getPublishVersionURL)
	request.Method(http.MethodGet)
	request.Use(url.Param("gateway", gatewayName))
	request.Use(url.Param("stage", stageName))

	// set X-Forwarded-For avoid apisix real-ip plugin logs get error: missing real address
	request.SetHeader("X-Forwarded-For", utils.GetLocalIP())

	return request
}

func evaluateReleaseVersionResponse(gateway, stage string, publishID int64, resp *VersionRouteResp,
	res *http.Response,
) error {
	// The http Client and Transport guarantee that Body is always non-nil
	// So this has to be closed or there could be a coroutine leak
	defer func() {
		_ = res.Body.Close()
	}()

	if res.StatusCode >= http.StatusInternalServerError || res.StatusCode == http.StatusTooManyRequests {
		err := fmt.Errorf(
			"configuration [gateway: %s,stage: %s] version route server error: status_code=%d",
			gateway,
			stage,
			res.StatusCode,
		)
		logging.GetLogger().Info(err)
		return err
	}
	// 虚拟路由不存在,继续重试
	if res.StatusCode == http.StatusNotFound {
		err := fmt.Errorf(
			"configuration [gateway: %s,stage: %s] version route not found", gateway, stage)
		logging.GetLogger().Info(err)
		return err
	}
	if res.StatusCode == http.StatusOK {
		// 解析返回结果
		result, readErr := io.ReadAll(res.Body)
		if readErr != nil {
			err := fmt.Errorf(
				"read configuration [gateway: %s,state: %s] version route body err: %w",
				gateway,
				stage,
				readErr,
			)
			logging.GetLogger().Error(err)
			return err
		}
		unmarshalErr := json.Unmarshal(result, resp)
		if unmarshalErr != nil {
			err := fmt.Errorf(
				"unmarshal configuration [gateway: %s,stage: %s] version route body err: %w",
				gateway, stage, unmarshalErr)
			logging.GetLogger().Error(err)
			return err
		}

		// 判断版本号
		if resp.PublishID < publishID {
			// 如果获取到的版本号比当前小，说明当前的版本还未加载完成
			err := fmt.Errorf(
				"configuration [gateway: %s,stage: %s]  [current: %d, expected: %d] is not latest",
				gateway,
				stage,
				resp.PublishID,
				publishID,
			)
			logging.GetLogger().Info(err)
			return err
		}

		// 如果发布的版本号比当前大，说明已经覆盖加载完成
		if resp.PublishID >= publishID {
			return nil
		}
	}

	return nil
}
