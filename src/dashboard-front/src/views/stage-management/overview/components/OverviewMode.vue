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
  <div>
    <BkAlert
      v-if="gatewayStore.isProgrammableGateway"
      :title="t('可编程网关的环境由平台内置，不能修改和新增')"
      class="mb-24px"
      closable
    />
    <div>
      <BkLoading :loading="isLoading && !stageList.length">
        <div class="w-full" />
      </BkLoading>
      <div class="card-list">
        <StageCardItem
          v-for="stage in stageList"
          :key="stage.id"
          :loading="loadingProgrammableStageIds.includes(stage.id)"
          :stage="stage"
          @click="handleToDetail"
          @delist="() => handleStageUnlist(stage.id)"
          @publish="() => handleRelease(stage)"
          @check-log="() => showLogs(stage)"
        />

        <div
          v-if="!gatewayStore.isProgrammableGateway && !isLoading"
          class="card-item add-stage"
          @click="handleAddStage"
        >
          <AgIcon
            name="add-small"
            size="40"
          />
        </div>
      </div>
    </div>

    <!-- 新建/编辑环境 -->
    <CreateStage ref="stageSidesliderRef" />

    <!-- 发布普通网关的资源至环境 -->
    <ReleaseStage
      ref="releaseStageRef"
      :current-assets="currentStage"
      @hidden="handleReleaseSuccess"
      @release-success="handleReleaseSuccess"
      @closed-on-publishing="handleSliderHideWhenPending"
    />

    <!-- 发布可编程网关的资源至环境 -->
    <ReleaseProgrammable
      ref="releaseProgrammableRef"
      :current-stage="currentStage"
      @hidden="handleReleaseSuccess"
      @release-success="handleReleaseSuccess"
      @closed-on-publishing="handleSliderHideWhenPending"
    />

    <!-- 日志抽屉 -->
    <ReleaseStageEvent
      ref="logDetailsRef"
      :history-id="historyId"
      @release-doing="handleSliderHideWhenPending"
    />

    <!-- 可编程网关日志抽屉 -->
    <ReleaseProgrammableEvent
      ref="programmableEventSliderRef"
      :deploy-id="deployId"
      :history-id="historyId"
      :stage="currentStage"
      @retry="handleRetry"
      @hide-when-pending="handleSliderHideWhenPending"
    />
  </div>
</template>

<script setup lang="ts">
import StageCardItem from './StageCardItem.vue';
import { useGateway } from '@/stores';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import {
  type IStageListItem,
  getStageList,
  toggleStatus,
} from '@/services/source/stage';
import { getGatewayDetail } from '@/services/source/gateway';
import { getProgrammableStageDetail } from '@/services/source/programmable';
import { useTimeoutPoll } from '@vueuse/core';
import { useRouteParams } from '@vueuse/router';
import ReleaseStage from '@/components/release-stage/Index.vue';
import ReleaseProgrammable from './ReleaseProgrammable.vue';
import CreateStage from './CreateStage.vue';
import ReleaseStageEvent from '@/components/release-stage-event/Index.vue';
import ReleaseProgrammableEvent from '../../components/ReleaseProgrammableEvent.vue';

type GatewayDetailType = Awaited<ReturnType<typeof getGatewayDetail>>;

type IPaasInfo = Awaited<ReturnType<typeof getProgrammableStageDetail>>;

interface ILocalStageItem extends IStageListItem { paasInfo?: IPaasInfo }

const { t } = useI18n();
const route = useRoute();
const gatewayStore = useGateway();
const gatewayId = useRouteParams('id', 0, { transform: Number });

const historyId = ref<number>();
const deployId = ref<string>();
const currentStage = ref<IStageListItem | null>(null);

const releaseStageRef = ref();
const releaseProgrammableRef = ref();
const logDetailsRef = ref();
const programmableEventSliderRef = ref();

// 当前网关基本信息
const basicInfoData = ref<Partial<GatewayDetailType>>({
  status: 1,
  name: '',
  description: '',
  description_en: '',
  public_key_fingerprint: '',
  bk_app_codes: [],
  docs_url: '',
  api_domain: '',
  created_by: '',
  created_time: '',
  public_key: '',
  maintainers: [],
  developers: [],
  is_public: true,
  is_official: false,
  related_app_codes: [],
  kind: 0,
});

const stageList = ref<ILocalStageItem[]>([]);
const stageSidesliderRef = ref();
const isLoading = ref(false);
const loadingProgrammableStageIds = ref<number[]>([]);

const fetchStageList = async () => {
  isLoading.value = true;
  const response = await getStageList(gatewayId.value);
  const _stageList = response as ILocalStageItem[] || [];

  // 获取可编程网关的 stage 详情
  if (basicInfoData.value.kind === 1) {
    const tasks: (ReturnType<typeof getProgrammableStageDetail> | Promise<undefined>)[] = [];

    for (const stage of _stageList) {
      if (stage.publish_version) {
        tasks.push(getProgrammableStageDetail(gatewayId.value, stage.id));
        loadingProgrammableStageIds.value.push(stage.id);
      }
      else {
        tasks.push(Promise.resolve(undefined));
        const index = loadingProgrammableStageIds.value.findIndex(id => id === stage.id);
        if (index !== -1) {
          loadingProgrammableStageIds.value.splice(index, 1);
        }
      }
    }

    const responses = await Promise.all(tasks);

    for (let i = 0; i < _stageList.length; i++) {
      _stageList[i].paasInfo = responses[i];
    }
    loadingProgrammableStageIds.value = [];
  }
  stageList.value = _stageList || [];
  isLoading.value = false;

  // 所有环境都不是 doing 或 pending 状态时，暂停轮询
  if (stageList.value.every((stage) => {
    let _status = '';
    if (stage.paasInfo?.latest_deployment?.status) {
      _status = stage?.paasInfo.latest_deployment.status;
    }
    else if (stage.paasInfo?.status) {
      _status = stage.paasInfo.status;
    }
    else if (stage.release?.status) {
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
} = useTimeoutPoll(fetchStageList, 10000, { immediate: false });

// 网关id
const apigwId = computed(() => +route.params.id);

watch(() => gatewayStore.currentGateway, () => {
  pausePollingStages();
  if (!gatewayStore.currentGateway?.id) {
    return;
  }
  startPollingStages();
}, {
  immediate: true,
  deep: true,
});

// 环境详情
const handleToDetail = () => {
  if (isLoading.value) {
    return;
  }
  // mitt.emit('switch-mode', {
  //   id: data.id,
  //   name: data.name,
  // });
};

// 发布资源
const handleRelease = async (stage: IStageListItem) => {
  currentStage.value = stage;
  // 普通网关
  if (!gatewayStore.isProgrammableGateway) {
    releaseStageRef.value?.showReleaseSideslider();
  }
  else {
    // 可编程网关
    releaseProgrammableRef.value?.showReleaseSideslider();
  }
};

// 发布成功
const handleReleaseSuccess = () => {
  // await mitt.emit('get-environment-list-data', loading);
  emit('updated');
  fetchStageList();
};

// 查看日志
const showLogs = (stage: any) => {
  currentStage.value = stage;
  // 普通网关
  if (!gatewayStore.isProgrammableGateway) {
    deployId.value = undefined;
    historyId.value = stage.publish_id;
    logDetailsRef.value?.showSideslider();
  }
  else {
    // 可编程网关
    historyId.value = undefined;
    if (stage.paasInfo?.latest_deployment?.deploy_id) {
      deployId.value = stage.paasInfo.latest_deployment.deploy_id;
    }
    else {
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
      const data = { status: 0 };
      await toggleStatus(apigwId.value, id, data);
      Message({
        message: t('下架成功'),
        theme: 'success',
      });
      // 获取网关列表
      // await mitt.emit('get-environment-list-data', true);
      await fetchStageList();
      startPollingStages();
    },
  });
};

const handleAddStage = () => {
  stageSidesliderRef.value?.handleShowSideslider('add');
};

// 获取网关基本信息
const getBasicInfo = async (apigwId: number) => {
  basicInfoData.value = await getGatewayDetail(apigwId);
};

const handleRetry = async () => {
  await fetchStageList();
  releaseProgrammableRef.value?.showReleaseSideslider();
};

const handleSliderHideWhenPending = () => {
  pausePollingStages();
  fetchStageList();
  startPollingStages();
};

onBeforeMount(async () => {
  await getBasicInfo(gatewayId.value);
});

onMounted(() => {
  // 等待 route 变化后再获取环境列表
  setTimeout(() => {
    fetchStageList();
  });
  // mitt.on('rerun-init', () => {
  //   fetchStageList();
  // });
});

onUnmounted(() => {
  pausePollingStages();
});

</script>

<style lang="scss" scoped>

.card-list {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}

.card-item {
  height: 238px;
  padding: 0 24px;
  font-size: 12px;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;

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
        width: 120px;
        padding-right: 8px;
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
          display: flex;
          max-width: 280px;
          align-items: center;

          .link {
            overflow: hidden;
            color: #313238;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          i {
            padding: 3px;
            margin-left: 3px;
            font-size: 12px;
            color: #3A84FF;
            cursor: pointer;
          }
        }
      }
    }

    .unrelease {
      display: inline-block;
      padding: 2px 5px;
      font-size: 10px;
      line-height: 1;
      border-radius: 2px;
    }
  }

  &.add-stage {
    display: flex;
    width: 517px;
    cursor: pointer;
    align-items: center;
    justify-content: center;

    i {
      font-size: 40px;
      color: #979BA5;
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
    cursor: pointer;
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
}
</style>
