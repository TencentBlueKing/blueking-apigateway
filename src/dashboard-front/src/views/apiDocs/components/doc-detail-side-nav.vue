<template>
  <!--  文档详情的内容导航栏  -->
  <ul class="ag-component-nav">
    <li v-for="nav of list" :key="nav.id">
      <span
        class="nav"
        :class="{ active: curNav?.id === nav.id }"
        @click="handleAnchor(nav)"
      >
        {{ nav.name }}
      </span>
    </li>
  </ul>
</template>

<script lang="ts" setup>
import {
  defineModel,
  toRefs,
  watch,
} from 'vue';
import { INavItem } from '@/views/apiDocs/types';

const curNav = defineModel<INavItem | null>({
  default: (): INavItem | null => null,
});

const props = defineProps({
  list: {
    type: Array<INavItem>,
    default() {
      return [];
    },
  },
});

const { list } = toRefs(props);

const handleAnchor = (nav: INavItem) => {
  const element = document.getElementById(nav.name);
  if (element) {
    curNav.value = nav;
    element.scrollIntoView({
      behavior: 'smooth', // 平滑滚动
      block: 'start', // 元素顶部与视口顶部对齐
    });
  }
};

watch(() => props.list, () => {
  curNav.value = null;
}, { deep: true });

</script>

<style lang="scss" scoped>
.ag-component-nav {
  width: 160px;
  font-size: 12px;
  text-align: left;
  color: #979ba5;
  line-height: 28px;
  border-left: 1px solid #dcdee5;

  .nav {
    padding-left: 16px;
    display: block;
    text-decoration: none;
    color: #63656e;
    cursor: pointer;

    &.active {
      color: #3a84ff;
      border-left: 1px solid #3a84ff;
      margin-left: -1px;
    }
  }
}
</style>
