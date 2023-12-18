<template>
  <div>
    <!-- 自定义头部 -->
    <stage-top-bar ref="stageTopBarRef" />
    <div class="detail-mode">
      <bk-loading :loading="stageStore.realStageMainLoading">
        <section class="stagae-info">
          <div class="stage-name">
            <span class="name">{{ stageData.name }}</span>
          </div>
          <div class="info">
            <div class="column">
              <div class="apigw-form-item">
                <div class="label">{{ `${t('访问地址')}：` }}</div>
                <div class="value url">
                  <p
                    class="link"
                    v-overflow-title
                    v-bk-tooltips="{ content: getStageAddress(stageData.name) }"
                  >
                    {{ getStageAddress(stageData.name) || '--' }}
                  </p>
                  <i
                    class="apigateway-icon icon-ag-copy-info"
                    v-if="getStageAddress(stageData.name)"
                    @click.self.stop="copy(getStageAddress(stageData.name))"
                  ></i>
                </div>
              </div>
              <div class="apigw-form-item">
                <div class="label">{{ `${t('当前资源版本')}：` }}</div>
                <div class="value">
                  <span
                    class="unrelease"
                    v-if="stageData.release.status === 'unreleased'"
                  >
                    {{ t('尚未发布') }}
                  </span>
                  <span v-else>{{ stageData.resource_version.version || '--' }}</span>
                </div>
              </div>
              <div class="apigw-form-item">
                <div class="label">{{ `${t('描述')}：` }}</div>
                <div
                  class="value"
                  v-overflow-title
                >
                  {{ stageData.description || '--' }}
                </div>
              </div>
            </div>
            <div class="column">
              <div class="apigw-form-item">
                <div class="label">{{ `${t('发布人')}：` }}</div>
                <div class="value">
                  {{ stageData.release.created_by || '--' }}
                </div>
              </div>
              <div class="apigw-form-item">
                <div class="label">{{ `${t('发布时间')}：` }}</div>
                <div class="value">
                  {{ stageData.release.created_time || '--' }}
                </div>
              </div>
              <div class="apigw-form-item">
                <div class="label">{{ `${t('创建时间')}：` }}</div>
                <div class="value">
                  {{ stageData.created_time || '--' }}
                </div>
              </div>
            </div>
          </div>
          <div class="operate">
            <div class="line"></div>
            <bk-button
              theme="primary"
              class="mr10"
              @click="handleRelease"
            >
              {{ t('发布资源') }}
            </bk-button>
            <bk-button
              class="mr10"
              @click="handleEditStage"
            >
              {{ t('编辑') }}
            </bk-button>
            <bk-dropdown>
              <bk-button class="more-cls">
                <i class="apigateway-icon icon-ag-gengduo"></i>
              </bk-button>
              <template #content>
                <bk-dropdown-menu ext-cls="stage-more-actions">
                  <bk-dropdown-item @click="handleStageUnlist()">
                    {{ t('下架') }}
                  </bk-dropdown-item>
                  <bk-dropdown-item
                    :ext-cls="{ disabled: stageData.status === 1 }"
                    v-bk-tooltips="t('环境下线后，才能删除')"
                    @click="handleStageDelete()"
                  >
                    {{ t('删除') }}
                  </bk-dropdown-item>
                </bk-dropdown-menu>
              </template>
            </bk-dropdown>
          </div>
        </section>
        <bk-alert
          type="warning"
          title="环境所有配置信息的变更（包含后端服务配置，插件配置，变量配置）将直接影响至线上环境，请谨慎操作"
          class="mt15 mb15"
        ></bk-alert>
        <div class="tab-wrapper">
          <bk-tab
            v-model:active="active"
            type="card-tab"
            @change="handleTabChange"
          >
            <bk-tab-panel
              v-for="item in panels"
              :key="item.name"
              :name="item.name"
              :label="item.label"
              render-directive="if"
            >
              <router-view
                :ref="item.name"
                :stage-id="stageData.id"
                :key="routeIndex"
                :version-id="stageData.resource_version.id"
              ></router-view>
            </bk-tab-panel>
          </bk-tab>
        </div>
      </bk-loading>

      <!-- 环境侧边栏 -->
      <edit-stage-sideslider ref="stageSidesliderRef" />

      <!-- 发布资源至环境 -->
      <release-sideslider :current-assets="stageData" ref="releaseSidesliderRef" @release-success="handleReleaseSuccess" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { copy } from '@/common/util';
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useStage, useCommon } from '@/store';
import releaseSideslider from '../comps/release-sideslider.vue';
import editStageSideslider from '../comps/edit-stage-sideslider.vue';
import stageTopBar from '@/components/stage-top-bar.vue';
import { useGetGlobalProperties } from '@/hooks';
import { deleteStage, removalStage } from '@/http';
import { Message, InfoBox } from 'bkui-vue';
import mitt from '@/common/event-bus';

const { t } = useI18n();
const stageStore = useStage();
const route = useRoute();
const router = useRouter();
const common = useCommon();

// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

const releaseSidesliderRef = ref(null);
const stageSidesliderRef = ref(null);
const stageTopBarRef = ref(null);

// 当前环境信息
const stageData: any = computed(() => {
  if (stageStore.curStageData.id !== null) {
    return stageStore.curStageData;
  }
  return {
    name: '',
    description: '',
    description_en: '',
    status: 0,
    created_time: '',
    release: {
      status: '',
      created_time: null,
      created_by: '',
    },
    resource_version: '',
    new_resource_version: '',
  };
});

// 当前激活name
const active = ref('resourceInfo');
// tab 选项卡
const panels = [
  { name: 'resourceInfo', label: '资源信息', routeName: 'apigwStageResourceInfo' },
  { name: 'pluginManage', label: '插件管理', routeName: 'apigwStagePluginManage' },
  { name: 'variableManage', label: '变量管理', routeName: 'apigwStageVariableManage' },
];

// 网关id
const apigwId = +route.params.id;

onMounted(() => {
  handleTabChange('resourceInfo');
});

// 发布成功，重新请求环境详情
const handleReleaseSuccess = () => {
  stageTopBarRef.value?.getStageDetailFun(stageData.value?.id);
};

// 重新加载子组件
const routeIndex = ref(0);
watch(
  () => route.query,
  () => {
    routeIndex.value += 1;
  },
);

// 选项卡切换
const handleTabChange = (name: string) => {
  const curPanel = panels.find(item => item.name === name);
  router.push({
    name: curPanel.routeName,
    params: {
      id: apigwId,
    },
  });
};

// 发布资源
const handleRelease = () => {
  releaseSidesliderRef.value.showReleaseSideslider();
};

// 下架环境
const handleStageUnlist = async () => {
  InfoBox({
    title: t('确认下架吗？'),
    onConfirm: async () => {
      const data = {
        status: 0,
      };
      try {
        await removalStage(apigwId, stageData.value.id, data);
        Message({
          message: t('下架成功'),
          theme: 'success',
        });
        // 获取网关列表
        await mitt.emit('get-stage-list');
        // 开启loading
      } catch (error) {
        console.error(error);
      }
    },
  });
};

// 删除环境
const handleStageDelete = async () => {
  if (stageData.value.status === 1) {
    return;
  }

  InfoBox({
    title: t('确认删除吗？'),
    onConfirm: async () => {
      try {
        await deleteStage(apigwId, stageData.value.id);
        Message({
          message: t('删除成功'),
          theme: 'success',
        });
        // 获取网关列表
        await mitt.emit('get-stage-list', { isUpdate: false, isDelete: true });
        // 切换前一个环境, 并且不需要获取当前环境详情
        await mitt.emit('switch-stage', true);
        // 开启loading
      } catch (error) {
        console.error(error);
      }
    },
  });
};

// 编辑环境
const handleEditStage = () => {
  stageSidesliderRef.value.handleShowSideslider('edit');
};

// 访问地址
const getStageAddress = (name: string) => {
  const keys: any = {
    api_name: common.apigwName?.name,
    stage_name: name,
    resource_path: '',
  };

  let url = GLOBAL_CONFIG.STAGE_DOMAIN;
  for (const name in keys) {
    const reg = new RegExp(`{${name}}`);
    url = url?.replace(reg, keys[name]);
  }
  return url;
};
</script>

<style lang="scss" scoped>
.detail-mode {
  min-width: calc(1280px - 260px);
  padding: 24px;
  font-size: 12px;
  .stagae-info {
    display: flex;
    height: 128px;
    padding: 24px;
    background: #ffffff;
    box-shadow: 0 2px 4px 0 #1919290d;

    .stage-name {
      width: 120px;
      height: 80px;
      margin-right: 35px;
      background: #f0f5ff;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .name {
      padding: 0 3px;
      font-weight: 700;
      font-size: 16px;
      color: #3a84ff;
      display: inline-block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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
          max-width: 200px;
          display: flex;
          align-items: center;

          .link {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
          }

          i {
            cursor: pointer;
            color: #3a84ff;
            margin-left: 3px;
            font-size: 12px;
            padding: 3px;
          }
        }
      }
      .unrelease {
        display: inline-block;
        font-size: 10px;
        color: #fe9c00;
        background: #fff1db;
        border-radius: 2px;
        padding: 2px 5px;
        line-height: 1;
      }
    }
  }

  .operate {
    display: flex;
    margin-left: 40px;
    .line {
      height: 32px;
      width: 1px;
      background: #dcdee5;
      margin-right: 20px;
    }
  }
}

.tab-wrapper {
  background: #ffffff;
  box-shadow: 0 2px 4px 0 #1919290d;
  border-radius: 0 0 2px 2px;

  :deep(.bk-tab-content) {
    padding: 24px;
  }
}

.stage-more-actions {
  :deep(.disabled) {
    color: #c9cacf;
    background: #f5f7fa;
  }
}

.more-cls {
  padding: 5px 7px;
  i {
    transform: rotate(90deg);
    font-size: 16px;
  }
}
</style>
