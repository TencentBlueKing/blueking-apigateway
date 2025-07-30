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
    :title=" t('主动授权') "
    ext-cls="app-auth-slider"
    @closed="handleCancel"
    @compare="handleCompare"
  >
    <template #default>
      <div class="app-auth-slider-content">
        <div class="ag-span-title">
          {{ t("你将对指定的蓝鲸应用添加访问资源的权限") }}
        </div>
        <BkForm
          ref="authFormRef"
          :label-width="120"
          class="mb-20px"
          :model="curAuthData"
        >
          <BkFormItem
            :label="t('蓝鲸应用ID')"
            :rules="rules.bk_app_code"
            property="bk_app_code"
            class="m-l-15px"
            required
          >
            <BkInput
              ref="appCodeRef"
              v-model="curAuthData.bk_app_code"
              class="code-input"
              :placeholder="t('请输入应用ID')"
            />
          </BkFormItem>
          <BkFormItem
            :label="t('有效时间')"
            :rules="rules.expire_type"
            property="expire_type"
            class="m-l-15px m-b-30px"
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
                  ref="expireTypeRef"
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
          <BkFormItem
            :rules="rules.dimension"
            :label-width="0"
            property="dimension"
            class="m-b-0!"
            required
          >
            <div class="ag-span-title mb-16px!">
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
                  ref="dimensionRef"
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
          </BkFormItem>
        </BkForm>
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
import {
  type IAuthData,
  authApiPermission,
  authResourcePermission,
} from '@/services/source/permission';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';

type ISliderParams = {
  isShow: boolean
  isLoading: boolean
  title: string
};

type FormMethod = {
  validate: () => void
  clearValidate: () => void
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

const route = useRoute();

const authFormRef = ref<InstanceType<typeof BkForm> & FormMethod>();
const appCodeRef = ref<InstanceType<typeof BkInput>>(null);
const expireTypeRef = ref<InstanceType<typeof BkInput>>(null);
const dimensionRef = ref<InstanceType<typeof BkTransfer>>(null);
const initData = ref({
  bk_app_code: '',
  expire_type: 'permanent',
  expire_days: null,
  resource_ids: [],
  dimension: 'api',
});
const rules = reactive({
  bk_app_code: [
    {
      required: true,
      message: t('请输入蓝鲸应用ID'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const codeReg = /^[a-z][a-z0-9-_]+$/;
        if (!codeReg.test(value)) {
          return false;
        }
        return true;
      },
      message: t('蓝鲸应用ID格式不正确，只能包含：小写字母、数字、连字符(-)、下划线(_)，首字母必须是字母'),
      trigger: 'blur',
    },
  ],
  expire_type: [
    {
      validator: (value: string) => {
        if (['custom'].includes(value) && !curAuthData.value.expire_days) {
          return false;
        }
        return true;
      },
      message: t('请输入有效时间'),
      trigger: 'change',
    },
  ],
  dimension: [
    {
      validator: (value: string) => {
        if (['resource'].includes(value) && !curAuthData.value.resource_ids.length) {
          return false;
        }
        return true;
      },
      message: t('请选择要授权的资源'),
      trigger: 'change',
    },
  ],
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

// 主动授权 不同选项，数据的更改
const formatData = () => {
  const params: IAuthData = cloneDeep(curAuthData.value);
  if (params.expire_type.includes('permanent')) {
    params.expire_days = null;
  }
  if (params.dimension.includes('api')) {
    params.resource_ids = null;
  }
  return params;
};

const handleScrollView = (el: HTMLInputElement | HTMLElement) => {
  el.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  });
};

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

const handleSave = async () => {
  try {
    await authFormRef?.value?.validate();
  }
  catch {
    const {
      bk_app_code,
      dimension,
      expire_type,
      expire_days,
      resource_ids,
    } = curAuthData.value;
    if (!bk_app_code) {
      appCodeRef.value?.focus();
      handleScrollView(appCodeRef?.value?.$el);
      return;
    }
    if (['custom'].includes(expire_type) && !expire_days) {
      expireTypeRef.value?.focus();
      handleScrollView(expireTypeRef?.value?.$el);
      return;
    }
    if (['resource'].includes(dimension) && !resource_ids.length) {
      handleScrollView(dimensionRef?.value?.$el);
      return;
    }
  }
  const params = formatData();
  const fetchMethod = ['resource'].includes(params.dimension)
    ? authResourcePermission
    : authApiPermission;
  await fetchMethod(route.params.id, params);
  handleCancel();
  emits('confirm');
};

const handleCancel = () => {
  authFormRef?.value?.clearValidate();
  curAuthData.value = cloneDeep(initData.value);
  authSliderConfig.value.isShow = false;
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
      line-height: 1;
      margin-bottom: 20px;
    }

    .ag-resource-radio {
      display: block;

      label {
        display: block;
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
</style>
