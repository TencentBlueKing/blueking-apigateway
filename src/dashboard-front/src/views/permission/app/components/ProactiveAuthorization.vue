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
                  :placeholder="t('请输入正整数')"
                  class="w-117px m-r-5px"
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
            class="auth-resource m-b-0!"
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
                  class="proactive-auth-transfer"
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
import { Form, Input, Transfer } from 'bkui-vue';
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

const authFormRef = ref<InstanceType<typeof Form> & FormMethod>();
const appCodeRef = ref<InstanceType<typeof Input>>(null);
const expireTypeRef = ref<InstanceType<typeof Input>>(null);
const dimensionRef = ref<InstanceType<typeof Transfer>>(null);
const transferIsAllEl = ref(null);
const transferInputEl = ref(null);
const clearIconEl = ref(null);
const transferSourceList = ref([]);
const transferTargetList = ref([]);
const searchTargetList = ref([]);
const resourceTransferList = ref([]);
const resourceTransferListBack = ref([]);
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

watch(authSliderConfig.value, ({ isShow }: { isShow: boolean }) => {
  if (isShow) {
    resourceTransferList.value = cloneDeep(resourceList);
    resourceTransferListBack.value = cloneDeep(resourceList);
  }
}, { immediate: true });

watch(curAuthData.value, (authData) => {
  if (['resource'].includes(authData.dimension)) {
    nextTick(() => {
      const transferSourceEl = document.querySelector('.proactive-auth-transfer .source-list');
      transferIsAllEl.value = transferSourceEl.querySelector('.select-all');
      transferInputEl.value = transferSourceEl.querySelector('input');
      transferIsAllEl.value?.addEventListener('click', handleSetSearchAll, { capture: true });
      transferInputEl.value?.addEventListener('input', getTransferSearch, { capture: true });
    });
  }
});

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
  // 这里change会触发两次
  setTimeout(() => {
    transferSourceList.value = [...sourceList];
    transferTargetList.value = [...targetList];
    const isTargetEmpty = document.querySelector('.proactive-auth-transfer .target-list .empty');
    if (isTargetEmpty && dimensionRef.value.selectListSearch.length < resourceTransferListBack.value.length) {
      searchTargetList.value = [];
      curAuthData.value.resource_ids = [];
      resourceTransferList.value = cloneDeep(resourceTransferListBack.value);
    }
    if (searchTargetList.value.length) {
      curAuthData.value.resource_ids = searchTargetList.value.map(item => item.id);
    }
    else {
      curAuthData.value.resource_ids = targetValueList;
    }
  }, 100);
};

// 设置transfer组件搜索状态选择全部交互
function handleSetSearchAll() {
  searchTargetList.value = [];
  const searchKeyword = dimensionRef.value.selectSearchQuery;
  // 获取搜索列表的数据
  if (searchKeyword) {
    const transferEl = document.querySelector('.proactive-auth-transfer');
    const sourceEl = transferEl.querySelector('.source-list > ul');
    // 获取所有li下transfer-source-item元素
    const sourceItems = sourceEl?.querySelectorAll('.transfer-source-item');
    if (sourceItems) {
      const itemTexts = Array.from(sourceItems).map((item) => {
        return item.textContent.trim();
      });
      searchTargetList.value = resourceTransferListBack.value.filter(item =>
        itemTexts.includes(item.name) || transferTargetList.value.map(target => target.id).includes(item.id),
      );
    }
    // 重置已选资源
    setTimeout(() => {
      dimensionRef.value.selectedList = searchTargetList.value;
    }, 0);
  }
};

const handleResetTransferData = () => {
  if (!curAuthData.value.resource_ids.length) {
    searchTargetList.value.map(item => item.id);
  }
  const hasSelected = resourceTransferListBack.value.filter(item =>
    curAuthData.value.resource_ids.includes(item.id),
  );
  resourceTransferList.value = resourceTransferListBack.value.filter(item =>
    item.name.indexOf(dimensionRef.value.selectSearchQuery) > -1
    && !hasSelected.map(target => target.id).includes(item.id),
  );
  setTimeout(() => {
    dimensionRef.value.selectedList = hasSelected;
  }, 0);
};

function handleClearTransferSearch() {
  dimensionRef.value.selectSearchQuery = '';
  handleResetTransferData();
}

// 获取transfer实时输入值
function getTransferSearch(e: InputEvent) {
  const target = e.target as HTMLInputElement;
  dimensionRef.value.selectSearchQuery = target.value;
  // 清空按钮实例
  nextTick(() => {
    clearIconEl.value = document.querySelector('.proactive-auth-transfer .source-list .bk-input--clear-icon');
    clearIconEl.value?.addEventListener('click', handleClearTransferSearch, { capture: true });
  });
  handleResetTransferData();
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
  clearIconEl.value?.removeEventListener('click', handleClearTransferSearch, { capture: true });
  transferIsAllEl.value?.removeEventListener('click', handleSetSearchAll, { capture: true });
  transferInputEl.value?.removeEventListener('input', getTransferSearch, { capture: true });
  transferIsAllEl.value = null;
  transferInputEl.value = null;
  clearIconEl.value = null;
  transferSourceList.value = [];
  transferTargetList.value = [];
  searchTargetList.value = [];
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
      margin-bottom: 20px;
      font-size: 14px;
      font-weight: bold;
      line-height: 1;
      color: #63656e;
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
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }

    .auth-resource {
      :deep(.bk-form-error) {
        margin-top: 4px;
        margin-left: 20px;
      }
    }
  }
}
</style>
