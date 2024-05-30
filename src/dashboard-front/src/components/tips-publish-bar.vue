<template>
  <div class="tips-publish-bar">
    <bk-alert
      theme="warning"
    >
      <template #title>
        <div class="tips-main">
          <span>{{ t('API 网关 1.13 版本现已发布，为避免插件、后端服务等信息在页面修改后但实际并未生效的问题，请尽快生成并发布新版本至所有环境。') }}</span>
          <a
            :href="GLOBAL_CONFIG.DOC.UPGRADE_TO_113_TIP"
            v-if="GLOBAL_CONFIG.DOC.UPGRADE_TO_113_TIP"
            target="_blank"
            class="guide">
            {{ t('查看操作指引') }}
          </a>
          <bk-button theme="primary" v-if="!stage.getExist2" @click="handleCreateVersion">
            {{ t('生成版本并发布') }}
          </bk-button>
          <bk-button theme="primary" v-else @click="handlePublish">
            {{ t('去发布') }}
          </bk-button>
        </div>
      </template>
    </bk-alert>

    <!-- 生成版本 -->
    <version-sideslider
      ref="versionSidesliderRef"
      @done="getStagesStatus()"
    />

    <!-- 发布资源 -->
    <release-sideslider
      ref="releaseSidesliderRef"
      :current-assets="stageData"
      @release-success="getStagesStatus()"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStage } from '@/store';
import { useRoute } from 'vue-router';
import { getStageList } from '@/http';
import { useGetGlobalProperties, useGetStageList } from '@/hooks';
import VersionSideslider from '@/views/resource/setting/comps/version-sideslider.vue';
import releaseSideslider from '@/views/stage/overview/comps/release-sideslider.vue';

const route = useRoute();
const { t } = useI18n();
const stage = useStage();
// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

const apigwId = computed(() => +route.params.id);
const versionSidesliderRef = ref(null);
const releaseSidesliderRef = ref(null);
const stageData = ref<any>({});
const { getStagesStatus } = useGetStageList();

const handleCreateVersion = () => {
  versionSidesliderRef.value.showReleaseSideslider();
};

const handlePublish = () => {
  releaseSidesliderRef.value.showReleaseSideslider();
};

const getDefaultStage = async () => {
  if (!apigwId.value) return;
  const res = await getStageList(apigwId.value);

  const [defaultStage] = res;
  stageData.value = defaultStage;
};
getDefaultStage();

watch(
  () => apigwId.value,
  () => {
    getDefaultStage();
  },
);
</script>

<style lang="scss" scoped>
.tips-publish-bar {
  position: absolute;
  top: 0px;
  width: 100%;
  box-sizing: border-box;
  height: 42px;
  border: 1px solid #FFDFAC;
  border-radius: 2px;
  z-index: 99;
  :deep(.bk-alert) {
    box-sizing: border-box;
  }
  :deep(.bk-alert-wraper) {
    padding: 4px 10px;
    display: flex;
    align-items: center;
  }
  .tips-main {
    span {
      font-size: 12px;
      color: #63656E;
    }
    .guide {
      color: #1768EF;
      margin-left: 38px;
      margin-right: 46px;
    }
  }
}
</style>
