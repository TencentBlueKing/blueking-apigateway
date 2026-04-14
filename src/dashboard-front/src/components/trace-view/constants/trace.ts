/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import type { ITraceLog } from '@/services/source/observability';

export const DEFAULT_TRACE_DATA: ITraceLog = {
  app_code: '',
  client_ip: '',
  tool_name: '',
  request_id: '',
  x_request_id: '',
  status: '',
  mcp_method: '',
  mcp_server_name: '',
  logList: [],
  spans: [],
  span_count: 0,
  service_count: 0,
  timestamp: 0,
  total_latency_ms: 0,
  error: '',
  upstream_gateway_log: null,
  downstream_gateway_log: null,
  services: [],
};
