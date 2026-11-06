<template>
  <div class="ai-instance-name-list">
    <div
      v-for="instance in config.instances"
      :key="instance.uid"
      class="instance-row"
    >
      <BkTag
        size="small"
        class="role-tag"
        :theme="instance.role === 'primary' ? 'info' : 'warning'"
      >
        {{ instance.role === 'primary' ? t('主') : t('备') }}
      </BkTag>
      <span
        class="instance-name"
        :title="instance.name"
      >{{ instance.name }}</span>
    </div>
    <span v-if="!config.instances.length">--</span>
  </div>
</template>

<script setup lang="ts">
import type { IAIBackendConfigFormData } from '@/views/model-services/utils/ai-backend-config.ts';

interface IProps {
  // 来自接口的已保存配置，后端保证每个实例都有名称
  config: IAIBackendConfigFormData
}

const { config } = defineProps<IProps>();

const { t } = useI18n();
</script>

<style lang="scss" scoped>
.ai-instance-name-list {
  min-width: 0;
  padding: 2px 0;
}

.instance-row {
  display: flex;
  line-height: 20px;
  align-items: center;
  gap: 8px;
}

.role-tag {
  flex-shrink: 0;
}

.instance-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
