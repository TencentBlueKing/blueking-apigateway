<template>
  <BkFormItem
    label="Key"
    property="configs.key"
    required
    :rules="rules"
    v-bind="$attrs"
  >
    <BkDropdown
      placement="bottom-start"
      :popover-options="{
        boundary: 'parent',
        width: '100%',
      }"
      class="w-full!"
      :disabled="disabled"
    >
      <BkInput
        v-model="localStageConfig.configs.key"
        :disabled="disabled"
      />
      <template
        v-if="localStageConfig.configs.hash_on !== 'header' && localStageConfig.configs.hash_on !== 'cookie'"
        #content
      >
        <BkDropdownMenu>
          <BkDropdownItem
            v-for="option in hashOnKeyOptions"
            :key="option.id"
            @click="() => handleHashOnKeyClick(option.id)"
          >
            {{ option.name }}
          </BkDropdownItem>
        </BkDropdownMenu>
      </template>
    </BkDropdown>
  </BkFormItem>
</template>

<script setup lang="ts">
import {
  cloneDeep,
  isEqual,
} from 'lodash-es';

interface IProps {
  disabled?: boolean
  stageConfig: IStageConfig
}

interface IStageConfig {
  description: string
  id: number
  name: string
  configs: {
    loadbalance: string
    hash_on?: string
    key?: string
    timeout: number
    hosts: any[]
    stage_id: number
  }
}

const { disabled, stageConfig } = defineProps<IProps>();

const emit = defineEmits<{ change: [IStageConfig] }>();

const { t } = useI18n();

const localStageConfig = ref(stageConfig);

const hashOnKeyOptions = [
  {
    id: 'uri',
    name: 'uri',
  },
  {
    id: 'server_name',
    name: 'server_name',
  },
  {
    id: 'server_addr',
    name: 'server_addr',
  },
  {
    id: 'request_uri',
    name: 'request_uri',
  },
  {
    id: 'remote_port',
    name: 'remote_port',
  },
  {
    id: 'remote_addr',
    name: 'remote_addr',
  },
  {
    id: 'query_string',
    name: 'query_string',
  },
  {
    id: 'host',
    name: 'host',
  },
  {
    id: 'hostname',
    name: 'hostname',
  },
  {
    id: 'arg_***',
    name: 'arg_***',
  },
];

const rules = [
  {
    validator: (value: string) => {
      if (localStageConfig.value.configs.hash_on === 'header') {
        if (value.startsWith('http_')) {
          return /http_[0-9a-zA-z_-]+/.test(value);
        }
      }
      return true;
    },
    message: t('必须以 http_ 开头并填写数字、字母、下划线、减号'),
    trigger: 'blur',
  },
  {
    validator: (value: string) => {
      if (localStageConfig.value.configs.hash_on === 'cookie') {
        if (value.startsWith('cookie_')) {
          return /cookie_[0-9a-zA-z_-]+/.test(value);
        }
      }
      return true;
    },
    message: t('必须以 cookie_ 开头并填写数字、字母、下划线、减号'),
    trigger: 'blur',
  },
  {
    validator: (value: string) => {
      if (localStageConfig.value.configs.hash_on === 'vars') {
        if (value.startsWith('arg_')) {
          return /arg_[0-9a-zA-z_-]+/.test(value);
        }
      }
      return true;
    },
    message: t('必须以arg_ 开头并填写数字、字母、下划线、减号'),
    trigger: 'blur',
  },
];

watch(() => stageConfig, () => {
  if (isEqual(localStageConfig.value, stageConfig)) {
    return;
  }
  localStageConfig.value = cloneDeep(stageConfig);
}, {
  deep: true,
  immediate: true,
});

watch(localStageConfig, () => {
  emit('change', localStageConfig.value);
}, { deep: true });

const handleHashOnKeyClick = (value: string) => {
  if (localStageConfig.value) {
    localStageConfig.value.configs.key = value;
  }
};
</script>
