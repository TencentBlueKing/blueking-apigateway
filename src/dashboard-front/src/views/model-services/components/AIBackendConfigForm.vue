<template>
  <BkForm
    ref="formRef"
    :model="config"
    form-type="vertical"
  >
    <BkFormItem
      label="Provider"
      property="provider"
      required
      :rules="formRules.provider"
    >
      <BkSelect
        v-model="config.provider"
        :clearable="false"
        :filterable="false"
        @change="handleProviderChange"
      >
        <BkOption
          v-for="provider in AI_BACKEND_PROVIDER_OPTIONS"
          :id="provider"
          :key="provider"
          :name="provider"
        />
      </BkSelect>
      <p class="help-text">
        {{ t('支持 OpenAI、DeepSeek 和 OpenAI Compatible Provider') }}
      </p>
    </BkFormItem>

    <BkFormItem
      label="Endpoint"
      property="endpoint"
      :required="config.provider === 'openai-compatible'"
      :rules="endpointRules"
    >
      <BkInput
        v-model="config.endpoint"
        :disabled="isBuiltinProvider"
        :placeholder="t('格式如：api.example.com/v1/chat/completions')"
      >
        <template #prefix>
          <BkSelect
            v-model="config.endpointScheme"
            class="endpoint-scheme"
            :clearable="false"
            :filterable="false"
            :disabled="isBuiltinProvider"
          >
            <BkOption
              v-for="scheme in AI_BACKEND_SCHEME_OPTIONS"
              :id="scheme"
              :key="scheme"
              :name="scheme"
            />
          </BkSelect>
          <div class="slash">
            ://
          </div>
        </template>
      </BkInput>
      <p class="help-text">
        {{ t('模型后端的完整 Chat Completions 地址') }}
      </p>
    </BkFormItem>

    <BkFormItem
      label="Models Endpoint"
      property="modelsEndpoint"
      :rules="formRules.modelsEndpoint"
    >
      <BkInput
        v-model="config.modelsEndpoint"
        :disabled="isBuiltinProvider"
        :placeholder="t('可选，如 https://api.example.com/v1/models，用于拉取可用模型列表')"
      />
    </BkFormItem>

    <BkFormItem
      v-if="isBuiltinProvider"
      :label="t('API Key')"
      property="apiKey"
      required
      :rules="formRules.apiKey"
    >
      <BkInput
        v-model="config.apiKey"
        :placeholder="t('请输入 API Key')"
      />
      <p class="help-text">
        {{ t('内置 Provider 使用 API Key 进行认证') }}
      </p>
    </BkFormItem>

    <BkFormItem
      v-else
      :label="t('认证 Header')"
    >
      <div class="auth-header-row">
        <BkInput
          v-model="config.authHeaderKey"
          :placeholder="t('Header 名，如 Authorization')"
          @input="config.authError = ''"
        />
        <BkInput
          v-model="config.authHeaderValue"
          :placeholder="t('Header 值，如 Bearer sk-xxxxxx')"
          @input="config.authError = ''"
        />
      </div>
      <p
        v-if="config.authError"
        class="form-error-text"
      >
        {{ config.authError }}
      </p>
      <p class="help-text">
        {{ t('作为请求头透传到模型后端，如 Authorization: Bearer sk-xxx') }}
      </p>
    </BkFormItem>

    <BkFormItem
      label="Model"
      property="model"
    >
      <BkSelect
        v-model="config.model"
        allow-create
        :placeholder="t('请输入或选择模型')"
      >
        <BkOption
          v-for="model in modelOptions"
          :id="model"
          :key="model"
          :name="model"
        />
      </BkSelect>
      <p class="help-text">
        {{ t('留空时由调用方在请求体中指定 model') }}
      </p>
    </BkFormItem>

    <BkFormItem label="Model Options">
      <BkRadioGroup
        v-model="config.optionMode"
        type="capsule"
        class="option-mode"
        @change="handleOptionModeChange"
      >
        <BkRadioButton label="table">
          <span class="flex items-center gap-2px">
            <AgIcon name="cardd" />
            <span>{{ t('表格模式') }}</span>
          </span>
        </BkRadioButton>
        <BkRadioButton label="text">
          <span class="flex items-center gap-2px">
            <AgIcon name="geshihua" />
            <span>{{ t('文本模式') }}</span>
          </span>
        </BkRadioButton>
      </BkRadioGroup>

      <div
        v-if="config.optionMode === 'table'"
        class="option-table"
      >
        <div
          v-for="(option, optionIndex) in config.optionRows"
          :key="optionIndex"
          class="option-row"
        >
          <BkInput
            v-model="option.key"
            :placeholder="t('参数名')"
            @input="config.optionsError = ''"
          />
          <BkInput
            v-model="option.value"
            :placeholder="t('参数值')"
            @input="config.optionsError = ''"
          />
          <AgIcon
            name="minus-circle-shape"
            class="hover:color-#63656e hover:cursor-pointer"
            :class="{ 'color-#dcdee5! cursor-not-allowed!': config.optionRows.length === 1 }"
            @click="() => handleDeleteOption(optionIndex)"
          />
        </div>
        <BkButton
          text
          theme="primary"
          @click="handleAddOption"
        >
          <AgIcon
            name="plus-circle-shape"
            class="mr-4px"
          />
          {{ t('添加') }}
        </BkButton>
      </div>
      <BkInput
        v-else
        v-model="config.optionsText"
        class="options-editor"
        type="textarea"
        @input="handleOptionsTextInput"
      />
      <p class="help-text">
        {{ t('附加到请求体的参数字典，JSON 格式，会合并到上游请求体') }}，
        <span class="danger-text">{{ t('不包含 model 字段') }}</span>
      </p>
      <p
        v-if="config.optionsError"
        class="help-text color-#ea3636!"
      >
        <AgIcon
          name="exclamation-circle-fill"
          class="mr-4px"
        />
        <span>{{ t('校验失败') }}: <span>{{ config.optionsError }}</span></span>
      </p>
    </BkFormItem>

    <BkFormItem
      :label="t('超时时间')"
      property="timeout"
      required
      :rules="formRules.timeout"
      class="timeout-item"
    >
      <BkInput
        v-model="config.timeout"
        type="number"
        :min="1"
        :max="300"
        :precision="0"
      >
        <template #suffix>
          <span class="timeout-unit">{{ t('秒') }}</span>
        </template>
      </BkInput>
      <p class="help-text">
        {{ t('取值范围 1-300 秒，默认 300') }}
      </p>
    </BkFormItem>

    <div class="test-row">
      <BkButton
        outline
        theme="primary"
        :loading="config.testStatus === 'testing'"
        @click="handleTest"
      >
        {{ t('连通测试') }}
      </BkButton>
      <span
        v-if="config.testStatus === 'success'"
        class="test-tip color-#299e56"
      ><AgIcon name="check-circle-shape" />{{ t('连通正常') }}</span>
      <span
        v-else-if="config.testStatus === 'failed'"
        class="test-tip color-#ea3636"
      ><AgIcon name="close-circle-filled" />{{ t('连通失败') }}</span>
      <span
        v-else
        class="test-tip color-#979ba5"
      ><AgIcon name="info" />{{ t('配置变更后需重新测试') }}</span>
    </div>
  </BkForm>
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
import { testBackendServiceConnection } from '@/services/source/backend-services.ts';
import type { IBackendTestConnectionInputSLZ } from '@/services/types/body/post/gateways.ts';
import type { IFormMethod } from '@/types/common';
import {
  type AIBackendOptionMode,
  AI_BACKEND_PROVIDER_OPTIONS,
  AI_BACKEND_SCHEME_OPTIONS,
  type IAIBackendConfigFormData,
  buildAIBackendConfig,
  isBuiltinAIBackendProvider,
  isValidAIBackendHttpUrl,
  parseAIBackendOptionsTable,
  parseAIBackendOptionsText,
  validateAIBackendConfigExtra,
} from '@/views/model-services/utils/ai-backend-config.ts';

interface IProps {
  apigwId: number
  backendId?: number
  stageId: number
}

const config = defineModel<IAIBackendConfigFormData>({ required: true });

const {
  apigwId,
  backendId = 0,
  stageId,
} = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef<InstanceType<typeof Form> & IFormMethod>('formRef');

const PROVIDER_ENDPOINT = {
  openai: {
    endpoint: 'api.openai.com/v1/chat/completions',
    modelsEndpoint: 'https://api.openai.com/v1/models',
  },
  deepseek: {
    endpoint: 'api.deepseek.com/chat/completions',
    modelsEndpoint: 'https://api.deepseek.com/models',
  },
};

const requiredRule = {
  required: true,
  message: t('必填项'),
  trigger: 'blur',
};
const formRules = {
  provider: [{
    ...requiredRule,
    trigger: 'change',
  }],
  apiKey: [requiredRule],
  modelsEndpoint: [{
    validator: (value: string) => !value || isValidAIBackendHttpUrl(value.trim()),
    message: t('请输入合法的 HTTP/HTTPS 地址'),
    trigger: 'blur',
  }],
  timeout: [
    requiredRule,
    {
      validator: (value: number) => Number(value) >= 1 && Number(value) <= 300,
      message: t('超时时间不能小于1且不能大于300'),
      trigger: 'change',
    },
  ],
};

const isBuiltinProvider = computed(() => isBuiltinAIBackendProvider(config.value.provider));
const endpointRules = computed(() => {
  if (isBuiltinProvider.value) {
    return [];
  }
  return [
    requiredRule,
    {
      validator: (value: string) => isValidAIBackendHttpUrl(
        `${config.value.endpointScheme}://${value.trim()}`,
      ),
      message: t('请输入合法的 HTTP/HTTPS 地址'),
      trigger: 'blur',
    },
  ];
});
const modelOptions = computed(() => [...new Set([
  config.value.model,
  ...config.value.models,
].filter(Boolean))]);

watch(config, (value) => {
  if (value.testStatus === 'testing') {
    return;
  }
  const currentSnapshot = buildAIBackendConfig(value, stageId);
  const initialSnapshot = value.initialTestConfigSnapshot;
  if (value.testStatus === 'untested' && initialSnapshot && isEqual(initialSnapshot, currentSnapshot)) {
    value.testStatus = 'success';
    value.testConfigSnapshot = cloneDeep(initialSnapshot);
    return;
  }
  if (value.testConfigSnapshot && !isEqual(value.testConfigSnapshot, currentSnapshot)) {
    value.testStatus = 'untested';
    value.testConfigSnapshot = undefined;
  }
}, { deep: true });

const formatOptionValue = (value: unknown) => {
  return typeof value === 'string' ? value : JSON.stringify(value) ?? '';
};

const handleProviderChange = async (provider: string) => {
  config.value.endpoint = '';
  config.value.modelsEndpoint = '';
  config.value.apiKey = '';
  config.value.authHeaderKey = '';
  config.value.authHeaderValue = '';
  config.value.authError = '';
  config.value.models = [];
  await nextTick();
  formRef.value?.clearValidate();
  if (provider === 'openai') {
    const { endpoint, modelsEndpoint } = PROVIDER_ENDPOINT.openai;
    config.value.endpoint = endpoint;
    config.value.modelsEndpoint = modelsEndpoint;
    config.value.endpointScheme = 'https';
  }
  else if (provider === 'deepseek') {
    const { endpoint, modelsEndpoint } = PROVIDER_ENDPOINT.deepseek;
    config.value.endpoint = endpoint;
    config.value.modelsEndpoint = modelsEndpoint;
    config.value.endpointScheme = 'https';
  }
};

const handleOptionsTextInput = (value: string) => {
  config.value.optionsError = parseAIBackendOptionsText(value).error;
};

const handleOptionModeChange = (mode: AIBackendOptionMode) => {
  config.value.optionsError = '';
  if (mode === 'table') {
    const result = parseAIBackendOptionsText(config.value.optionsText);
    if (result.error) {
      config.value.optionsError = result.error;
      config.value.optionMode = 'text';
      return;
    }
    config.value.optionRows = Object.entries(result.data).map(([key, value]) => ({
      key,
      value: formatOptionValue(value),
    }));
    if (!config.value.optionRows.length) {
      config.value.optionRows = [{
        key: '',
        value: '',
      }];
    }
    return;
  }

  const result = parseAIBackendOptionsTable(config.value.optionRows);
  if (result.error) {
    config.value.optionsError = result.error;
    config.value.optionMode = 'table';
    return;
  }
  config.value.optionsText = JSON.stringify(result.data, null, 2);
};

const handleAddOption = () => {
  config.value.optionRows.push({
    key: '',
    value: '',
  });
};

const handleDeleteOption = (index: number) => {
  if (config.value.optionRows.length > 1) {
    config.value.optionRows.splice(index, 1);
  }
};

const validate = async () => {
  try {
    await formRef.value?.validate();
  }
  catch {
    return false;
  }
  return validateAIBackendConfigExtra(config.value);
};

const handleTest = async () => {
  if (!await validate()) {
    return;
  }
  const testSnapshot = cloneDeep(buildAIBackendConfig(config.value, stageId));
  config.value.testStatus = 'testing';
  config.value.testConfigSnapshot = testSnapshot;
  const params: IBackendTestConnectionInputSLZ = {
    config: buildAIBackendConfig(config.value, stageId),
  };
  if (backendId && stageId) {
    params.backend_id = backendId;
  }
  try {
    const result = await testBackendServiceConnection(apigwId, params);
    if (!isEqual(testSnapshot, buildAIBackendConfig(config.value, stageId))) {
      config.value.testStatus = 'untested';
      config.value.testConfigSnapshot = undefined;
      Message({
        message: t('配置已变更，请重新测试'),
        theme: 'warning',
      });
      return;
    }
    config.value.models = result.models;
    config.value.testStatus = 'success';
    Message({
      message: t('连通测试成功'),
      theme: 'success',
    });
  }
  catch {
    config.value.testStatus = 'failed';
    Message({
      message: t('连通测试失败'),
      theme: 'error',
    });
  }
};

defineExpose({ validate });
</script>

<style lang="scss" scoped>
.help-text {
  margin-top: 4px;
  font-size: 12px;
  line-height: 20px;
  color: #979ba5;
}

.form-error-text {
  margin-top: 4px;
  font-size: 12px;
  color: #ea3636;
}

.endpoint-scheme {
  width: 80px;
  overflow: hidden;

  :deep(.bk-input) {
    border: none;
    border-right: 1px solid #c4c6cc;
    box-shadow: none;
  }
}

.slash {
  padding: 0 10px;
  color: #63656e;
  background: #fafbfd;
  border-right: 1px solid #c4c6cc;
}

.auth-header-row {
  display: grid;
  grid-template-columns: 1fr 1.6fr;
  gap: 8px;
}

.option-mode {
  margin-bottom: 8px;
}

.option-table {
  padding: 12px;
  background: #fff;
  border: 1px solid #dcdee5;
}

.option-row {
  display: grid;
  margin-bottom: 8px;
  grid-template-columns: 1fr 1.6fr 28px;
  gap: 8px;
  align-items: center;
}

.options-editor {

  :deep(textarea) {
    min-height: 88px;
    font-family: Consolas, Monaco, monospace;
  }
}

.danger-text {
  color: #ea3636;
}

.timeout-item {
  width: 180px;
}

.timeout-unit {
  padding: 0 8px;
  border-left: 1px solid #c4c6cc;
}

.test-row {
  display: flex;
  margin-top: 24px;
  align-items: center;
  gap: 12px;
}

.test-tip {
  display: flex;
  font-size: 12px;
  align-items: center;
  gap: 4px;
}
</style>
