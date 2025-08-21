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
      class="release-sideslider"
      :width="960"
      :title="t('发布资源至环境【{stage}】', { stage: chooseAssets?.name || '--' })"
      quick-close
      @animation-end="handleAnimationEnd"
    >
      <template #default>
        <div class="sideslider-content">
          <div class="top-steps">
            <BkSteps
              :controllable="stepsConfig.controllable"
              :cur-step="stepsConfig.curStep"
              :steps="stepsConfig.objectSteps"
            />
          </div>
          <div>
            <template v-if="stepsConfig.curStep === 1">
              <div class="main">
                <BkAlert
                  v-if="chooseAssets?.release?.status === 'unreleased'"
                  theme="info"
                  :title="t('尚未发布')"
                  class="mt-15px mb-15px"
                />
                <BkAlert
                  v-else
                  theme="info"
                  :title="
                    chooseAssets?.resource_version?.version ?
                      t('当前版本号: {version},于 {created_time} 发布成功; 资源更新成功后, 需发布到指定的环境, 方可生效', {
                        version: chooseAssets?.resource_version?.version,
                        created_time: chooseAssets?.release.created_time
                      }) :
                      t('资源更新成功后, 需发布到指定的环境, 方可生效')"
                  class="mt-15px mb-15px"
                />

                <BkForm
                  ref="formRef"
                  :model="formData"
                  :rules="rules"
                  form-type="vertical"
                >
                  <BkFormItem
                    :label="t('发布的环境')"
                    property="stage_id"
                  >
                    <BkSelect
                      v-model="formData.stage_id"
                      :clearable="false"
                      @change="getMcpServersDel"
                    >
                      <BkOption
                        v-for="item in stageList"
                        :id="item.id"
                        :key="item.id"
                        :name="item.name"
                      />
                    </BkSelect>
                  </BkFormItem>
                  <p class="publish-version-tips">
                    {{
                      t('发布的资源版本（ 当前版本：{version}', { version: chooseAssets?.resource_version?.version || '--' })
                    }}
                    <template v-if="isRollback && chooseAssets?.resource_version?.version">
                      ，<span>{{ t('发布后，将回滚至 {version} 版本', { version: resourceVersion }) }}</span>
                    </template>
                    {{ t('）') }}
                  </p>
                  <BkFormItem
                    property="resource_version_id"
                    label=""
                  >
                    <BkSelect
                      ref="selectVersionRef"
                      v-model="formData.resource_version_id"
                      :clearable="false"
                      :input-search="false"
                      :popover-options="{
                        extCls: 'custom-version-list'
                      }"
                      :list="versionList"
                      filterable
                      id-key="id"
                      display-key="version"
                    >
                      <template #optionRender="{ item }">
                        <div
                          class="version-options"
                          :class="[
                            { 'version-options-disabled': item.id === curVersionId || item.schema_version === '1.0' },
                          ]"
                          @click.stop="() => handleVersionChange(item)"
                        >
                          <span class="version-name">
                            {{ item.version }}
                          </span>
                          <span
                            v-if="item.schema_version === '1.0'"
                            class="version-tips"
                          >
                            ({{ t('老版本，未包含后端服务等信息，发布可能会导致数据不一致，请新建版本再发布') }})
                          </span>
                          <span
                            v-if="chooseAssets?.resource_version?.version === item.version"
                            class="cur-version"
                          >
                            <BkTag theme="info">
                              {{ t('当前版本') }}
                            </BkTag>
                          </span>
                          <span
                            v-if="item.isLatestVersion"
                            :class="[{ 'cur-version': chooseAssets?.resource_version?.version !== item.version }]"
                          >
                            <BkTag
                              theme="success"
                              @click.stop="() => handleVersionChange(item)"
                            >
                              {{
                                t('最新版本')
                              }}</BkTag>
                          </span>
                        </div>
                      </template>
                      <template #extension>
                        <div class="extension-add">
                          <div
                            class="extension-add-content"
                            @click.stop="handleOpenResource"
                          >
                            <AgIcon
                              class="add-resource-btn"
                              name="plus-circle"
                            />
                            <span>{{ t('去新建') }}</span>
                          </div>
                        </div>
                      </template>
                    </BkSelect>
                    <p class="change-msg">
                      <span>
                        {{ t("新增") }}
                        <span class="font-bold color-#2dcb56">{{ diffData.add.length }}</span>
                        {{ t("个资源") }}，
                      </span>
                      <span>
                        {{ t("更新") }}
                        <span class="font-bold color-#ff9c01">{{ diffData.update.length }}</span>
                        {{ t("个资源") }}，
                      </span>
                      <span>
                        {{ t("删除") }}
                        <span class="font-bold color-#ea3636">{{ diffData.delete.length }}</span>
                        {{ t("个资源") }}
                      </span>
                    </p>
                  </BkFormItem>
                  <BkFormItem
                    :label="t('版本日志')"
                    property="comment"
                  >
                    <BkInput
                      v-model="chooseVersionComment"
                      placeholder="--"
                      type="textarea"
                      disabled
                      :rows="4"
                      :maxlength="100"
                    />
                  </BkFormItem>
                </BkForm>

                <div
                  v-show="mcpCheckData?.has_related_changes"
                  class="del-mcp-confirm"
                >
                  <div class="title">
                    {{ t('确认删除风险') }}
                  </div>
                  <BkAlert
                    theme="error"
                    class="tips"
                    :title="t('删除的资源中以下 {count} 个资源被 MCP Server 用到，删除后也会同步删除 MCP Server 中的资源',
                              { count: mcpCheckData?.deleted_resource_count } )"
                    closable
                  />
                  <div class="table-layout">
                    <BkTable
                      :data="mcpCheckData?.details || []"
                      show-overflow-tooltip
                      :columns="mcpCheckColumns"
                      border="outer"
                    />
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="resource-diff-main">
                <VersionDiff
                  page-type="publishEnvironment"
                  :source-id="chooseAssets?.resource_version?.id || currentAssets?.resource_version?.id || 'current'"
                  :target-id="formData.resource_version_id"
                  :source-switch="false"
                  :target-switch="false"
                />
              </div>
            </template>
            <div :class="stepsConfig.curStep === 1 ? 'operate1' : 'operate2'">
              <BkButton
                v-if="stepsConfig.curStep === 1"
                v-bk-tooltips="{ content: t('请新建版本再发布'), disabled: !isNextBtnDisabled }"
                :disabled="isNextBtnDisabled"
                theme="primary"
                class="w-100px"
                @click="handleNext"
              >
                {{ t('下一步') }}
              </BkButton>
              <template v-else-if="stepsConfig.curStep === 2">
                <BkButton
                  theme="primary"
                  class="w-100px"
                  @click="showPublishConfirmInfoBox"
                >
                  <!-- {{ isRollback ? t('确认回滚') : t('确认发布') }} -->
                  {{ t('确认发布') }}
                </BkButton>
                <BkButton
                  class="w-100px ml-8px"
                  @click="handleBack"
                >
                  {{ t('上一步') }}
                </BkButton>
              </template>
              <BkButton
                class="w-100px ml-8px"
                @click="handleCancel"
              >
                {{ t('取消') }}
              </BkButton>
            </div>
          </div>
        </div>
      </template>
    </BkSideslider>

    <!-- 日志弹窗 -->
    <ReleaseStageEvent
      ref="logDetailsRef"
      :history-id="publishId"
      @release-success="handleReleaseSuccess"
      @release-doing="handleReleaseDoing"
    />
  </div>
</template>

<script setup lang="ts">
import {
  type IStageListItem,
  getStageList,
} from '@/services/source/stage.ts';
import { getVersionDiff, getVersionList } from '@/services/source/resource.ts';
import { createRelease } from '@/services/source/release.ts';
import { checkMcpServersDel } from '@/services/source/mcp-market.ts';
import VersionDiff from '@/components/version-diff/Index.vue';
import ReleaseStageEvent from '@/components/release-stage-event/Index.vue';
import { Message } from 'bkui-vue';
import dayjs from 'dayjs';
import { usePopInfoBox } from '@/hooks';

interface FormData {
  resource_version_id: number | undefined
  stage_id: number | undefined
  comment: string
}

type VersionType = {
  id: number
  version: string
  isLatestVersion: boolean
};

interface IProps {
  currentAssets: any
  version?: any
}

const { currentAssets, version = {} } = defineProps<IProps>();

const emit = defineEmits<{
  'release-success': [void]
  'hidden': [void]
  'closed-on-publishing': [void]
}>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const mcpCheckData = ref({
  has_related_changes: false,
  deleted_resource_count: 0,
  details: [],
});

const chooseVersionComment = ref('');

const isShow = ref(false);
const versionList = ref<VersionType[]>([]);
const formRef = ref();
const logDetailsRef = ref();
const selectVersionRef = ref();
const isRollback = ref(false);
const isConfirmDialogVisible = ref(false);
// 提交数据
const formData = reactive<FormData>({
  resource_version_id: undefined,
  stage_id: undefined,
  comment: '',
});
// 差异数据
const diffData = ref({
  add: [],
  delete: [],
  update: [],
});

const stepsConfig = ref({
  objectSteps: [{ title: t('发布信息') }, { title: t('差异确认') }],
  curStep: 1,
  controllable: true,
});

const rules = {
  resource_version_id: [
    {
      required: true,
      message: t('请选择'),
      trigger: 'change',
    },
  ],
  stage_id: [
    {
      require: true,
      message: t('请选择'),
      trigger: 'change',
    },
  ],
};
const publishId = ref();
const chooseAssets = ref(currentAssets);
const stageList = ref<IStageListItem[]>([]);
const mcpCheckColumns = [
  {
    label: t('资源名称'),
    field: 'resource_name',
  },
  {
    label: 'MCP Server',
    field: 'mcp_server.name',
  },
];

const apigwId = computed(() => +route.params.id);

const resourceVersion = computed(() => {
  let version = '';
  versionList.value?.forEach((item: any) => {
    if (item.id === formData.resource_version_id) {
      version = item.version;
    }
  });
  return version;
});

// 当版本过旧时“下一步”按钮不能点击
const isNextBtnDisabled = computed(() => {
  const currentResource = versionList.value.find(version => version.id === formData.resource_version_id);
  if (currentResource) {
    return currentResource.schema_version === '1.0';
  }
  return false;
});

const curVersionId = computed(() => {
  const version = versionList.value?.filter(item => item.id === chooseAssets.value?.resource_version?.id)?.[0];
  return version?.id;
});

watch(
  isShow,
  async (val) => {
    if (val) {
      await getStageData();
      await getResourceVersions();
      if (currentAssets?.id) {
        formData.stage_id = currentAssets.id;
        chooseAssets.value = currentAssets;

        // const params = {
        //   stepsConfig: stepsConfig.value,
        //   formData,
        //   diffData: diffData.value,
        // };
        // initSidebarFormData(params);
      }

      if (version?.id) {
        const curVersion = versionList.value.find((item: any) => item.id === version?.id);
        if (curVersion) {
          formData.resource_version_id = curVersion?.id;
          handleVersionChange({ id: version?.id });
        }
      }
    }
    else {
      resetSliderData();
      emit('hidden');
    }
  },
);

watch(
  () => formData.stage_id,
  (v) => {
    if (v && stageList.value?.length) {
      chooseAssets.value = stageList.value?.filter((item: any) => item.id === v)[0];
    }
  },
);

watch(
  () => formData.resource_version_id,
  (v) => {
    const choVersion = versionList.value.filter((item: any) => item.id === v)[0];
    if (choVersion) {
      chooseVersionComment.value = choVersion.comment;
    }
  },
);

watch(
  () => [formData.resource_version_id, formData.stage_id],
  () => {
    const curVersion = versionList.value.filter(item => item.id === chooseAssets.value.resource_version?.id)[0];
    const choVersion = versionList.value.filter(item => item.id === formData.resource_version_id)[0];
    if (curVersion && choVersion) {
      const curDate = dayjs(curVersion.created_time);
      const chooseDate = dayjs(choVersion.created_time);
      if (curDate.isBefore(chooseDate) || curDate.isSame(chooseDate)) {
        isRollback.value = false;
      }
      else {
        isRollback.value = true;
      }
    }
  },
);

const getStageData = async () => {
  stageList.value = await getStageList(apigwId.value);
};

const showPublishConfirmInfoBox = () => {
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: isRollback.value
      ? t('确认回滚 {version} 版本至 {stage} 环境？', {
        version: resourceVersion.value,
        stage: chooseAssets.value?.name ?? '--',
      })
      : t('确认发布 {version} 版本至 {stage} 环境？', {
        version: resourceVersion.value,
        stage: chooseAssets.value?.name ?? '--',
      }),
    subTitle: t('发布后，将会覆盖原来的资源版本，请谨慎操作！'),
    confirmText: isRollback.value ? t('确认回滚') : t('确认发布'),
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
      stage_id: chooseAssets.value.id,
      ...formData,
    };
    const res = await createRelease(apigwId.value, params);

    publishId.value = res?.id;
    isShow.value = false;
    isConfirmDialogVisible.value = false;
    logDetailsRef.value.showSideslider();
    emit('closed-on-publishing');
  }
  catch (e: any) {
    // 自定义错误处理
    const regex = /`([^`]+?)`/;
    const msg = e?.error?.message ?? e?.message ?? '';
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
                name: 'BackendService',
                params: { id: apigwId.value },
              });
            },
          },
        ],
        message: {
          code: e?.error?.code ?? e.code,
          overview: msg,
          suggestion: '',
        },
        extCls: 'customize-error-message-cls',
      });
    }
    else {
      Message({
        theme: 'error',
        message: msg,
      });
    }
  }
};

const handleReleaseSuccess = () => {
  emit('release-success');
  // getStagesStatus();
};

const handleReleaseDoing = () => {
  emit('closed-on-publishing');
  // setTimeout(() => {
  //   getStagesStatus();
  // }, 3000);
};

// 显示侧边栏
const showReleaseSideslider = () => {
  // const params = {
  //   stepsConfig: stepsConfig.value,
  //   formData,
  //   diffData: diffData.value,
  // };
  // initSidebarFormData(params);
  isShow.value = true;
};

// 获取资源版本列表
const getResourceVersions = async () => {
  const response = await getVersionList(apigwId.value, {
    offset: 0,
    limit: 1000,
  });
  response.results.forEach((item: VersionType, index: number) => {
    item.isLatestVersion = index === 0;
  });
  versionList.value = response.results;
};

const getMcpServersDel = async () => {
  const { stage_id, resource_version_id } = formData;

  if (!stage_id || !resource_version_id) {
    mcpCheckData.value.details = [];
    mcpCheckData.value.has_related_changes = false;
    return;
  }

  mcpCheckData.value = await checkMcpServersDel(apigwId.value, {
    stage_id,
    resource_version_id,
  });
};

const handleVersionChange = async (payload: any) => {
  // 检查是否为 v1 版本，是的话不能发布，禁止选中
  if (payload.id === curVersionId.value || payload.schema_version === '1.0') return;

  if (!payload.id) {
    diffData.value = {
      add: [],
      delete: [],
      update: [],
    };
    selectVersionRef.value?.hidePopover();
    return;
  }

  const query = {
    source_resource_version_id: chooseAssets.value.resource_version?.id,
    target_resource_version_id: payload.id,
  };
  diffData.value = await getVersionDiff(apigwId.value, query);
  formData.resource_version_id = payload?.id;
  selectVersionRef.value?.hidePopover();
  getMcpServersDel();
};

// 下一步
const handleNext = async () => {
  await formRef.value?.validate();
  stepsConfig.value.curStep = 2;
};

// 上一步
const handleBack = () => {
  stepsConfig.value.curStep = 1;
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
  stepsConfig.value.curStep = 1;
  formData.resource_version_id = undefined;
  formData.stage_id = undefined;
  formData.comment = '';
  diffData.value = {
    add: [],
    delete: [],
    update: [],
  };
};

const handleOpenResource = () => {
  const routeData = router.resolve({ name: 'ResourceSetting' });
  window.open(routeData.href, '_blank');
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

    .top-steps {
      width: 100%;
      padding: 16px 300px;
      border-bottom: 1px solid #dcdee5;
    }

    .main {
      padding: 0 100px;

      .add {
        color: #34d97b;
      }

      .update {
        color: #ffb400;
      }

      .delete {
        color: #ff5656;
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
        color: #63656E;
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
      color: #63656E;
      align-items: center;

      .add-resource-btn {
        margin-right: 5px;
        font-size: 16px;
        color: #979BA5;
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
    color: #FF9C01;
  }
}

.version-tips {
  margin-left: 4px;
  color: #979ba5;
}

.del-mcp-confirm {
  margin-bottom: 24px;

  .title {
    margin-bottom: 12px;
    font-size: 14px;
    font-weight: bold;
    color: #4D4F56;
  }

  .tips {
    margin-bottom: 12px;
  }

  .table-layout {
    height: 215px;
    overflow-y: auto;
  }
}
</style>
