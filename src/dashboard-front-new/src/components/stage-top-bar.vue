<template>
  <div class="stage-top-bar">
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
    <!-- 详情模式环境 -->
    <ul
      v-if="curActive === 'detail'"
      class="stage-list"
    >
      <li
        v-for="(item, index) in stageStore.stageList"
        :key="index"
        class="stage-item"
        :title="item?.name"
        :class="{ active: curStage?.name === item?.name }"
        @click="handleChangeStage(item?.name)"
      >
        <spinner v-if="item?.release.status === 'doing'" fill="#3A84FF" />
        <span v-else :class="['dot', item?.release.status]"></span>
        <span v-overflow-title>{{ item?.name }}</span>
      </li>
    </ul>

    <plus
      v-if="curActive === 'detail'"
      fill="#3785ff"
      @click="handleAddStage"
      style="font-size: 28px; cursor: pointer;"
    />

    <!-- 环境侧边栏 -->
    <edit-stage-sideslider ref="stageSidesliderRef" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onBeforeMount, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getStageList, getStageDetail } from '@/http';
import { useStage, useCommon } from '@/store';
import { useI18n } from 'vue-i18n';
import mitt from '@/common/event-bus';
import { Spinner, Plus } from 'bkui-vue/lib/icon';
import editStageSideslider from '@/views/stage/overview/comps/edit-stage-sideslider.vue';

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

const init = async (isUpdate?: Boolean, isDelete?: Boolean) => {
  stageStore.setStageMainLoading(true);
  try {
    const data = await getStageList(apigwId.value);
    stageStore.setStageList(data);

    if (route.query?.stage) {
      curStage.value = stageStore.stageList?.find(stage => stage.name === route.query.stage);
    } else if (!isUpdate) { // 更新停留当前环境
      curStage.value = data[0];
    }
    if (!isDelete) {
      getStageDetailFun(curStage.value?.id);
    }
  } catch (error) {
    console.error(error);
  } finally {
    setTimeout(() => {
      stageStore.setStageMainLoading(false);
    }, 300);
  }
};
init();

// 是否为详情模式
const isDetailMode = computed(() => {
  return route.path.includes('/detail-mode');
});

// 当前环境概览模式
const curActive = ref(isDetailMode.value ? 'detail' : 'abbreviation');

// 获取环境详情
const getStageDetailFun = (id: number) => {
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
      id: route.params.id,
    },
    query: {
      stage: stageName || curStage.value.name,
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

onMounted(() => {
  // 事件总线监听重新获取环境列表
  mitt.on('get-stage-list', (data) => {
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
});

onBeforeMount(() => {
  mitt.off('get-stage-list');
  mitt.off('switch-mode');
  mitt.off('switch-stage');
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
  .stage-list {
    margin-left: 350px;
    height: 100%;
    display: flex;
    .stage-item {
      cursor: pointer;
      width: 100px;
      height: 100%;
      box-sizing: border-box;
      font-size: 14px;
      color: #63656e;
      display: flex;
      align-items: center;
      justify-content: center;
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
}
</style>
