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

/*
* MCP 市场相关类型
*  */

import type { IMCPServerCategory } from '@/types/mcp-server';

export interface IMarketplaceItem {
  id: number
  name: string
  description: string
  is_public: boolean
  is_official: boolean
  is_featured: boolean
  labels: string[]
  resource_names: string[]
  tool_names: string[]
  status: number
  tools_count: number
  prompts_count: number
  url: string
  protocol_type: string
  stage: {
    id: number
    name: string
  }
  gateway: {
    id: number
    name: string
    is_official: boolean
  }
}

// MCP 市场分类（在 MCP Server 分类的基础上增加市场展示所需字段）
export interface IMCPMarketCategory extends IMCPServerCategory {
  mcp_server_count?: number
  isOverflow?: boolean
}

//  UI 扩展类型
export type IMarketplaceItemWithUIState = IMarketplaceItem & { is_checked?: boolean };
