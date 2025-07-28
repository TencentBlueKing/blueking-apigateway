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
    v-model="authSliderConfig.isShow"
    :width="800"
    :init-data="initData"
    quick-close
    ext-cls="app-auth-slider"
    @closed="handleCancel"
    @compare="handleCompare"
  >
    <template #header>
      <div class="title">
        {{ t('主动授权') }}
      </div>
    </template>
    <template #default>
      <div class="app-auth-slider-content">
        <div class="ag-span-title">
          {{ t("你将对指定的蓝鲸应用添加访问资源的权限") }}
        </div>
        <BkForm
          class="m-b-30px m-l-15px"
          :label-width="120"
          :model="curAuthData"
        >
          <BkFormItem
            :label="t('蓝鲸应用ID')"
            required
          >
            <BkInput
              v-model="curAuthData.bk_app_code"
              class="code-input"
              :placeholder="t('请输入应用ID')"
            />
          </BkFormItem>
          <BkFormItem
            :label="t('有效时间')"
            required
          >
            <BkRadioGroup v-model="curAuthData.expire_type">
              <BkRadio
                label="permanent"
                class="m-r-15px"
              >
                {{ t("永久有效") }}
              </BkRadio>
              <BkRadio label="custom">
                <BkInput
                  v-model="curAuthData.expire_days"
                  type="number"
                  :min="0"
                  class="w-85px m-r-5px"
                  @focus="curAuthData.expire_type = 'custom'"
                />
                {{ t("天") }}
              </BkRadio>
            </BkRadioGroup>
          </BkFormItem>
        </BkForm>
        <div class="ag-span-title">
          {{ t("请选择要授权的资源") }}
        </div>
        <div class="m-l-20px">
          <BkRadioGroup
            v-model="curAuthData.dimension"
            class="ag-resource-radio"
          >
            <BkRadio label="api">
              {{ t("按网关") }}
              <span v-bk-tooltips="t('包括网关下所有资源，包括未来新创建的资源')">
                <i class="apigateway-icon icon-ag-help" />
              </span>
            </BkRadio>
            <BkRadio
              label="resource"
              class="m-l-0!"
            >
              {{ t("按资源") }}
              <span v-bk-tooltips="t('仅包含当前选择的资源')">
                <i class="apigateway-icon icon-ag-help" />
              </span>
            </BkRadio>
          </BkRadioGroup>
          <div
            v-if="['resource'].includes(curAuthData.dimension)"
            class="ag-transfer-box"
          >
            <BkTransfer
              :source-list="resourceTransferList"
              :display-key="'name'"
              :setting-key="'id'"
              :title="[t('未选资源'), t('已选资源')]"
              searchable
              @change="handleResourceChange"
            >
              <template #source-option="data">
                <div class="transfer-source-item">
                  {{ data.name }}
                </div>
              </template>
              <template #target-option="data">
                <div class="transfer-source-item">
                  {{ data.name }}
                </div>
              </template>
            </BkTransfer>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="p-l-50px">
        <BkButton
          class="w-88px"
          theme="primary"
          @click="handleSave"
        >
          {{ t("保存") }}
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

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import { t } from '@/locales';
import { type IResource } from '@/types/permission';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';

type ISliderParams = {
  isShow: boolean
  isLoading: boolean
  title: string
};

type IAuthData = {
  bk_app_code: string
  expire_type: string
  dimension: string
  expire_days: null | number
  resource_ids: string[] | number[]
};

interface IProps {
  sliderParams?: ISliderParams
  authData?: IAuthData
  resourceList?: IResource[]
}

interface Emits {
  (e: 'update:sliderParams', value: ISliderParams)
  (e: 'update:authData', value: IAuthData)
  (e: 'confirm'): void
}

const {
  sliderParams = {
    isShow: false,
    title: '',
  },
  authData = {
    bk_app_code: '',
    dimension: 'api',
    expire_type: 'permanent',
    expire_days: null,
    resource_ids: [],
  },
  resourceList = [],
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const initData = ref({
  bk_app_code: '',
  expire_type: 'permanent',
  expire_days: null,
  resource_ids: [],
  dimension: 'api',
});

const authSliderConfig = computed({
  get: () => sliderParams,
  set: (params) => {
    emits('update:sliderParams', params);
  },
});

const curAuthData = computed({
  get: () => authData,
  set: (params) => {
    emits('update:authData', params);
  },
});

const resourceTransferList = computed(() => resourceList);

const handleCompare = (callback) => {
  callback(cloneDeep(curAuthData.value));
};

// 选择授权的资源数量发生改变触发
const handleResourceChange = (
  sourceList: IResource[],
  targetList: IResource[],
  targetValueList: number[],
) => {
  curAuthData.value.resource_ids = targetValueList;
};

const handleSave = () => {
  emits('confirm');
};

const handleCancel = () => {
  authSliderConfig.value.isShow = false;
  curAuthData.value = cloneDeep(initData.value);
};
</script>

<style lang="scss" scoped>
.app-auth-slider {
  .app-auth-slider-content {
    padding: 30px;
    padding-bottom: 0;

    .code-input {
      width: 256px;
    }

    .ag-span-title {
      font-size: 14px;
      font-weight: bold;
      color: #63656e;
      margin-bottom: 20px;
    }

    .ag-resource-radio {
      display: block;

      label {
        display: block;
        margin-bottom: 10px;
      }
    }

    .ag-transfer-box {
      padding: 20px;
      background: #fafbfd;
      border: 1px solid #f0f1f5;
      border-radius: 2px;

      .bk-transfer {
        color: #63656e;

        :deep(.header) {
          font-weight: normal;
        }

        .transfer-source-item {
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }
      }
    }
  }
}
.drawer-container {
    margin: 30px !important;
  }
</style>
