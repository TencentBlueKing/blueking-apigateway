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
  <AgSideSlider
    v-model="renewalSliderConfig.isShow"
    width="960"
    quick-close
    ext-cls="app-renewal-slider"
    :init-data="initData"
    @closed="handleCancel"
    @compare="handleCompare"
  >
    <template #header>
      <div class="title">
        {{ renewalSliderConfig.title }}
      </div>
    </template>
    <template #default>
      <div class="p-24px p-b-0">
        <ExpireDaySelector
          v-model:expire-days="expireDays"
          form-type="vertical"
          label-position="left"
        />
        <div class="collapse-wrap">
          <BkCollapse
            v-model="activeIndex"
            class="collapse-cls"
            use-card-theme
          >
            <BkCollapsePanel name="resource">
              <template #header>
                <div class="flex items-center panel-header">
                  <AngleUpFill
                    :class="[
                      activeIndex?.includes('resource')
                        ? 'panel-header-show'
                        : 'panel-header-hide',
                    ]"
                  />
                  <div class="title">
                    {{ t("按资源") }}
                  </div>
                </div>
              </template>
              <template #content>
                <BkTable
                  size="small"
                  :data="resourceTableList"
                  :columns="tableColumns"
                  :border="['row', 'outer']"
                  show-overflow-tooltip
                />
              </template>
            </BkCollapsePanel>
            <BkCollapsePanel name="gateway">
              <template #header>
                <div class="flex items-center panel-header">
                  <AngleUpFill
                    :class="[
                      activeIndex?.includes('gateway')
                        ? 'panel-header-show'
                        : 'panel-header-hide',
                    ]"
                  />
                  <div class="title">
                    {{ t("按网关") }}
                  </div>
                </div>
              </template>
              <template #content>
                <BkTable
                  size="small"
                  :data="apiTableList"
                  :columns="tableColumns"
                  :border="['row', 'outer']"
                  show-overflow-tooltip
                />
              </template>
            </BkCollapsePanel>
          </BkCollapse>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="p-l-24px">
        <BkButton
          class="w-88px"
          theme="primary"
          :disabled="applyCount === 0"
          :loading="renewalSliderConfig.saveLoading"
          @click="handleConfirm"
        >
          {{ t("确定") }}
        </BkButton>
        <BkButton
          class="m-l-8px w-88px"
          @click="handleCancel"
        >
          {{ t("取消") }}
        </BkButton>
      </div>
    </template>
  </AgSideSlider>
</template>

<script lang="tsx" setup>
import { AngleUpFill } from 'bkui-lib/icon';
import { t } from '@/locales';
import { usePermission } from '@/stores';
import { type IPermission } from '@/types/permission';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';
import ExpireDaySelector from '@/views/permission/app/components/ExpireDaySelector.vue';

type ISliderParams = {
  isShow: boolean
  saveLoading: boolean
  title: string
};

interface IProps {
  applyCount?: number
  expireDate: number
  apiList?: IPermission[]
  resourceList?: IPermission[]
  sliderParams?: ISliderParams
}

interface Emits {
  (e: 'update:expireDate', value: number)
  (e: 'update:sliderParams', value: ISliderParams)
  (e: 'confirm'): void
}

const expireDays = defineModel('expireDate', {
  type: Number,
  required: true,
  default: 0,
});
const {
  applyCount = 0,
  sliderParams = {
    title: '',
    saveLoading: false,
    isShow: false,
  },
  apiList = [],
  resourceList = [],
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const permissionStore = usePermission();

const activeIndex = ref(['resource', 'gateway']);
const tableColumns = shallowRef([
  {
    label: t('蓝鲸应用ID'),
    field: 'bk_app_code',
  },
  {
    label: t('资源名称'),
    field: 'resource_name',
    render: ({ row }: { row?: IPermission }) => {
      return (
        <span>{ row.resource_name || '--' }</span>
      );
    },
  },
  {
    label: t('有效期'),
    field: 'expires',
    render: ({ row }: { row?: IPermission }) => {
      return (
        <div>
          <span style={{ color: permissionStore.getDurationTextColor(row.expires) }}>
            { permissionStore.getDurationText(row?.expires) }
          </span>
          <span class="m-l-4px m-r-4px">
            <AgIcon name="arrows--right--line" style="color: #699df4;" />
          </span>
          <span>
            {
              row.renewable
                ? (
                  <span class="ag-normal primary">
                    { permissionStore.getDurationAfterRenew(row?.expires, expireDays.value) }
                  </span>
                )
                : (
                  <span class="font-bold color-#ea3636">
                    { t('不可续期') }
                  </span>
                )
            }
          </span>
        </div>
      );
    },
  },
]);
const initData = reactive({ expireDays: 0 });

const renewalSliderConfig = computed({
  get: () => sliderParams,
  set: (params) => {
    emits('update:sliderParams', params);
  },
});
// 资源表格
const resourceTableList = computed(() => resourceList);
// 网关表格
const apiTableList = computed(() => apiList);

const handleCompare = (callback) => {
  callback({ expireDays: expireDays.value });
};

const handleConfirm = () => {
  emits('confirm');
};

const handleCancel = () => {
  expireDays.value = 0;
  renewalSliderConfig.value.isShow = false;
};
</script>

<style lang="scss" scoped>
.app-renewal-slider {

  .collapse-wrap {

    :deep(.collapse-cls) {
      margin-bottom: 24px;

      .bk-collapse-item {
        margin-bottom: 16px;
        background-color: #f0f1f5;
        box-shadow: none;
      }
    }

    .panel-header {
      padding: 10px 12px;
      color: #63656e;
      cursor: pointer;

      .title {
        margin-left: 8px;
        font-size: 14px;
        font-weight: 700;
      }

      .panel-header-show {
        transform: rotate(0deg);
        transition: 0.2s;
      }

      .panel-header-hide {
        transform: rotate(-90deg);
        transition: 0.2s;
      }
    }

    :deep(.bk-collapse-content) {
      padding: 0 !important;
    }
  }
}
</style>
