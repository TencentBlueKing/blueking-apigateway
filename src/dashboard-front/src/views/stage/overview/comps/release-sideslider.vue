<template>
  <div>
    <bk-sideslider
      class="release-sideslider"
      v-model:isShow="isShow"
      :width="960"
      :title="t('发布资源至环境【{stage}】', { stage: chooseAssets.name })"
      quick-close
      :before-close="handleBeforeClose"
      @animation-end="handleAnimationEnd"
    >
      <template #default>
        <div class="sideslider-content">
          <div class="top-steps">
            <bk-steps
              :controllable="stepsConfig.controllable" :cur-step="stepsConfig.curStep"
              :steps="stepsConfig.objectSteps"
            />
          </div>
          <div>
            <template v-if="stepsConfig.curStep === 1">
              <div class="main">
                <bk-alert
                  theme="info"
                  :title="$t('尚未发布')"
                  v-if="chooseAssets.release?.status === 'unreleased'"
                  class="mt15 mb15"
                />
                <bk-alert
                  v-else
                  theme="info"
                  :title="
                    chooseAssets.resource_version?.version ?
                      t('当前版本号: {version},于 {created_time} 发布成功; 资源更新成功后, 需发布到指定的环境, 方可生效', {
                        version: chooseAssets.resource_version?.version,
                        created_time: chooseAssets.release.created_time
                      }) :
                      t('资源更新成功后, 需发布到指定的环境, 方可生效')"
                  class="mt15 mb15"
                />

                <bk-form ref="formRef" :model="formData" :rules="rules" form-type="vertical">
                  <bk-form-item property="stage_id" :label="$t('发布的环境')">
                    <bk-select v-model="formData.stage_id" :clearable="false">
                      <bk-option
                        v-for="item in stageList"
                        :id="item.id"
                        :key="item.id"
                        :name="item.name"
                      />
                    </bk-select>
                  </bk-form-item>
                  <p class="publish-version-tips">
                    {{
                      t('发布的资源版本（ 当前版本：{version}', { version: chooseAssets.resource_version?.version || '--' })
                    }}
                    <template v-if="isRollback && chooseAssets.resource_version?.version">
                      ，<span>{{ t('发布后，将回滚至 {version} 版本', { version: resourceVersion }) }}</span>
                    </template>
                    {{ t('）') }}
                  </p>
                  <bk-form-item
                    property="resource_version_id"
                    label=""
                  >
                    <bk-select
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
                          :class="[
                            'version-options',
                            { 'version-options-disabled': item.id === curVersionId || item.schema_version === '1.0' },
                          ]"
                          @click.stop="handleVersionChange(item)"
                        >
                          <span class="version-name">
                            {{ item.version }}
                          </span>
                          <span class="version-tips" v-if="item.schema_version === '1.0'">
                            ({{ t('老版本，未包含后端服务等信息，发布可能会导致数据不一致，请新建版本再发布') }})
                          </span>
                          <span v-if="chooseAssets.resource_version?.version === item.version" class="cur-version">
                            <bk-tag theme="info">
                              {{ t('当前版本') }}
                            </bk-tag>
                          </span>
                          <span
                            v-if="item.isLatestVersion"
                            :class="[{ 'cur-version': chooseAssets.resource_version?.version !== item.version }]"
                          >
                            <bk-tag theme="success" @click.stop="handleVersionChange(item)">
                              {{
                                t('最新版本')
                              }}</bk-tag>
                          </span>
                        </div>
                      </template>
                      <template #extension>
                        <div class="extension-add">
                          <div class="extension-add-content" @click.stop="handleOpenResource">
                            <i
                              class="apigateway-icon icon-ag-plus-circle add-resource-btn"
                            />
                            <span>{{ t('去新建') }}</span>
                          </div>
                        </div>
                      </template>
                    </bk-select>
                    <p class="change-msg">
                      <span>
                        {{ $t("新增") }}
                        <strong class="ag-strong success">{{ diffData.add.length }}</strong>
                        {{ $t("个资源") }}，
                      </span>
                      <span>
                        {{ $t("更新") }}
                        <strong class="ag-strong warning">{{ diffData.update.length }}</strong>
                        {{ $t("个资源") }}，
                      </span>
                      <span>
                        {{ $t("删除") }}
                        <strong class="ag-strong danger">{{ diffData.delete.length }}</strong>
                        {{ $t("个资源") }}
                      </span>
                    </p>
                  </bk-form-item>
                  <!-- <bk-form-item property="comment" :label="$t('发布日志')">
                    <bk-input v-model="formData.comment" type="textarea" :rows="4" :maxlength="100" />
                  </bk-form-item> -->
                  <bk-form-item property="comment" :label="$t('版本日志')">
                    <bk-input
                      v-model="chooseVersionComment"
                      placeholder="--"
                      type="textarea"
                      disabled
                      :rows="4"
                      :maxlength="100"
                    />
                  </bk-form-item>
                </bk-form>
              </div>
            </template>
            <template v-else>
              <div class="resource-diff-main">
                <version-diff
                  ref="diffRef"
                  page-type="publishEnvironment"
                  :source-id="chooseAssets?.resource_version?.id || currentAssets?.resource_version?.id || 'current'"
                  :target-id="formData.resource_version_id"
                  :source-switch="false"
                  :target-switch="false"
                >
                </version-diff>
              </div>
            </template>
            <div :class="stepsConfig.curStep === 1 ? 'operate1' : 'operate2'">
              <bk-button
                v-if="stepsConfig.curStep === 1"
                :disabled="isNextBtnDisabled"
                theme="primary"
                style="width: 100px"
                v-bk-tooltips="{ content: t('请新建版本再发布'), disabled: !isNextBtnDisabled }"
                @click="handleNext"
              >
                {{ $t('下一步') }}
              </bk-button>
              <template v-else-if="stepsConfig.curStep === 2">
                <bk-button theme="primary" style="width: 100px" @click="showPublishDia">
                  <!-- {{ isRollback ? $t('确认回滚') : $t('确认发布') }} -->
                  {{ $t('确认发布') }}
                </bk-button>
                <bk-button style="margin-left: 4px; width: 100px" @click="handleBack">
                  {{ $t('上一步') }}
                </bk-button>
              </template>
              <bk-button style="margin-left: 4px; width: 100px" @click="handleCancel">
                {{ $t('取消') }}
              </bk-button>
            </div>
          </div>
        </div>
      </template>
    </bk-sideslider>

    <!-- <bk-dialog
      :is-show="isBackDialogShow"
      class="sideslider-close-back-dialog-cls"
      width="0"
      height="0"
      dialog-type="show">
    </bk-dialog> -->

    <!-- 日志弹窗 -->
    <log-details
      ref="logDetailsRef"
      :history-id="publishId"
      @release-success="handleReleaseSuccess"
      @release-doing="handleReleaseDoing"
    >
    </log-details>
    <!--  发布确认弹窗  -->
    <bk-dialog
      v-model:is-show="isConfirmDialogVisible"
      class="custom-main-dialog"
      width="400"
      mask-close
    >
      <div class="dialog-content">
        <header class="dialog-icon"><i class="apigateway-icon icon-ag-exclamation-circle-fill"></i></header>
        <main class="dialog-main">
          <div class="dialog-title">
            {{
              isRollback ? t('确认回滚 {version} 版本至 {stage} 环境？', {
                version: resourceVersion,
                stage: chooseAssets.name ?? '--',
              }) : t('确认发布 {version} 版本至 {stage} 环境？', {
                version: resourceVersion,
                stage: chooseAssets.name ?? '--',
              })
            }}
          </div>
          <div class="dialog-subtitle">
            {{ t('发布后，将会覆盖原来的资源版本，请谨慎操作！') }}
          </div>
        </main>
        <footer class="dialog-footer">
          <bk-button theme="primary" @click="handlePublish()">
            {{
              isRollback ? t('确认回滚') : t('确认发布')
            }}
          </bk-button>
          <bk-button class="ml10" @click="isConfirmDialogVisible = false">{{ t('取消') }}</bk-button>
        </footer>
      </div>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import {
  computed,
  nextTick,
  reactive,
  ref,
  watch,
} from 'vue';
import {
  createReleases,
  getResourceVersionsList,
  getStageList,
  resourceVersionsDiff,
} from '@/http';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import versionDiff from '@/components/version-diff/index.vue';
import logDetails from '@/components/log-details/index.vue';
import { Message } from 'bkui-vue';
import {
  useGetStageList,
  useSidebar,
} from '@/hooks';
import dayjs from 'dayjs';

type VersionType = {
  id: number
  version: string
  isLatestVersion: boolean
};

const route = useRoute();
const router = useRouter();
const { initSidebarFormData, isSidebarClosed/* , isBackDialogShow */ } = useSidebar();
const { getStagesStatus } = useGetStageList();
const apigwId = computed(() => +route.params.id);

const { t } = useI18n();

const props = defineProps({
  currentAssets: {
    type: Object,
    default: () => ({}),
  },
  version: {
    type: Object,
    required: false,
  },
});

const emit = defineEmits<(e: 'release-success' | 'hidden' | 'closed-on-publishing') => void>();

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

const chooseVersionComment = ref<string>('');

const isShow = ref(false);
const versionList = ref<VersionType[]>([]);
const formRef = ref(null);
const logDetailsRef = ref(null);
const selectVersionRef = ref(null);
const isRollback = ref<boolean>(false);
const isConfirmDialogVisible = ref(false);

interface FormData {
  resource_version_id: number | undefined;
  stage_id: number | undefined;
  comment: string;
};
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
const chooseAssets = ref<any>(props.currentAssets);
const stageList = ref<any>([]);

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
      ...formData,
    };
    const res = await createReleases(apigwId.value, params);

    publishId.value = res?.id;
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
    formData,
    diffData: diffData.value,
  };
  initSidebarFormData(params);
  isShow.value = true;
};

const curVersionId = computed(() => {
  const version = versionList.value?.filter(item => item.id === chooseAssets.value.resource_version?.id)[0];
  return version?.id;
});

// 获取资源版本列表
const getResourceVersions = async () => {
  const response = await getResourceVersionsList(apigwId.value, { offset: 0, limit: 1000 });
  response.results.forEach((item: VersionType, index: number) => {
    item.isLatestVersion = index === 0;
  });
  versionList.value = response.results;
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
    selectVersionRef.value.hidePopover();
    return;
  }

  const query = {
    source_resource_version_id: chooseAssets.value.resource_version?.id,
    target_resource_version_id: payload.id,
  };
  diffData.value = await resourceVersionsDiff(apigwId.value, query);
  formData.resource_version_id = payload?.id;
  selectVersionRef.value.hidePopover();
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

const handleBeforeClose = async () => {
  const params = {
    stepsConfig: stepsConfig.value,
    formData,
    diffData: diffData.value,
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
  const routeData = router.resolve({
    name: 'apigwResource',
  });
  window.open(routeData.href, '_blank');
};

watch(
  () => isShow.value,
  async (val) => {
    if (val) {
      await getStageData();
      await getResourceVersions();
      if (props.currentAssets?.id) {
        formData.stage_id = props.currentAssets.id;
        chooseAssets.value = props.currentAssets;
      }

      if (props.version?.id) {
        const curVersion = versionList.value.find((item: any) => item.id === props.version?.id);
        if (curVersion) {
          formData.resource_version_id = curVersion?.id;
          handleVersionChange({
            id: props.version?.id,
          });
        }
      }
    } else {
      resetSliderData();
      emit('hidden');
    };
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
      } else {
        isRollback.value = true;
      }
    }
  },
);

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
        color: #63656E;
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
      color: #63656E;
      font-size: 12px;

      .add-resource-btn {
        margin-right: 5px;
        font-size: 16px;
        color: #979BA5;
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
    color: #FF9C01;
  }
}

.version-tips {
  color: #979ba5;
  margin-left: 4px;
}
</style>
