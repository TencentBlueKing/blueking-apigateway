<template>
  <ul class="ag-component-nav">
    <li v-for="item of list" :key="item.id">
      <a
        :class="{ active: curSideNavId === item.id }"
        href="javascript: void(0);"
        @click="handleAnchor(item.id)">
        {{item.name}}
      </a>
    </li>
  </ul>
</template>

<script lang="ts" setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';
import { throttle } from 'lodash';

const route = useRoute();

const curSideNavId = ref<string>('');
const contentHeightList = ref<any>(null);
const triggerFlag = ref<boolean>(false);

const props = defineProps({
  offsetTop: {
    type: Number,
    default: 60,
  },
  containerId: {
    type: String,
    default: '.container-content',
  },
  list: {
    type: Array<any>,
    default() {
      return [];
    },
  },
});

const getChildrenHeigh = () => {
  const container = document.querySelector('.component-content') || document.body;
  const OFFSET = props.offsetTop;
  const arr: any = [];
  for (const i of props.list) {
    const child = document.getElementById(`${props.list[i]?.id}`);
    if (child) {
      const rect = child.getBoundingClientRect();
      arr.push(container.scrollTop + rect.top - OFFSET);
      // arr.push(child.offsetTop - OFFSET)
    }
  }
  contentHeightList.value = arr;
};

const handleAnchor = (id: string) => {
  const OFFSET = props.offsetTop;
  const element = document.getElementById(id);
  curSideNavId.value = id;
  triggerFlag.value = true;

  if (element) {
    const rect = element.getBoundingClientRect();
    const container = document.querySelector('.component-content') || document.body;
    const top = container.scrollTop + rect.top - OFFSET;

    container.scrollTo({
      top,
      behavior: 'smooth',
    });
  }
};

const handleScroll = () => {
  if (triggerFlag.value) {
    return;
  }
  const scrollTop = document.querySelector('.component-content')?.scrollTop || document.documentElement?.scrollTop;
  if (contentHeightList.value) {
    for (let i = 0; i < contentHeightList.value.length; i++) {
      if (scrollTop >= contentHeightList.value[i] && scrollTop <= contentHeightList.value[i + 1]) {
        curSideNavId.value = props.list[i]?.id;
      }
      if (scrollTop < contentHeightList.value[0]) {
        curSideNavId.value = props.list[0]?.id;
      }
    }
  }
};

const handleTrolley = () => {
  triggerFlag.value = false;
};

onMounted(() => {
  nextTick(() => {
    setTimeout(() => {
      getChildrenHeigh();
    }, 1000);
    const content = document.querySelector('.component-content');
    content?.addEventListener('scroll', throttle(handleScroll, 100), true);

    window.addEventListener('wheel', throttle(handleTrolley, 500), true);
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('wheel', handleTrolley, true);
  const content = document.querySelector('.component-content');
  if (content) {
    content.removeEventListener('scroll', handleScroll, true);
  }
});

watch(
  () => route,
  () => {
    nextTick(() => {
      getChildrenHeigh();
    });
  },
  { immediate: true, deep: true },
);
</script>

<style lang="scss" scoped>
.ag-component-nav {
  width: 160px;
  font-size: 12px;
  text-align: left;
  color: #979ba5;
  line-height: 28px;
  border-left: 1px solid #DCDEE5;
  a {
    padding-left: 16px;
    display: block;
    text-decoration: none;
    color: #63656E;

    &.active {
      color: #3A84FF;
      border-left: 1px solid #3A84FF;
      margin-left: -1px;
    }
  }
}
</style>
