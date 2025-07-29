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
import http from '../http';

const path = '/docs/esb';

/**
 *  获取组件系统列表
 * @param board
 * @param data 查询参数
 */
export const getComponentSystemList = (board: string, data: any = {}) =>
  http.get(`${path}/boards/${board}/systems/`, data);

/**
 *  获取组件系统信息
 * @param board
 * @param system_name  系统名称
 */
export const getComponenSystemDetail = (board: string, system_name: string) =>
  http.get(`${path}/boards/${board}/systems/${system_name}/`);

/**
 *  查询指定组件系统下的组件 API 列表，仅返回公开的组件
 * @param board
 * @param system_name  系统名称
 */
export const getSystemAPIList = (board: string, system_name: string) =>
  http.get(`${path}/boards/${board}/systems/${system_name}/components/`);

/**
 *  查询组件 API，根据筛选条件模糊搜索，仅返回前 30 条记录
 * @param board
 * @param data 查询参数
 * @param system_name  系统名称
 */
export const searchAPI = (board: string, system_name: string, data: any) =>
  http.get(`${path}/boards/${board}/systems/${system_name}/components/search/`, data);

/**
 *  获取组件 API 文档，仅获取当前语言（中文/英文）的文档
 * @param board
 * @param system_name  系统名称
 * @param component_name   组件名称
 */
export const getSystemComponentDoc = (board: string, system_name: string, component_name: string) =>
  http.get(`${path}/boards/${board}/systems/${system_name}/components/${component_name}/doc/`);

/**
 *  获取指定组件的指定语言（python） SDK 的调用示例
 * @param data
 * @param board   系统名称
 */
export const getSDKDoc = (board: string, data: any) => http.get(`${path}/boards/${board}/sdks/usage-example/`, data);

/**
 *  获取所有的组件 SDK 列表，单个 SDK 仅返回最新版本 SDK 信息
 * @param board
 * @param data 查询参数
 */
export const getESBSDKlist = (board: string, data: any) => http.get(`${path}/boards/${board}/sdks/`, data);

/**
 *  获取指定语言（python）组件 SDK 的调用样例
 * @param board
 * @param data 查询参数
 */
export const getESBSDKDoc = (board: string, data: any) => http.get(`${path}/boards/${board}/sdks/doc/`, data);

/**
 *  获取指定语言（python） 组件 SDK 的信息
 * @param board
 * @param data 查询参数
 */
export const getESBSDKDetail = (board: string, data: any) => http.get(`${path}/boards/${board}/sdks/latest/`, data);
