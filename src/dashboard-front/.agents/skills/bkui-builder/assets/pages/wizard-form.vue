<template>
  <div class="wizard-container mx-auto py-32px">
    <div class="mb-24px">
      <BkSteps
        :cur-step="currentStep"
        :steps="stepList"
      />
    </div>

    <div class="wizard-card bg-#fff p-24px rounded-2px">
      <!-- 步骤 1: 基本信息 -->
      <BkForm
        v-if="currentStep === 1"
        ref="stepOneFormRef"
        :model="formData"
        :rules="stepOneRules"
        form-type="vertical"
      >
        <BkFormItem
          :label="t('名称')"
          property="name"
          required
        >
          <BkInput
            v-model="formData.name"
            :placeholder="t('请输入名称')"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('执行模式')"
          property="mode"
        >
          <BkRadioGroup v-model="formData.mode">
            <BkRadio label="sync">
              {{ t('同步') }}
            </BkRadio>
            <BkRadio label="async">
              {{ t('异步') }}
            </BkRadio>
          </BkRadioGroup>
        </BkFormItem>
      </BkForm>

      <!-- 步骤 2: 参数配置 -->
      <div v-else-if="currentStep === 2">
        <BkAlert
          class="mb-16px"
          theme="warning"
          :title="t('请仔细检查参数配置，确认无误后再进入下一步。')"
        />
        <BkForm
          :model="formData"
          form-type="vertical"
        >
          <BkFormItem :label="t('并发数')">
            <BkSlider
              v-model="formData.concurrency"
              :max-value="100"
            />
          </BkFormItem>
          <BkFormItem :label="t('通知对象')">
            <BkTagInput
              v-model="formData.receivers"
              :placeholder="t('请输入并回车确认')"
              allow-create
            />
          </BkFormItem>
        </BkForm>
      </div>

      <!-- 步骤 3: 确认提交 -->
      <div
        v-else
        class="text-center py-16px"
      >
        <BkException
          type="empty"
          scene="part"
          :title="t('配置确认')"
        >
          <div class="inline-block w-320px text-left bg-#f5f7fa p-16px rounded-2px text-14px">
            <div class="mb-8px">
              {{ t('名称') }}：{{ formData.name }}
            </div>
            <div>
              {{ t('并发数') }}：{{ formData.concurrency }}
            </div>
          </div>
        </BkException>
      </div>
    </div>

    <div class="flex items-center gap-12px mt-20px">
      <BkButton
        v-if="currentStep > 1"
        @click="handlePrev"
      >
        {{ t('上一步') }}
      </BkButton>
      <BkButton
        v-if="currentStep < 3"
        theme="primary"
        @click="handleNext"
      >
        {{ t('下一步') }}
      </BkButton>
      <BkButton
        v-else
        theme="primary"
        :loading="submitting"
        @click="handleFinish"
      >
        {{ t('提交') }}
      </BkButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type Form, Message } from 'bkui-vue';

interface IWizardForm {
  name: string
  mode: 'sync' | 'async'
  concurrency: number
  receivers: string[]
}

const emit = defineEmits<{
  done: [payload: IWizardForm]
}>();

const { t } = useI18n();

const stepOneFormRef = useTemplateRef<InstanceType<typeof Form>>('stepOneFormRef');
const currentStep = shallowRef(1);
const submitting = shallowRef(false);

const formData = reactive<IWizardForm>({
  name: '',
  mode: 'sync',
  concurrency: 20,
  receivers: [],
});

const stepList = computed(() => [
  { title: t('基本信息') },
  { title: t('参数配置') },
  { title: t('确认提交') },
]);

const stepOneRules = computed(() => ({
  name: [
    {
      required: true,
      message: t('请输入名称'),
      trigger: 'blur',
    },
  ],
}));

const handlePrev = () => {
  currentStep.value = Math.max(1, currentStep.value - 1);
};

const handleNext = async () => {
  if (currentStep.value === 1) {
    await stepOneFormRef.value?.validate();
  }
  currentStep.value = Math.min(3, currentStep.value + 1);
};

const handleFinish = async () => {
  submitting.value = true;
  try {
    // 替换为实际提交接口
    Message({
      theme: 'success',
      message: t('提交成功'),
    });
    emit('done', { ...formData });
  }
  finally {
    submitting.value = false;
  }
};
</script>

<style lang="scss" scoped>
.wizard-container {
  max-width: 900px;
}

.wizard-card {
  box-shadow: 0 2px 4px 0 rgb(0 0 0 / 10%);
}
</style>
