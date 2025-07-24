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

const path = '/esb/doc-categories/';

export interface ICategoryItem {
  id?: number
  name: string
  priority: number
  is_official: boolean
  updated_time: string
  system_count: number
}
/**
 *  获取文档列表
 */
export function getDocCategory() {
  return http.get(`${path}`);
}

/**
 *  获取某个文档详情
 * @param id 文档id
 */
export function getDocCategoryDetail(id: number) {
  return http.get(`${path}${id}/`);
}

/**
 *  新建文档
 * @param params 新建数据
 */
export function addDocCategory(params: ICategoryItem) {
  return http.post(`${path}`, params);
}

/**
 *  更新文档
 * @param id 文档id
 * @param params 更新数据
 */
export function updateDocCategory(id: number, params: ICategoryItem) {
  return http.put(`${path}${id}/`, params);
}

/**
 *  删除文档
 * @param id 文档id
 */
export function deleteDocCategory(id: number) {
  return http.delete(`${path}${id}/`);
}
