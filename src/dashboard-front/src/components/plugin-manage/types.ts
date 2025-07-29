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

/**
 * 插件接口，定义了插件的基本结构
 * @template T 插件配置的类型
 */
interface IPlugin<T> {
  code?: string // 插件代码，可选
  type?: string // 插件类型，可选
  name: string // 插件名称
  config: T // 插件配置
  config_id: number // 插件配置ID
}

/**
 * 表格列接口，定义了表格列的基本结构
 * @template T 表格行的类型，默认为IBaseTableRow
 */
interface IColumn<T = IBaseTableRow> {
  label: string // 列标签
  field?: string // 列字段，可选
  prop?: string // 列属性，可选
  width?: string // 列宽度，可选
  align?: string // 列对齐方式，可选
  rowspan?: ({ row }: { row: T }) => number // 行跨度函数，可选
  index?: number // 列索引，可选
  render?: ValueRenderType // 渲染函数，可选
}

/**
 * 基础表格行接口，定义了表格行的基本结构
 */
interface IBaseTableRow {
  key?: string // 行键值，可选
  value?: unknown // 行值，可选
  rowSpan?: number // 行跨度，可选
}

/**
 * 值渲染类型，定义了一个函数类型，该函数返回一个渲染函数
 * @template T 表格行的类型，默认为IBaseTableRow
 */
type ValueRenderType<T = IBaseTableRow> = (props: { row: T }) => unknown;

export type {
  IPlugin,
  IColumn,
  IBaseTableRow,
  ValueRenderType,
};
