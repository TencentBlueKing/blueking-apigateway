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
<template>
  <div class="apigw-access-manager-wrapper">
    <div class="p-24px wrapper">
      <BkForm
        form-type="inline"
        class="m-b-16px"
      >
        <BkFormItem
          :label="t('选择时间')"
          :label-width="locale === 'zh-cn' ? 86 : 100"
        >
          <BkDatePicker
            :key="dateKey"
            v-model="dateValue"
            style="width: 320px;"
            :placeholder="t('选择日期时间范围')"
            type="datetimerange"
            use-shortcut-text
            :shortcuts="shortcutsRange"
            :shortcut-selected-index="shortcutSelectedIndex"
            @change="handleChange"
            @shortcut-change="handleShortcutChange"
            @clear="handlePickClear"
            @pick-success="handlePickSuccess"
            @selection-mode-change="handleSelectionModeChange"
          />
        </BkFormItem>
      </BkForm>
      <AgTable
        ref="tableRef"
        v-model:table-data="tableData"
        show-settings
        resizable
        :api-method="getTableData"
        :columns="tableColumns"
        :max-limit-config="{ allocatedHeight: 268, mode: 'tdesign'}"
        @clear-filter="handleClearFilter"
      />
    </div>
  </div>
</template>

<script lang="tsx" setup>
import { Button, Loading } from 'bkui-vue';
import { useDatePicker } from '@/hooks';
import { OPERATE_STATUS_MAP } from '@/enums';
import type { ITableMethod } from '@/types/common';
import { type ISyncHistoryItem, getSyncHistory } from '@/services/source/componentManagement';
import AgTable from '@/components/ag-table/Index.vue';

const router = useRouter();
const { t, locale } = useI18n();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableColumns = shallowRef([
  {
    title: 'ID',
    colKey: 'resource_version_title',
    cell: (h, { row }: { row?: Partial<ISyncHistoryItem> }) => {
      if (!row?.id) {
        return '--';
      }
      return (
        <Button
          theme="primary"
          class="mr-10px"
          text
          onClick={() => handleVersion(row.id)}
        >
          { row.id }
        </Button>
      );
    },
  },
  {
    title: t('同步时间'),
    colKey: 'created_time',
    ellipse: true,
  },
  {
    title: t('同步版本号（版本标题）'),
    colKey: 'resource_version_name',
    ellipse: true,
    cell: (h, { row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <span>
          { row?.resource_version_display || '--' }
        </span>
      );
    },
  },
  {
    title: t('操作人'),
    colKey: 'component_name',
    ellipse: true,
    cell: (h, { row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <span>
          { row?.created_by || '--' }
        </span>
      );
    },
  },
  {
    title: t('操作结果'),
    colKey: 'status ',
    ellipse: true,
    cell: (h, { row }: { row?: Partial<ISyncHistoryItem> }) => {
      if (['releasing'].includes(row?.status)) {
        return (
          <span>
            <Loading
              size="mini"
              theme="primary"
              mode="spin"
              class="mr-4px"
            />
            { t('同步中') }
          </span>
        );
      }
      return (
        <span>
          <span class={`ag-dot ${row?.status} m-r-5px`} />
          { OPERATE_STATUS_MAP[row?.status] }
        </span>
      );
    },
  },
  {
    title: t('操作日志'),
    field: 'message',
    ellipse: true,
    cell: (h, { row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <span>
          { row?.message || '--' }
        </span>
      );
    },
  },
]);
const tableData = ref([]);
const dateKey = ref('dateKey');
const searchParams = ref({
  time_start: '',
  time_end: '',
});

const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleClear,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
} = useDatePicker(searchParams);

const getList = () => {
  tableRef.value?.fetchData(searchParams.value, { resetPage: true });
};

const getTableData = async (params: Record<string, any> = {}) => {
  const res = await getSyncHistory(params);
  return res ?? {};
};

const handlePickClear = () => {
  handleClear();
  getList();
};

const handlePickSuccess = () => {
  handleConfirm();
  getList();
};

const handleClearFilter = () => {
  handlePickClear();
  dateKey.value = String(+new Date());
};

const handleVersion = (id: string) => {
  router.push({
    name: 'SyncVersion',
    query: { id },
  });
};
</script>
