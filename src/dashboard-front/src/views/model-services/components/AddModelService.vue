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
  <AgSideslider
    v-model="sliderConfig.isShow"
    ext-cls="model-service-slider"
    :init-data="initData"
    render-directive="if"
    @closed="handleCancel"
    @compare="handleCompare"
  >
    <template #header>
      <div class="custom-side-header">
        <div class="title">
          {{ t(isEditing ? '编辑模型服务' : '新建模型服务') }}
        </div>
        <template v-if="isEditing">
          <span />
          <div class="subtitle">
            {{ baseInfo.name }}
          </div>
        </template>
      </div>
    </template>

    <template #default>
      <div class="slider-content">
        <BkCollapse
          v-model="activeKey"
          class="model-service-collapse"
        >
          <BkCollapsePanel name="base-info">
            <template #header>
              <div class="flex items-center panel-header">
                <AngleUpFill
                  :class="activeKey.includes('base-info') ? 'panel-header-show' : 'panel-header-hide'"
                />
                <div class="title">
                  {{ t('基础信息') }}
                </div>
              </div>
            </template>
            <template #content>
              <BkForm
                ref="baseInfoRef"
                :model="baseInfo"
                form-type="vertical"
              >
                <BkFormItem
                  :label="t('服务名称')"
                  property="name"
                  required
                  :rules="baseInfoRules.name"
                >
                  <BkInput
                    v-model="baseInfo.name"
                    :disabled="isEditing"
                    :placeholder="t('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头')"
                  />
                  <p class="help-text">
                    {{ t('模型服务唯一标识，创建后不可修改') }}
                  </p>
                </BkFormItem>
                <BkFormItem
                  :label="t('描述')"
                  property="description"
                  class="mt-12px"
                >
                  <BkInput
                    v-model="baseInfo.description"
                    :placeholder="t('请输入描述')"
                  />
                </BkFormItem>
              </BkForm>
            </template>
          </BkCollapsePanel>

          <BkCollapsePanel name="stage-config">
            <template #header>
              <div class="flex items-center panel-header">
                <AngleUpFill
                  :class="activeKey.includes('stage-config') ? 'panel-header-show' : 'panel-header-hide'"
                />
                <div class="title">
                  {{ t('各环境的服务配置') }}
                </div>
              </div>
            </template>
            <template #content>
              <BkAlert
                class="stage-config-alert"
                theme="info"
                :title="t('模型服务不支持负载均衡；创建时需配置所有环境，变更过的环境需重新连通测试')"
              />
              <BkCollapse
                v-model="activeStageIds"
                class="stage-list"
              >
                <BkCollapsePanel
                  v-for="(stage, index) in stageConfigs"
                  :key="stage.id"
                  :name="stage.id"
                >
                  <template #header>
                    <div class="stage-panel-header">
                      <AngleUpFill
                        class="stage-toggle-icon"
                        :class="activeStageIds.includes(stage.id) ? 'panel-header-show' : 'panel-header-hide'"
                      />
                      <span class="stage-name">{{ stage.name }}</span>
                      <BkTag :theme="AI_BACKEND_TEST_STATUS_META[stage.config.testStatus].theme">
                        <status-tag
                          type="filled"
                          :theme="AI_BACKEND_TEST_STATUS_META[stage.config.testStatus].tagTheme"
                          status=""
                          class="mr--4px"
                        />{{ t(AI_BACKEND_TEST_STATUS_META[stage.config.testStatus].text) }}
                      </BkTag>
                    </div>
                  </template>
                  <template #content>
                    <div class="stage-card-content">
                      <AIBackendConfigForm
                        :ref="(el: any) => setStageFormRef(el, index)"
                        v-model="stage.config"
                        :apigw-id="apigwId"
                        :backend-id="currentServiceId"
                        :stage-id="stage.id"
                      />
                    </div>
                  </template>
                </BkCollapsePanel>
              </BkCollapse>
            </template>
          </BkCollapsePanel>
        </BkCollapse>
      </div>
    </template>

    <template #footer>
      <div class="pl-40px">
        <BkButton
          class="mr-8px w-88px"
          theme="primary"
          :disabled="!canSubmit"
          :loading="isSaveLoading"
          @click="handleConfirm"
        >
          {{ t('保存') }}
        </BkButton>
        <BkButton
          class="w-88px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </AgSideslider>
</template>

<script setup lang="ts">
import {
  cloneDeep,
  isEqual,
} from 'lodash-es';
import {
  Form,
  Message,
} from 'bkui-vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import AgSideslider from '@/components/ag-sideslider/Index.vue';
import {
  createBackendService,
  getBackendServiceDetail,
  updateBackendService,
} from '@/services/source/backend-services.ts';
import { getStageList } from '@/services/source/stage';
import type { IBackendInputSLZ } from '@/services/types/body/post/gateways.ts';
import type { IAIBackendConfigOutput } from '@/services/types/responses/gateways.ts';
import type { IExtractApiReturn } from '@/services/types/utils.ts';
import { useGateway } from '@/stores';
import type { IFormMethod } from '@/types/common';
import AIBackendConfigForm from '@/views/model-services/components/AIBackendConfigForm.vue';
import {
  AI_BACKEND_TEST_STATUS_META,
  type IAIBackendConfigFormData,
  type IAIBackendConfigFormMethod,
  type ICompatibleAIBackendConfigOutput,
  type IInternalAIBackendConfigOutput,
  buildAIBackendConfig,
  createDefaultAIBackendConfigFormData,
  createEditAIBackendConfigFormData,
  getAIBackendConfigStageId,
  getAIBackendFormSnapshot,
  isAIBackendConfigTestPassed,
  isBuiltinAIBackendProvider,
} from '@/views/model-services/utils/ai-backend-config.ts';

interface IModelStageConfig {
  id: number
  name: string
  config: IAIBackendConfigFormData
}

interface IModelServiceDetail {
  id: number
  name: string
  description: string | null
  kind: 'ai'
  type: 'http'
  configs: (IAIBackendConfigOutput | IInternalAIBackendConfigOutput)[]
}

interface IEmits {
  done: []
}

type IStage = IExtractApiReturn<typeof getStageList>[number];

const emit = defineEmits<IEmits>();

const { t } = useI18n();
const gatewayStore = useGateway();

const activeKey = ref(['base-info', 'stage-config']);
const activeStageIds = ref<number[]>([]);
const baseInfo = ref({
  name: '',
  description: '',
});
const stageConfigs = ref<IModelStageConfig[]>([]);
const stageFormRefs = ref<Array<IAIBackendConfigFormMethod | null>>([]);
const initData = ref<object>();
const isSaveLoading = ref(false);
const currentServiceId = ref(0);
const sliderConfig = reactive({
  isShow: false,
});

const baseInfoEl = useTemplateRef<InstanceType<typeof Form> & IFormMethod>('baseInfoRef');

const nameReg = /^[a-zA-Z][a-zA-Z0-9-]{0,19}$/;
const baseInfoRules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => nameReg.test(value),
      message: t('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头'),
      trigger: 'blur',
    },
  ],
};

const apigwId = computed(() => gatewayStore.apigwId);
const isEditing = computed(() => Boolean(currentServiceId.value));
const canSubmit = computed(() => {
  return nameReg.test(baseInfo.value.name)
    && stageConfigs.value.length > 0
    && stageConfigs.value.every((stage) => {
      const { config } = stage;
      const hasEndpoint = config.provider !== 'openai-compatible' || Boolean(config.endpoint.trim());
      const hasApiKey = !isBuiltinAIBackendProvider(config.provider) || Boolean(config.apiKey.trim());
      return hasEndpoint && hasApiKey && isAIBackendConfigTestPassed(config, stage.id);
    });
});

const setStageFormRef = (el: IAIBackendConfigFormMethod, index: number) => {
  if (el) {
    stageFormRefs.value[index] = el;
  }
};

const getSnapshot = () => ({
  baseInfo: baseInfo.value,
  stageConfigs: stageConfigs.value.map(stage => ({
    id: stage.id,
    name: stage.name,
    config: getAIBackendFormSnapshot(stage.config),
  })),
});

const validateForms = async () => {
  try {
    await baseInfoEl.value?.validate();
  }
  catch {
    return false;
  }

  for (let index = 0; index < stageFormRefs.value.length; index++) {
    const form = stageFormRefs.value[index];
    if (form && !await form.validate()) {
      const currentStageId = stageConfigs.value[index]?.id;
      if (currentStageId && !activeStageIds.value.includes(currentStageId)) {
        activeStageIds.value.push(currentStageId);
      }
      return false;
    }
  }
  return true;
};

const handleConfirm = async () => {
  if (!await validateForms()) {
    return;
  }
  if (isEditing.value && isEqual(initData.value, getSnapshot())) {
    handleCancel();
    return;
  }

  const params: IBackendInputSLZ = {
    name: baseInfo.value.name,
    description: baseInfo.value.description,
    kind: 'ai',
    type: 'http',
    configs: stageConfigs.value.map(stage => buildAIBackendConfig(stage.config, stage.id)),
  };
  isSaveLoading.value = true;
  try {
    if (isEditing.value) {
      await updateBackendService(apigwId.value, currentServiceId.value, params);
    }
    else {
      await createBackendService(apigwId.value, params);
    }
    Message({
      message: t(isEditing.value ? '更新成功' : '新建成功'),
      theme: 'success',
    });
    sliderConfig.isShow = false;
    emit('done');
  }
  finally {
    isSaveLoading.value = false;
  }
};

const handleCancel = () => {
  sliderConfig.isShow = false;
  stageFormRefs.value = [];
  baseInfoEl.value?.clearValidate();
};

const handleCompare = (callback: (data: object) => void) => {
  callback(cloneDeep(getSnapshot()));
};

const createDefaultStageConfig = (stage: IStage): IModelStageConfig => ({
  id: stage.id,
  name: stage.name,
  config: createDefaultAIBackendConfigFormData(),
});

const createDetailStageConfig = (
  config: ICompatibleAIBackendConfigOutput,
  stage: IStage,
  isClone = false,
): IModelStageConfig => {
  const formConfig = createEditAIBackendConfigFormData(config, stage.id);
  if (isClone) {
    formConfig.apiKey = '';
    formConfig.testStatus = 'untested';
    formConfig.testConfigSnapshot = undefined;
    formConfig.initialTestConfigSnapshot = undefined;
  }
  return {
    id: stage.id,
    name: stage.name,
    config: formConfig,
  };
};

const initializeAndShow = async (serviceId?: number, isClone = false) => {
  const detailServiceId = serviceId || 0;
  currentServiceId.value = isClone ? 0 : detailServiceId;
  stageFormRefs.value = [];
  activeKey.value = ['base-info', 'stage-config'];
  const stages = await getStageList(apigwId.value);
  activeStageIds.value = stages.map(stage => stage.id);
  if (detailServiceId) {
    const detail = await getBackendServiceDetail(
      apigwId.value,
      detailServiceId,
    ) as IModelServiceDetail;
    const cloneSuffix = isClone ? '-clone' : '';
    baseInfo.value = {
      name: `${detail.name}${cloneSuffix}`,
      description: `${detail.description || ''}${cloneSuffix}`,
    };
    const configMap = new Map(detail.configs.map(config => [getAIBackendConfigStageId(config), config]));
    stageConfigs.value = stages.map((stage) => {
      const config = configMap.get(Number(stage.id));
      return config
        ? createDetailStageConfig(config, stage, isClone)
        : createDefaultStageConfig(stage);
    });
  }
  else {
    baseInfo.value = {
      name: '',
      description: '',
    };
    stageConfigs.value = stages.map(createDefaultStageConfig);
  }
  initData.value = cloneDeep(getSnapshot());
  sliderConfig.isShow = true;
};

const show = (serviceId?: number) => {
  return initializeAndShow(serviceId);
};

const showClone = (serviceId: number) => {
  return initializeAndShow(serviceId, true);
};

defineExpose({
  show,
  showClone,
});
</script>

<style lang="scss" scoped>
.model-service-slider {

  :deep(.bk-modal-content) {
    overflow-y: auto;
    scrollbar-gutter: stable;
  }

  :deep(.bk-sideslider-footer) {
    margin-top: 0;
  }

  .title {
    margin-left: 8px;
    font-size: 14px;
    font-weight: 700;
    color: #323237;
  }

  .slider-content {
    padding: 20px 34px 32px 40px;

    .bk-form-label {
      line-height: 22px;
    }
  }

  .model-service-collapse {

    .panel-header {
      margin-bottom: 16px;
      font-size: 14px;
      font-weight: 700;
      color: #313238;
      cursor: pointer;
    }

    .panel-header-show {
      transform: rotate(0deg);
    }

    .panel-header-hide {
      transform: rotate(-90deg);
    }

    :deep(.bk-collapse-content) {
      padding: 0;
    }
  }

  .stage-config-alert {
    margin: 8px 0 12px;
  }

  .stage-list {

    :deep(.bk-collapse-item) {
      margin-bottom: 24px;
      background: #f5f7fb;

      .bk-collapse-header {
        height: 40px;
        line-height: 40px;
        background: #f0f1f5;
      }

      .bk-collapse-content {
        padding: 0 32px;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  .stage-panel-header {
    display: flex;
    width: 100%;
    height: 40px;
    padding: 0 16px;
    color: #4d4f56;
    background: #eaebf0;
    align-items: center;
    box-sizing: border-box;

    .stage-toggle-icon {
      margin-right: 8px;
      transition: transform .2s;
    }

    .stage-name {
      font-weight: 700;
      flex: 1;
    }
  }

  .stage-card-content {
    padding: 20px 0 24px;
    background: #f5f7fa;
  }

  .help-text {
    margin-top: 4px;
    font-size: 12px;
    line-height: 20px;
    color: #979ba5;
  }
}
</style>
