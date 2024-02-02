<template>
  <div class="stage-top-bar">
    <div class="top-title-wrapper">
      <div class="title">{{ t('环境概览') }}</div>
      <div class="model-type mr8">
        <div
          v-for="item in modelTypes"
          :key="item?.key"
          :class="['item', { active: item?.key === curActive }]"
          @click="switchModelType(item?.key, item?.routeName)"
        >
          {{ item?.text }}
        </div>
      </div>
    </div>
    <!-- 详情模式环境 -->
    <div class="stage-list-container" v-if="curActive === 'detail'">
      <ul
        class="stage-list"
        :style="{ transform: `translateX(${scrollState.offset}px)` }"
      >
        <li
          v-for="(item, index) in stageStore.stageList"
          :key="index"
          class="stage-item"
          :title="item?.name"
          :class="{ active: curStage?.name === item?.name }"
          @click="handleChangeStage(item?.name)"
        >
          <spinner v-if="getStatus(item) === 'doing'" fill="#3A84FF" />
          <span v-else :class="['dot', getStatus(item)]"></span>
          <span>{{ item?.name }}</span>
        </li>
      </ul>

      <i
        v-if="scrollState.isShowIcon"
        class="apigateway-icon icon-ag-pa-arrow-left"
        @click="handlePrev"
      ></i>

      <i
        v-if="scrollState.isShowIcon"
        class="apigateway-icon icon-ag-ps-arrow-right"
        @click="handleNext"
      ></i>
      <!-- 添加环境 -->
      <plus
        :class="['add-stage-icon', { notposition: !scrollState.isShowIcon }]"
        fill="#3785ff"
        @click="handleAddStage"
        style="font-size: 28px; cursor: pointer;"
      />
    </div>

    <!-- 环境侧边栏 -->
    <edit-stage-sideslider ref="stageSidesliderRef" />
  </div>
</template>

<script setup lang="ts">
/* eslint-disable prefer-destructuring */

import { computed, ref, watch, onBeforeMount, onMounted, nextTick, Ref  } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getStageList, getStageDetail } from '@/http';
import { useStage, useCommon } from '@/store';
import { useI18n } from 'vue-i18n';
import mitt from '@/common/event-bus';
import { Spinner, Plus } from 'bkui-vue/lib/icon';
import { getStatus } from '@/common/util';
import editStageSideslider from '@/views/stage/overview/comps/edit-stage-sideslider.vue';
import { throttle } from 'lodash';

const router = useRouter();
const route = useRoute();
const stageStore = useStage();
const common = useCommon();
const { t } = useI18n();

const modelTypes = ref([
  {
    key: 'abbreviation',
    text: '缩略模式',
    routeName: 'apigwStageOverview',
  },
  {
    key: 'detail',
    text: '详情模式',
    routeName: 'apigwStageDetail',
  },
]);

// 获取环境列表
const apigwId = computed(() => common.apigwId);

// 新建环境
const stageSidesliderRef = ref(null);
const handleAddStage = () => {
  stageSidesliderRef.value.handleShowSideslider('add');
};

// 当前环境
const curStage = ref(stageStore.curStageData || stageStore.defaultStage);
// 当前选中环境name
const curStageName = ref('prod');

const init = async (isUpdate?: Boolean, isDelete?: Boolean) => {
  stageStore.setStageMainLoading(true);
  try {
    // 获取环境列表
    const data = await getStageList(apigwId.value);
    stageStore.setStageList(data);
    // 删除环境
    if (isDelete) {
      curStage.value = data[0];
      router.push({
        query: {
          stage: curStage.value.name,
          tab: 'resourceInfo',
        },
      });
    } else if (route.query?.stage && !isUpdate) { // 更新停留当前环境
      // 停留当前环境
      curStage.value = stageStore.stageList?.find(stage => stage.name === route.query.stage);
    } else {
      curStage.value = data.find((item: { name: string; }) => item.name === curStageName.value) || data[0];
    }
    curStageName.value = curStage.value?.name;

    // 获取当前环境的详情数据
    await getStageDetailFun(curStage.value?.id);
  } catch (error) {
    console.error(error);
  } finally {
    setTimeout(() => {
      stageStore.setStageMainLoading(false);
    }, 300);
  }
};
init();

// 当前环境概览模式
const curActive = ref(route.path.includes('/stage-detail') ? 'detail' : 'abbreviation');

// 获取环境详情
const getStageDetailFun = (id: number) => {
  if (curActive.value === 'abbreviation' || !route.path.includes('/stage-detail')) {
    return;
  }
  if (!id) {
    curStage.value = stageStore.stageList[0];
    id = curStage.value.id;
  }

  stageStore.setStageMainLoading(true);
  getStageDetail(apigwId.value, id).then((data) => {
    stageStore.curStageData = data;
    curStage.value = data;
    stageStore.curStageId = data.id;
    setTimeout(() => {
      stageStore.setStageMainLoading(false);
    }, 300);
  });
};

// 切换模式
const switchModelType = (key: string, routeName: string, stageName?: string) => {
  curActive.value = key;

  const data = {
    name: routeName,
    params: {
      id: apigwId.value,
    },
    query: {
      stage: stageName || curStage.value.name,
      tab: 'resourceInfo',
    },
  };
  if (key === 'abbreviation') {
    delete data.query;
  }

  // 是否改变路径
  router.push({ ...data });
};

// 切换环境
const handleChangeStage = async (name: string, isDelete?: Boolean) => {
  curStageName.value = name;
  if (name === curStage.value.name) return;
  // 获取切换环境的名字
  const data = stageStore.stageList.find(item => item?.name === name);
  if (!isDelete) {
    await getStageDetailFun(data.id);
  }
  stageStore.curStageId = data.id;
  router.push({
    query: {
      stage: data.name,
    },
  });
};

// 滚动数据
const scrollState = ref({
  position: 'left',
  offset: 24,
  width: 0,
  containerWidth: 0,
  isShowIcon: false,
});

// 最大偏移量
const maxScrollLeft = ref(0);
// 单次滚动偏移量
const curScrollOffset = 200;
const envContainerElement: Ref<HTMLElement | null> = ref(null);
const envListElement: Ref<HTMLElement | null> = ref(null);
// 左侧按钮宽度
const leftIconWidth = 24;
// 窗口拖动是否为拖大
const isWiden = ref(false);
// 窗口宽度
let windowWidth = window?.innerWidth;
let isNextClick = false;

// 监听环境列表是否变化，更新对应DOM数据
watch(() => stageStore.stageList, async () => {
  await nextTick(() => {
    // 容器
    envContainerElement.value = document.querySelector('.stage-list-container') as HTMLElement;
    scrollState.value.containerWidth = envContainerElement.value?.offsetWidth || 0;

    // 环境列表元素
    envListElement.value = document.querySelector('.stage-list-container .stage-list') as HTMLElement;
    scrollState.value.width = envListElement.value?.offsetWidth || 0;

    calculateMaxScroll();
  });
});

// 判断是否需要隐藏或显示控制按钮
const toggleControlButtons = () => {
  if (envListElement.value?.scrollWidth <= envContainerElement.value?.clientWidth - 52) {
    scrollState.value.isShowIcon = false;
    isNextClick = false;
  } else {
    scrollState.value.isShowIcon = true;
  }
};

// 获取最大偏移量/拖动偏移量
const calculateMaxScroll = () => {
  if (envListElement.value === null) {
    envListElement.value = document.querySelector('.stage-list-container .stage-list') as HTMLElement;
  }
  const actionbuts = 52;
  const previousMaxScrollLeft = maxScrollLeft.value;
  if (envListElement.value?.scrollWidth && envContainerElement.value?.clientWidth) {
    maxScrollLeft.value = (envListElement.value.scrollWidth - envContainerElement.value.clientWidth) + actionbuts;
  }

  // 当元素滚动到最右侧，拖动窗口列表需要跟随滚动
  if (isWiden.value && scrollState.value.isShowIcon && isNextClick) {
    const curMaxScrollLeft = maxScrollLeft.value - leftIconWidth;
    if (scrollState.value.offset <= -previousMaxScrollLeft && curMaxScrollLeft > previousMaxScrollLeft) {
      scrollState.value.offset -= curMaxScrollLeft - previousMaxScrollLeft;
    } else {
      // 更新当前位置以避免超出新的滚动边界值
      scrollState.value.offset = Math.max(scrollState.value.offset, -curMaxScrollLeft);
    }
    if (scrollState.value.offset > leftIconWidth) {
      scrollState.value.offset = leftIconWidth;
    }
  }

  // 判断是否需要隐藏或显示控制按钮
  toggleControlButtons();
};

// 左侧点击滚动
const handlePrev = () => {
  if (scrollState.value.offset < leftIconWidth) {
    scrollState.value.offset = Math.min(scrollState.value.offset + curScrollOffset, leftIconWidth);
  }
};

// 右侧点击滚动
const handleNext = () => {
  // 边界判断
  if (Math.abs(scrollState.value.offset) < maxScrollLeft.value) {
    scrollState.value.offset = Math.max(scrollState.value.offset - curScrollOffset, - maxScrollLeft.value);
    isNextClick = true;
  } else {
    isNextClick = true;
  }
};

// 窗口事件
const onWindowResize = () => {
  scrollState.value.containerWidth = envContainerElement.value?.offsetWidth || 0;
  isWiden.value = window.innerWidth > windowWidth;
  windowWidth = window.innerWidth;
  calculateMaxScroll();
};


onMounted(() => {
  // 监听窗口变化
  window.addEventListener('resize', throttle(onWindowResize, 100));

  // 事件总线监听重新获取环境列表，并获取当前环境详情
  mitt.on('rerun-init', (data) => {
    if (typeof data === 'boolean') {
      init(data);
    } else {
      init(data?.isUpdate, data?.isDelete);
    }
  });
  // 切换概览模式
  mitt.on('switch-mode', async (data) => {
    await getStageDetailFun(data.id);
    switchModelType('detail', 'apigwStageDetail', data.name);
  });
  // 切换环境
  mitt.on('switch-stage', async (isDelete?: Boolean) => {
    handleChangeStage(curStage.value.name, isDelete);
  });
  // 不开启loading，只获取环境列表
  mitt.on('get-environment-list-data', async (isLoading = false) => {
    if (isLoading) {
      stageStore.setStageMainLoading(true);
    }
    const data = await getStageList(apigwId.value);
    stageStore.setStageList(data);
    setTimeout(() => {
      stageStore.setStageMainLoading(false);
    }, 200);
  });
});

onBeforeMount(() => {
  mitt.off('rerun-init');
  mitt.off('switch-mode');
  mitt.off('switch-stage');
  mitt.off('get-environment-list-data');
  window.removeEventListener('resize', onWindowResize);
});

defineExpose({
  getStageDetailFun,
});
</script>

<style lang="scss" scoped>
.stage-top-bar {
  position: absolute;
  height: 51px;
  display: flex;
  align-items: center;
  top: 0;
  width: 100%;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #dcdee5;
  box-shadow: 0 3px 4px rgba(64,112,203,0.05882);

  .top-title-wrapper {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    width: 326px;
  }
  .title {
    color: #313238;
    font-size: 16px;
  }
  .model-type {
    display: flex;
    align-items: center;
    height: 32px;
    margin-left: 18px;
    padding: 4px;
    background: #f0f1f5;
    color: #63656e;
    border-radius: 2px;
    .item {
      font-size: 12px;
      line-height: 24px;
      padding: 0 10px;
      &:hover {
        cursor: pointer;
      }
      &.active {
        background: #fff;
        color: #3a84ff;
        border-radius: 2px;
      }
    }
  }
  .stage-list-container {
    display: flex;
    position: relative;
    margin-right: 276px;
    height: 100%;
    overflow: hidden;
    flex: 1;
    min-width: 360px;
  }
  .stage-list {
    transition: all .3s;
    transform: translateX(24px);
    // width: 100%;
    position: relative;
    height: 100%;
    display: flex;
    .stage-item {
      cursor: pointer;
      width: 100px;
      height: 100%;
      padding: 0 5px;
      box-sizing: border-box;
      font-size: 14px;
      color: #63656e;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      span {
        text-align: center;
        padding-left: 6px;
        display: inline-block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;

        &.success {
          border: 1px solid #3FC06D;
          background: #E5F6EA;
        }

        &.unreleased {
          border: 1px solid #C4C6CC;
          background: #F0F1F5;
        }

        &.delist {
          border: 1px solid #C4C6CC;
          background: #F0F1F5;
        }

        &.failure {
          border: 1px solid #EA3636;
          background: #FFE6E6;
        }
      }

      &:hover {
        background-color: #f0f5ff;
      }
      &.active {
        border-top: 3px solid #3a84ff;
        background-color: #f0f5ff;
      }
    }
  }
  .add-stage-icon,
  .icon-ag-pa-arrow-left,
  .icon-ag-ps-arrow-right {
    height: 51px;
    background: #fff;
    top: 50%;
    transform: translateY(-50%);
    position: absolute;
    right: 0;
    cursor: pointer;
  }

  .notposition {
    position: relative;
    right: -28px;
  }

  .icon-ag-pa-arrow-left,
  .icon-ag-ps-arrow-right {
    width: 24px;
    line-height: 51px;
    font-size: 16px;
    font-weight: 700;
    color: #979ba5;

    &:hover {
      color: #3a84ff;
      background: #F0F5FF;
    }
  }
  .icon-ag-pa-arrow-left {
    box-shadow: 4px 0 8px 0 #0000001a;
    left: 0;
  }
  .icon-ag-ps-arrow-right {
    box-shadow: -4px 0 8px 0 #0000001a;
    right: 28px;
  }
}
</style>
