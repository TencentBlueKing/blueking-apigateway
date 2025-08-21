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
  <div class="detail-mode">
    <BkAlert
      v-if="currentStage?.status === 0 && currentStage?.release.status !== 'unreleased'"
      theme="warning"
      :title="t('当前环境已下架，所有内容的更新均不会生效，如需重新启用，需要重新发布')"
      class="mb-16px"
    />
    <BkAlert
      v-if="gatewayStore.isProgrammableGateway"
      :title="t('可编程网关的环境由平台内置，不能修改和新增')"
      class="mb-24px"
      closable
    />
    <BkLoading :loading="isStageLoading">
      <section class="stage-info">
        <div
          class="stage-name"
          :class="[currentStage?.release.status === 'unreleased' ? 'no-release' : '']"
        >
          <template v-if="currentStage?.release.status === 'unreleased'">
            <span class="no-release-label">{{ t('未发布') }}</span>
            <span class="no-release-label">{{ t('未发布') }}</span>
            <span class="no-release-dot" />
          </template>
          <span class="name">
            {{ currentStage?.name || '--' }}
          </span>
        </div>
        <div class="info">
          <div class="column">
            <div class="apigw-form-item">
              <div class="label">
                {{ `${t('访问地址')}：` }}
              </div>
              <div class="value url">
                <p
                  v-bk-tooltips="{ content: getStageAddress(currentStage?.name) }"
                  class="link"
                >
                  {{ getStageAddress(currentStage?.name) || '--' }}
                </p>
                <CopyButton
                  v-if="getStageAddress(currentStage?.name)"
                  :source="getStageAddress(currentStage?.name)"
                />
              </div>
            </div>
            <div class="apigw-form-item">
              <div class="label">
                {{ `${t('当前资源版本')}：` }}
              </div>
              <div class="value">
                <span
                  v-if="currentStage?.release.status === 'unreleased'"
                  class="unrelease"
                >
                  --
                </span>
                <span v-else>{{ currentStage?.resource_version.version || '--' }}</span>
                <BkTag
                  v-if="getStageStatus(currentStage) === 'doing'"
                  class="ml-8px h-16px text-10px"
                  theme="info"
                >
                  {{ currentStage?.publish_version }} {{ t('发布中') }}
                </BkTag>
              </div>
            </div>
            <div class="apigw-form-item">
              <div class="label">
                {{ `${t('描述')}：` }}
              </div>
              <div class="value">
                {{ currentStage?.description || '--' }}
              </div>
            </div>
          </div>
          <div class="column">
            <div class="apigw-form-item">
              <div class="label">
                {{ `${t('发布人')}：` }}
              </div>
              <div class="value">
                <span v-if="!featureFlagStore.isTenantMode">{{ currentStage?.release.created_by || '--' }}</span>
                <span v-else><bk-user-display-name :user-id="currentStage?.release.created_by" /></span>
              </div>
            </div>
            <div class="apigw-form-item">
              <div class="label">
                {{ `${t('发布时间')}：` }}
              </div>
              <div class="value">
                {{ currentStage?.release.created_time || '--' }}
              </div>
            </div>
            <div class="apigw-form-item">
              <div class="label">
                {{ `${t('创建时间')}：` }}
              </div>
              <div class="value">
                {{ currentStage?.created_time || '--' }}
              </div>
            </div>
          </div>
        </div>
        <div class="operate">
          <div class="line" />
          <BkButton
            v-if="gatewayStore.currentGateway?.status === 0"
            v-bk-tooltips="{ content: t('当前网关已停用，如需使用，请先启用'), delay: 300 }"
            class="mr-10px"
            disabled
            theme="primary"
          >
            {{ t('发布资源') }}
          </BkButton>
          <BkButton
            v-else
            v-bk-tooltips="{
              content: getStageStatus(currentStage) === 'doing'
                ? t('当前有版本正在发布，请稍后再操作')
                : (currentStage?.publish_validate_msg || '--'),
              disabled: getStageStatus(currentStage) !== 'doing' && !currentStage?.publish_validate_msg
            }"
            theme="primary"
            class="mr-10px"
            :disabled="!!currentStage?.publish_validate_msg || getStageStatus(currentStage) === 'doing'"
            @click="handleRelease"
          >
            {{ t('发布资源') }}
          </BkButton>
          <BkButton
            v-if="!gatewayStore.isProgrammableGateway"
            v-bk-tooltips="{
              content: t('当前有版本正在发布，请稍后再操作'),
              disabled: getStageStatus(currentStage) !== 'doing'
            }"
            class="mr-10px"
            :disabled="getStageStatus(currentStage) === 'doing'"
            @click="handleEditStage"
          >
            {{ t('编辑') }}
          </BkButton>
          <BkDropdown
            v-model:is-show="showDropdown"
            trigger="click"
          >
            <BkButton
              class="more-cls"
              @click="showDropdown = true"
            >
              <AgIcon
                name="gengduo"
                size="16"
              />
            </BkButton>
            <template #content>
              <BkDropdownMenu ext-cls="stage-more-actions">
                <BkDropdownItem
                  v-bk-tooltips="
                    currentStage?.release.status === 'unreleased' ?
                      t('尚未发布，不可下架') :
                      currentStage?.status === 0 && currentStage?.release.status !== 'unreleased' ?
                        t('已下架') :
                        t('下架环境')"
                  :ext-cls="currentStage?.status !== 1 ? 'disabled' : ''"
                  @click="currentStage?.status === 1 ? handleStageUnlist() : void 0"
                >
                  {{ t('下架') }}
                </BkDropdownItem>
                <BkDropdownItem
                  v-if="!gatewayStore.isProgrammableGateway"
                  v-bk-tooltips="currentStage?.status === 1 ? t('环境下架后，才能删除') : t('删除环境')"
                  :ext-cls="currentStage?.status !== 0 ? 'disabled' : ''"
                  @click="currentStage?.status === 0 ? handleStageDelete() : void 0"
                >
                  {{ t('删除') }}
                </BkDropdownItem>
              </BkDropdownMenu>
            </template>
          </BkDropdown>
        </div>
      </section>
    </BkLoading>
    <div class="mt-15px">
      <BkAlert
        v-if="gatewayStore.isProgrammableGateway"
        class="mb-15px"
      >
        <template #title>
          <div>
            <span>{{ t('可编程网关的配置信息（如后端服务、插件配置、变量配置等）均在代码仓库中声明。') }}</span>
            <BkButton
              text
              theme="primary"
              @click="handleDevGuideClick"
            >
              {{ t('查看开发指南') }}
            </BkButton>
          </div>
        </template>
      </BkAlert>
      <BkAlert
        v-else
        class="mb-15px"
        theme="warning"
      >
        <template #title>
          <div>
            {{ t('修改环境的配置信息（含后端服务配置、插件配置、变量配置）后，会') }}<span
              class="stress"
            >{{ t('立即在线上环境生效，请谨慎操作') }}</span>
          </div>
        </template>
      </BkAlert>
    </div>
    <div class="tab-wrapper">
      <BkTab
        v-model:active="active"
        type="card-tab"
        @change="handleTabChange"
      >
        <BkTabPanel
          v-for="item in panels"
          :key="item.name"
          :name="item.name"
          :label="item.label"
          render-directive="if"
        >
          <component
            :is="componentMap[item.name as keyof typeof componentMap]"
            ref="tabComponentRefs"
            :stage-address="getStageAddress(currentStage?.name)"
            :version-id="currentStage?.resource_version?.id"
            :stage-id="stageId"
            :stage="currentStage"
          />
        </BkTabPanel>
      </BkTab>
    </div>

    <!-- 新建/编辑环境 -->
    <CreateStage
      ref="stageSidesliderRef"
      :stage-id="stageId"
      @done="handleCreateStageDone"
    />

    <!-- 发布普通网关的资源至环境 -->
    <ReleaseStage
      ref="releaseStageRef"
      :current-assets="currentStage"
      @release-success="handleReleaseSuccess"
      @closed-on-publishing="handleClosedOnPublishing"
    />

    <!-- 发布可编程网关的资源至环境 -->
    <ReleaseProgrammable
      ref="releaseProgrammableRef"
      :current-stage="currentStage"
      @hidden="handleReleaseSuccess"
      @release-success="handleReleaseSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { Message } from 'bkui-vue';
import { getStageStatus } from '@/utils';
import {
  type IStageListItem,
  deleteStage,
  getStageDetail,
  toggleStatus,
} from '@/services/source/stage';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
} from '@/stores';
import ReleaseProgrammable from '../components/ReleaseProgrammable.vue';
import CreateStage from '../components/CreateStage.vue';
import ReleaseStage from '@/components/release-stage/Index.vue';
import { usePopInfoBox } from '@/hooks';
import ResourceInfo from './components/ResourceInfo.vue';
import PluginManagement from './components/PluginManagement.vue';
import VarManagement from './components/VarManagement.vue';

interface IProps { stageId: number }

const { stageId } = defineProps<IProps>();

const emit = defineEmits<{ updated: [void] }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();
// 当前环境信息
const currentStage = ref<IStageListItem | null>(null);
const releaseStageRef = ref();
const releaseProgrammableRef = ref();
const stageSidesliderRef = ref();
const tabComponentRefs = ref();

const showDropdown = ref(false);

// 当前激活name
const active = ref('resourceInfo');

// 是否正在删除
const isDeleteLoading = ref(false);
const isStageLoading = ref(false);

// tab 选项卡
const panels = [
  {
    name: 'resourceInfo',
    label: t('资源信息'),
  },
  {
    name: 'pluginManagement',
    label: t('插件管理'),
  },
  {
    name: 'varManagement',
    label: t('变量管理'),
  },
];

const componentMap = {
  resourceInfo: ResourceInfo,
  pluginManagement: PluginManagement,
  varManagement: VarManagement,
};

// 网关id
const gatewayId = computed(() => Number(route.params.id));

watch(
  () => stageId,
  async () => {
    if (stageId) {
      currentStage.value = await getStageDetail(gatewayId.value, stageId);
    }
  },
  { immediate: true },
);

watch(
  () => route.query,
  () => {
    if (route.query.tab) {
      active.value = route.query.tab as string;
    }
  },
  { immediate: true },
);

// 发布成功，重新请求环境详情
const handleReleaseSuccess = async () => {
  currentStage.value = await getStageDetail(gatewayId.value, stageId);
  // await mitt.emit('rerun-init');
  emit('updated');
  tabComponentRefs.value?.forEach((component: InstanceType<typeof ResourceInfo>) => {
    component.reload?.();
  });
};

// 处理在版本还在发布时关闭抽屉的情况（刷新 stage 状态）
const handleClosedOnPublishing = async () => {
  // mitt.emit('rerun-init');
  emit('updated');
  currentStage.value = await getStageDetail(gatewayId.value, stageId);
};

// 选项卡切换
const handleTabChange = (name: string) => {
  active.value = name;
  // 更新query参数
  router.push({ query: { tab: name } });
};

// 发布资源
const handleRelease = () => {
  // 普通网关
  if (gatewayStore.currentGateway?.kind !== 1) {
    releaseStageRef.value?.showReleaseSideslider();
  }
  else {
    // 可编程网关
    releaseProgrammableRef.value?.showReleaseSideslider();
  }
};

// 下架环境
const handleStageUnlist = async () => {
  showDropdown.value = false;
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t('确认下架环境？'),
    subTitle: t('可能会导致正在使用该接口的服务异常，请确认'),
    confirmText: t('确认下架'),
    confirmButtonTheme: 'primary',
    contentAlign: 'left',
    showContentBgColor: true,
    onConfirm: async () => {
      if (isDeleteLoading.value) {
        return;
      }
      isDeleteLoading.value = true;
      const data = { status: 0 };
      try {
        await toggleStatus(gatewayId.value, currentStage.value!.id, data);
        Message({
          message: t('下架成功'),
          theme: 'success',
        });
        // 获取网关列表
        // await mitt.emit('rerun-init');
        emit('updated');
        currentStage.value = await getStageDetail(gatewayId.value, stageId);
        tabComponentRefs.value?.forEach((component: InstanceType<typeof ResourceInfo>) => {
          component.reload?.();
        });
        // 开启loading
      }
      finally {
        showDropdown.value = false;
      }
    },
  });
};

// 删除环境
const handleStageDelete = async () => {
  showDropdown.value = false;
  if (currentStage.value!.name === 'prod') {
    return Message({
      message: t('prod 环境不可删除'),
      theme: 'warning',
    });
  }
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t('确认删除吗？'),
    confirmText: t('确认删除'),
    confirmButtonTheme: 'primary',
    contentAlign: 'left',
    showContentBgColor: true,
    onConfirm: async () => {
      await deleteStage(gatewayId.value, currentStage.value!.id);
      Message({
        message: t('删除成功'),
        theme: 'success',
      });
      // 获取网关列表
      // await mitt.emit('rerun-init', {
      //   isUpdate: false,
      //   isDelete: true,
      // });
      emit('updated');
      // 切换前一个环境, 并且不需要获取当前环境详情
      // await mitt.emit('switch-stage', true);
      router.replace({ name: 'StageOverviewCardMode' });
      // 开启loading
    },
  });
};

// 编辑环境
const handleEditStage = () => {
  stageSidesliderRef.value.handleShowSideslider('edit');
};

const handleCreateStageDone = async () => {
  currentStage.value = await getStageDetail(gatewayId.value, stageId);
};

// 访问地址
const getStageAddress = (name?: string) => {
  if (!name) return '';

  const keys: any = {
    api_name: gatewayStore.currentGateway?.name,
    stage_name: name,
    resource_path: '',
  };

  let url = envStore.env.BK_API_RESOURCE_URL_TMPL;
  for (const name of Object.keys(keys)) {
    const reg = new RegExp(`{${name}}`);
    url = url?.replace(reg, keys[name]);
  }
  return url;
};

const handleDevGuideClick = () => {
  const lang = gatewayStore.currentGateway?.extra_info?.language || 'python';
  if (lang === 'python') {
    window.open('https://github.com/TencentBlueKing/bk-apigateway-framework/blob/master/docs/python.md');
  }
  else {
    window.open('https://github.com/TencentBlueKing/bk-apigateway-framework/blob/master/docs/golang.md');
  }
};
</script>

<style lang="scss" scoped>
.detail-mode {
  min-width: calc(1280px - 260px);
  font-size: 12px;

  .stage-info {
    display: flex;
    min-height: 128px;
    padding: 24px;
    background: #fff;
    box-shadow: 0 2px 4px 0 #1919290d;

    .stage-name {
      position: relative;
      display: flex;
      width: 120px;
      height: 80px;
      margin-right: 35px;
      background-color: #f0f5ff;
      border-radius: 8px;
      align-items: center;
      justify-content: center;

      &.no-release {
        background-color: #f0f1f5;

        .name {
          color: #979ba5;
        }
      }

      .no-release-dot {
        width: 8px;
        height: 8px;
        margin-right: 2px;
        background: #f0f1f5;
        border: 1px solid #c4c6cc;
        border-radius: 50%;
      }

      .no-release-label {
        position: absolute;
        top: 3px;
        left: 3px;
        padding: 2px 6px;
        font-size: 12px;
        color: #63656e;
        background-color: #fafbfd;
        border-radius: 2px;
      }

      .no-release-icon {
        position: absolute;
        top: 3px;
        right: 3px;
        padding: 4px;
        font-size: 14px;
        color: #979ba5;
        cursor: pointer;
        background-color: #fff;
        border-radius: 4px;
      }
    }

    .name {
      display: inline-block;
      padding: 0 3px;
      overflow: hidden;
      font-size: 16px;
      font-weight: 700;
      color: #3a84ff;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .info {
    display: flex;

    .column {
      transform: translateY(-8px);

      &:first-child {
        margin-right: 80px;
      }
    }

    .apigw-form-item {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      line-height: 32px;
      color: #63656e;

      .value {
        max-width: 220px;
        color: #313238;

        &.url {
          display: flex;
          max-width: 200px;
          align-items: center;

          .link {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          i {
            padding: 3px;
            margin-left: 3px;
            font-size: 12px;
            color: #3a84ff;
            cursor: pointer;
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
  }

  .operate {
    display: flex;
    margin-left: 40px;

    .line {
      width: 1px;
      height: 32px;
      margin-right: 20px;
      background: #dcdee5;
    }
  }
}

.tab-wrapper {
  font-size: 14px;
  background: #fff;
  border-radius: 0 0 2px 2px;
  box-shadow: 0 2px 4px 0 #1919290d;

  :deep(.bk-tab-panel) {
    min-height: 420px;
  }

  :deep(.bk-tab-content) {
    padding: 24px;
  }
}

.stage-more-actions {

  :deep(.disabled) {
    color: #c4c6cc !important;
    cursor: not-allowed;
    background-color: #fff !important;
    border-color: #dcdee5 !important;
  }
}

.more-cls {
  padding: 5px 7px;

  i {
    font-size: 16px;
    transform: rotate(90deg);
  }
}

.stress {
  color: red;
}
</style>
