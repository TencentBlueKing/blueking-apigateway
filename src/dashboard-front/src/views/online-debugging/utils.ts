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

import type { ITableColumn, TableRowData } from '@/components/base/ag-table';

/**
 * kv 行数组 → 对象：跳过无 name 的行，同名行后者覆盖前者
 * （在线调试发送请求时组装 query/path/headers 参数共用）
 */
export const kvRowsToObject = (
  rows?: Array<{ name: string
    value: any }> | null,
): Record<string, any> => {
  if (!rows?.length) return {};

  const obj: Record<string, any> = {};
  rows.forEach((item) => {
    if (item.name) {
      obj[item.name] = item.value;
    }
  });
  return obj;
};

/**
 * 对象 → kv 行数组
 * （历史记录回填、请求/响应 header 表格展示共用）
 */
export const objectToKvRows = <T = any>(
  obj?: Record<string, T> | null,
): Array<{ name: string
  value: T }> => {
  return Object.keys(obj ?? {}).map(key => ({
    name: key,
    value: (obj as Record<string, T>)[key],
  }));
};

/**
 * 「名称 / 值」两列表格列定义
 * （调用历史请求详情、响应详情的 header 表格共用）
 */
export const createNameValueColumns = <T extends TableRowData = TableRowData>(
  t: (key: string) => string,
): ITableColumn<T>[] => [
  { title: t('名称'),
    colKey: 'name' },
  { title: t('值'),
    colKey: 'value' },
];
