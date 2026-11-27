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
import { isEqual } from 'lodash-es';
import {
  type ITablePreferenceKeys,
  type TablePreferences,
  readTablePreferences,
  resolveTableRowSize,
  writeTablePreferences,
} from './table-preferences';
import type { ITableColumn, ITableSettings, TableRowSize } from '../types';

interface ITableSettingsOptions {
  showSettings: () => boolean
  preferenceKeys: ComputedRef<ITablePreferenceKeys>
  initialPreferences: TablePreferences
  columns: () => ITableColumn<any>[]
  hiddenColumnKeys: () => string[]
  uncheckedColumnKeys: () => string[]
  defaultRowSize: () => TableRowSize
}

const buildDefaultSettings = (options: ITableSettingsOptions): BkUiSettings => {
  const columnsWithKeys = options.columns().filter((column): column is ITableColumn<any> & { colKey: string } =>
    typeof column.colKey === 'string');
  const hiddenKeys = options.hiddenColumnKeys();
  const uncheckedKeys = options.uncheckedColumnKeys();
  const fields = columnsWithKeys.filter(column => !hiddenKeys.includes(column.colKey)).map(column => ({
    label: column.displayTitle ?? (typeof column.title === 'string' ? column.title : column.colKey),
    field: column.colKey,
  }));
  // 设置面板锁定第一个业务列的勾选状态，跳过勾选框和序号列。
  const firstDataColumn = columnsWithKeys.find(column => !['row-select', 'serial-number'].includes(column.colKey));
  return {
    fields,
    disabled: firstDataColumn ? [firstDataColumn.colKey] : [],
    checked: fields.map(({ field }) => field).filter(key => !uncheckedKeys.includes(key)),
    fontSize: 'medium',
  };
};

export const useTableSettings = (settingsModel: Ref<BkUiSettings | null>, options: ITableSettingsOptions) => {
  const { preferenceKeys } = options;
  const userPreferences = shallowRef(options.initialPreferences);
  const parentSettings = shallowRef(settingsModel.value);
  const settingsEnabled = computed(() => options.showSettings() || Boolean(parentSettings.value));
  let lastEmittedSettings: BkUiSettings | null = null;
  // 禁用本地缓存或写入失败时，标记偏好仅存在于内存中，避免父组件置 null 时被空缓存覆盖。
  let hasUnsavedPreferences = false;

  const resolvedSettings = computed<BkUiSettings | undefined>((previous) => {
    if (!settingsEnabled.value) return undefined;
    const baseSettings = parentSettings.value ?? buildDefaultSettings(options);
    const mergedSettings = {
      ...baseSettings,
      ...userPreferences.value,
      rowSize: resolveTableRowSize(userPreferences.value, parentSettings.value, options.defaultRowSize()),
    };
    const availableKeys = baseSettings.fields?.map(({ field }) => field)
      ?? (baseSettings.checked?.length ? baseSettings.checked : undefined);
    if (userPreferences.value.checked && availableKeys) {
      mergedSettings.checked = userPreferences.value.checked.filter(key => availableKeys.includes(key));
    }
    return previous && isEqual(previous, mergedSettings) ? previous : mergedSettings;
  });

  const syncSettingsToModel = () => {
    const nextSettings = resolvedSettings.value;
    if (!nextSettings) return;
    if (toRaw(settingsModel.value) === nextSettings || isEqual(settingsModel.value, nextSettings)) return;
    lastEmittedSettings = toRaw(nextSettings);
    settingsModel.value = nextSettings;
  };

  watch(preferenceKeys, (keys, previousKeys) => {
    if (!isEqual(keys, previousKeys)) {
      hasUnsavedPreferences = false;
      userPreferences.value = settingsEnabled.value ? readTablePreferences(keys) : {};
    }
  }, { flush: 'sync' });

  watch(settingsEnabled, (enabled) => {
    if (enabled && !hasUnsavedPreferences && preferenceKeys.value.storageKey) {
      userPreferences.value = readTablePreferences(preferenceKeys.value);
    }
  }, { flush: 'sync' });

  watch(settingsModel, (incomingSettings) => {
    // 同一 v-model 也接收页面定义的字段。组件自己回写的合并结果不能成为下一张表的默认设置。
    if (incomingSettings && toRaw(incomingSettings) === lastEmittedSettings) return;
    parentSettings.value = incomingSettings;
    if (!incomingSettings && settingsEnabled.value && !hasUnsavedPreferences && preferenceKeys.value.storageKey) {
      userPreferences.value = readTablePreferences(preferenceKeys.value);
    }
    syncSettingsToModel();
  }, { flush: 'sync' });
  watch([resolvedSettings, settingsEnabled], syncSettingsToModel, { immediate: true });

  const handleSettingsChange = ({ columns, fontSize, rowSize }: ITableSettings) => {
    const current = resolvedSettings.value;
    if (!current) return;
    const checked = [...new Set(columns)];
    if (isEqual(checked, current.checked) && fontSize === current.fontSize && rowSize === current.rowSize) return;
    userPreferences.value = {
      checked,
      fontSize,
      rowSize,
    };
    hasUnsavedPreferences = !writeTablePreferences(preferenceKeys.value, userPreferences.value);
    syncSettingsToModel();
  };

  // PrimaryTable 的列宽监听随子组件卸载后，再释放组件回写的合并设置；父组件自定义的 fields 定义保持原样。
  onUnmounted(() => {
    if (!parentSettings.value) {
      if (settingsModel.value !== null) settingsModel.value = null;
    }
    else if (settingsModel.value && toRaw(settingsModel.value) === lastEmittedSettings) {
      settingsModel.value = parentSettings.value;
    }
  });

  return {
    settingsEnabled,
    resolvedSettings,
    handleSettingsChange,
  };
};
