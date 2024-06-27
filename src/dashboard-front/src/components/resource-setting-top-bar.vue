<template>
  <div class="resource-top-bar" :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'">
    <div class="top-title-wrapper">
      <div class="title">{{ t('资源配置') }}</div>
      <div class="is-latest" v-show="!latest">
        {{ t('当前最新资源') }}
      </div>
      <div class="current-resource" v-show="isDetail && currentSource?.name">
        {{ currentSource?.name }}
      </div>
    </div>

    <div class="operate-btn-wrapper">
      <bk-button class="operate-btn" @click="handleShowDiff">
        <i class="apigateway-icon icon-ag-chayiduibi-shixin"></i>
        {{ t('与历史版本对比') }}
      </bk-button>
      <bk-button
        class="operate-btn-primary"
        theme="primary"
        @click="handleCreateResourceVersion"
        :disabled="!latest"
        v-bk-tooltips="{ content: '资源无更新，无需生成版本', disabled: latest }"
      >
        <i class="apigateway-icon icon-ag-version"></i>
        {{ t('生成版本') }}
      </bk-button>
    </div>
  </div>

  <!-- 生成版本 -->
  <version-sideslider ref="versionSidesliderRef" @done="mitt.emit('on-update-plugin');" />

  <!-- 版本对比 -->
  <bk-sideslider
    v-model:isShow="diffSidesliderConf.isShow"
    :title="diffSidesliderConf.title"
    :width="diffSidesliderConf.width"
    :quick-close="true"
  >
    <template #default>
      <div class="p20 pure-diff">
        <version-diff ref="diffRef" :source-id="diffSourceId" :target-id="diffTargetId" />
      </div>
    </template>
  </bk-sideslider>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import { getResourceVersionsList } from '@/http';
import versionDiff from '@/components/version-diff/index.vue';
import VersionSideslider from '@/views/resource/setting/comps/version-sideslider.vue';
import mitt from '@/common/event-bus';
import { useStage } from '@/store';

const { t } = useI18n();
const stage = useStage();

const route = useRoute();
const apigwId = computed(() => +route.params.id);

const props = defineProps({
  latest: {
    type: Boolean,
    default: false,
  },
  currentSource: {
    type: Object,
    default: {},
  },
  isDetail: {
    type: Boolean,
    default: false,
  },
});

// ref
const versionSidesliderRef = ref(null);
// 版本对比抽屉
const diffSidesliderConf = reactive({
  isShow: false,
  width: 1040,
  title: t('版本资源对比'),
});
const diffSourceId = ref();
const diffTargetId = ref();

// 版本对比
const handleShowDiff = async () => {
  try {
    const res = await getResourceVersionsList(apigwId.value, { offset: 0, limit: 999 });
    diffSourceId.value = res.results[0]?.id || '';
    diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280;
    diffSidesliderConf.isShow = true;
  } catch (e) {
    Message({
      message: t('操作失败，请稍后再试！'),
      theme: 'error',
      width: 'auto',
    });
    console.log(e);
  }
};

// 生成版本功能
const handleCreateResourceVersion = async () => {
  if (!props.latest) {
    Message({
      message: t('资源及资源文档无变更, 不需要生成新版本'),
      theme: 'error',
      width: 'auto',
    });
    return;
  }

  versionSidesliderRef.value.showReleaseSideslider();
};
</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  // top: 0;
  // top: 42px;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #FFFFFF;
  // border-bottom: 1px solid #dcdee5;
  // box-shadow: 0 3px 4px 0 #0000000a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 1280px;
  .top-title-wrapper {
    display: flex;
    align-items: center;
    .title {
      font-size: 16px;
      color: #313238;
      margin-right: 8px;
    }
    .is-latest {
      font-size: 12px;
      color: #3A84FF;
      background: #EDF4FF;
      border-radius: 2px;
      padding: 4px 8px;
      margin-right: 4px;
    }
    .current-resource {
      font-size: 12px;
      color: #63656E;
      background: #F0F1F5;
      padding: 4px 8px;
      border-radius: 2px;
    }
  }
  .operate-btn-wrapper {
    .operate-btn,
    .operate-btn-primary {
      height: 26px;
      font-size: 12px;
      padding: 0 12px;
      i {
        font-size: 16px;
        margin-right: 4px;
      }
    }
    .operate-btn {
      color: #63656E;
      &.bk-button.is-disabled {
        color: #dcdee5;
        cursor: not-allowed;
        border-color: #dcdee5;
      }
    }
  }
}

.pure-diff {
  :deep(.diff-main) {
    max-height: calc(100vh - 240px) !important;
  }
}
</style>
