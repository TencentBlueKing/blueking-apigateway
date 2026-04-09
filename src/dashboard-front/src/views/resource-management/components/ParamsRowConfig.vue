<template>
  <div class="pr-4px">
    <BkPopover
      trigger="click"
      theme="light"
      width="300"
      :disabled="disabled"
      @after-hidden="onPopoverHidden"
    >
      <div
        v-bk-tooltips="{content:t('枚举值'), disabled:disabled}"
        class="row-config-icon"
        :class="{'is-disabled': disabled}"
      >
        <AgIcon
          name="settings"
          size="14"
        />
      </div>
      <template #content>
        <div class="enum-config-panel">
          <div class="enum-config-switch">
            <span class="enum-config-label">{{ t('枚举值') }}</span>
            <BkSwitcher
              v-model="enums.enabled"
              theme="primary"
              size="small"
            />
          </div>
          <div
            v-if="enums.enabled"
            class="enum-config-input"
          >
            <BkTagInput
              v-model="enums.values"
              :copyable="false"
              :list="[]"
              :placeholder="t('输入枚举值并按 Enter 添加')"
              allow-create
              has-delete-icon
              allow-auto-match
            />
          </div>
        </div>
      </template>
    </BkPopover>
  </div>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash-es';

export interface IConfig { enums: IEnumConfig }

interface IEnumConfig {
  enabled: boolean
  values: (string | number)[]
}

interface IProps {
  row: {
    [key: string]: any
    type: string
    enum?: any[]
  }
}

interface IEmits { change: [config: IConfig] }

const { row } = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const enums = ref<IEnumConfig>({
  enabled: false,
  values: [],
});

const disabled = computed(() => ['array', 'object', 'boolean'].includes(row?.type || ''));

watch(
  () => row.enum,
  () => {
    if (row.enum?.length) {
      enums.value = {
        enabled: true,
        values: [...row.enum],
      };
    }
    else {
      enums.value = {
        enabled: false,
        values: [],
      };
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

const onPopoverHidden = () => {
  if (isEqual(enums.value, row.enum)) {
    return;
  }
  emit('change', { enums: enums.value });
};

</script>

<style lang="scss" scoped>

.row-config-icon {
  display: inline-flex;
  padding: 4px;
  color: #979BA5;
  cursor: pointer;
  background: transparent;
  border-radius: 2px;
  transition: all 0.2s;
  align-items: center;
  justify-content: center;

  &:hover {
    color: #3A84FF;
    background: #E1ECFF;
  }

  &:active {
    color: #2B6ACF;
    background: #CCDDF9;
  }

  &.is-disabled {
    cursor: not-allowed;

    &:hover {
      color: #fff;
      background: #DCDEE5;
    }
  }
}

.enum-config-panel {
  min-width: 280px;
  padding: 8px 0;

  .enum-config-switch {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .enum-config-label {
    font-size: 12px;
    color: #63656E;
  }

  .enum-config-input {
    margin-top: 8px;
  }
}

</style>
