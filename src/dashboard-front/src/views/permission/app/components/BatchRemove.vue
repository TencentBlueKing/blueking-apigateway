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
<template>
  <AgSideSlider
    v-model="removalSliderConfig.isShow"
    :width="960"
    quick-close
    ext-cls="app-renewal-slider"
    @closed="handleCancel"
  >
    <template #header>
      <div class="title">
        {{ removalSliderConfig.title }}
      </div>
    </template>
    <template #default>
      <div class="p-24px p-b-0">
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
                    {{ t('按资源') }}
                  </div>
                </div>
              </template>
              <template #content>
                <AgTable
                  v-model:table-data="resourceTableList"
                  local-page
                  :columns="tableColumns"
                  :show-pagination="false"
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
                    {{ t('按网关') }}
                  </div>
                </div>
              </template>
              <template #content>
                <AgTable
                  v-model:table-data="apiTableList"
                  :columns="tableColumns"
                  local-page
                  :show-pagination="false"
                />
              </template>
            </BkCollapsePanel>
          </BkCollapse>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="pl-24px">
        <BkButton
          class="w-88px"
          theme="danger"
          :loading="removalSliderConfig.saveLoading"
          @click="handleConfirm"
        >
          {{ t('删除') }}
        </BkButton>
        <BkButton
          class="ml-8px w-88px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </AgSideSlider>
</template>

<script lang="tsx" setup>
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { usePermission } from '@/stores';
import { type IPermission } from '@/types/permission';
import AgTable from '@/components/ag-table/Index.vue';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';

type ISliderParams = {
  isShow: boolean
  saveLoading: boolean
  title: string
};

interface IProps {
  apiList?: IPermission[]
  resourceList?: IPermission[]
  sliderParams?: ISliderParams
}

interface IEmits {
  'update:sliderParams': [value: ISliderParams]
  'confirm': [void]
}

const {
  sliderParams = {
    title: '',
    saveLoading: false,
    isShow: false,
  },
  apiList = [],
  resourceList = [],
} = defineProps<IProps>();

const emits = defineEmits<IEmits>();

const { t } = useI18n();
const permissionStore = usePermission();

const activeIndex = ref(['resource', 'gateway']);
const tableColumns = shallowRef<any[]>([
  {
    title: t('蓝鲸应用ID'),
    colKey: 'bk_app_code',
    ellipsis: true,
  },
  {
    title: t('资源名称'),
    colKey: 'resource_name',
    ellipsis: true,
    cell: (h: any, { row }: { row?: IPermission }) => {
      return (
        <span>{ row!.resource_name || '--' }</span>
      );
    },
  },
  {
    title: t('有效期'),
    colKey: 'expires',
    ellipsis: true,
    cell: (h: any, { row }: { row?: IPermission }) => {
      return (
        <div>
          <span style={{ color: permissionStore.getDurationTextColor(row!.expires ?? null) }}>
            { permissionStore.getDurationText(row?.expires ?? null) }
          </span>
        </div>
      );
    },
  },
]);

const removalSliderConfig = computed({
  get: () => sliderParams,
  set: (params: any) => {
    emits('update:sliderParams', params);
  },
});
// 资源表格
const resourceTableList = computed(() => resourceList);
// 网关表格
const apiTableList = computed(() => apiList);

const handleConfirm = () => {
  emits('confirm');
};

const handleCancel = () => {
  removalSliderConfig.value.isShow = false;
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
