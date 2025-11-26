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
    v-model="sliderConfig.isShow"
    ext-cls="apigw-access-manager-slider-cls"
    :width="960"
    :init-data="initData"
    @compare="handleCompare"
    @closed="handleCancel"
  >
    <template #header>
      <div class="custom-side-header">
        <div class="title">
          {{ sliderConfig.title }}
        </div>
      </div>
    </template>
    <template #default>
      <div class="p-20px p-b-0">
        <BkLoading :loading="sliderConfig.loading">
          <BkForm
            ref="componentFormRef"
            :label-width="180"
            :rules="rules"
            :model="formData"
          >
            <BkFormItem
              :label="t('系统')"
              required
              property="system_id"
              :error-display-type="'normal'"
            >
              <BkSelect
                v-model="formData.system_id"
                :disabled="isDisabled"
                :clearable="false"
                @selected="handleSysSelect"
              >
                <BkOption
                  v-for="option in systemList"
                  :id="option.id"
                  :key="option.id"
                  :name="option.name"
                />
              </BkSelect>
            </BkFormItem>
            <BkFormItem
              :label="t('组件名称simple')"
              required
              property="name"
              :error-display-type="'normal'"
            >
              <BkInput
                v-model="formData.name"
                :maxlength="128"
                :disabled="isDisabled"
                :placeholder="
                  t(
                    '由字母、数字、下划线（_）组成，首字符必须是字母，长度小于128个字符'
                  )
                "
              />
              <p class="tips">
                <i class="apigateway-icon icon-ag-info" />
                {{ t("组件名称在具体系统下应唯一，将用于展示组件时的标识") }}
              </p>
            </BkFormItem>
            <BkFormItem
              :label="t('组件描述simple')"
              required
              property="description"
              :error-display-type="'normal'"
            >
              <BkInput
                v-model="formData.description"
                :maxlength="128"
                :disabled="isDisabled"
                :placeholder="t('不超过128个字符')"
              />
            </BkFormItem>
            <BkFormItem
              :label="t('请求方法')"
              required
              property="method"
              :error-display-type="'normal'"
            >
              <BkSelect
                v-model="formData.method"
                :disabled="isDisabled"
                :clearable="false"
              >
                <BkOption
                  v-for="option in methodList"
                  :id="option.id"
                  :key="option.id"
                  :name="option.name"
                />
              </BkSelect>
            </BkFormItem>
            <BkFormItem
              :label="t('组件路径')"
              required
              property="path"
              :error-display-type="'normal'"
            >
              <BkInput
                v-model="formData.path"
                :disabled="isDisabled"
                :maxlength="255"
                :placeholder="
                  t(
                    '以斜杠开头，可包含斜杠、字母、数字、下划线(_)、连接符(-)，长度小于255个字符'
                  )
                "
              />
              <p class="tips">
                <i class="apigateway-icon icon-ag-info" />
                {{
                  t(
                    `可设置为'/{system_name}/{component_name}/'，例如'/host/get_host_list/'`
                  )
                }}
              </p>
            </BkFormItem>
            <BkFormItem
              :label="t('组件类代号')"
              required
              property="component_codename"
              :error-display-type="'normal'"
            >
              <BkInput
                v-model="formData.component_codename"
                :disabled="isDisabled"
                :placeholder="t('包含小写字母、数字、下划线或点号，长度小于255个字符')"
              />
              <p class="tips">
                <i class="apigateway-icon icon-ag-info" />
                {{
                  t(
                    '一般由三部分组成：“前缀(generic).小写的系统名.小写的组件类名”，例如 "generic.host.get_host_list"'
                  )
                }}
              </p>
            </BkFormItem>
            <BkFormItem
              :label="t('权限级别')"
              required
              property="permission_level"
              :error-display-type="'normal'"
            >
              <BkSelect
                v-model="formData.permission_level"
                :clearable="false"
              >
                <BkOption
                  v-for="option in levelList"
                  :id="option.id"
                  :key="option.id"
                  :name="option.name"
                />
              </BkSelect>
              <p class="tips">
                <i class="apigateway-icon icon-ag-info" />
                {{
                  t(
                    "无限制，应用不需申请组件API权限；普通权限，应用需在开发者中心申请组件API权限，审批通过后访问"
                  )
                }}
              </p>
            </BkFormItem>
            <BkFormItem
              :label="t('用户认证')"
              required
              property="verified_user_required"
              :error-display-type="'normal'"
            >
              <BkCheckbox
                v-model="formData.verified_user_required"
                true-value
                :false-value="false"
              />
              <p class="ag-tip m-t-5px">
                <i class="apigateway-icon icon-ag-info" />
                {{ t("用户认证，请求方需提供蓝鲸用户身份信息") }}
              </p>
            </BkFormItem>
            <BkFormItem :label="t('超时时长')">
              <BkInput
                v-model="formData.timeout"
                type="number"
                :max="600"
                :min="1"
                :precision="0"
              >
                <template #suffix>
                  <section class="timeout-append">
                    <div>{{ t("秒") }}</div>
                  </section>
                </template>
              </BkInput>
              <p class="tips">
                <i class="apigateway-icon icon-ag-info" />
                {{ t("未设置时使用系统的超时时长，最大600秒") }}
              </p>
            </BkFormItem>
            <BkFormItem
              v-if="formData.config_fields.length > 0"
              :label="t('组件配置')"
            >
              <RenderConfig
                ref="configRef"
                :list="formData.config_fields"
              />
            </BkFormItem>
            <BkFormItem :label="t('是否开启')">
              <BkCheckbox
                v-model="formData.is_active"
                true-value
                :false-value="false"
              />
            </BkFormItem>
          </BkForm>
        </BkLoading>
      </div>
    </template>
    <template #footer>
      <div class="p-l-90px">
        <BkButton
          theme="primary"
          class="w-88px"
          :loading="submitLoading"
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
import { cloneDeep, isEqual } from 'lodash-es';
import { Form, Message } from 'bkui-vue';
import { useAccessLog } from '@/stores';
import {
  type IComponentItem,
  addComponent,
  updateComponent,
} from '@/services/source/componentManagement';
import { type ISystemItem } from '@/services/source/system';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';
import RenderConfig from './RenderConfig.vue';

type ISliderParams = {
  isShow: boolean
  loading: boolean
  title: string
};

type IDetailData = { detailData: IComponentItem };

type FormMethod = {
  validate: () => void
  clearValidate: () => void
};

interface IProps {
  sliderParams?: ISliderParams
  detailData?: IComponentItem
  initData?: Partial<IComponentItem>
  systemList?: ISystemItem[]
}

interface Emits {
  (e: 'update:detailData', value: IDetailData)
  (e: 'update:sliderParams', value: ISliderParams)
  (e: 'sys-select',
    value: number,
    option: {
      id: number
      name: string
    })
  (e: 'confirm'): void
}

const {
  sliderParams = {},
  detailData = {},
  initData = {},
  systemList = [],
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const accessLogStore = useAccessLog();
const { t } = useI18n();

const componentFormRef = ref<InstanceType<typeof Form> & FormMethod>();
const configRef = ref<InstanceType<typeof RenderConfig> & { getData: () => void }>();
const submitLoading = ref(false);
const methodList = ref(accessLogStore.methodList);
const levelList = ref([
  {
    id: 'unlimited',
    name: t('无限制'),
  },
  {
    id: 'normal',
    name: t('普通'),
  },
]);
const rules = reactive({
  system_id: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      regex: /^[a-zA-Z][a-zA-Z0-9_]{0,128}$|^$/,
      message: t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于128个字符'),
      trigger: 'blur',
    },
  ],
  description: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  method: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  component_codename: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  path: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      regex: /^\/[\w{}/.-]*$/,
      message: t(
        '以斜杠开头，可包含斜杠、字母、数字、下划线(_)、连接符(-)，长度小于255个字符',
      ),
      trigger: 'blur',
    },
  ],
  permission_level: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  verified_user_required: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});

const sliderConfig = computed({
  get: () => sliderParams,
  set: (form) => {
    emits('update:sliderParams', form);
  },
});
const formData = computed({
  get: () => detailData,
  set: (form) => {
    emits('update:detailData', form);
  },
});
const componentId = computed(() => formData.value.id);
const isEdit = computed(() => Boolean(componentId.value));
const isDisabled = computed(() => isEdit.value && formData.value?.is_official);

const handleSysSelect = (
  value: number,
  option: {
    id: number
    name: string
  },
) => {
  emits('sys-select', value, option);
};

const handleSave = async () => {
  await componentFormRef?.value?.validate();
  const configData = configRef.value?.getData() ?? {};
  const initConfigFields = {};
  // 默认组件配置转换成标准格式
  initData?.config_fields?.forEach((item) => {
    initConfigFields[item.variable] = item.default;
  });
  // 是否存在组件配置，存在则作对比是否存在数据更新
  const isExistConfig = Object.keys(configData)?.length > 0 ? isEqual(initConfigFields, configData) : true;
  // 如果内容一致无需调用编辑接口
  if (isEdit.value && (isEqual(initData, formData.value) && isExistConfig)) {
    handleCancel();
    return;
  }
  const tempData = Object.assign({}, formData.value);
  if (!tempData.timeout) {
    tempData.timeout = null;
  }
  if (tempData.method === '*') {
    tempData.method = '';
  }
  if (tempData.config_fields?.length > 0) {
    tempData.config = configData;
    delete tempData.config_fields;
  }
  if (!isEdit.value) {
    delete tempData.config_fields;
  }
  submitLoading.value = true;
  try {
    let msg = '';
    if (!isEdit.value) {
      delete tempData.id;
      await addComponent(tempData);
      msg = t('新建成功');
    }
    else {
      await updateComponent(formData.value?.id, tempData);
      msg = t('编辑成功');
    }
    Message({
      message: msg,
      theme: 'success',
    });
    sliderConfig.value.isShow = false;
    emits('confirm');
  }
  finally {
    submitLoading.value = false;
  }
};

const handleCompare = (callback) => {
  callback(cloneDeep(formData.value));
};

const handleCancel = () => {
  componentFormRef?.value?.clearValidate();
  sliderConfig.value = Object.assign(sliderConfig.value, {
    title: '',
    isShow: false,
    loading: false,
  });
};
</script>

<style lang="scss" setup>
.apigw-access-manager-slider-cls {
  .tips {
    line-height: 24px;
    font-size: 12px;
    color: #63656e;

    i {
      position: relative;
      top: -1px;
      margin-right: 3px;
    }
  }

  .timeout-append {
    width: 50px;
    line-height: 32px;
    font-size: 12px;
    text-align: center;
  }

  .ag-tip {
    color: #63656e;
    line-height: 16px;
    clear: both;
    font-weight: normal;
    font-size: 12px;
    font-weight: 400;
  }
}
</style>
