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

import type { BkUiSettings } from '@blueking/tdesign-ui';
import type { TableRowSize } from '../types';

const TABLE_PREFERENCE_PREFIX = 'table-settings-';
const LEGACY_TABLE_PREFERENCE_PREFIX = 'table-setting-';
const TABLE_PREFERENCE_BUILD_ID_KEY = 'table-settings:__build_id__';

export type TablePreferences = Pick<BkUiSettings, 'checked' | 'fontSize' | 'rowSize'>;

export interface ITablePreferenceKeys {
  identifier?: string
  storageKey?: string
  legacyRowSizeKey?: string
}

export function getTablePreferenceKeys(
  enabled: boolean,
  cacheIdentifier?: string,
  className?: string,
): ITablePreferenceKeys {
  const identifier = cacheIdentifier?.trim() || undefined;
  const legacyClassName = className?.trim() || undefined;
  if (!enabled) return { identifier };

  return {
    identifier,
    storageKey: identifier ? `${TABLE_PREFERENCE_PREFIX}${identifier}` : undefined,
    legacyRowSizeKey: legacyClassName && legacyClassName !== identifier
      ? `${TABLE_PREFERENCE_PREFIX}${legacyClassName}`
      : undefined,
  };
}

/**
 * 每次新构建首次启动时清空旧的表格偏好缓存；仅清理表格设置前缀键，不触碰其他本地存储。
 */
export function pruneTablePreferences(buildId: string): boolean {
  const normalizedBuildId = buildId.trim();
  if (!normalizedBuildId) return false;
  try {
    if (localStorage.getItem(TABLE_PREFERENCE_BUILD_ID_KEY) === normalizedBuildId) return false;
    const staleKeys: string[] = [];
    for (let index = 0; index < localStorage.length; index++) {
      const key = localStorage.key(index);
      if (!key) continue;
      if (key.startsWith(TABLE_PREFERENCE_PREFIX) || key.startsWith(LEGACY_TABLE_PREFERENCE_PREFIX)) {
        staleKeys.push(key);
      }
    }
    staleKeys.forEach(key => localStorage.removeItem(key));
    localStorage.setItem(TABLE_PREFERENCE_BUILD_ID_KEY, normalizedBuildId);
    return true;
  }
  catch {
    // 浏览器禁用存储或配额受限时静默跳过，避免阻塞应用启动。
    return false;
  }
}

export const isTableRowSize = (size: unknown): size is TableRowSize =>
  size === 'mini' || size === 'small' || size === 'medium' || size === 'large';

export const resolveTableRowSize = (
  preferences: TablePreferences,
  settings: BkUiSettings | null,
  defaultSize: TableRowSize,
) => [preferences.rowSize, settings?.rowSize, defaultSize].find(isTableRowSize) ?? 'medium';

function readStoredPreferences(storageKey?: string): TablePreferences {
  if (!storageKey) return {};
  try {
    const cached: Record<string, unknown> | null = JSON.parse(localStorage.getItem(storageKey) ?? 'null');
    if (!cached || typeof cached !== 'object') return {};

    // 旧缓存还包含 fields 和 disabled，列定义始终取自当前页面。
    const preferences: TablePreferences = {};
    if (Array.isArray(cached.checked)) {
      preferences.checked = cached.checked.filter((key): key is string => typeof key === 'string');
    }
    if (cached.fontSize === 'medium' || cached.fontSize === 'large') preferences.fontSize = cached.fontSize;
    const rowSize = isTableRowSize(cached.rowSize) ? cached.rowSize : cached.size;
    if (isTableRowSize(rowSize)) preferences.rowSize = rowSize;
    return preferences;
  }
  catch {
    return {};
  }
}

export function readTablePreferences({ storageKey, legacyRowSizeKey }: ITablePreferenceKeys): TablePreferences {
  const preferences = readStoredPreferences(storageKey);
  // 旧版 maxLimitConfig.className 只标识行高，不能从该键恢复另一张表的勾选列。
  if (!preferences.rowSize && legacyRowSizeKey) {
    const { rowSize } = readStoredPreferences(legacyRowSizeKey);
    if (rowSize) preferences.rowSize = rowSize;
  }
  return preferences;
}

export function writeTablePreferences({ storageKey }: ITablePreferenceKeys, preferences: TablePreferences): boolean {
  if (!storageKey) return false;
  try {
    localStorage.setItem(storageKey, JSON.stringify(preferences));
    return true;
  }
  catch {
    // 浏览器禁用存储或配额已满时，本次编辑仍保留在当前表格中。
    return false;
  }
}
