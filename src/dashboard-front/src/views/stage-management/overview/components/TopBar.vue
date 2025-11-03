/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

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
          @click="() => switchMode(item)"
        >
          {{ item?.text }}
        </div>
      </div>
    </div>
    <!-- 详情模式环境 -->
    <div
      v-if="mode === 'detail-mode'"
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
            v-bk-tooltips="{
              content: getStageStatus(stage) === 'unreleased' ? t('未发布') : t('未上线'),
              disabled: !['unreleased', 'delist'].includes(getStageStatus(stage))
            }"
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
    <CreateStage
      ref="stageSidesliderRef"
      @done="handleCreateDone"
    />
  </div>
</template>

<script setup lang="ts">
import { type IStageListItem, getStageList } from '@/services/source/stage';
import { Spinner } from 'bkui-vue/lib/icon';
import { getStageStatus } from '@/utils';
import { useGateway, useStage } from '@/stores';
import CreateStage from '@/views/stage-management/overview/components/CreateStage.vue';

interface IProps { stageId: number | string }

const mode = defineModel<string>('mode', { default: 'card-mode' });
const { stageId } = defineProps<IProps>();

const emit = defineEmits<{ 'change-stage': [stageId: number] }>();

const { t } = useI18n();
const gatewayStore = useGateway();
const stageStore = useStage();

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
    key: 'card-mode',
    text: t('缩略模式'),
    routeName: 'StageOverviewCardMode',
  },
  {
    key: 'detail-mode',
    text: t('详情模式'),
    routeName: 'StageOverviewDetailMode',
  },
];

const gatewayId = computed(() => gatewayStore.apigwId);

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
const switchMode = (item: typeof modeList[number]) => {
  mode.value = item.key;
  const firstStage = stageList.value[0];
  if (firstStage) {
    curStage.value = firstStage;
    // stageId.value = firstStage.id;
  }
};

// 切换环境
const handleChangeStage = async (stage: IStageListItem) => {
  setStageInfo(stage);
  emit('change-stage', stage.id);
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

const handleCreateDone = async () => {
  stageList.value = await getStageList(gatewayId.value);
  const lastStage = stageList.value[stageList.value.length - 1];
  if (lastStage) {
    handleChangeStage(lastStage);
  }
};

const setStageInfo = (stage) => {
  curStage.value = stage;
  stageStore.curStageData = curStage.value;
  stageStore.curStageId = curStage.value.id;
  stageStore.setStageList(stageList.value);
};

onMounted(() => {
  setTimeout(async () => {
    stageList.value = await getStageList(gatewayId.value);
    if (stageList.value?.length) {
      setStageInfo(stageList.value[0]);
      emit('change-stage', curStage.value.id);
    }
  });
});

defineExpose({
  reload: async () => {
    stageList.value = await getStageList(gatewayId.value);
  },
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
