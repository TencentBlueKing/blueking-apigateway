<template>
  <div class="ai-instances-form">
    <div class="section-title">
      {{ t('模型实例') }}
      <span class="section-desc">
        {{ t('主实例分担流量；备用实例平时不接收请求，所有主实例都失败后才启用') }}
      </span>
    </div>

    <div
      v-for="(instance, index) in config.instances"
      :key="instance.uid"
      class="instance-card"
      :class="{ 'is-failed': getAIBackendInstanceTestStatus(instance) === 'failed' }"
    >
      <div
        class="instance-header"
        @click="() => toggleInstance(instance.uid)"
      >
        <AngleUpFill
          class="toggle-icon"
          :class="expandedUids.includes(instance.uid) ? 'is-expanded' : 'is-collapsed'"
        />
        <BkTag
          size="small"
          :theme="instance.role === 'primary' ? 'info' : 'warning'"
        >
          {{ instance.role === 'primary' ? t('主') : t('备') }}
        </BkTag>
        <span class="instance-name">{{ instance.name.trim() || getInstanceLabel(index) }}</span>
        <span class="instance-summary">{{ getInstanceSummary(instance) }}</span>
        <BkTag
          size="small"
          class="instance-status"
          :theme="AI_BACKEND_TEST_STATUS_META[getAIBackendInstanceTestStatus(instance)].theme"
        >
          {{ t(AI_BACKEND_TEST_STATUS_META[getAIBackendInstanceTestStatus(instance)].text) }}
        </BkTag>
        <span
          v-bk-tooltips="{
            content: t('至少保留一个主实例'),
            disabled: canRemove(instance),
          }"
          class="instance-remove"
          :class="{ 'is-disabled': !canRemove(instance) }"
          @click.stop="() => handleRemove(index)"
        >
          <AgIcon name="delet" />
        </span>
      </div>
      <div
        v-show="expandedUids.includes(instance.uid)"
        class="instance-body"
      >
        <AIBackendConfigForm
          :ref="(el: any) => setInstanceFormRef(el, instance.uid)"
          v-model="config.instances[index]"
          :apigw-id="apigwId"
          :backend-id="backendId"
          :stage-id="stageId"
          :sibling-names="getSiblingNames(instance.uid)"
        />
      </div>
    </div>

    <div class="add-row">
      <BkButton
        text
        theme="primary"
        @click="() => handleAdd('primary')"
      >
        <AgIcon
          name="plus-circle-shape"
          class="mr-4px"
        />
        {{ t('添加主实例') }}
      </BkButton>
      <span
        v-bk-tooltips="{
          content: t('最多添加 {count} 个备用实例', { count: AI_BACKEND_MAX_BACKUP_COUNT }),
          disabled: canAddBackup,
        }"
      >
        <BkButton
          text
          theme="primary"
          :disabled="!canAddBackup"
          @click="() => handleAdd('backup')"
        >
          <AgIcon
            name="plus-circle-shape"
            class="mr-4px"
          />
          {{ t('添加备用实例') }}
        </BkButton>
      </span>
    </div>

    <p
      v-if="config.instances.length === 1"
      class="traffic-hint"
    >
      <AgIcon
        name="info"
        class="mr-4px"
      />
      {{ t('添加主实例可做负载均衡，添加备用实例可做故障切换') }}
    </p>

    <BkForm
      ref="commonFormRef"
      :model="config"
      form-type="vertical"
      class="common-form"
    >
      <div
        v-if="showFallback"
        class="traffic-block"
      >
        <div class="traffic-title">
          {{ t('多实例配置') }}
          <span class="section-desc">{{ t('决定请求在以上实例间如何分配') }}</span>
        </div>
        <BkFormItem
          v-if="showBalancer"
          :label="t('负载均衡算法')"
        >
          <BkRadioGroup
            v-model="config.balancerAlgorithm"
            class="balancer-radio-group"
          >
            <BkRadio
              v-for="(text, algorithm) in AI_BACKEND_BALANCER_TEXT"
              :key="algorithm"
              :label="algorithm"
            >
              {{ t(text) }}<span class="radio-desc">（{{ t(AI_BACKEND_BALANCER_DESC[algorithm]) }}）</span>
            </BkRadio>
          </BkRadioGroup>
          <BkAlert
            v-if="config.balancerAlgorithm === 'chash'"
            theme="warning"
            closable
            class="mt-8px chash-alert"
          >
            <template #icon>
              <div class="line-height-20px">
                <AgIcon
                  name="remind"
                  class="color-#e38b02"
                />
              </div>
            </template>
            <template #title>
              <div class="ml-8px line-height-20px color-#e38b02">
                {{ t('使用此模型服务的资源必须开启「应用认证」，否则一致性哈希无法生效') }}
              </div>
            </template>
          </BkAlert>
        </BkFormItem>

        <BkFormItem
          v-if="showFallback"
          :label="t('故障切换条件')"
          :required="hasBackup"
        >
          <BkCheckboxGroup
            v-model="config.fallbackStrategy"
            @change="() => config.strategyError = ''"
          >
            <BkCheckbox
              v-for="(text, item) in AI_BACKEND_FALLBACK_TEXT"
              :key="item"
              :label="item"
            >
              {{ t(text) }}
            </BkCheckbox>
          </BkCheckboxGroup>
          <p
            v-if="config.strategyError"
            class="form-error-text"
          >
            {{ config.strategyError }}
          </p>
          <p class="help-text">
            {{ t('实例返回所选错误时自动切换：先切到其他主实例，所有主实例都失败后才切到备用实例') }}
          </p>
        </BkFormItem>
      </div>

      <BkFormItem
        :label="t('超时时间')"
        property="timeout"
        required
        :rules="timeoutRules"
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
          {{ t('对本环境所有实例生效，取值范围 1-300 秒，默认 300') }}
        </p>
      </BkFormItem>
    </BkForm>
  </div>
</template>

<script setup lang="ts">
import { Form } from 'bkui-vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import type { IFormMethod } from '@/types/common';
import AIBackendConfigForm from '@/views/model-services/components/AIBackendConfigForm.vue';
import {
  type AIBackendInstanceRole,
  AI_BACKEND_BALANCER_DESC,
  AI_BACKEND_BALANCER_TEXT,
  AI_BACKEND_FALLBACK_TEXT,
  AI_BACKEND_MAX_BACKUP_COUNT,
  AI_BACKEND_PROVIDER_LABEL,
  AI_BACKEND_TEST_STATUS_META,
  type IAIBackendConfigFormData,
  type IAIBackendConfigFormMethod,
  type IAIBackendInstanceFormData,
  createDefaultAIBackendInstanceFormData,
  getAIBackendInstanceCount,
  getAIBackendInstanceLabel,
  getAIBackendInstanceTarget,
  getAIBackendInstanceTestStatus,
  isAIBackendInstanceTestPassed,
  shouldShowAIBackendBalancer,
  shouldShowAIBackendFallback,
  validateAIBackendStrategy,
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

const instanceFormRefs = new Map<string, IAIBackendConfigFormMethod>();
const getDefaultExpandedUids = () => config.value.instances
  .filter(instance => config.value.instances.length === 1 || !isAIBackendInstanceTestPassed(instance))
  .map(instance => instance.uid);

const expandedUids = ref<string[]>(getDefaultExpandedUids());

watch(config, () => {
  expandedUids.value = getDefaultExpandedUids();
});

const commonFormRef = useTemplateRef<InstanceType<typeof Form> & IFormMethod>('commonFormRef');

const timeoutRules = [
  {
    required: true,
    message: t('必填项'),
    trigger: 'blur',
  },
  {
    validator: (value: number) => Number(value) >= 1 && Number(value) <= 300,
    message: t('超时时间不能小于1且不能大于300'),
    trigger: 'change',
  },
];

const primaryCount = computed(() => getAIBackendInstanceCount(config.value, 'primary'));
const hasBackup = computed(() => getAIBackendInstanceCount(config.value, 'backup') > 0);
const canAddBackup = computed(() => {
  return getAIBackendInstanceCount(config.value, 'backup') < AI_BACKEND_MAX_BACKUP_COUNT;
});
const showBalancer = computed(() => shouldShowAIBackendBalancer(config.value));
const showFallback = computed(() => shouldShowAIBackendFallback(config.value));

const setInstanceFormRef = (el: IAIBackendConfigFormMethod | null, uid: string) => {
  if (el) {
    instanceFormRefs.set(uid, el);
  }
  else {
    instanceFormRefs.delete(uid);
  }
};

const getInstanceLabel = (index: number) => getAIBackendInstanceLabel(config.value, index);

const getSiblingNames = (uid: string) => config.value.instances
  .filter(item => item.uid !== uid)
  .map(item => item.name.trim())
  .filter(Boolean);

const getInstanceSummary = (instance: IAIBackendInstanceFormData) => {
  return [AI_BACKEND_PROVIDER_LABEL[instance.provider], getAIBackendInstanceTarget(instance)]
    .filter(Boolean)
    .join(' · ');
};

const canRemove = (instance: IAIBackendInstanceFormData) => {
  return instance.role === 'backup' || primaryCount.value > 1;
};

const toggleInstance = (uid: string) => {
  const index = expandedUids.value.indexOf(uid);
  if (index > -1) {
    expandedUids.value.splice(index, 1);
  }
  else {
    expandedUids.value.push(uid);
  }
};

const handleAdd = (role: AIBackendInstanceRole) => {
  if (role === 'backup' && !canAddBackup.value) {
    return;
  }
  const instance = createDefaultAIBackendInstanceFormData(role);
  const firstBackupIndex = config.value.instances.findIndex(item => item.role === 'backup');
  if (role === 'primary' && firstBackupIndex > -1) {
    config.value.instances.splice(firstBackupIndex, 0, instance);
  }
  else {
    config.value.instances.push(instance);
  }
  expandedUids.value.push(instance.uid);
};

const handleRemove = (index: number) => {
  const instance = config.value.instances[index];
  if (!canRemove(instance)) {
    return;
  }
  config.value.instances.splice(index, 1);
  expandedUids.value = expandedUids.value.filter(uid => uid !== instance.uid);
  if (!hasBackup.value) {
    config.value.strategyError = '';
  }
};

const validate = async () => {
  for (const instance of config.value.instances) {
    const form = instanceFormRefs.get(instance.uid);
    if (form && !await form.validate()) {
      if (!expandedUids.value.includes(instance.uid)) {
        expandedUids.value.push(instance.uid);
      }
      return false;
    }
  }
  try {
    await commonFormRef.value?.validate();
  }
  catch {
    return false;
  }
  return validateAIBackendStrategy(config.value);
};

const expandUntested = () => {
  config.value.instances
    .filter(instance => !isAIBackendInstanceTestPassed(instance) && !expandedUids.value.includes(instance.uid))
    .forEach(instance => expandedUids.value.push(instance.uid));
};

defineExpose({
  validate,
  expandUntested,
});
</script>

<style lang="scss" scoped>
.ai-instances-form {

  .section-title {
    margin-bottom: 12px;
    font-size: 14px;
    font-weight: 700;
    line-height: 22px;
    color: #313238;
  }

  .section-desc {
    margin-left: 8px;
    font-size: 12px;
    font-weight: 400;
    color: #979ba5;
  }

  .instance-card {
    margin-bottom: 12px;
    background: #fff;
    border: 1px solid #dcdee5;
    border-radius: 2px;

    &.is-failed {
      border-color: #ea3636;
    }
  }

  .instance-header {
    display: flex;
    height: 40px;
    padding: 0 16px;
    cursor: pointer;
    align-items: center;
    gap: 8px;

    .toggle-icon {
      color: #979ba5;
      transition: transform .2s;

      &.is-collapsed {
        transform: rotate(-90deg);
      }
    }

    .instance-name {
      font-weight: 700;
      color: #313238;
      white-space: nowrap;
    }

    .instance-summary {
      overflow: hidden;
      font-size: 12px;
      color: #979ba5;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1;
    }

    .instance-status {
      flex-shrink: 0;
    }

    .instance-remove {
      display: flex;
      font-size: 16px;
      color: #979ba5;
      align-items: center;

      &:hover {
        color: #ea3636;
      }

      &.is-disabled {
        color: #dcdee5;
        cursor: not-allowed;
      }
    }
  }

  .instance-body {
    padding: 16px 24px 20px;
    border-top: 1px solid #f0f1f5;
  }

  .add-row {
    display: flex;
    align-items: center;
    gap: 24px;
  }

  .traffic-hint {
    display: flex;
    margin-top: 8px;
    font-size: 12px;
    line-height: 20px;
    color: #979ba5;
    align-items: center;
  }

  .common-form {
    margin-top: 16px;

    :deep(.bk-form-item) {
      margin-bottom: 16px;
    }
  }

  .traffic-block {
    padding: 16px 24px 0;
    margin-bottom: 24px;
    background: #fff;
    border: 1px solid #dcdee5;
    border-radius: 2px;
  }

  .balancer-radio-group {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;

    :deep(.bk-radio ~ .bk-radio) {
      margin-left: 0;
    }
  }

  .radio-desc {
    color: #979ba5;
  }

  // bkui 默认把关闭图标顶在内容顶部，这里让它和 20px 高的首行文字垂直居中
  .chash-alert :deep(.bk-alert-close) {
    display: flex;
    height: 20px;
    padding-top: 0;
    margin-top: 0;
    align-items: center;
  }

  .traffic-title {
    margin-bottom: 12px;
    font-size: 14px;
    font-weight: 700;
    line-height: 22px;
    color: #313238;
  }

  .help-text {
    margin-top: 4px;
    font-size: 12px;
    line-height: 20px;
    color: #979ba5;
  }

  .form-error-text {
    margin-top: 4px;
    font-size: 12px;
    line-height: 20px;
    color: #ea3636;
  }

  .timeout-item :deep(.bk-input) {
    width: 180px;
  }

  .timeout-unit {
    padding: 0 8px;
    border-left: 1px solid #c4c6cc;
  }
}
</style>
