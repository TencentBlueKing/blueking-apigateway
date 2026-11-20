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

import type {
  IResourceVersionDiffResource,
  ResourceVersionDiff,
} from '@/services/types/gateway/resource-version';
import type { IDiffData } from '@/types/resource-version';

interface IResourceDiffFilters {
  keyword: string
  diffType: string
  hideOnlyDiffInDocUpdatedTime: boolean
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

/** 合并两侧差异字段，不按值的真假判断；文档增删时两侧语言键可能不对称。 */
export const createDiffIndex = (
  current: ResourceVersionDiff | null | undefined,
  other: ResourceVersionDiff | null | undefined,
): Set<string> => {
  const paths = new Set<string>();
  const pending = [current, other].filter(isRecord).map(value => ({
    value,
    path: '',
  }));

  while (pending.length) {
    const entry = pending.pop()!;
    for (const [key, value] of Object.entries(entry.value)) {
      const path = entry.path ? `${entry.path}.${key}` : key;
      // 同时记录父字段和完整路径，模板直接查找，避免前缀相似的字段互相影响。
      paths.add(path);
      if (isRecord(value)) {
        pending.push({
          value,
          path,
        });
      }
      // 数组是一个配置字段；空数组、空对象也必须保留其字段差异。
    }
  }
  return paths;
};

/** 后端以插件 type 为键：两侧都包含表示更新，仅当前侧包含表示该侧新增或删除。 */
export const getPluginDiffClass = (
  type: string,
  current: ResourceVersionDiff | null | undefined,
  other: ResourceVersionDiff | null | undefined,
  isSource: boolean,
): string => {
  if (!isRecord(current?.plugins) || !Object.hasOwn(current.plugins, type)) {
    return 'no-diff';
  }
  if (isRecord(other?.plugins) && Object.hasOwn(other.plugins, type)) {
    return 'item-updated';
  }
  return isSource ? 'item-deleted' : 'item-added';
};

export const hasOnlyDocTimeDiff = (
  source: ResourceVersionDiff | null | undefined,
  target: ResourceVersionDiff | null | undefined,
): boolean => {
  const fields = new Set([...Object.keys(source ?? {}), ...Object.keys(target ?? {})]);
  return fields.size === 1 && fields.has('doc_updated_time');
};

// 后端比较接口返回配置对象，兼容旧快照使用 JSON 字符串的展示路径。
const parseConfig = <T extends object>(config: string | T | undefined): T =>
  typeof config === 'string' ? JSON.parse(config) : config ?? {} as T;

/** 只生成展示数据，后端名称随列表更新重新计算，不写入接口返回的 diff。 */
export const normalizeResource = (
  resource: IResourceVersionDiffResource | null,
  backends: { id: number
    name: string }[],
) => ({
  ...resource,
  contexts: {
    ...resource?.contexts,
    resource_auth: {
      ...resource?.contexts?.resource_auth,
      config: parseConfig(resource?.contexts?.resource_auth?.config),
    },
  },
  proxy: {
    ...resource?.proxy,
    config: parseConfig(resource?.proxy?.config),
    backend_name: backends.find(backend => backend.id === resource?.proxy?.backend_id)?.name ?? '',
  },
  doc_updated_time: resource?.doc_updated_time ?? {},
  plugins: resource?.plugins ?? [],
});

export const matchesResourceKeyword = (resource: IResourceVersionDiffResource, keyword: string): boolean => {
  const backendPath = parseConfig(resource.proxy?.config).path;
  return [resource.method, resource.path, resource.name, backendPath]
    .some(value => typeof value === 'string' && value.toLowerCase().includes(keyword.toLowerCase()));
};

/** 更新资源任意一侧匹配即可显示；文档过滤只作用于更新，不影响新增和删除。 */
export const filterDiffData = (data: IDiffData, filters: IResourceDiffFilters): IDiffData => {
  const matchesType = (type: keyof IDiffData) => !filters.diffType || filters.diffType === type;
  return {
    add: data.add.filter(item => matchesType('add') && matchesResourceKeyword(item, filters.keyword)),
    delete: data.delete.filter(item => matchesType('delete') && matchesResourceKeyword(item, filters.keyword)),
    update: data.update.filter(item =>
      matchesType('update')
      && (!filters.hideOnlyDiffInDocUpdatedTime || !hasOnlyDocTimeDiff(item.source.diff, item.target.diff))
      && (matchesResourceKeyword(item.source, filters.keyword)
        || matchesResourceKeyword(item.target, filters.keyword))),
  };
};
