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
	"encoding/json"
	"fmt"

	"gopkg.in/h2non/gentleman.v2"

	"operator/pkg/logging"
	"operator/pkg/utils"
)

type baseClient struct {
	client *gentleman.Client
}

// RequestOption http option
type RequestOption func(request *gentleman.Request) error

// DoHttpRequest do http request with opt
func (c *baseClient) doHttpRequest(request *gentleman.Request, options ...RequestOption) error {
	for _, opt := range options {
		err := opt(request)
		if err != nil {
			return err
		}
	}
	return nil
}

// sendAndDecodeResp do http request and decode resp
func sendAndDecodeResp(result any) RequestOption {
	return func(request *gentleman.Request) error {
		var resp *gentleman.Response
		var err error
		defer func() {
			if err != nil {
				logging.GetLogger().Errorf("do http request fail: %+v", err)
			}
		}()

		// send request
		resp, err = request.Send()
		if err != nil {
			return fmt.Errorf("send http fail: %w", err)
		}
		defer func() {
			_ = resp.Close()
		}()

		// decode common resp
		var res utils.CommonResp
		err = json.Unmarshal(resp.Bytes(), &res)
		if err != nil {
			return fmt.Errorf("unmarshal http resp err: %w", err)
		}
		if res.Error.Code != "" {
			return fmt.Errorf("code: %s,msg: %s", res.Error.Code, res.Error.Message)
		}

		// decode resp
		if result != nil {
			var resultByte []byte
			resultByte, err = json.Marshal(res.Data)
			if err != nil {
				return fmt.Errorf("marshal http result data err: %w", err)
			}
			return json.Unmarshal(resultByte, &result)
		}
		return nil
	}
}
