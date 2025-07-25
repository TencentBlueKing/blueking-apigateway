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

import type { IPosition } from 'monaco-editor';

// 导航栏菜单
export interface IHeaderNav {
  id: number
  name: string
  url: string
  link?: string
  enabled: boolean
}

export interface IMenu {
  name: string
  title: string
  icon?: string
  enabled?: boolean
  children?: IMenu[]
  // 是否在可编程网关中隐藏，默认 false
  hideInProgrammable?: boolean
}

// 分页接口
export interface IPagination {
  // 是否使用小型分页样式
  small?: boolean
  // 数据偏移量
  offset: number
  // 每页显示的数据条数
  limit: number
  // 数据总条数;
  count: number
  // 是否存在异常
  abnormal?: boolean
  // 可选的每页显示条数列表
  limitList?: number[]
  // 当前页码
  current?: number
}

export interface IDropList {
  value: string
  label: string
  disabled?: boolean
}

export interface ISearchSelect {
  id: number
  name: string
  values: {
    id: number
    name: string
  }[]
}

// 对话框接口
export interface IDialog {
  isShow: boolean // 是否显示对话框
  title: string // 对话框标题
  loading?: boolean // 是否显示加载状态
}

// 资源导出
export interface IExportDialog extends IDialog {
  [x: string]: any
  exportFileDocType: string
}

export interface IExportParams {
  export_type?: string
  query?: string
  method?: string
  label_name?: string
  file_type?: string
  resource_ids?: Array<number>
  resource_filter_condition?: any
}

export type ReturnRecordType<T, U> = Record<string, (arg?: T) => U>;

// monaco editor 代码错误高亮要用的类型
export type CodeErrorMsgType = 'All' | 'Error' | 'Warning';

// 错误原因类型
export type ErrorReasonType = {
  json_path?: string // JSON路径，可能为空
  paths?: string[] // 路径数组，可能为空
  pathValue?: any[] // 路径值数组，可能为空
  quotedValue?: string // 引用值，可能为空
  stringToFind?: string // 要查找的字符串，可能为空
  message: string // 错误信息
  isDecorated?: boolean // 是否装饰，可能为空
  level: CodeErrorMsgType // 错误级别
  offset?: number // 偏移量，可能为空
  position?: IPosition | null // 位置，可能为空
  regex?: RegExp | null // 正则表达式，可能为空
};
