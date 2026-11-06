<template>
  <BkDialog
    v-model:is-show="isShow"
    class="service-publish-dialog"
    width="500"
  >
    <div class="dialog-content">
      <div class="publish-icon">
        <Success fill="#3FC06D" />
      </div>
      <div class="dialog-title">
        {{ t("内容保存成功，正在发布至对应环境...") }}
      </div>
      <div class="dialog-main">
        <div class="publish-tips">
          {{ t("当前服务") }} <span>{{ serviceName }}</span>{{ t("，") }} {{ t("已绑定以下") }}
          <span>{{ stageNames.length }}</span>
          {{ t("个环境，所有修改都将发布到这些环境中：") }}
        </div>
        <div class="flex flex-wrap publish-stages">
          <div
            v-for="stage in stageNames"
            :key="stage"
            class="stage-item"
          >
            {{ stage }}
          </div>
        </div>
      </div>
      <div class="dialog-footer">
        <BkButton
          theme="primary"
          @click="handleViewReleaseRecord"
        >
          {{ t("去查看发布记录") }}
        </BkButton>
        <BkButton
          class="ml-10px"
          @click="isShow = false"
        >
          {{ t("关闭") }}
        </BkButton>
      </div>
    </div>
  </BkDialog>
</template>

<script setup lang="ts">
// 后端服务/模型服务更新后，提示配置有变化的环境正在发布。只代表保存成功，发布结果需去发布记录查看
import { Success } from 'bkui-vue/lib/icon';

interface IProps {
  serviceName: string
  stageNames: string[]
}

const isShow = defineModel<boolean>('isShow', { required: true });

const {
  serviceName,
  stageNames,
} = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();

const handleViewReleaseRecord = () => {
  router.push({ name: 'StageReleaseRecord' });
};
</script>

<style lang="scss" scoped>
.service-publish-dialog {

  :deep(.bk-dialog-title) {
    display: none;
  }

  :deep(.bk-modal-footer) {
    display: none;
  }

  .dialog-content {

    .publish-icon {
      margin-bottom: 18px;
      font-size: 42px;
      line-height: 32px;
      text-align: center;
    }

    .dialog-title {
      margin-bottom: 16px;
      font-size: 20px;
      color: #313238;
      text-align: center;
    }

    .dialog-main {
      padding: 12px 16px 18px;
      margin-bottom: 25px;
      background-color: #f5f6fa;
      border-radius: 2px;

      .publish-tips {
        margin-bottom: 10px;
        font-size: 14px;
        color: #63656e;

        span {
          font-weight: 700;
        }
      }

      .publish-stages {

        .stage-item {
          position: relative;
          width: 33%;
          padding-left: 12px;
          font-size: 14px;
          color: #63656e;

          &::after {
            position: absolute;
            top: 10px;
            left: 0;
            width: 4px;
            height: 4px;
            background-color: #63656e;
            border-radius: 50%;
            content: " ";
          }
        }
      }
    }

    .dialog-footer {
      text-align: center;
    }
  }
}
</style>
