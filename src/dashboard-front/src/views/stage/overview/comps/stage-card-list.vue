<template>
  <BkLoading :loading="isLoading">
    <div class="card-list">
      <StageCardItem
        v-for="stage in stageList"
        :key="stage.id"
        :stage="stage"
        @click="handleToDetail(stage)"
        @delist="() => handleStageUnlist(stage.id)"
        @publish="() => handleRelease(stage)"
        @check-log="() => showLogs(stage)"
      />

      <div v-if="!common.isProgrammableGateway" class="card-item add-stage" @click="handleAddStage">
        <i class="apigateway-icon icon-ag-add-small" />
      </div>

      <!-- 环境侧边栏 -->
      <edit-stage-sideslider ref="stageSidesliderRef" />

      <!-- 发布资源至环境 -->
      <release-sideslider
        ref="releaseSidesliderRef"
        :current-assets="currentStage"
        @hidden="handleReleaseSuccess(false)"
        @release-success="handleReleaseSuccess"
      />

      <!-- 发布可编程网关的资源至环境 -->
      <ReleaseProgrammableSlider
        ref="releaseProgrammableSliderRef"
        :current-stage="currentStage"
        @hidden="handleReleaseSuccess(false)"
        @release-success="handleReleaseSuccess"
        @closed-on-publishing="handleSliderHideWhenPending"
      />

      <!-- 日志抽屉 -->
      <log-details ref="logDetailsRef" :history-id="historyId" />

      <!-- 可编程网关日志抽屉 -->
      <ProgrammableEventSlider
        ref="programmableEventSliderRef"
        :deploy-id="deployId"
        :history-id="historyId"
        :stage="currentStage"
        @retry="handleRetry"
        @hide-when-pending="handleSliderHideWhenPending"
      />
    </div>
  </BkLoading>
</template>

<script setup lang="ts">
import {
  computed,
  onBeforeMount,
  onMounted,
  onUnmounted,
  ref,
  watch,
} from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import logDetails from '@/components/log-details/index.vue';
import mitt from '@/common/event-bus';
import {
  useCommon,
  useStage,
} from '@/store';
import {
  getGateWaysInfo,
  getStageList,
  removalStage,
} from '@/http';
import { BasicInfoParams } from '@/views/basic-info/common/type';
import editStageSideslider from './edit-stage-sideslider.vue';
import releaseSideslider from './release-sideslider.vue';
import ReleaseProgrammableSlider from './release-programmable-slider.vue';
import StageCardItem from '@/views/stage/overview/comps/stage-card-item.vue';
import { getProgrammableStageDetail } from '@/http/programmable';
import { useTimeoutPoll } from '@vueuse/core';
import ProgrammableEventSlider from '@/components/programmable-deploy-events-slider/index.vue';

const { t } = useI18n();
const route = useRoute();
const common = useCommon();
const stageStore = useStage();

const historyId = ref<number | undefined>(undefined);
const deployId = ref<string | undefined>(undefined);
const currentStage = ref<any>({});

const releaseSidesliderRef = ref();
const releaseProgrammableSliderRef = ref();
const logDetailsRef = ref(null);
const programmableEventSliderRef = ref(null);

// 当前基本信息
const basicInfoData = ref<BasicInfoParams>({
  status: 1,
  name: '',
  url: '',
  description: '',
  description_en: '',
  public_key_fingerprint: '',
  bk_app_codes: '',
  docs_url: '',
  api_domain: '',
  created_by: '',
  created_time: '',
  public_key: '',
  maintainers: [],
  developers: [],
  is_public: true,
  is_official: false,
  related_app_codes: '',
  kind: 0,
});

const stageList = ref<any[]>([]);
const stageSidesliderRef = ref(null);
const isLoading = ref(false);

const fetchStageList = async () => {
  isLoading.value = true;
  const response = await getStageList(common.apigwId);
  const _stageList = response || [];
  setTimeout(() => {
    stageStore.setStageMainLoading(false);
  }, 200);

  // 获取可编程网关的 stage 详情
  if (basicInfoData.value.kind === 1) {
    const tasks: ReturnType<typeof getProgrammableStageDetail>[] = [];

    for (const stage of _stageList) {
      tasks.push(getProgrammableStageDetail(common.apigwId, stage.id));
    }

    const responses = await Promise.all(tasks);

    for (let i = 0; i < _stageList.length; i++) {
      _stageList[i].paasInfo = responses[i];
    }
  }
  stageList.value = _stageList || [];
  stageStore.setStageList(_stageList);
  isLoading.value = false;

  if (stageList.value.every((stage) => {
    let _status = '';
    if (stage.paasInfo?.latest_deployment?.status) {
      _status = stage?.paasInfo.latest_deployment.status;
    } else if (stage.paasInfo?.status) {
      _status = stage.paasInfo.status;
    } else if (stage.release?.status) {
      _status = stage.release.status;
    }
    return _status !== 'doing' && _status !== 'pending';
  })) {
    pausePollingStages();
  }
};

const {
  pause: pausePollingStages,
  resume: startPollingStages,
} = useTimeoutPoll(fetchStageList, 10000, {
  immediate: false,
});

// 网关id
const apigwId = computed(() => +route.params.id);

watch(() => common.curApigwData, () => {
  pausePollingStages();
  if (!common.curApigwData?.id) {
    return;
  }
  startPollingStages();
}, { immediate: true, deep: true });

// 环境详情
const handleToDetail = (data: any) => {
  mitt.emit('switch-mode', { id: data.id, name: data.name });
};

// 发布资源
const handleRelease = async (stage: any) => {
  currentStage.value = stage;
  // 普通网关
  if (!common.isProgrammableGateway) {
    releaseSidesliderRef.value?.showReleaseSideslider();
  } else {
    // 可编程网关
    releaseProgrammableSliderRef.value?.showReleaseSideslider();
  }
};

// 发布成功
const handleReleaseSuccess = async (loading = true) => {
  await mitt.emit('get-environment-list-data', loading);
};

// 查看日志
const showLogs = (stage: any) => {
  currentStage.value = stage;
  // 普通网关
  if (!common.isProgrammableGateway) {
    deployId.value = undefined;
    historyId.value = stage.publish_id;
    logDetailsRef.value?.showSideslider();
  } else {
    // 可编程网关
    historyId.value = undefined;
    if (stage.paasInfo?.latest_deployment?.deploy_id) {
      deployId.value = stage.paasInfo.latest_deployment.deploy_id;
    } else {
      deployId.value = stage.paasInfo?.deploy_id;
    }
    programmableEventSliderRef.value?.showSideslider();
  }
};

// 下架环境
const handleStageUnlist = async (id: number) => {
  InfoBox({
    infoType: 'warning',
    title: t('确认下架环境？'),
    subTitle: t('可能会导致正在使用该接口的服务异常，请确认'),
    confirmText: t('确认下架'),
    onConfirm: async () => {
      const data = {
        status: 0,
      };
      try {
        await removalStage(apigwId.value, id, data);
        Message({
          message: t('下架成功'),
          theme: 'success',
        });
        // 获取网关列表
        await mitt.emit('get-environment-list-data', true);
        // 开启loading
      } catch (error) {
        console.error(error);
      }
    },
  });
};

const handleAddStage = () => {
  stageSidesliderRef.value.handleShowSideslider('add');
};

// 获取网关基本信息
const getBasicInfo = async (apigwId: number) => {
  const res = await getGateWaysInfo(apigwId);
  basicInfoData.value = Object.assign({}, res);
};

const handleRetry = async () => {
  await fetchStageList();
  releaseProgrammableSliderRef.value?.showReleaseSideslider();
};

const handleSliderHideWhenPending = () => {
  pausePollingStages();
  fetchStageList();
  startPollingStages();
};

onBeforeMount(async () => {
  await getBasicInfo(common.apigwId);
});

onMounted(async () => {
  await fetchStageList();
});

onUnmounted(() => {
  pausePollingStages();
});

</script>

<style lang="scss" scoped>
.card-list {
  min-width: calc(1280px - 260px);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-gap: 18px; /* 设置盒子之间的间隔 */
}

/* 分辨率大于1920时 */
@media (min-width: 1921px) {
  .card-list {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* 适应更小的分辨率，每行最多显示三个盒子 */
@media (max-width: 1920px) {
  .card-list {
    grid-template-columns: repeat(3, 1fr);
  }
}

.card-item {
  font-size: 12px;
  height: 238px;
  background: #ffffff;
  padding: 0 24px;
  box-shadow: 0 2px 4px 0 #1919290d;;
  border-radius: 2px;
  &:hover {
    box-shadow: 0 2px 4px 0 #0000001a, 0 2px 4px 0 #1919290d;
  }

  .title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 52px;
    border-bottom: 1px solid #DCDEE5;
    .title-lf {
      display: flex;
      align-items: center;
      font-size: 14px;
      font-weight: 700;
      color: #313238;
      span {
        margin-right: 8px;
      }
    }
    .title-rg {
      display: flex;
    }
  }

  .content {
    padding-top: 16px;
    font-size: 12px;
    cursor: pointer;
    .apigw-form-item {
      display: flex;
      align-items: center;
      line-height: 32px;
      color: #63656e;

      .label {
        padding-right: 8px;
        width: 120px;
        text-align: right;
        &.en {
          width: 158px;
        }
      }

      .value {
        max-width: 220px;
        color: #313238;
        flex-shrink: 0;

        &.url {
          max-width: 280px;
          display: flex;
          align-items: center;

          .link {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            color: #313238;
          }

          i {
            cursor: pointer;
            color: #3A84FF;
            margin-left: 3px;
            font-size: 12px;
            padding: 3px;
          }
        }
      }
    }

    .unrelease {
      display: inline-block;
      font-size: 10px;
      border-radius: 2px;
      padding: 2px 5px;
      line-height: 1;
    }
  }

  &.add-stage {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;

    i {
      color: #979BA5;
      font-size: 40px;
    }

    &:hover {
      cursor: pointer;
      i {
        color: #3A84FF;
      }
    }
  }


  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    cursor: pointer;
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
}</style>
