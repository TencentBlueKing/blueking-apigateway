<template>
  <BkDialog
    :is-show="isShow"
    :title="t('API 网关 1.13 版本发布说明')"
    theme="primary"
    dialog-type="confirm"
    :width="1074"
    header-align="center"
    class="release-note-dialog"
    :confirm-text="stage.getExist2 ? t('去发布') : t('生成版本并发布')"
    @closed="() => isShow = false"
    @confirm="handleConfirm"
  >
    <div class="version-release-note">
      <div class="mb-32px">
        {{ t('API 网关在 2024-05-30 推出了 1.13 大版本更新。新版本中引入了后端服务，并将访问策略转换为插件形式，同时优化了环境、资源与插件之间的绑定关系。') }}
      </div>
      <div class="mb-24px">
        {{ t('为保证网关数据一致性，您需要执行以下步骤：') }}
      </div>
      <div class="mb-16px clause">
        {{ t('1. 为当前网关生成新的版本') }}
      </div>
      <div class="mb-32px clause">
        {{ t('2. 将新版本发布至所有环境') }}（{{ t('目前尚未更新的环境：') }}<span class="stage">{{ stageNames }}</span>）
      </div>
      <div>
        {{ t('请尽快更新，以避免插件、后端服务等信息在页面修改后但实际并未生效的问题。') }}
        <a
          v-if="envStore.env?.DOC_LINKS?.UPGRADE_TO_113_TIP"
          :href="envStore.env?.DOC_LINKS?.UPGRADE_TO_113_TIP"
          target="_blank"
          class="guide"
        >
          {{ t('查看操作指引') }}
        </a>
      </div>
    </div>
  </BkDialog>

  <!-- 生成版本 -->
  <CreateResourceVersion
    ref="createResourceVersionRef"
    @done="getStagesStatus"
  />

  <!-- 发布资源 -->
  <ReleaseStage
    ref="releaseStageRef"
    :current-assets="stageData"
    @release-success="getStagesStatus"
  />
</template>

<script lang="ts" setup>
import { useEnv, useStage } from '@/stores';
import { useGetStageList } from '@/hooks';
import { getStageList } from '@/services/source/stage';
import CreateResourceVersion from '@/components/create-resource-version/Index.vue';
import ReleaseStage from '@/components/release-stage/Index.vue';

const { t } = useI18n();
const route = useRoute();
const stage = useStage();
const envStore = useEnv();

const apigwId = computed(() => +route.params.id);
const { getStagesStatus } = useGetStageList();

const createResourceVersionRef = ref();
const releaseStageRef = ref();
const isShow = ref(false);
const stageData = ref<any>({});

const stageNames = computed(() => {
  return stage.getNotUpdatedStages?.join('、');
});

const handleConfirm = () => {
  isShow.value = false;
  if (stage.getExist2) { // 去发布
    releaseStageRef.value!.showReleaseSideslider();
  }
  else { // 生成版本再发布
    createResourceVersionRef.value!.showReleaseSideslider();
  }
};

const getDefaultStage = async () => {
  if (!apigwId.value) return;
  const [defaultStage] = await getStageList(apigwId.value);
  stageData.value = defaultStage;
};

const show = async () => {
  if (stage.getExist2) {
    await getDefaultStage();
  }

  isShow.value = true;
};

defineExpose({ show });
</script>

<style lang="scss" scoped>
.release-note-dialog {

  :deep(.bk-dialog-header) {
    padding-top: 24px;
  }
}

.version-release-note {
  padding-top: 20px;
  padding-bottom: 21px;
  padding-left: 6px;
  font-size: 14px;
  color: #63656E;

  .stage {
    color: #E02020;
  }

  .clause {
    text-indent: 2em;
  }
}

.guide {
  color: #1768EF;
}
</style>
