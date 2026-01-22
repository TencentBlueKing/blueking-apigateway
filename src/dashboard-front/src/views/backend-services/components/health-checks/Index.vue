<template>
  <div class="mt-18px">
    <div
      class="text-14px line-height-22px flex items-center cursor-pointer color-#3a84ff mb-24px"
      @click="visible = !visible"
    >
      <span>{{ t('高级配置') }}</span>
      <AgIcon
        :class="{ 'rotate-180': visible }"
        color="#3a84ff"
        name="arrows-down"
        size="22"
      />
    </div>
    <div
      v-show="visible"
      class="mt-18px"
    >
      <BkFormItem :label="t('健康检查')">
        <ActiveChecks
          ref="active-checks"
          v-model:enabled="isActiveEnabled"
          :checks="checks?.active"
          class="mt-18px mb-24px"
        />
        <PassiveChecks
          ref="passive-checks"
          v-model:enabled="isPassiveEnabled"
          :checks="checks?.passive"
        />
      </BkFormItem>
    </div>
  </div>
</template>

<script setup lang="ts">
import ActiveChecks from './components/ActiveChecks.vue';
import PassiveChecks from './components/PassiveChecks.vue';
import type { IHealthCheck } from '@/services/source/backend-services.ts';
import { isPlainObject } from 'lodash-es';

interface IProps { checks?: IHealthCheck }

const { checks = undefined } = defineProps<IProps>();

const { t } = useI18n();

const visible = ref(false);
const activeChecksRef = useTemplateRef('active-checks');
const passiveChecksRef = useTemplateRef('passive-checks');

const isActiveEnabled = ref(false);
const isPassiveEnabled = ref(false);

watch(() => checks, () => {
  if (checks && isPlainObject(checks)) {
    isActiveEnabled.value = checks.active !== undefined;
    isPassiveEnabled.value = checks.passive !== undefined;
  }
}, {
  immediate: true,
  deep: true,
});

defineExpose({
  getValue: () => {
    const checks = {};
    if (isActiveEnabled.value) {
      Object.assign(checks, { active: activeChecksRef.value!.getValue() });
    }
    if (isPassiveEnabled.value) {
      Object.assign(checks, { passive: passiveChecksRef.value!.getValue() });
    }
    return Object.keys(checks).length > 0 ? checks : undefined;
  },
});

</script>
