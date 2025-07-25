<template>
  <div
    class="resource-top-bar"
    :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'"
  >
    <div class="top-title-wrapper">
      <div class="title">
        {{ t('资源配置') }}
      </div>
      <div
        v-show="showNewTips"
        class="is-latest"
      >
        {{ t('当前最新资源') }}
      </div>
      <div
        v-show="isDetail && currentSource?.name"
        class="current-resource"
      >
        {{ currentSource?.name }}
      </div>
    </div>

    <!-- <div class="operate-btn-wrapper">
      <BkButton class="operate-btn" @click="handleShowDiff">
      <i class="apigateway-icon icon-ag-chayiduibi-shixin"></i>
      {{ t('与历史版本对比') }}
      </BkButton>
      <BkButton
      class="operate-btn-primary"
      theme="primary"
      @click="handleCreateResourceVersion"
      :disabled="!latest"
      v-bk-tooltips="{ content: '资源无更新，无需生成版本', disabled: latest }"
      >
      <i class="apigateway-icon icon-ag-version"></i>
      {{ t('生成版本') }}
      </BkButton>
      </div> -->
  </div>

  <!-- 生成版本 -->
  <!-- <version-sideslider ref="versionSidesliderRef" @done="mitt.emit('on-update-plugin');" /> -->

  <!-- 版本对比 -->
  <!-- <BkSideslider
    v-model:isShow="diffSidesliderConf.isShow"
    :title="diffSidesliderConf.title"
    :width="diffSidesliderConf.width"
    :quick-close="true"
    >
    <template #default>
    <div class="p-20px pure-diff">
    <version-diff ref="diffRef" :source-id="diffSourceId" :target-id="diffTargetId" />
    </div>
    </template>
    </BkSideslider> -->
</template>

<script setup lang="ts">
// import { Message } from 'bkui-vue';
// import { getResourceVersionsList } from '@/http';
// import versionDiff from '@/components/version-diff/index.vue';
// import VersionSideslider from '@/views/resource/setting/comps/version-sideslider.vue';
// import mitt from '@/common/event-bus';
import { useStage } from '@/stores';

interface IProps {
  latest?: boolean
  currentSource?: any
  isDetail?: boolean
  showNewTips?: boolean
}

// const route = useRoute();
// const apigwId = computed(() => +route.params.id);

const {
  // latest = false,
  currentSource = {},
  isDetail = false,
  showNewTips = false,
} = defineProps<IProps>();

const { t } = useI18n();
const stage = useStage();

// ref
// const versionSidesliderRef = ref(null);
// 版本对比抽屉
// const diffSidesliderConf = reactive({
//   isShow: false,
//   width: 1040,
//   title: t('版本资源对比'),
// });
// const diffSourceId = ref();
// const diffTargetId = ref();

// 版本对比
// const handleShowDiff = async () => {
//   try {
//     const res = await getResourceVersionsList(apigwId.value, { offset: 0, limit: 999 });
//     diffSourceId.value = res.results[0]?.id || '';
//     diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280;
//     diffSidesliderConf.isShow = true;
//   } catch (e) {
//     Message({
//       message: t('操作失败，请稍后再试！'),
//       theme: 'error',
//       width: 'auto',
//     });
//     console.log(e);
//   }
// };

// 生成版本功能
// const handleCreateResourceVersion = async () => {
//   if (!props.latest) {
//     Message({
//       message: t('资源及资源文档无变更, 不需要生成新版本'),
//       theme: 'error',
//       width: 'auto',
//     });
//     return;
//   }

//   versionSidesliderRef.value.showReleaseSideslider();
// };
</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;

  // border-bottom: 1px solid #dcdee5;
  // box-shadow: 0 3px 4px 0 #0000000a;
  display: flex;

  // top: 0;
  // top: 42px;
  width: 100%;
  height: 52px;
  padding: 0 24px;
  background: #FFF;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;

  // min-width: 1280px;

  .top-title-wrapper {
    display: flex;
    align-items: center;

    .title {
      margin-right: 8px;
      font-size: 16px;
      color: #313238;
    }

    .is-latest {
      padding: 4px 8px;
      margin-right: 4px;
      font-size: 12px;
      color: #3A84FF;
      background: #EDF4FF;
      border-radius: 2px;
    }

    .current-resource {
      padding: 4px 8px;
      font-size: 12px;
      color: #63656E;
      background: #F0F1F5;
      border-radius: 2px;
    }
  }

  .operate-btn-wrapper {

    .operate-btn,
    .operate-btn-primary {
      height: 26px;
      padding: 0 12px;
      font-size: 12px;

      i {
        margin-right: 4px;
        font-size: 16px;
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
