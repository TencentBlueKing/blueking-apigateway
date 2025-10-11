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
                  class="proactive-auth-transfer"
                  :display-key="'name'"
                  :setting-key="'id'"
                  :source-list="resourceTransferList"
                  :title="[t('未选资源'), t('已选资源')]"
                  searchable
                  @change="handleResourceChange"
                  @update:target-list="handleUpdateTarget"
                >
                  <template #left-header>
                    <div class="flex items-center justify-between h-40px left-header">
                      <div>
                        <span>{{ t('未选资源') }}</span>
                        <span class="ml-8px">{{ `(${sourceListLen})` }}</span>
                      </div>
                      <div class="add-all">
                        <BkButton
                          text
                          theme="primary"
                          class="text-12px!"
                          :disabled="sourceListLen === 0"
                          @click.stop="handleAddAllResource"
                        >
                          {{ t('选择全部') }}
                        </BkButton>
                      </div>
                    </div>
                  </template>
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
const transferInputEl = ref(null);
const clearIconEl = ref(null);
const sourceListLen = ref(0);
// 这里设置isSelectAll判断是否选择全部，是因为先选择几个资源，然后再点击选择全部后返回的资源总数不是所有的
const isSelectAll = ref(false);
const resourceTransferList = ref([]);
const resourceTransferListBack = ref([]);
const targetTransferList = ref([]);
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
    sourceListLen.value = resourceList.length;
    resourceTransferList.value = cloneDeep(resourceList);
    resourceTransferListBack.value = cloneDeep(resourceList);
  }
}, { immediate: true });

watch(curAuthData.value, (payload) => {
  if (['resource'].includes(payload.dimension)) {
    nextTick(() => {
      // 输入框实例
      transferInputEl.value = document.querySelector('.proactive-auth-transfer .source-list input');
      transferInputEl.value?.addEventListener('input', getTransferSearch, { capture: true });
      transferInputEl.value?.addEventListener('paste', getTransferSearch, { capture: true });
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

// 设置动态添加空文本节点
const handleSetEmptyContent = (isAll: boolean) => {
  const sourceEl = document.querySelector('.proactive-auth-transfer .source-list');
  const sourceUl = sourceEl.querySelector('ul.is-search');
  const emptyEl = sourceEl.querySelector('.empty');
  // 是否选择全部
  const isSelectAllResource = isAll && !sourceListLen.value;
  // 组件内部无数据会去掉ul标签
  if (sourceUl) {
    sourceUl.style.display = isSelectAllResource ? 'none' : 'block';
    // 如果是选择全部，移除掉所有li节点
    if (isAll && !dimensionRef.value.selectSearchQuery) {
      const customItems = sourceUl.querySelectorAll('li.custom-item');
      if (customItems) {
        customItems.forEach(li => li.remove());
      }
    }
  }
  emptyEl?.parentNode?.removeChild(emptyEl);
  if (isSelectAllResource && !emptyEl) {
    // 选择全部后，创建空数据文本
    const emptyDiv = document.createElement('div');
    emptyDiv.className = 'empty';
    emptyDiv.textContent = t('无数据');
    sourceEl.appendChild(emptyDiv);
  }
};

// 选择授权的资源数量发生改变触发
const handleResourceChange = (
  sourceList: IResource[],
  targetList: IResource[],
  targetValueList: number[],
) => {
  const listBack = cloneDeep(resourceTransferListBack.value);
  const searchKeyword = dimensionRef.value.selectSearchQuery;
  const allResourceId = listBack.map(item => item.id);
  sourceListLen.value = allResourceId.filter(id => !targetTransferList.value.includes(id))?.length;
  if (targetValueList.length >= listBack.length) {
    sourceListLen.value = 0;
  }
  // 如果sourceListLen大于零代表是一个个选，否则是选择全部
  if (sourceListLen.value) {
    // 是否是搜索后选择全部
    const isSearch = !!searchKeyword;
    if (isSearch) {
      resetSourceData();
    }
    handleSetEmptyContent(isSearch);
    curAuthData.value.resource_ids = targetValueList;
    dimensionRef.value.targetValueList = curAuthData.value.resource_ids;
  }
  else {
    handleSetEmptyContent(true);
    if (!searchKeyword) {
      curAuthData.value.resource_ids = allResourceId;
    }
  }
  isSelectAll.value = !sourceListLen.value;
  removeDuplicateEmpty();
};

const handleUpdateTarget = (list: IResource[]) => {
  targetTransferList.value = list;
};

// 自定义选择全部
const handleAddAllResource = () => {
  isSelectAll.value = true;
  const searchValue = dimensionRef.value.selectSearchQuery;
  const searchList = resourceTransferListBack.value.filter(item =>
    item.name.indexOf(searchValue) > -1,
  );
  // 过滤掉已选的资源
  const noSelectList = resourceTransferListBack.value.filter(item =>
    !curAuthData.value.resource_ids.includes(item.id)
    && searchList.map(searchItem => searchItem.id).includes(item.id),
  );
  const noSelectIds = noSelectList.map(item => item.id);
  // 如果有搜索条件
  if (searchValue) {
    const hasSelectedResource
      = resourceTransferListBack.value.filter(item => curAuthData.value.resource_ids.includes(item.id));
    dimensionRef.value.selectedList = [...hasSelectedResource, ...noSelectList];
    dimensionRef.value.targetValueList = dimensionRef.value.selectedList.map(item => item.id);
  }
  else {
    if (noSelectList?.length) {
      curAuthData.value.resource_ids = [
        ...new Set([...curAuthData.value.resource_ids, ...noSelectIds]),
      ];
    }
    dimensionRef.value.selectedList = searchList;
    dimensionRef.value.targetValueList = curAuthData.value.resource_ids;
  }
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
  transferInputEl.value?.removeEventListener('input', getTransferSearch, { capture: true });
  transferInputEl.value?.removeEventListener('paste', getTransferSearch, { capture: true });
  clearIconEl.value?.removeEventListener('click', handleClearTransferSearch, { capture: true });
};

const resetSourceData = () => {
  sourceListLen.value = resourceTransferListBack.value.filter(item =>
    item.name.indexOf(dimensionRef.value.selectSearchQuery) > -1 && !targetTransferList.value.includes(item.id),
  )?.length;
  handleSetEmptyContent(false);
};

function handleClearTransferSearch() {
  dimensionRef.value.selectSearchQuery = '';
  resetSourceData();
}

// 获取transfer实时输入值
function getTransferSearch(e: InputEvent) {
  dimensionRef.value.selectSearchQuery = e.target.value;
  resetSourceData();
  nextTick(() => {
    clearIconEl.value = document.querySelector('.proactive-auth-transfer .source-list .bk-input--clear-icon');
    // 清空按钮实例
    clearIconEl.value?.addEventListener('click', handleClearTransferSearch, { capture: true });
  });
};

// 移除重复的empty节点
function removeDuplicateEmpty() {
  setTimeout(() => {
    const empties = document.querySelectorAll('.proactive-auth-transfer .source-list .empty');
    if (empties.length > 1) {
      // 从第二个开始移除
      for (let i = 1; i < empties.length; i++) {
        empties[i].remove();
      }
    }
  }, 0);
}
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
