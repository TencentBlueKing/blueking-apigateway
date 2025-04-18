<template>
  <div>
    <bk-sideslider
      v-model:isShow="isShow"
      :before-close="handleBeforeClose"
      :title="t('发布资源至环境【{stage}】', { stage: chooseAssets.name })"
      :width="1100"
      class="release-sideslider"
      quick-close
      @animation-end="handleAnimationEnd"
    >
      <template #default>
        <div class="sideslider-content">
          <div>
            <div class="main">
              <BkAlert
                class="mt15 mb15"
                theme="info"
              >
                <div class="alert-content">
                  <span class="pr12">
                    <span class="pr4">{{ t('当前版本号') }}: </span>
                    <span class="pr4">{{ stageDetail.version }}</span>
                  </span>
                  <span class="pr12">{{ t('代码分支') }}: <span>{{ stageDetail.branch }}</span></span>
                  <span class="pr12">CommitID: <span>{{ stageDetail.commit_id }}</span></span>
                  <span class="pr12">
                    {{
                      `由 ${stageDetail.created_by || '--'}  于 ${dayjs(stageDetail.created_time)
                        .format('YYYY-MM-DD HH:mm:ss') || '--'}  发布`
                    }}
                  </span>
                </div>
              </BkAlert>
              <bk-form ref="formRef" :model="formData" :rules="rules" form-type="vertical">
                <bk-form-item :label="t('代码仓库')" required>
                  <div class="repo-item-wrapper">
                    <div class="input-item-wrapper">
                      <bk-input v-model="stageDetail.repo_info.repo_url" disabled />
                    </div>
                    <div class="icon-wrapper">
                      <i
                        class="apigateway-icon icon-ag-copy-info mr8" @click="copyRepo"
                      />
                      <i class="apigateway-icon icon-ag-jump" @click="handleRepoClick" />
                    </div>
                  </div>
                </bk-form-item>
                <bk-form-item :label="t('代码分支')" property="branch" required>
                  <bk-select v-model="formData.branch" :clearable="false">
                    <bk-option
                      v-for="branch in stageDetail.repo_info.branch_list"
                      :id="branch"
                      :key="branch"
                      :name="branch"
                    />
                  </bk-select>
                  <!--                  <bk-input v-model="formData.branch" disabled />-->
                </bk-form-item>
                <bk-form-item :label="t('版本类型')" property="version" required>
                  <bk-radio-group v-model="semVerType" @change="handleSemverChange">
                    <bk-radio label="major">
                      {{ t('重大版本') }}
                    </bk-radio>
                    <bk-radio label="minor">
                      {{ t('次版本') }}
                    </bk-radio>
                    <bk-radio label="patch">
                      {{ t('修正版本') }}
                    </bk-radio>
                  </bk-radio-group>
                </bk-form-item>
                <bk-form-item :label="t('版本号')" required>
                  <bk-input v-model="formData.version" :placeholder="t('选择版本类型后自动生成')" disabled />
                </bk-form-item>
                <bk-form-item label="CommitID" property="commit_id" required>
                  <div class="commit-id-wrapper">
                    <span class="id-content">{{ formData.commit_id }}</span>
                    <span class="commit-suffix">{{
                      `由 ${stageDetail.created_by || '--'}  于 ${dayjs(stageDetail.created_time)
                        .format('YYYY-MM-DD HH:mm:ss') || '--'}  发布`
                    }}</span>
                  </div>
                </bk-form-item>
                <bk-form-item :label="t('版本日志')" property="comment">
                  <bk-input
                    v-model="formData.comment"
                    :maxlength="100"
                    :rows="4"
                    disabled
                    placeholder="--"
                    type="textarea"
                  />
                </bk-form-item>
              </bk-form>
            </div>
          </div>
          <div class="operate1">
            <bk-button style="width: 100px" theme="primary" @click="showPublishDia">
              {{ t('确认发布') }}
            </bk-button>
            <bk-button style="margin-left: 4px; width: 100px" @click="handleCancel">
              {{ t('取消') }}
            </bk-button>
          </div>
        </div>
      </template>
    </bk-sideslider>

    <!-- 日志弹窗 -->
    <EventSlider
      ref="logDetailsRef"
      :current-stage="currentStage"
      :deploy-id="deployId"
      @release-success="handleReleaseSuccess"
      @release-doing="handleReleaseDoing"
    />
    <!--  发布确认弹窗  -->
    <bk-dialog
      v-model:is-show="isConfirmDialogVisible"
      class="custom-main-dialog"
      mask-close
      width="400"
    >
      <div class="dialog-content">
        <header class="dialog-icon"><i class="apigateway-icon icon-ag-exclamation-circle-fill"></i></header>
        <main class="dialog-main">
          <div class="dialog-title">
            {{
              t('确认发布 {version} 版本至 {stage} 环境？', {
                version: formData.version,
                stage: chooseAssets.name ?? '--',
              })
            }}
          </div>
          <div class="dialog-subtitle">
            {{ t('发布后，将会覆盖原来的资源版本，请谨慎操作！') }}
          </div>
        </main>
        <footer class="dialog-footer">
          <bk-button theme="primary" @click="handlePublish">
            {{ t('确认发布') }}
          </bk-button>
          <bk-button class="ml10" @click="isConfirmDialogVisible = false">{{ t('取消') }}</bk-button>
        </footer>
      </div>
    </bk-dialog>
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';

import { useI18n } from 'vue-i18n';
import {
  computed,
  nextTick,
  ref,
  watch,
} from 'vue';
import { getStageList } from '@/http';
import {
  deployReleases,
  getProgrammableStageDetail,
  getProgrammableStageNextVersion,
} from '@/http/programmable';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import EventSlider from '@/components/programmable-deploy-events-slider/index.vue';
import { Message } from 'bkui-vue';
import {
  useGetStageList,
  useSidebar,
} from '@/hooks';
import { copy } from '@/common/util';

interface FormData {
  stage_id: number | undefined;
  branch: string;
  commit_id: string;
  version: string;
  comment: string;
}

const route = useRoute();
const router = useRouter();
const { initSidebarFormData, isSidebarClosed } = useSidebar();
const { getStagesStatus } = useGetStageList();

const { t } = useI18n();

const props = defineProps({
  currentStage: {
    type: Object,
    default: () => ({}),
  },
  version: {
    type: Object,
    required: false,
  },
});

const emit = defineEmits<(e: 'release-success' | 'hidden' | 'closed-on-publishing') => void>();

const isShow = ref(false);
const formRef = ref(null);
const logDetailsRef = ref(null);
const isConfirmDialogVisible = ref(false);

// 提交数据
const formData = ref<FormData>({
  stage_id: undefined,
  branch: 'master',
  commit_id: '',
  version: '',
  comment: '--',
});
const stageDetail = ref({
  branch: '',
  commit_id: '',
  created_by: '',
  created_time: '',
  deploy_id: '',
  latest_deployment: {
    branch: '',
    commit_id: '',
    deploy_id: '',
    history_id: 0,
    version: '',
  },
  repo_info: {
    branch_commit_info: {},
    branch_list: [],
    repo_url: '',
  },
  version: '',
});

const stepsConfig = ref({
  objectSteps: [
    { title: t('发布信息') },
    { title: t('差异确认') },
  ],
  controllable: true,
});

const rules = {
  stage_id: [
    {
      require: true,
      message: t('请选择'),
      trigger: 'change',
    },
  ],
};
const deployId = ref(0);
const chooseAssets = ref<any>(props.currentStage);
const stageList = ref<any>([]);
const semVerType = ref('major');

const apigwId = computed(() => +route.params.id);

watch(isShow, async (val) => {
  if (val) {
    await getStageData();
    stageDetail.value = await getProgrammableStageDetail(apigwId.value, props.currentStage!.id);
    formData.value.commit_id = stageDetail.value.commit_id;
    const { version } = await getVersion();
    formData.value.version = version;
    formData.value.branch = stageDetail.value.latest_deployment?.branch || 'master';

    if (props.currentStage?.id) {
      formData.value.stage_id = props.currentStage.id;
      chooseAssets.value = props.currentStage;
    }
  } else {
    resetSliderData();
    emit('hidden');
  }
});

watch(
  () => formData.value.stage_id,
  (v) => {
    if (v && stageList.value?.length) {
      chooseAssets.value = stageList.value?.filter((item: any) => item.id === v)[0];
    }
  },
);

const getStageData = async () => {
  stageList.value = await getStageList(apigwId.value);
};

const showPublishDia = () => {
  isConfirmDialogVisible.value = true;
};

const handlePublish = async () => {
  try {
    const params = {
      stage_id: chooseAssets.value.id,
      ...formData.value,
    };
    const res = await deployReleases(apigwId.value, params);
    deployId.value = res.deploy_id;
    isShow.value = false;
    isConfirmDialogVisible.value = false;
    logDetailsRef.value.showSideslider();
  } catch (e: any) {
    // 自定义错误处理
    const regex = /`([^`]+?)`/;
    const msg = e?.message || '';
    const match = msg.match(regex);
    if (match?.[1]?.includes('后端服务')) {
      // 后端服务地址为空需要单独处理
      Message({
        theme: 'error',
        actions: [
          {
            id: 'customize',
            text: () => t('后端服务'),
            onClick: () => {
              isShow.value = false;
              router.push({
                name: 'apigwBackendService',
                params: {
                  id: apigwId.value,
                },
              });
            },
          },
        ],
        message: {
          code: e.code,
          overview: e.message || '',
          suggestion: '',
        },
        extCls: 'customize-error-message-cls',
      });
    } else {
      Message({ theme: 'error', message: e.message });
    }
  }
};

const handleReleaseSuccess = () => {
  emit('release-success');
  getStagesStatus();
};

const handleReleaseDoing = () => {
  nextTick(() => {
    emit('closed-on-publishing');
  });
  setTimeout(() => {
    getStagesStatus();
  }, 3000);
};

// 显示侧边栏
const showReleaseSideslider = () => {
  const params = {
    stepsConfig: stepsConfig.value,
    ...formData.value,
  };
  initSidebarFormData(params);
  isShow.value = true;
};

// 下一步
// const handleNext = async () => {
//   await formRef.value?.validate();
// };

const handleBeforeClose = async () => {
  const params = {
    stepsConfig: stepsConfig.value,
    ...formData.value,
  };
  return isSidebarClosed(JSON.stringify(params));
};

const handleAnimationEnd = () => {
  handleCancel();
};

// 取消
const handleCancel = () => {
  isShow.value = false;
  resetSliderData();
};

const resetSliderData = () => {
  formData.value = {
    stage_id: undefined,
    branch: 'master',
    commit_id: '',
    version: '',
    comment: '--',
  };
};

const copyRepo = () => {
  copy(stageDetail.value.repo_info.repo_url);
};

const handleRepoClick = () => {
  window.open(stageDetail.value.repo_info.repo_url);
};

const getVersion = async (): Promise<{ version: string }> => {
  return await getProgrammableStageNextVersion(
    apigwId.value,
    { stage_name: props.currentStage.name, version_type: semVerType.value },
  );
};

const handleSemverChange = async () => {
  const { version } = await getVersion();
  formData.value.version = version || '';
};

defineExpose({
  showReleaseSideslider,
});
</script>

<style lang="scss" scoped>
.release-sideslider {
  :deep(.bk-modal-content) {
    overflow-y: auto;
  }

  .sideslider-content {
    width: 100%;

    .main {
      padding: 0 100px;

      :deep(.bk-alert-wraper) {
        align-items: center;
      }

      .alert-content {
        display: flex;
        align-items: center;
      }
    }

    .resource-diff-main {
      padding: 18px 24px 24px;
    }

    .operate1 {
      padding: 8px 100px 24px;
    }

    .operate2 {
      padding: 8px 24px 24px;
    }

    .change-msg {
      font-size: 12px;
      color: #63656e;
    }
  }

  .repo-item-wrapper {
    display: flex;
    gap: 6px;

    .input-item-wrapper {
      flex-grow: 1;
    }

    .icon-wrapper {
      .apigateway-icon {
        color: #979ba5;
        font-size: 14px;

        &:hover {
          color: #3c96ff;
          cursor: pointer;
        }
      }
    }
  }

  .commit-id-wrapper {
    .id-content {
      font-size: 14px;
      color: #4d4f56;
      line-height: 22px;
    }

    .commit-suffix {
      font-size: 12px;
      color: #979ba5;
    }
  }
}

.custom-main-dialog {
  :deep(.bk-dialog-title) {
    display: none;
  }

  :deep(.bk-dialog-footer) {
    display: none;
  }

  .dialog-content {
    .dialog-icon {
      text-align: center;
      margin-bottom: 18px;

      .apigateway-icon {
        font-size: 42px;
        color: #ff9c01;
      }
    }

    .dialog-main {
      .dialog-title {
        margin-bottom: 8px;
        font-size: 20px;
        line-height: 32px;
        text-align: center;
        color: #313238;
      }

      .dialog-subtitle {
        font-size: 14px;
        line-height: 22px;
        text-align: center;
        color: #63656e;
      }
    }

    .dialog-footer {
      margin-top: 24px;
      text-align: center;
    }
  }
}
</style>
<style lang="scss">
.customize-error-message-cls .bk-message-content .overview .tools {
  .assistant,
  .details,
  .fix {
    display: none !important;
    opacity: 0 !important;
  }
}

.custom-version-list {
  .bk-select-content {
    .bk-select-dropdown {
      .bk-select-options {
        .bk-select-option {
          padding-inline: 0;

          .version-options {
            padding-inline: 12px;
            width: 100%;

            .cur-version {
              margin-left: 6px;
            }

            &-disabled {
              color: #c4c6cc;
              cursor: not-allowed;

              .bk-tag {
                cursor: not-allowed;
              }
            }
          }
        }
      }
    }
  }

  .extension-add {
    margin: 0 auto;
    cursor: pointer;

    .extension-add-content {
      display: flex;
      align-items: center;
      color: #63656e;
      font-size: 12px;

      .add-resource-btn {
        margin-right: 5px;
        font-size: 16px;
        color: #979ba5;
      }
    }
  }
}

.publish-version-tips {
  font-size: 14px;
  font-weight: 400;
  color: #63656e;
  margin-bottom: 8px;

  span {
    color: #ff9c01;
  }
}

.version-tips {
  color: #979ba5;
  margin-left: 4px;
}
</style>
