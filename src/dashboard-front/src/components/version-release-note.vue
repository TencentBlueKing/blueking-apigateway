<template>
  <bk-dialog
    :is-show="isShow"
    :title="t('API 网关 1.13 版本发布说明')"
    theme="primary"
    dialog-type="confirm"
    :width="1074"
    @closed="() => isShow = false"
    @confirm="handleConfirm"
    header-align="center"
    class="release-note-dialog"
    :confirm-text="stage.getExist2 ? t('去发布') : t('生成版本并发布')"
  >
    <div class="version-release-note">
      <div class="mb-32">
        {{ t('API 网关在 2024-05-30 推出了 1.13 大版本更新。新版本中引入了后端服务，并将访问策略转换为插件形式，同时优化了环境、资源与插件之间的绑定关系。') }}
      </div>
      <div class="mb-24">{{ t('为保证网关数据一致性，你需要执行以下步骤：') }}</div>
      <div class="mb-16 clause">{{ t('1. 为当前网关生成新的版本') }}</div>
      <div class="mb-32 clause">
        {{ t('2. 将新版本发布至所有环境') }}（{{ t('目前尚未更新的环境：') }}<span class="stage">{{ stageNames }}</span>）
      </div>
      <div>
        {{ t('请尽快更新，以避免插件、后端服务等信息在页面修改后但实际并未生效的问题。') }}
        <a
          :href="GLOBAL_CONFIG.DOC.UPGRADE_TO_113_TIP"
          v-if="GLOBAL_CONFIG.DOC.UPGRADE_TO_113_TIP"
          target="_blank"
          class="guide">
          {{ t('查看操作指引') }}
        </a>
      </div>
    </div>
  </bk-dialog>

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
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStage } from '@/store';
import { useRoute } from 'vue-router';
import { useGetGlobalProperties, useGetStageList } from '@/hooks';
import { getStageList } from '@/http';
import VersionSideslider from '@/views/resource/setting/comps/version-sideslider.vue';
import releaseSideslider from '@/views/stage/overview/comps/release-sideslider.vue';

const route = useRoute();
const stage = useStage();
const { t } = useI18n();
// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;
const apigwId = computed(() => +route.params.id);
const { getStagesStatus } = useGetStageList();

const versionSidesliderRef = ref(null);
const releaseSidesliderRef = ref(null);
const isShow = ref<boolean>(false);
const stageData = ref<any>({});

const stageNames = computed(() => {
  return stage.getNotUpdatedStages?.join('、');
});

const handleConfirm = () => {
  isShow.value = false;
  if (stage.getExist2) {  // 去发布
    releaseSidesliderRef.value.showReleaseSideslider();
  } else { // 生成版本再发布
    versionSidesliderRef.value.showReleaseSideslider();
  };
};

const getDefaultStage = async () => {
  if (!apigwId.value) return;
  const res = await getStageList(apigwId.value);

  const [defaultStage] = res;
  stageData.value = defaultStage;
};

const show = async () => {
  if (stage.getExist2) {
    await getDefaultStage();
  }

  isShow.value = true;
};

defineExpose({
  show,
});
</script>

<style lang="scss" scoped>
.release-note-dialog {
  :deep(.bk-dialog-header) {
    padding-top: 24px;
  }
}
.version-release-note {
  font-size: 14px;
  color: #63656E;
  padding-top: 20px;
  padding-bottom: 21px;
  padding-left: 6px;
  .stage {
    color: #E02020;
  }
  .mb-32 {
    margin-bottom: 32px;
  }
  .mb-16 {
    margin-bottom: 16px;
  }
  .mb-24 {
    margin-bottom: 24px;
  }
  .clause {
    text-indent: 2em;
  }
}
.guide {
  color: #1768EF;
}
</style>
