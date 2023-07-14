/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

package constant

const (
	// dashboard
	EventNameGenerateReleaseTask     = "generate_release_task"
	EventNameDistributeConfiguration = "distribute_configuration"

	// operator
	EventNameParseConfiguration = "parse_configuration"
	EventNameApplyConfiguration = "apply_configuration"

	// apisix
	EventNameLoadConfiguration = "load_configuration"
)

func GetStep(name string) int {
	/**
	publish event report chain:
	GenerateTask-> DistributeConfiguration-> ParseConfiguration-> ApplyConfiguration-> LoadConfiguration
	*/
	switch name {
	case EventNameGenerateReleaseTask:
		return 1
	case EventNameDistributeConfiguration:
		return 2
	case EventNameParseConfiguration:
		return 3
	case EventNameApplyConfiguration:
		return 4
	case EventNameLoadConfiguration:
		return 5
	}
	return 0
}

const (
	EventStatusSuccess = "success" // 执行成功
	EventStatusFailure = "failure" // 执行失败
	EventStatusPending = "pending" // 待执行
	EventStatusDoing   = "doing"   // 执行中
)
