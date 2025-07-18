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
  <BkDialog
    theme="primary"
    :is-show="removeDialogConfig.isShow"
    :width="940"
    :title="removeDialogConfig.title"
    quick-close
    @closed="removeDialogConfig.isShow = false"
    @confirm="handleConfirm"
  >
    <div>
      <BkTable
        size="small"
        class="m-b-16px"
        :columns="tableColumns"
        :data="[curPermission]"
        show-overflow-tooltip
      />
    </div>
  </BkDialog>
</template>

<script lang="tsx" setup>
import { t } from '@/locales';
import { type IPermission } from '@/types/permission';

type IDialogParams = {
  isShow: boolean
  title: string
};

interface IProps {
  permissions: IPermission
  dialogParams?: IDialogParams
}

interface Emits {
  (e: 'update:dialogParams', value: IDialogParams)
  (e: 'confirm'): void
}

const curPermission = defineModel('permissions', {
  type: Object as PropType<IPermission>,
  required: true,
  default: {},
});
const {
  dialogParams = {
    title: '',
    saveLoading: false,
    isShow: false,
  },
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const tableColumns = shallowRef([
  {
    label: t('蓝鲸应用ID'),
    field: 'bk_app_code',
  },
  {
    label: t('搜索维度'),
    field: 'grant_dimension',
    render: ({ row }: { row?: IPermission }) => {
      function getSearchDimensionText() {
        if (['resource'].includes(row.grant_dimension)) return t('按资源');
        if (['api'].includes(row.grant_dimension)) return t('按网关');
        return '--';
      }
      return (
        <span class="ag-auto-text">{ getSearchDimensionText(row.grant_dimension) }</span>
      );
    },
  },
  {
    label: t('资源名称'),
    field: 'resource_name ',
    render: ({ row }: { row?: IPermission }) => {
      return (
        <span>{ row.resource_name || '--' }</span>
      );
    },
  },
  {
    label: t('请求路径'),
    field: 'resource_path ',
    render: ({ row }: { row?: IPermission }) => {
      return (
        <span>{ row.resource_path || '--' }</span>
      );
    },
  },
  {
    label: t('过期时间'),
    field: 'expires',
    render: ({ row }: { row?: IPermission }) => {
      return (
        <span>{ row.expires || t('永久有效') }</span>
      );
    },
  },

]);

const removeDialogConfig = computed({
  get: () => dialogParams,
  set: (params) => {
    emits('update:dialogParams', params);
  },
});

const handleConfirm = () => {
  emits('confirm');
};
</script>

<style lang="scss" scoped>
.app-renewal-slider {
  :deep(.bk-modal-content) {
    padding: 20px 24px 0;
    overflow-y: auto;
  }

  .collapse-wrap {
    :deep(.collapse-cls) {
      margin-bottom: 24px;

      .bk-collapse-item {
        box-shadow: none;
        margin-bottom: 16px;
        background-color: #f0f1f5;
      }
    }

    .panel-header {
      padding: 10px 12px;
      color: #63656e;
      cursor: pointer;

      .title {
        font-weight: 700;
        font-size: 14px;
        margin-left: 8px;
      }

      .panel-header-show {
        transition: 0.2s;
        transform: rotate(0deg);
      }

      .panel-header-hide {
        transition: 0.2s;
        transform: rotate(-90deg);
      }
    }

    :deep(.bk-collapse-content) {
      padding: 0 !important;
    }
  }
}
</style>
