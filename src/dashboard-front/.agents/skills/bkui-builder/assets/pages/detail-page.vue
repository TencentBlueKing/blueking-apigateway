<template>
  <div class="detail-page p-20px">
    <!-- 状态概览栏 -->
    <BkCard
      class="mb-16px"
      :border="false"
    >
      <div class="flex items-center justify-between py-8px">
        <div class="flex items-center gap-12px">
          <h2 class="text-18px font-bold color-#313238 m-0">
            {{ title }}
          </h2>
          <BkTag :theme="statusTheme">
            {{ statusText }}
          </BkTag>
        </div>

        <div class="w-400px">
          <BkSteps
            :cur-step="currentStep"
            :steps="steps"
          />
        </div>
      </div>
    </BkCard>

    <!-- 分组详情 -->
    <BkCollapse v-model="activePanels">
      <BkCollapsePanel name="basic">
        {{ t('基本信息') }}
        <template #content>
          <div class="grid grid-cols-2 gap-y-12px gap-x-24px">
            <div
              v-for="field in basicFields"
              :key="field.key"
              class="flex items-center text-14px"
            >
              <span class="detail-label shrink-0">{{ field.label }}：</span>
              <span class="color-#313238 truncate">{{ field.value || '--' }}</span>
            </div>
          </div>
        </template>
      </BkCollapsePanel>

      <BkCollapsePanel name="log">
        {{ t('执行记录') }}
        <template #content>
          <BkTimeline :list="timelineList" />
        </template>
      </BkCollapsePanel>
    </BkCollapse>
  </div>
</template>

<script setup lang="ts">
interface IDetailField {
  key: string
  label: string
  value: string
}

interface IStepItem {
  title: string
}

interface ITimelineRecord {
  tag: string
  content: string
  type?: 'default' | 'primary' | 'warning' | 'success' | 'danger'
}

interface IProps {
  title: string
  status?: 'success' | 'running' | 'failed'
  currentStep?: number
  basicFields?: IDetailField[]
  timelineList?: ITimelineRecord[]
}

const {
  title,
  status = 'success',
  currentStep = 3,
  basicFields = [],
  timelineList = [],
} = defineProps<IProps>();

const { t } = useI18n();

const activePanels = ref<string[]>(['basic', 'log']);

const steps = computed<IStepItem[]>(() => [
  { title: t('提交申请') },
  { title: t('审批通过') },
  { title: t('执行完成') },
]);

const statusTheme = computed(() => {
  const map = {
    success: 'success',
    running: 'info',
    failed: 'danger',
  } as const;
  return map[status];
});

const statusText = computed(() => {
  const map = {
    success: t('执行成功'),
    running: t('执行中'),
    failed: t('执行失败'),
  } as const;
  return map[status];
});
</script>

<style lang="scss" scoped>
.detail-label {
  display: inline-block;
  width: 96px;
  color: #979ba5;
  text-align: right;
}
</style>
