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
  <div>
    <BkSideslider
      v-model:is-show="isShow"
      :title="t('发布资源至环境【{stage}】', { stage: currentStage?.name })"
      :width="1100"
      class="release-sideslider"
      quick-close
      @animation-end="handleAnimationEnd"
    >
      <template #default>
        <BkLoading :loading="isLoading">
          <div class="sideslider-content">
            <div>
              <div class="main">
                <BkAlert
                  v-if="currentStage?.status === 1"
                  class="mt-15px"
                  theme="info"
                >
                  <div class="alert-content">
                    <span class="pr-12px">
                      <span class="pr-4px">{{ t('当前版本号') }}: </span>
                      <span class="pr-4px">{{ stageDetail.version || '--' }}</span>
                    </span>
                    <span class="pr-12px">{{ t('代码分支') }}: <span> {{ stageDetail.branch || '--' }}</span></span>
                    <span class="pr-12px">CommitID: <span> {{ stageDetail.commit_id || '--' }}</span></span>
                    <span class="pr-12px">
                      {{
                        `由 ${stageDetail.created_by || '--'}  于 ${dayjs(stageDetail.created_time)
                          .format('YYYY-MM-DD HH:mm:ss') || '--'}  发布`
                      }}
                    </span>
                  </div>
                </BkAlert>
                <div class="mt-15px">
                  <BkForm
                    ref="formRef"
                    :model="formData"
                    :rules="rules"
                    form-type="vertical"
                  >
                    <BkFormItem
                      :label="t('代码仓库')"
                      required
                    >
                      <div class="repo-item-wrapper">
                        <div class="input-item-wrapper">
                          <BkInput
                            v-model="stageDetail.repo_info.repo_url"
                            disabled
                          />
                        </div>
                        <div class="icon-wrapper">
                          <CopyButton
                            class="mr-8px"
                            :source="stageDetail.repo_info.repo_url"
                          />
                          <AgIcon
                            name="jump"
                            @click="handleRepoClick"
                          />
                        </div>
                      </div>
                    </BkFormItem>
                    <BkFormItem
                      :label="t('代码分支')"
                      property="branch"
                      required
                    >
                      <BkSelect
                        v-model="formData.branch"
                        :clearable="false"
                      >
                        <BkOption
                          v-for="branch in stageDetail.repo_info.branch_list"
                          :id="branch"
                          :key="branch"
                          :name="branch"
                        />
                      </BkSelect>
                    </BkFormItem>
                    <BkFormItem
                      :label="t('版本类型')"
                      property="version"
                      required
                    >
                      <BkRadioGroup
                        v-model="semVerType"
                        @change="handleSemverChange"
                      >
                        <BkRadio label="major">
                          {{ t('重大版本') }}
                        </BkRadio>
                        <BkRadio label="minor">
                          {{ t('次版本') }}
                        </BkRadio>
                        <BkRadio label="patch">
                          {{ t('修正版本') }}
                        </BkRadio>
                      </BkRadioGroup>
                    </BkFormItem>
                    <BkFormItem
                      :label="t('版本号')"
                      required
                    >
                      <BkInput
                        v-model="formData.version"
                        :placeholder="t('选择版本类型后自动生成')"
                      />
                    </BkFormItem>
                    <BkFormItem
                      label="CommitID"
                      property="commit_id"
                      required
                    >
                      <div class="commit-id-wrapper">
                        <span class="id-content">{{ currentCommitInfo.commit_id }}</span>
                        <span class="commit-suffix">{{
                          `${
                            currentCommitInfo.last_update ?
                              dayjs(currentCommitInfo.last_update).format('YYYY-MM-DD HH:mm:ss')
                              : '--'
                          }  提交`
                        }}</span>
                      </div>
                    </BkFormItem>
                    <BkFormItem
                      :label="t('版本日志')"
                      property="comment"
                    >
                      <BkInput
                        v-model="formData.comment"
                        :maxlength="100"
                        :rows="4"
                        placeholder="--"
                        type="textarea"
                      />
                    </BkFormItem>
                  </BkForm>
                </div>
              </div>
            </div>
            <div class="operate1">
              <BkButton
                class="w-100px"
                theme="primary"
                @click="showPublishDia"
              >
                {{ t('确认发布') }}
              </BkButton>
              <BkButton
                class="w-100px ml-8px"
                @click="handleCancel"
              >
                {{ t('取消') }}
              </BkButton>
            </div>
          </div>
        </BkLoading>
      </template>
    </BkSideslider>

    <!-- 可编程网关日志抽屉 -->
    <ReleaseProgrammableEvent
      ref="logDetailsRef"
      :stage="localStage"
      :deploy-id="deployId"
      :version="stageDetail.version"
      @release-success="handleReleaseSuccess"
      @hide-when-pending="handleReleaseDoing"
      @retry="handleRetry"
    />
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';
import {
  type IStageListItem,
  getStageList,
} from '@/services/source/stage';
import {
  deployReleases,
  getProgrammableStageDetail,
  getStageNextVersion,
} from '@/services/source/programmable';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import ReleaseProgrammableEvent from '../../components/ReleaseProgrammableEvent.vue';
import { Message } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';
import { usePopInfoBox } from '@/hooks';

interface FormData {
  stage_id: number | undefined
  branch: string
  commit_id: string
  version: string
  comment: string
  version_type: string
}

type ProgrammableStageDetailType = Awaited<ReturnType<typeof getProgrammableStageDetail>>;

interface ICommitInfo {
  commit_id: string
  extra: object
  last_update: string
  message: string
  type: string
}

interface IProps { currentStage?: IStageListItem }

const { currentStage = {} } = defineProps<IProps>();

const emit = defineEmits<{
  'release-success': [void]
  'hidden': [void]
  'closed-on-publishing': [void]
  'retry': [void]
}>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const isShow = ref(false);
const formRef = ref();
const logDetailsRef = ref();

// 提交数据
const formData = ref<FormData>({
  stage_id: undefined,
  branch: '',
  commit_id: '',
  version: '',
  comment: '',
  version_type: '',
});
const localStage = ref<any>({});
const stageDetail = ref<ProgrammableStageDetailType>({
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
    status: '',
  },
  repo_info: {
    branch_commit_info: {},
    branch_list: [],
    repo_url: '',
  },
  status: '',
  version: '',
});

const deployId = ref('');
const stageList = ref<IStageListItem[]>([]);
const semVerType = ref('minor');
const currentCommitInfo = ref<ICommitInfo>({
  commit_id: '',
  extra: {},
  last_update: '',
  message: '',
  type: '',
});
const isLoading = ref(false);

watch(() => formData.value.branch, () => {
  const commitInfo = stageDetail.value.repo_info.branch_commit_info[formData.value.branch];
  if (commitInfo) {
    currentCommitInfo.value = commitInfo;
    formData.value.version_type = commitInfo.type;
    formData.value.comment = commitInfo.message;
    formData.value.commit_id = commitInfo.commit_id;
  }
  else {
    currentCommitInfo.value = {
      commit_id: '',
      extra: {},
      last_update: '',
      message: '',
      type: '',
    };
  }
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

const apigwId = computed(() => +route.params.id);

watch(isShow, async (val) => {
  if (val) {
    try {
      isLoading.value = true;
      await fetchStageList();
      stageDetail.value = await getProgrammableStageDetail(apigwId.value, currentStage!.id);
      const { version } = await getVersion();
      formData.value.version = version;
      formData.value.branch = stageDetail.value.branch || stageDetail.value.latest_deployment?.branch || '';
      localStage.value.paasInfo = stageDetail.value;

      if (currentStage?.id) {
        formData.value.stage_id = currentStage.id;
      }

      // const params = {
      //   semVerType: semVerType.value,
      //   ...formData.value,
      // };
      // initSidebarFormData(params);
    }
    finally {
      isLoading.value = false;
    }
  }
  else {
    resetSliderData();
    emit('hidden');
  }
});

watchEffect(() => {
  localStage.value = cloneDeep(currentStage);
});

const fetchStageList = async () => {
  stageList.value = await getStageList(apigwId.value);
};

const showPublishDia = () => {
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t('确认发布 {version} 版本至 {stage} 环境？', {
      version: formData.value.version,
      stage: currentStage?.name || '--',
    }),
    subTitle: t('发布后，将会覆盖原来的资源版本，请谨慎操作！'),
    confirmText: t('确认发布'),
    confirmButtonTheme: 'primary',
    contentAlign: 'left',
    showContentBgColor: true,
    onConfirm: () => {
      handlePublish();
    },
  });
};

const handlePublish = async () => {
  try {
    const params = {
      ...formData.value,
      stage_id: currentStage?.id,
      version: `${formData.value.version}+${currentStage?.name}`,
    };
    const res = await deployReleases(apigwId.value, params);
    deployId.value = res.deploy_id;
    isShow.value = false;
    logDetailsRef.value.showSideslider();
  }
  catch (e: any) {
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
                params: { id: apigwId.value },
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
    }
    else {
      Message({
        theme: 'error',
        message: e.message,
      });
    }
  }
};

const handleReleaseSuccess = () => {
  emit('release-success');
  // getStagesStatus();
};

const handleReleaseDoing = () => {
  nextTick(() => {
    emit('closed-on-publishing');
  });
  // setTimeout(() => {
  //   getStagesStatus();
  // }, 3000);
};

// 显示侧边栏
const showReleaseSideslider = () => {
  // const params = {
  //   semVerType: semVerType.value,
  //   ...formData.value,
  // };
  // initSidebarFormData(params);
  isShow.value = true;
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
    branch: '',
    commit_id: '',
    version: '',
    comment: '',
    version_type: '',
  };
  semVerType.value = 'minor';
};

const handleRepoClick = () => {
  window.open(stageDetail.value.repo_info.repo_url);
};

const getVersion = async (): Promise<{ version: string }> => {
  return await getStageNextVersion(
    apigwId.value,
    {
      stage_name: currentStage?.name,
      version_type: semVerType.value,
    },
  );
};

const handleSemverChange = async () => {
  const { version } = await getVersion();
  formData.value.version = version || '';
};

const handleRetry = () => {
  emit('retry');
};

defineExpose({ showReleaseSideslider });
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
        font-size: 14px;
        color: #979ba5;

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
      line-height: 22px;
      color: #4d4f56;
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
      margin-bottom: 18px;
      text-align: center;

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
        color: #313238;
        text-align: center;
      }

      .dialog-subtitle {
        font-size: 14px;
        line-height: 22px;
        color: #63656e;
        text-align: center;
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
    opacity: 0% !important;
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
      font-size: 12px;
      color: #63656e;
      align-items: center;

      .add-resource-btn {
        margin-right: 5px;
        font-size: 16px;
        color: #979ba5;
      }
    }
  }
}

.publish-version-tips {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 400;
  color: #63656e;

  span {
    color: #ff9c01;
  }
}

.version-tips {
  margin-left: 4px;
  color: #979ba5;
}
</style>
