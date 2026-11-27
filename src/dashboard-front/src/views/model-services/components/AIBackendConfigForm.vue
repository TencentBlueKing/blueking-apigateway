<template>
  <BkForm
    ref="formRef"
    :model="config"
    form-type="vertical"
  >
    <BkFormItem
      :label="t('名称')"
      property="name"
      required
      :rules="nameRules"
    >
      <BkInput
        v-model="config.name"
        :maxlength="100"
        :placeholder="t('用于区分该实例，如 gpt-4o，最长 100 个字符')"
      />
    </BkFormItem>

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
          v-for="provider in PROVIDER_OPTIONS"
          :id="provider.value"
          :key="provider.value"
          :name="provider.label"
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
      <p
        v-if="shouldHintAIBackendModelsEndpoint(config)"
        class="help-text color-#e38b02!"
      >
        {{ t('Endpoint 不以 /chat/completions 结尾，无法自动推导模型列表地址，请填写 Models Endpoint') }}
      </p>
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
        @mousedown="handleCredentialMousedown"
        @focus="handleCredentialFocus"
        @input="config.authError = ''"
      />
      <p
        v-if="credentialError"
        class="form-error-text"
      >
        {{ credentialError }}
      </p>
      <p
        v-else-if="credentialWarning"
        class="help-text color-#e38b02!"
      >
        {{ credentialWarning }}
      </p>
      <p class="help-text">
        {{ t('用于向上游 Provider 鉴权的 API Key') }}
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
          @mousedown="handleCredentialMousedown"
          @focus="handleCredentialFocus"
          @input="config.authError = ''"
        />
      </div>
      <p
        v-if="credentialError"
        class="form-error-text"
      >
        {{ credentialError }}
      </p>
      <p
        v-else-if="credentialWarning"
        class="help-text color-#e38b02!"
      >
        {{ credentialWarning }}
      </p>
      <p class="help-text">
        {{ t('作为请求头透传到模型后端，如 Authorization: Bearer sk-xxx') }}
      </p>
    </BkFormItem>

    <BkFormItem
      label="Model"
      property="model"
      :rules="formRules.model"
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
        {{ t('可留空，由调用方指定 model。') + t('填写后将强制覆盖调用方传入的 model。') }}
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
        {{ t('JSON 键值对，将合并到上游请求体，相同字段以此处为准覆盖调用方。') }}
        <span class="danger-text">{{ t('请勿在此处配置 model（在上方 Model 字段配置）') }}</span>
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

    <div class="test-row">
      <BkButton
        outline
        theme="primary"
        :loading="config.testStatus === 'testing'"
        @click="handleTest"
      >
        {{ t('连通测试') }}
      </BkButton>
      <span class="test-tip color-#979ba5"><AgIcon name="info" />{{ t('配置变更后需重新测试') }}</span>
    </div>
    <BkAlert
      v-if="testResult === 'success'"
      theme="success"
      closable
      class="mt-12px test-result-alert"
      @close="() => testResult = ''"
    >
      <template #icon>
        <div class="line-height-20px">
          <AgIcon
            name="check-circle-shape"
            class="color-#2caf5e"
          />
        </div>
      </template>
      <template #title>
        <div class="ml-8px line-height-20px">
          {{ isModelListEmpty ? t('测试成功，但未获取到可选模型，可手动填写 Model') : t('测试成功') }}
        </div>
      </template>
    </BkAlert>
    <BkAlert
      v-if="testResult === 'failed'"
      theme="danger"
      closable
      class="mt-12px test-result-alert"
      @close="() => testResult = ''"
    >
      <template #icon>
        <div class="line-height-20px">
          <AgIcon
            name="remind"
            class="color-#ea3636"
          />
        </div>
      </template>
      <template #title>
        <div class="ml-8px line-height-20px break-all">
          {{ testFailMessage ? t('测试失败，原因：{reason}', { reason: testFailMessage }) : t('测试失败') }}
        </div>
      </template>
    </BkAlert>
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
import { testBackendServiceConnection } from '@/services/source/gateway/backend';
import type { IFormMethod } from '@/types/common';
import {
  type AIBackendOptionMode,
  AI_BACKEND_ENV_VAR_TEXT,
  AI_BACKEND_SCHEME_OPTIONS,
  type IAIBackendInstanceFormData,
  buildAIBackendInstanceSnapshot,
  buildAIBackendTestParams,
  getAIBackendCredentialError,
  getAIBackendCredentialWarning,
  hasAIBackendEnvVar,
  isAIBackendSavedCredentialMask,
  isBuiltinAIBackendProvider,
  isValidAIBackendHttpUrl,
  parseAIBackendOptionsTable,
  parseAIBackendOptionsText,
  shouldHintAIBackendModelsEndpoint,
  validateAIBackendInstanceExtra,
} from '@/views/model-services/utils/ai-backend-config.ts';

interface IProps {
  apigwId: number
  backendId?: number
  stageId: number
  siblingNames?: string[]
}

const config = defineModel<IAIBackendInstanceFormData>({ required: true });

const {
  apigwId,
  backendId = 0,
  stageId,
  siblingNames = [],
} = defineProps<IProps>();

const { t } = useI18n();

const testFailMessage = ref('');
// 本次连通测试的结果，用于展示提示条；配置变更导致状态变化后自动隐藏
const testResult = ref<'' | 'success' | 'failed'>('');
// Models Endpoint 返回空列表时也算连通成功，但没有可选模型
const isModelListEmpty = ref(false);

const formRef = useTemplateRef<InstanceType<typeof Form> & IFormMethod>('formRef');

const PROVIDER_OPTIONS = [
  {
    label: 'OpenAI',
    value: 'openai',
  },
  {
    label: 'DeepSeek',
    value: 'deepseek',
  },
  {
    label: 'openai-compatible',
    value: 'openai-compatible',
  },
];

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
const envVarRule = {
  validator: (value: string) => !hasAIBackendEnvVar(value || ''),
  message: AI_BACKEND_ENV_VAR_TEXT,
  trigger: 'blur',
};
const nameRules = computed(() => [
  {
    validator: (value: string) => Boolean(value?.trim()),
    message: t('必填项'),
    trigger: 'blur',
  },
  {
    validator: (value: string) => value.trim().length <= 100,
    message: t('不能超过 {max} 个字符', { max: 100 }),
    trigger: 'blur',
  },
  {
    validator: (value: string) => {
      const name = value.trim();
      return !name || !siblingNames.includes(name);
    },
    message: t('同一环境下的实例名称不能重复'),
    trigger: 'blur',
  },
  envVarRule,
]);
const formRules = {
  provider: [{
    ...requiredRule,
    trigger: 'change',
  }],
  apiKey: [requiredRule, envVarRule],
  modelsEndpoint: [
    envVarRule,
    {
      validator: (value: string) => !value || isValidAIBackendHttpUrl(value.trim()),
      message: t('请输入合法的 HTTP/HTTPS 地址'),
      trigger: 'blur',
    },
  ],
  model: [{
    ...envVarRule,
    trigger: 'change',
  }],
};

const isBuiltinProvider = computed(() => isBuiltinAIBackendProvider(config.value.provider));

// 掩码被部分修改，或已保存实例改名、改连接身份后原掩码无法恢复时立即提示；改回原值或重新输入后自动消失
const credentialError = computed(() => config.value.authError || getAIBackendCredentialError(config.value));
const credentialWarning = computed(() => getAIBackendCredentialWarning(config.value));

// 本次聚焦是否由鼠标点击触发：只有这种情况随后会有 mouseup 把选区还原成光标
let isPointerFocus = false;
const handleCredentialMousedown = (event: MouseEvent) => {
  isPointerFocus = document.activeElement !== event.target;
};

// 聚焦到接口返回的掩码时整体选中，直接输入即可替换，避免在掩码上增删字符
const handleCredentialFocus = (event: FocusEvent) => {
  const fromPointer = isPointerFocus;
  isPointerFocus = false;
  const input = event.target as HTMLInputElement | null;
  if (!input || !isAIBackendSavedCredentialMask(config.value, input.value)) {
    return;
  }
  input.select();
  // 鼠标点击聚焦时拦截随后的这一次 mouseup，保留选区；键盘聚焦不拦截，以免影响之后的点击
  if (fromPointer) {
    input.addEventListener('mouseup', e => e.preventDefault(), { once: true });
  }
};

const endpointRules = computed(() => {
  if (isBuiltinProvider.value) {
    return [];
  }
  return [
    requiredRule,
    envVarRule,
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
  const currentSnapshot = buildAIBackendInstanceSnapshot(value);
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

watch(() => config.value.testStatus, (status) => {
  if (status !== testResult.value) {
    testResult.value = '';
  }
});

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
  return validateAIBackendInstanceExtra(config.value);
};

const handleTest = async () => {
  if (!await validate()) {
    return;
  }
  const testSnapshot = cloneDeep(buildAIBackendInstanceSnapshot(config.value));
  testFailMessage.value = '';
  config.value.testStatus = 'testing';
  config.value.testConfigSnapshot = testSnapshot;
  try {
    const result = await testBackendServiceConnection(
      apigwId,
      buildAIBackendTestParams(config.value, stageId, backendId),
    );
    if (!isEqual(testSnapshot, buildAIBackendInstanceSnapshot(config.value))) {
      config.value.testStatus = 'untested';
      config.value.testConfigSnapshot = undefined;
      Message({
        message: t('配置已变更，请重新测试'),
        theme: 'warning',
      });
      return;
    }
    config.value.models = result.models ?? [];
    isModelListEmpty.value = !config.value.models.length;
    config.value.testStatus = 'success';
    testResult.value = 'success';
  }
  catch (e) {
    config.value.testStatus = 'failed';
    testResult.value = 'failed';
    const _e = e as { error: { message: string } };
    testFailMessage.value = _e?.error?.message ?? '';
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
  color: #F59500;
}

.test-row {
  display: flex;
  margin-top: 8px;
  align-items: center;
  gap: 12px;
}

.test-tip {
  display: flex;
  font-size: 12px;
  align-items: center;
  gap: 4px;
}

// bkui 默认把关闭图标顶在内容顶部，这里让它和 20px 高的首行文字垂直居中
.test-result-alert :deep(.bk-alert-close) {
  display: flex;
  height: 20px;
  padding-top: 0;
  margin-top: 0;
  align-items: center;
}
</style>
