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

import {
  type IMCPAIConfig,
  type IMCPServerWithUIState,
} from '@/services/source/mcp-server.ts';
import type { IMarketplaceItemWithUIState } from '@/services/source/mcp-market.ts';
import type { IMcpClientConfig } from '@/services/types/responses/mcp-marketplace.ts';

// 客户端类型枚举
export const CLIENT_TYPE_ENUMS = ['codebuddy', 'cursor', 'claude', 'vscode'] as const;

type ClientType = typeof CLIENT_TYPE_ENUMS[number];

// 通用的MCP Server行数据类型（兼容列表和市场两种场景）
type IMCPServerItem = IMCPServerWithUIState & IMarketplaceItemWithUIState;

type IMcpBatchConfigQuery = {
  client_type: string
  mcp_server_ids: number[]
};

// 定义动态接口函数类型
type FetchConfigFunc = (
  apigwIdOrData?: number | IMcpBatchConfigQuery,
  data?: IMcpBatchConfigQuery
) => Promise<IMcpClientConfig>;

/**
 * 动态支持 MCP 列表页 + MCP 市场页 的批量复制配置 Hooks
 * @param fetchApi 动态传入接口函数
 * @param gatewayId 可选（列表页需要传，市场页不传）
 */
export const useMcpBatchCopyConfig = ({
  gatewayId,
  fetchApi,
}: {
  gatewayId?: number
  fetchApi: FetchConfigFunc
}) => {
  // 复制配置加载状态
  const copyConfigLoading = ref(false);
  // 复制配置列表
  const mcpConfigList = ref<IMCPAIConfig[]>([]);

  /**
   * 获取MCP批量复制配置列表
   * @param row 单行数据（单选时传入）
   * @param selections 多选时的选中列表（Map结构）
   */
  const fetchMcpBatchCopyConfigList = async ({
    row,
    selections,
  }: {
    row?: IMCPServerItem
    selections?: Map<number, IMCPServerItem>
  }) => {
    // 复制的MCP Server ID列表
    const mcpServerIds = row
      ? [row.id]
      : selections ? Array.from(selections.keys()) : [];

    if (mcpServerIds.length === 0) {
      mcpConfigList.value = [];
      return;
    }

    copyConfigLoading.value = true;

    // 按客户端类型合并配置
    const configMap = new Map<string, IMCPAIConfig>();

    try {
      // 批量请求不同客户端类型的配置
      const requestList = CLIENT_TYPE_ENUMS.map((clientType: ClientType) => {
        const params: IMcpBatchConfigQuery = {
          mcp_server_ids: mcpServerIds,
          client_type: clientType,
        };

        if (gatewayId) {
          return fetchApi(gatewayId, params);
        }
        else {
          return fetchApi(params);
        }
      });

      const results = await Promise.allSettled(requestList);

      // 过滤成功的请求结果
      const successResults = results
        .filter((item): item is PromiseFulfilledResult<IMcpClientConfig> => item.status === 'fulfilled')
        .map(item => item.value);

      for (const cg of successResults) {
        const { client_type: name, display_name, config = {} } = cg;
        const configWithIndex: { [key: string]: any } = config;
        const rootKey = Object.keys(configWithIndex)[0] || 'servers'; // 自动识别根节点
        const serverMap = configWithIndex[rootKey] || {};
        const mergedServerConfig: Record<string, any> = {};

        // 单选/多选逻辑处理
        if (row) {
          // 单选：仅处理当前行
          const serverKey = row.name;
          if (serverMap[serverKey]) {
            mergedServerConfig[serverKey] = serverMap[serverKey];
          }
        }
        else if (selections) {
          // 多选：合并所有选中项
          Array.from(selections.values()).forEach((st) => {
            const serverKey = st.name;
            if (serverMap[serverKey]) {
              mergedServerConfig[serverKey] = serverMap[serverKey];
            }
          });
        }

        // 格式化配置为JSON代码块
        const fullConfigObj = { [rootKey]: mergedServerConfig };
        const formattedContent = `\`\`\`json\n${JSON.stringify(fullConfigObj, null, 2)}\n\`\`\``;

        configMap.set(name, {
          name,
          display_name,
          install_url: '',
          content: formattedContent,
        });
      }
      mcpConfigList.value = Array.from(configMap.values());
    }
    catch {
      mcpConfigList.value = [];
    }
    finally {
      copyConfigLoading.value = false;
      configMap?.clear();
    }
  };

  return {
    copyConfigLoading,
    mcpConfigList,
    fetchMcpBatchCopyConfigList,
  };
};
