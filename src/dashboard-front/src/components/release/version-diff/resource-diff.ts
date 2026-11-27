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
import type { IAuthConfig } from '@/types/resource';
import type { IDiffData } from '@/types/resource-version';
import {
  canAllowApplyPermission,
  isResourcePermEffective,
  parseResourceAuthConfig,
} from '@/utils/auth-config';

/** 资源版本差异分类 */
export type ResourceDiffType = keyof IDiffData;

/** 详情区插件卡片的差异样式类名 */
export type PluginDiffClass = 'item-added' | 'item-deleted' | 'item-updated' | 'no-diff';

/** 后端服务名称映射所需的最小结构 */
export interface IBackendOption {
  id: number
  name: string
}

/** 资源版本对比列表的筛选条件 */
export interface IResourceDiffFilters {
  keyword: string
  diffType: ResourceDiffType | ''
  hideOnlyDiffInDocUpdatedTime: boolean
}

/**
 * 详情区「后端配置」实际渲染的差异字段路径。
 * 显式限定在可展示字段内，避免未渲染字段（如 proxy.config.upstreams / transform_headers）
 * 变化时在「仅显示有差异的资源属性」模式下产生无内容的空标题分组。
 */
const PROXY_DISPLAY_DIFF_PATHS = [
  'proxy.type',
  'proxy.backend_id',
  'proxy.config.method',
  'proxy.config.timeout',
  'proxy.config.path',
  'proxy.config.code',
  'proxy.config.body',
  'proxy.config.headers',
] as const;

/** 判断值是否为非 null、非数组的普通对象 */
const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

/**
 * 安全解析代理配置对象（兼容历史快照使用 JSON 字符串的场景）。
 * 空值、空字符串或非法 JSON 均返回 null，避免单条异常快照中断整个 diff 列表渲染。
 */
const parseJsonConfig = <T extends Record<string, any>>(
  config: string | T | null | undefined,
): T | null => {
  if (!config) {
    return null;
  }
  if (typeof config !== 'string') {
    return isPlainObject(config) ? config : null;
  }
  try {
    const parsed = JSON.parse(config);
    return isPlainObject(parsed) ? parsed as T : null;
  }
  catch {
    return null;
  }
};

/**
 * 合并源/目标两侧的差异对象并构建点分路径索引。
 *
 * - 合并两侧：文档或代理类型变更时，两侧差异键可能不对称，合并后两边均可稳定高亮。
 * - 不按值真假过滤：`false`、`0`、`""`、`null`、`[]`、`{}` 均代表真实字段差异。
 * - 同时记录父字段与叶子路径：供模板使用 `Set.has` 精确查找，避免前缀相似字段误匹配。
 */
export const createDiffIndex = (
  currentDiff: ResourceVersionDiff | null | undefined,
  otherDiff: ResourceVersionDiff | null | undefined,
): Set<string> => {
  const diffPaths = new Set<string>();
  const stack = [currentDiff, otherDiff]
    .filter(isPlainObject)
    .map(node => ({
      node,
      prefix: '',
    }));

  while (stack.length > 0) {
    const { node, prefix } = stack.pop()!;
    for (const [key, value] of Object.entries(node)) {
      const path = prefix ? `${prefix}.${key}` : key;
      diffPaths.add(path);
      // 仅展开嵌套对象；数组作为整体配置字段保留当前路径即可
      if (isPlainObject(value)) {
        stack.push({
          node: value,
          prefix: path,
        });
      }
    }
  }

  return diffPaths;
};

/** 判断「后端配置」分组中是否有任一可见展示字段发生变化 */
export const hasProxyDisplayDiff = (diffIndex: ReadonlySet<string>): boolean =>
  PROXY_DISPLAY_DIFF_PATHS.some(path => diffIndex.has(path));

/**
 * 计算单个插件在当前侧的差异状态样式。
 * 后端 `diff.plugins` 以插件 `type` 为键：两侧均存在表示配置更新，仅当前侧存在表示删除（源侧）或新增（目标侧）。
 */
export const getPluginDiffClass = (
  pluginType: string,
  currentDiff: ResourceVersionDiff | null | undefined,
  otherDiff: ResourceVersionDiff | null | undefined,
  isSource: boolean,
): PluginDiffClass => {
  if (!isPlainObject(currentDiff?.plugins) || !Object.hasOwn(currentDiff.plugins, pluginType)) {
    return 'no-diff';
  }
  if (isPlainObject(otherDiff?.plugins) && Object.hasOwn(otherDiff.plugins, pluginType)) {
    return 'item-updated';
  }
  return isSource ? 'item-deleted' : 'item-added';
};

/**
 * 判断资源变更是否「仅包含文档更新时间变化」。
 * 需要合并源/目标两侧的差异键集合，避免某一侧缺失该键或另一侧存在额外变更时误判。
 */
export const hasOnlyDocTimeDiff = (
  sourceDiff: ResourceVersionDiff | null | undefined,
  targetDiff: ResourceVersionDiff | null | undefined,
): boolean => {
  const changedFields = new Set([
    ...Object.keys(sourceDiff ?? {}),
    ...Object.keys(targetDiff ?? {}),
  ]);
  return changedFields.size === 1 && changedFields.has('doc_updated_time');
};

/**
 * 将资源快照归一化为只读展示结构，不修改接口返回的原始对象。
 * - `contexts.resource_auth.config` 原样透传，统一由 `parseResourceAuthConfig` 解析，避免维护两套解析逻辑。
 * - `proxy.config` 始终归一化为对象，确保模板访问代理子字段安全。
 * - `proxy.backend_name` 随 `backends` 列表动态映射，不受接口返回顺序影响。
 */
export const normalizeResource = (
  resource: IResourceVersionDiffResource | null,
  backends: IBackendOption[],
) => {
  const proxyConfig = parseJsonConfig<Record<string, any>>(resource?.proxy?.config) ?? {};
  const backendName = backends.find(backend => backend.id === resource?.proxy?.backend_id)?.name ?? '';

  return {
    ...resource,
    proxy: {
      ...resource?.proxy,
      config: proxyConfig,
      backend_name: backendName,
    },
    doc_updated_time: resource?.doc_updated_time ?? {},
    plugins: resource?.plugins ?? [],
  };
};

/** 按关键词（不区分大小写）匹配资源的请求方法、路径、名称或后端请求路径 */
export const matchesResourceKeyword = (
  resource: IResourceVersionDiffResource,
  keyword: string,
): boolean => {
  if (!keyword) {
    return true;
  }
  const lowerKeyword = keyword.toLowerCase();
  const backendPath = parseJsonConfig<Record<string, any>>(resource.proxy?.config)?.path;

  return [resource.method, resource.path, resource.name, backendPath]
    .some(value => typeof value === 'string' && value.toLowerCase().includes(lowerKeyword));
};

/**
 * 基于后端 `diff.py` 局部差异协议，使用「当前侧完整认证配置 + 对侧局部差异」对称还原对侧认证配置。
 */
const reconstructOtherSideAuth = (
  currentAuth: Partial<IAuthConfig> | null,
  otherSideDiff: ResourceVersionDiff,
): Partial<IAuthConfig> | null => {
  const otherAuthDiff = parseResourceAuthConfig(otherSideDiff.contexts?.resource_auth?.config);
  return currentAuth
    ? {
      ...currentAuth,
      ...otherAuthDiff,
    }
    : otherAuthDiff;
};

/**
 * 判断「校验应用权限」的实际生效展示值在源/目标两侧是否存在差异。
 *
 * 复用后端 `diff.py` 的局部差异协议还原对侧配置并比较 `isResourcePermEffective`：
 * 避免双方均关闭应用认证时，历史快照残留的原始 `resource_perm_required` 变化导致两侧均显示「否」却误报高亮，
 * 也避免仅变更 `app_verified_required` 导致生效值变化时漏报高亮。
 */
export const hasEffectiveResourcePermDiff = (
  resource: Pick<IResourceVersionDiffResource, 'contexts'> | null | undefined,
  otherSideDiff: ResourceVersionDiff | null | undefined,
): boolean => {
  if (!resource || !otherSideDiff) {
    return false;
  }

  const currentAuth = parseResourceAuthConfig(resource.contexts?.resource_auth?.config);
  const otherAuth = reconstructOtherSideAuth(currentAuth, otherSideDiff);
  return isResourcePermEffective(currentAuth) !== isResourcePermEffective(otherAuth);
};

/**
 * 判断「允许申请权限」的实际生效展示值在源/目标两侧是否存在差异。
 *
 * 依赖后端 `diff.py` 的局部差异协议：`otherSideDiff`（含 `contexts.resource_auth.config`）
 * 仅包含两侧发生变化的字段，未出现的字段表示与当前侧一致，因此可通过「当前侧完整配置 + 对侧局部差异」
 * 对称还原对侧的生效结果；仅当两侧有效结果不一致时返回 true，避免不公开或未开应用权限校验时误报高亮。
 */
export const hasEffectiveAllowApplyDiff = (
  resource: Pick<IResourceVersionDiffResource, 'is_public' | 'allow_apply_permission' | 'contexts'> | null | undefined,
  otherSideDiff: ResourceVersionDiff | null | undefined,
): boolean => {
  if (!resource || !otherSideDiff) {
    return false;
  }

  const currentAuth = parseResourceAuthConfig(resource.contexts?.resource_auth?.config);
  const currentEffective = canAllowApplyPermission(Boolean(resource.is_public), currentAuth)
    && Boolean(resource.allow_apply_permission);

  const otherIsPublic = 'is_public' in otherSideDiff
    ? Boolean(otherSideDiff.is_public)
    : Boolean(resource.is_public);
  const otherAllowApply = 'allow_apply_permission' in otherSideDiff
    ? Boolean(otherSideDiff.allow_apply_permission)
    : Boolean(resource.allow_apply_permission);
  const otherAuth = reconstructOtherSideAuth(currentAuth, otherSideDiff);
  const otherEffective = canAllowApplyPermission(otherIsPublic, otherAuth) && otherAllowApply;

  return currentEffective !== otherEffective;
};

/**
 * 按筛选条件过滤新增、删除与更新三类资源列表，并保留原条目对象引用以维持展开状态。
 * 更新资源只要源侧或目标侧任一命中关键词即保留；「隐藏仅文档更新」仅作用于更新列表。
 */
export const filterDiffData = (
  data: IDiffData,
  filters: IResourceDiffFilters,
): IDiffData => {
  const matchesDiffType = (type: ResourceDiffType) => !filters.diffType || filters.diffType === type;

  return {
    add: data.add.filter(item =>
      matchesDiffType('add') && matchesResourceKeyword(item, filters.keyword)),
    delete: data.delete.filter(item =>
      matchesDiffType('delete') && matchesResourceKeyword(item, filters.keyword)),
    update: data.update.filter(item =>
      matchesDiffType('update')
      && (!filters.hideOnlyDiffInDocUpdatedTime || !hasOnlyDocTimeDiff(item.source.diff, item.target.diff))
      && (matchesResourceKeyword(item.source, filters.keyword)
        || matchesResourceKeyword(item.target, filters.keyword))),
  };
};
