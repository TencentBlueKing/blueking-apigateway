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

// Package validator provides validation functionality for API Gateway resources.
package validator

import (
	"fmt"

	"operator/pkg/constant"
	"operator/pkg/utils"
	"operator/pkg/utils/schema"
)

// ValidateApisixJsonSchema validates the APISIX configuration against the JSON schema.
func ValidateApisixJsonSchema(version string, resourceType constant.APISIXResource, config []byte) error {
	// 校验资源配置
	apisixVersion, err := utils.ToXVersion(version)
	if err != nil {
		return fmt.Errorf("to x version failed, err: %w", err)
	}
	validator, err := schema.NewAPISIXJsonSchemaValidator(
		apisixVersion,
		resourceType,
		"main."+resourceType.String(),
	)
	if err != nil {
		return err
	}
	err = validator.Validate(config)
	if err != nil {
		return fmt.Errorf("validate apisix json schema failed, err: %w", err)
	}
	return nil
}
