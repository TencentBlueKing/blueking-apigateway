<template>
  <div class="detail-mode">
    <section class="stagae-info">
      <div class="stage-name">
        <span class="name">{{ stageData.name }}</span>
      </div>
      <div class="info">
        <div class="column">
          <div class="apigw-form-item">
            <div class="label">{{ `${t('访问地址')}：` }}</div>
            <div class="value url">
              <p class="link">--</p>
              <i
                class="apigateway-icon icon-ag-copy-info"
                @click.self.stop="copy('--')"
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
              <span v-else>{{ stageData.resource_version || '--' }}</span>
            </div>
          </div>
          <div class="apigw-form-item">
            <div class="label">{{ `${t('描述')}：` }}</div>
            <div class="value">
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
          发布资源
        </bk-button>
        <bk-button class="mr10">编辑</bk-button>
        <bk-button>
          更多
        </bk-button>
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
          ></router-view>
        </bk-tab-panel>
      </bk-tab>
    </div>
    
    <!-- 发布资源至环境 -->
    <release-sideslider ref="releaseSidesliderRef" />
  </div>
</template>

<script setup lang="ts">
import { copy } from '@/common/util';
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useStage } from '@/store';
import releaseSideslider from '../comps/release-sideslider.vue'
import { IStageData } from '../types/stage';

const { t } = useI18n();
const stageStore = useStage();
const route = useRoute();

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

// tab 选项卡
const active = ref('resourceInfo');
const panels = [
  { name: 'resourceInfo', label: '资源信息', routeName: 'apigwStageResourceInfo' },
  { name: 'pluginManage', label: '插件管理', routeName: 'apigwStagePluginManage' },
  { name: 'variableManage', label: '变量管理', routeName: 'apigwStageVariableManage' },
];

// 网关id
const apigwId = +route.params.id;

onMounted(() => {
  handleTabChange('resourceInfo');
})

// 重新加载子组件
const routeIndex = ref(0);
watch(
  () => route.query,
  () => {
    routeIndex.value += 1;
  }
);

const router = useRouter();
const handleTabChange = (name: string) => {
  const curPanel = panels.find((item) => item.name === name);
  router.push({
    name: curPanel.routeName,
    params: {
      id: apigwId,
    },
  });
};

const releaseSidesliderRef = ref(null);
// 发布资源
const handleRelease = () => {
  releaseSidesliderRef.value.showReleaseSideslider();
}
</script>

<style lang="scss" scoped>
.detail-mode {
  min-width: 1280px;
  padding: 24px;
  font-size: 12px;
  .stagae-info {
    height: 128px;
    padding: 24px;
    background: #ffffff;
    box-shadow: 0 2px 4px 0 #1919290d;

    display: flex;

    .stage-name {
      width: 120px;
      height: 80px;
      margin-right: 35px;
      background: #f0f5ff;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;

      .name {
        font-weight: 700;
        font-size: 16px;
        color: #3a84ff;
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
}
</style>
