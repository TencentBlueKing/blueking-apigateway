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
 * 对元素为对象的数组进行简单排序
 */
export function sortByKey(list: any[] = [], key: string | number) {
  const results: any[] = [];
  let sortKeys = list.map((item: any) => {
    return item[key].toLowerCase();
  });
  sortKeys = [...new Set(sortKeys)];
  sortKeys.sort();
  sortKeys.forEach((sortItem: Record<string, string | number>) => {
    list.forEach((item: Record<string, any>) => {
      if (item[key]?.toLowerCase() === sortItem) {
        results.push(item);
      }
    });
  });
  return results;
}
