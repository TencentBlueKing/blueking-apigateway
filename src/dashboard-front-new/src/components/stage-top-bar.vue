<template>
  <div class="stage-top-bar">
    <div class="title">环境概览</div>
    <div class="model-type mr8">
      <div
        v-for="item in modelTypes"
        :key="item.key"
        :class="['item', { active: item.key === curActive }]"
        @click="switchModelType(item.key, item.routeName)"
      >
        {{ item.text }}
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
        :class="{ active: curStage.name === item.name }"
        @click="handleChangeStage(item.name)"
      >
        {{ item.name }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getStageList, getStageDetail } from '@/http';
import { useStage } from '@/store';
import mitt from '@/common/event-bus';
const router = useRouter();
const route = useRoute();
const stageStore = useStage();

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
const apigwId = +route.params.id;

// 当前环境
const curStage = ref(stageStore.curStageData || stageStore.defaultStage);

const init = async (isUpdate?: Boolean) => {
  stageStore.setStageMainLoading(true);
  try {
    const data = await getStageList(apigwId);
    stageStore.setStageList(data);

    // 更新停留当前环境
    if (!isUpdate) {
      curStage.value = data[0];
    }
    getStageDetailFun(curStage.value.id);
  } catch (error) {
    console.error(error);
  } finally {
    setTimeout(() => {
      stageStore.setStageMainLoading(false);
    }, 300);
  }
};
init();

// 事件总线监听重新获取环境列表
mitt.on('get-stage-list', (isUpdate) => {
  init(isUpdate);
});
// 切换概览模式
mitt.on('switch-mode', async (data) => {
  await getStageDetailFun(data.id);
  switchModelType('detail', 'apigwStageDetail', data.name);
});
// 切换环境
mitt.on('switch-stage', async () => {
  handleChangeStage(curStage.value.name);
});

// 是否为详情模式
const isDetailMode = computed(() => {
  return route.path.includes('/detail-mode');
});

// 当前环境概览模式
const curActive = ref(isDetailMode.value ? 'detail' : 'abbreviation');

// 获取环境详情
const getStageDetailFun = (id: number) => {
  stageStore.setStageMainLoading(true);
  getStageDetail(apigwId, id).then((data) => {
    stageStore.curStageData = data;
    curStage.value = data;
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
const handleChangeStage = async (name: string) => {
  // 获取切换环境的名字
  const data = stageStore.stageList.find(item => item.name === name);
  await getStageDetailFun(data.id);
  stageStore.curStageId = data.id;
  router.push({
    query: {
      stage: data.name,
    },
  });
};
</script>

<style lang="scss" scoped>
.stage-top-bar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
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
      width: 75px;
      height: 100%;
      font-size: 14px;
      color: #63656e;
      display: flex;
      align-items: center;
      justify-content: center;

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
