<template>
  <bk-dropdown :trigger="triggerType" class="mr10" @show="isOpen = true" @hide="isOpen = false">
    <bk-button :disabled="isDisabled">
      {{ text }}
      <i :class="['apigateway-icon icon-ag-down-small apigateway-select-icon', { 'is-open': isOpen }]">
      </i>
    </bk-button>
    <template #content>
      <bk-dropdown-menu>
        <bk-dropdown-item
          v-for="item in dropdownList"
          @click="handleDropdownClick(item)"
          :key="item.value"
        >
          {{ item.label }}
        </bk-dropdown-item>
      </bk-dropdown-menu>
    </template>
  </bk-dropdown>
</template>
<script setup lang="ts">
import { ref } from 'vue';
const props = defineProps({
  text: {
    type: String,
    default: '下拉菜单',
  },
  triggerType: {
    type: String,
    default: 'click',
  },
  dropdownList: {
    type: Array,
    default: [{ value: 'test', label: '测试' }],
  },
  isDisabled: {
    type: Boolean,
    default: false,
  },
});
const dropdownList = ref(props.dropdownList);
const isOpen = ref<boolean>(false);

const emit = defineEmits([
  'on-change',
]);

const handleDropdownClick = (data: {value: string, label: string}) => {
  emit('on-change', data);
};
</script>
