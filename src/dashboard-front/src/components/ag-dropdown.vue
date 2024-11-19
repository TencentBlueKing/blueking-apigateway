<template>
  <bk-dropdown :trigger="triggerType" class="mr8" @show="isOpen = true" @hide="isOpen = false" :placement="placement">
    <template v-if="isText">
      <div class="dropdown-text">{{ text }} <angle-right class="f22" /></div>
    </template>
    <bk-button :disabled="isDisabled" v-else>
      {{ text }}
      <i :class="['apigateway-icon icon-ag-down-small apigateway-select-icon', { 'is-open': isOpen }]">
      </i>
    </bk-button>
    <template #content>
      <bk-dropdown-menu v-if="isOpen">
        <template v-if="slots?.default">
          <slot></slot>
        </template>
        <template v-else>
          <bk-dropdown-item
            v-for="item in dropdownList"
            @click="handleDropdownClick(item)"
            :class="{ disabled: item.disabled }"
            :key="item.value"
            v-bk-tooltips="{ content: item?.tooltips, disabled: !item?.tooltips || !item.disabled }"
          >
            {{ item.label }}
          </bk-dropdown-item>
        </template>
      </bk-dropdown-menu>
    </template>
  </bk-dropdown>
</template>
<script setup lang="ts">
import { ref, PropType, useSlots, watch } from 'vue';
import { IDropList } from '@/types';
import { AngleRight } from 'bkui-vue/lib/icon';

const slots = useSlots();

interface ApigwIDropList extends IDropList {
  tooltips?: string;
}

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
    type: Array as PropType<ApigwIDropList[]>,
    default: [{ value: 'test', label: '测试' }],
  },
  isDisabled: {
    type: Boolean,
    default: false,
  },
  isText: {
    type: Boolean,
    default: false,
  },
  placement: {
    type: String,
    default: 'bottom',
  },
});
const dropdownList = ref(props.dropdownList);
const isOpen = ref<boolean>(false);

const emit = defineEmits([
  'on-change',
]);

watch(
  () => props.dropdownList,
  () => {
    dropdownList.value = props.dropdownList;
  },
);

const handleDropdownClick = (data: IDropList) => {
  if (data.disabled) return;
  isOpen.value = false;
  emit('on-change', data);
};
</script>
<style scoped lang="scss">
.disabled{
  cursor: not-allowed;
  color: #dcdee5;
}
.dropdown-text {
  display: flex;
  align-items: center;
  padding: 0 16px;
  line-height: 34px;
  cursor: pointer;
}
</style>
