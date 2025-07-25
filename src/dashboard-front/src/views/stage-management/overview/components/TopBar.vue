<template>
  <div class="stage-top-bar">
    <div class="top-title-wrapper">
      <div class="title">
        {{ t('环境概览') }}
      </div>
      <div class="model-type">
        <div
          v-for="item in modeList"
          :key="item.key"
          class="item"
          :class="[{ active: item.key === mode }]"
          @click="() => switchModelType(item)"
        >
          {{ item?.text }}
        </div>
      </div>
    </div>
    <!-- 详情模式环境 -->
    <div
      v-if="mode === 'detail'"
      class="stage-list-container"
    >
      <ul
        class="stage-list"
        :style="{ transform: `translateX(${scrollState.offset}px)` }"
      >
        <li
          v-for="stage in stageList"
          :key="stage.id"
          class="stage-item"
          :title="stage.name"
          :class="{ active: stageId === stage.id }"
          @click="() => handleChangeStage(stage)"
        >
          <Spinner
            v-if="getStageStatus(stage) === 'doing'"
            fill="#3A84FF"
          />
          <span
            v-else
            class="dot"
            :class="[getStageStatus(stage)]"
          />
          <span>{{ stage.name }}</span>
        </li>
      </ul>

      <AgIcon
        v-if="scrollState.isShowIcon"
        v-bk-tooltips="{ content: '已显示最前', disabled: prevDisabled }"
        name="pa-arrow-left"
        :class="[prevDisabled ? 'icon-arrow-enable' : '']"
        @click="handlePrev"
      />
      <AgIcon
        v-if="scrollState.isShowIcon"
        v-bk-tooltips="{ content: '没有更多了', disabled: nextDisabled }"
        name="ps-arrow-right"
        :class="[nextDisabled ? 'icon-arrow-enable' : '']"
        @click="handleNext"
      />
      <!-- 添加环境 -->
      <AgIcon
        v-if="!gatewayStore.isProgrammableGateway"
        name="add-small"
        size="28"
        class="ml-28px color-#3785ff cursor-pointer content-center"
        @click="handleAddStage"
      />
    </div>

    <!-- 新建/编辑环境 -->
    <CreateStage ref="stageSidesliderRef" />
  </div>
</template>

<script setup lang="ts">
import { type IStageListItem, getStageList } from '@/services/source/stage';
import { Spinner } from 'bkui-vue/lib/icon';
import { getStageStatus } from '@/utils';
import { useGateway } from '@/stores';
import { useRouteParams } from '@vueuse/router';
import CreateStage from '@/views/stage-management/overview/components/CreateStage.vue';

const mode = defineModel<string>('mode', { default: 'overview' });
const stageId = defineModel<number>('stageId', { default: 0 });

const { t } = useI18n();
const router = useRouter();
const gatewayStore = useGateway();

const gatewayId = useRouteParams('id', 0, { transform: Number });
const stageList = ref<IStageListItem[]>([]);

const prevDisabled = ref(false);
const nextDisabled = ref(true);

// 新建环境
const stageSidesliderRef = ref();

// 当前环境
const curStage = ref <IStageListItem | null>(null);

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
// const windowWidth = window?.innerWidth;
let isNextClick = false;

const modeList = [
  {
    key: 'overview',
    text: t('缩略模式'),
    routeName: 'StageOverview',
  },
  {
    key: 'detail',
    text: t('详情模式'),
    routeName: 'apigwStageDetail',
  },
];

// 监听环境列表是否变化，更新对应DOM数据
watch(stageList, async () => {
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

// 切换模式
const switchModelType = (item: typeof modeList[number]) => {
  mode.value = item.key;
  const firstStage = stageList.value[0];
  if (firstStage) {
    curStage.value = firstStage;
    stageId.value = firstStage.id;
  }
};

// 切换环境
const handleChangeStage = async (stage: IStageListItem) => {
  if (stage.id === curStage.value?.id) return;
  curStage.value = stage;
  stageId.value = stage.id;
  router.push({ query: { stage: stage.name } });
};

const handleAddStage = () => {
  stageSidesliderRef.value?.handleShowSideslider('add');
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
    }
    else {
      // 更新当前位置以避免超出新的滚动边界值
      scrollState.value.offset = Math.max(scrollState.value.offset, -curMaxScrollLeft);
    }
    if (scrollState.value.offset > leftIconWidth) {
      scrollState.value.offset = leftIconWidth;
    }
  }
};

// 左侧点击滚动
const handlePrev = () => {
  if (scrollState.value.offset < leftIconWidth) {
    scrollState.value.offset = Math.min(scrollState.value.offset + curScrollOffset, leftIconWidth);
    prevDisabled.value = true;
  }
  else {
    prevDisabled.value = false;
    nextDisabled.value = true;
  }
};

// 右侧点击滚动
const handleNext = () => {
  // 边界判断
  if (Math.abs(scrollState.value.offset) < maxScrollLeft.value) {
    scrollState.value.offset = Math.max(scrollState.value.offset - curScrollOffset, -maxScrollLeft.value);
    isNextClick = true;
    nextDisabled.value = true;
  }
  else {
    isNextClick = true;
    nextDisabled.value = false;
    prevDisabled.value = true;
  }
};

onMounted(() => {
  setTimeout(async () => {
    stageList.value = await getStageList(gatewayId.value);
  });
});
</script>

<style lang="scss" scoped>
.stage-top-bar {
  position: absolute;
  top: -1px;

  // top: 42px;
  display: flex;
  width: calc(100% - 48px);
  height: 52px;
  background: #fff;
  justify-content: space-between;
  align-items: center;

  .top-title-wrapper {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    width: 326px;
  }

  .title {
    font-size: 16px;
    color: #313238;
  }

  .model-type {
    display: flex;
    height: 32px;
    padding: 4px;
    margin-right: 8px;
    margin-left: 18px;
    color: #63656e;
    background: #f0f1f5;
    border-radius: 2px;
    align-items: center;

    .item {
      padding: 0 10px;
      font-size: 12px;
      line-height: 24px;

      &:hover {
        cursor: pointer;
      }

      &.active {
        color: #3a84ff;
        background: #fff;
        border-radius: 2px;
      }
    }
  }

  .stage-list-container {
    position: relative;
    display: flex;
    height: 100%;
    min-width: 360px;
    overflow: hidden;
    flex: 1;
  }

  .stage-list {
    position: relative;
    display: flex;
    height: 100%;
    transform: translateX(24px);
    transition: all .3s;

    .stage-item {
      display: flex;
      width: 100px;
      height: 100%;
      padding: 0 5px;
      font-size: 14px;
      color: #63656e;
      cursor: pointer;
      box-sizing: border-box;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      span {
        display: inline-block;
        padding-left: 6px;
        overflow: hidden;
        text-align: center;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;

        &.success {
          background: #E5F6EA;
          border: 1px solid #3FC06D;
        }

        &.unreleased {
          background: #F0F1F5;
          border: 1px solid #C4C6CC;
        }

        &.delist {
          background: #F0F1F5;
          border: 1px solid #C4C6CC;
        }

        &.failure {
          background: #FFE6E6;
          border: 1px solid #EA3636;
        }
      }

      &:hover {
        background-color: #f0f5ff;
      }

      &.active {
        font-weight: bold;
        color: #3a84ff;
        background-color: #f0f5ff;
        border-top: 3px solid #3a84ff;
      }
    }
  }

  .add-stage-icon,
  .icon-ag-pa-arrow-left,
  .icon-ag-ps-arrow-right {
    position: absolute;
    top: 50%;
    right: 0;
    height: 52px;
    background: #fff;
    transform: translateY(-50%);
  }

  .notposition {
    position: relative;
    right: -28px;
  }

  .icon-ag-pa-arrow-left,
  .icon-ag-ps-arrow-right {
    width: 24px;
    font-size: 16px;
    font-weight: 700;
    line-height: 51px;
    color: #979ba5;
    cursor: not-allowed;
  }

  .icon-ag-pa-arrow-left {
    left: 0;
    box-shadow: 4px 0 8px 0 #0000001a;
  }

  .icon-ag-ps-arrow-right {
    right: 28px;
    box-shadow: -4px 0 8px 0 #0000001a;
  }

  .icon-arrow-enable {
    cursor: pointer;

    &:hover {
      color: #3a84ff;
      background: #F0F5FF;
    }
  }
}
</style>
