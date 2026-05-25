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

// Package constant ...
package constant

type EventName string

const (
	// dashboard
	EventNameGenerateTask            EventName = "generate_release_task"
	EventNameDistributeConfiguration EventName = "distribute_configuration"

	// operator
	EventNameParseConfiguration EventName = "parse_configuration"
	EventNameApplyConfiguration EventName = "apply_configuration"

	// apisix
	EventNameLoadConfiguration EventName = "load_configuration"
)

const (
	// special event not need resport
	NoNeedReportPublishID = "-1"

	// 删除网关事件
	DeletePublishID = "-2"
)

type EventStatus string

const (
	EventStatusSuccess EventStatus = "success" // 执行成功
	EventStatusFailure EventStatus = "failure" // 执行失败
	EventStatusPending EventStatus = "pending" // 待执行
	EventStatusDoing   EventStatus = "doing"   // 执行中
)

const EventDuplicatedErrMsg = "duplicated"
