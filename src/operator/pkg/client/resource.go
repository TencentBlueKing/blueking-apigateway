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

// Package client ...
package client

import (
	"errors"
	"fmt"
	"net"
	"net/http"
	"strings"

	gentleman "gopkg.in/h2non/gentleman.v2"
	"gopkg.in/h2non/gentleman.v2/plugins/auth"
	"gopkg.in/h2non/gentleman.v2/plugins/body"

	"operator/pkg/config"
	"operator/pkg/constant"
)

const (
	getLeaderURL                    = "/v1/open/leader/"
	ResourceApigwURL                = "/v1/open/apigw/resources/"
	ResourceApigwCountURL           = "/v1/open/apigw/resources/count/"
	ResourceApigwCurrentVersionURL  = "/v1/open/apigw/resources/current-version/"
	ResourceApisixURL               = "/v1/open/apisix/resources/"
	ResourceApisixCountURL          = "/v1/open/apisix/resources/count/"
	ResourceApisixCurrentVersionURL = "/v1/open/apisix/resources/current-version/"
)

// ResourceClient is a client for the resource API.
type ResourceClient struct {
	baseClient
	Apikey string
}

var (
	serverHost     string
	serverBindPort = 6004
)

// InitResourceClient client
func InitResourceClient(cfg *config.Config) {
	switch {
	case cfg.HttpServer.BindAddress != "":
		serverHost = fmt.Sprintf(
			"http://%s:%d",
			cfg.HttpServer.BindAddress,
			cfg.HttpServer.BindPort,
		)
	case cfg.HttpServer.BindAddressV6 != "":
		serverHost = fmt.Sprintf(
			"http://%s:%d",
			cfg.HttpServer.BindAddressV6,
			cfg.HttpServer.BindPort,
		)
	default:
		serverHost = fmt.Sprintf("http://127.0.0.1:%d", cfg.HttpServer.BindPort)
	}

	serverBindPort = cfg.HttpServer.BindPort
}

// NewResourceClient New resource client with host and apiKey
func NewResourceClient(host, apiKey string) *ResourceClient {
	cli := gentleman.New()
	cli.URL(host)
	// set auth
	cli.Use(auth.Basic(constant.ApiAuthAccount, apiKey))
	return &ResourceClient{
		baseClient: baseClient{
			client: cli,
		},
		Apikey: apiKey,
	}
}

// GetLeaderResourceClient get leader resource client
func GetLeaderResourceClient(apiKey string) (*ResourceClient, error) {
	client := NewResourceClient(serverHost, apiKey)
	leader, err := client.GetLeader()
	if err != nil {
		return nil, err
	}
	leaderHost := GetHostFromLeaderName(leader)
	if leaderHost == "" {
		return nil, errors.New("empty leader host")
	}
	return NewResourceClient(leaderHost, apiKey), nil
}

// GetLeader Resource leader instance
func (r *ResourceClient) GetLeader() (string, error) {
	request := r.client.Request()
	request.Path(getLeaderURL)
	request.Method(http.MethodGet)
	var leader string
	return leader, r.doHttpRequest(request, sendAndDecodeResp(&leader))
}

// ApigwList apigw 资源列表
func (r *ResourceClient) ApigwList(req *ApigwListRequest) (ApigwListInfo, error) {
	request := r.client.Request()
	request.Path(ResourceApigwURL)
	request.Method(http.MethodPost)
	request.Use(body.JSON(req))
	var res ApigwListInfo
	return res, r.doHttpRequest(request, sendAndDecodeResp(&res))
}

// ApigwStageResourceCount apigw 资源数量
func (r *ResourceClient) ApigwStageResourceCount(req *ApigwListRequest) (ApigwListResourceCountResponse, error) {
	request := r.client.Request()
	request.Path(ResourceApigwCountURL)
	request.Method(http.MethodPost)
	request.Use(body.JSON(req))
	var res ApigwListResourceCountResponse
	return res, r.doHttpRequest(request, sendAndDecodeResp(&res))
}

// ApigwStageCurrentVersion apigw 环境发布版本
func (r *ResourceClient) ApigwStageCurrentVersion(
	req *ApigwListRequest,
) (ApigwListCurrentVersionInfoResponse, error) {
	request := r.client.Request()
	request.Path(ResourceApigwCurrentVersionURL)
	request.Method(http.MethodPost)
	request.Use(body.JSON(req))
	var res ApigwListCurrentVersionInfoResponse
	return res, r.doHttpRequest(request, sendAndDecodeResp(&res))
}

// ApisixList apisix 资源列表
func (r *ResourceClient) ApisixList(req *ApisixListRequest) (ApisixListInfo, error) {
	request := r.client.Request()
	request.Path(ResourceApisixURL)
	request.Method(http.MethodPost)
	request.Use(body.JSON(req))
	var res ApisixListInfo
	return res, r.doHttpRequest(request, sendAndDecodeResp(&res))
}

// ApisixStageResourceCount apisix 资源数量
func (r *ResourceClient) ApisixStageResourceCount(req *ApisixListRequest) (ApisixListResourceCountResponse, error) {
	request := r.client.Request()
	request.Path(ResourceApisixCountURL)
	request.Method(http.MethodPost)
	request.Use(body.JSON(req))
	var res ApisixListResourceCountResponse
	return res, r.doHttpRequest(request, sendAndDecodeResp(&res))
}

// ApisixStageCurrentVersion apisix 环境发布版本
func (r *ResourceClient) ApisixStageCurrentVersion(
	req *ApisixListRequest,
) (ApisixListCurrentVersionInfoResponse, error) {
	request := r.client.Request()
	request.Path(ResourceApisixCurrentVersionURL)
	request.Method(http.MethodPost)
	request.Use(body.JSON(req))
	var res ApisixListCurrentVersionInfoResponse
	return res, r.doHttpRequest(request, sendAndDecodeResp(&res))
}

// GetHostFromLeaderName eg: in:somename-ip1,ip2 out: http://ip1:port
func GetHostFromLeaderName(leader string) string {
	// format somename-ip1,ip2,ip3
	splitRes := strings.Split(leader, "_")
	addrAll := splitRes[len(splitRes)-1]
	if len(addrAll) == 0 {
		return ""
	}
	addrList := strings.Split(addrAll, ",")
	if ip := net.ParseIP(addrList[0]); ip == nil {
		return ""
	}
	return fmt.Sprintf("http://%s:%d", addrList[0], serverBindPort)
}
