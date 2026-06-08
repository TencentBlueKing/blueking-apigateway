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

import { Message } from 'bkui-vue';
import { t } from '@/locales';
import type { FilterValue } from '@blueking/tdesign-ui';
import type { IDropList } from '@/types/common';
import type { IGatewaysMcpServersPermissionsListQuery } from '@/services/types/query/gateways';
import {
  type IAppPermissionExport,
  type IExportType,
  type IPermissionApprovalFilterValue,
  deleteMcpPermissions,
  exportMcpAppPermissions,
} from '@/services/source/mcp-market.ts';

const exportType = ref<IExportType>('all');
// 导出下拉
const exportDropData = shallowRef<IDropList[]>([
  {
    value: 'all',
    label: t('导出全部'),
    tooltips: '',
    disabled: false,
  },
  {
    value: 'filtered',
    label: t('导出筛选项'),
    tooltips: t('请先选择筛选条件'),
    disabled: true,
  },
]);

// 处理Mcp权限管理和已授权应用公共部分
export function useMcpPermission() {
  // 删除应用
  const handleDelete = async (gatewayId: number, mcpServerId: number, id: number) => {
    await deleteMcpPermissions(gatewayId, mcpServerId, id);
    Message({
      theme: 'success',
      message: t('删除成功'),
    });
  };

  // 导出应用
  const handleExport = async (
    gatewayId: number,
    exportData: IDropList,
    filterData: Ref<FilterValue | IPermissionApprovalFilterValue | IGatewaysMcpServersPermissionsListQuery>,
  ) => {
    try {
      const params: IAppPermissionExport = {
        ...filterData.value,
        export_type: exportData.value as IExportType,
      };
      exportType.value = params.export_type;
      await exportMcpAppPermissions(gatewayId, params);
      Message({
        message: t('导出成功'),
        theme: 'success',
      });
    }
    finally {
      exportType.value = 'all';
    }
  };

  // 是否存在筛选项
  const getExportDropData = (fields: string[], filterData: FilterValue | Record<string, string>) => {
    // 只检查指定的筛选字段
    const filterParamKeys = fields;

    // 判断这些字段里 是否存在 非空值
    const isExistFilter = filterParamKeys.some((key) => {
      return Boolean(filterData.value[key]);
    });

    // 更新导出下拉选项状态
    exportDropData.value = exportDropData.value.map((item) => {
      if (item.value === 'filtered') {
        return {
          ...item,
          disabled: !isExistFilter,
          tooltips: isExistFilter ? '' : t('请先选择筛选条件'),
        };
      }
      return item;
    });
  };

  return {
    exportType,
    exportDropData,
    getExportDropData,
    handleDelete,
    handleExport,
  };
}
