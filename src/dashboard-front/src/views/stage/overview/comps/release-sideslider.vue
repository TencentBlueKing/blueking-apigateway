<template>
  <div>
    <bk-sideslider
      class="release-sideslider"
      v-model:isShow="isShow"
      :width="960"
      :title="`发布到环境【${currentAssets.name}】`"
      quick-close
      :before-close="handleBeforeClose"
      @animation-end="handleAnimationEnd">
      <template #default>
        <div class="sideslider-content">
          <div class="top-steps">
            <bk-steps
              :controllable="stepsConfig.controllable" :cur-step="stepsConfig.curStep"
              :steps="stepsConfig.objectSteps" />
          </div>
          <div>
            <template v-if="stepsConfig.curStep === 1">
              <div class="main">
                <bk-alert
                  theme="info"
                  :title="$t('尚未发布')"
                  v-if="currentAssets.release.status === 'unreleased'"
                  class="mt15 mb15" />
                <bk-alert
                  v-else
                  theme="info"
                  :title="
                    currentAssets.resource_version.version ?
                      `当前版本号: ${currentAssets.resource_version.version},
                  于${currentAssets.release.created_time}发布成功; 资源更新成功后, 需发布到指定的环境, 方可生效` :
                      '资源更新成功后, 需发布到指定的环境, 方可生效'"
                  class="mt15 mb15" />

                <bk-form ref="formRef" :model="formData" :rules="rules" form-type="vertical">
                  <p class="publish-version-tips">
                    {{ t('发布的资源版本（ 当前版本：{version}', { version: currentAssets.resource_version.version || '--' }) }}
                    <template v-if="isRollback">
                      ，<span>{{ t('发布后，将回滚至 {version} 版本', { version: resourceVersion }) }}</span>
                    </template>
                    {{ t('）') }}
                  </p>
                  <bk-form-item
                    property="resource_version_id"
                    label="">
                    <bk-select
                      ref="selectVersionRef"
                      v-model="formData.resource_version_id"
                      :input-search="false"
                      :popover-options="{
                        extCls: 'custom-version-list'
                      }"
                      :list="versionList"
                      filterable
                      id-key="id"
                      display-key="version"
                    >
                      <!-- <bk-option
                        v-for="(item) in versionList"
                        :key="item.id"
                        :value="item.id"
                        :label="item.version"
                        :disabled="item.disabled"
                      /> -->
                      <template #optionRender="{ item }">
                        <div
                          :class="[
                            'version-options',
                            { 'version-options-disabled': item.disabled },
                          ]"
                          @click.stop="handleVersionChange(item)"
                        >
                          <span class="version-name">
                            {{ item.version }}
                          </span>
                          <span v-if="currentAssets.resource_version.version === item.version" class="cur-version">
                            <bk-tag theme="info">
                              {{ t('当前版本') }}
                            </bk-tag>
                          </span>
                          <span
                            v-if="item.isLatestVersion"
                            :class="[{ 'cur-version': currentAssets.resource_version.version !== item.version }]">
                            <bk-tag theme="success" @click.stop="handleVersionChange(item)"> {{ t('最新版本') }}</bk-tag>
                          </span>
                        </div>
                      </template>
                      <template #extension>
                        <div class="extension-add">
                          <div class="extension-add-content" @click.stop="handleOpenResource">
                            <i class="apigateway-icon icon-ag-plus-circle add-resource-btn"
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
                  <bk-form-item property="comment" :label="$t('发布日志')">
                    <bk-input v-model="formData.comment" type="textarea" :rows="4" :maxlength="100" />
                  </bk-form-item>
                </bk-form>
              </div>
            </template>
            <template v-else>
              <div class="resource-diff-main">
                <version-diff
                  ref="diffRef"
                  page-type="publishEnvironment"
                  :source-id="currentAssets.resource_version.id"
                  :target-id="formData.resource_version_id"
                  :source-switch="false"
                  :target-switch="false"
                >
                </version-diff>
              </div>
            </template>
            <div :class="stepsConfig.curStep === 1 ? 'operate1' : 'operate2'">
              <bk-button v-if="stepsConfig.curStep === 1" theme="primary" style="width: 100px" @click="handleNext">
                {{ $t('下一步') }}
              </bk-button>
              <template v-else-if="stepsConfig.curStep === 2">
                <bk-button theme="primary" style="width: 100px" @click="showPublishDia">
                  {{ isRollback ? $t('确认回滚') : $t('确认发布') }}
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
    <log-details ref="logDetailsRef" :history-id="publishId" @release-success="emit('release-success')"></log-details>
  </div>
</template>

<script setup lang="ts">
import { IDialog } from '@/types';
import { useI18n } from 'vue-i18n';
import { ref, reactive, watch, computed } from 'vue';
import { getResourceVersionsList, resourceVersionsDiff, createReleases } from '@/http';
import { useRoute, useRouter } from 'vue-router';
import versionDiff from '@/components/version-diff/index.vue';
import logDetails from '@/components/log-details/index.vue';
import { Message, InfoBox } from 'bkui-vue';
import { useSidebar } from '@/hooks';
import dayjs from 'dayjs';

const route = useRoute();
const router = useRouter();
const { initSidebarFormData, isSidebarClosed/* , isBackDialogShow */ } = useSidebar();

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

const emit = defineEmits<(e: 'release-success' | 'hidden') => void>();

const resourceVersion = computed(() => {
  let version = '';
  versionList.value?.forEach((item: any) => {
    if (item.id === formData.resource_version_id) {
      version = item.version;
    }
  });
  return version;
});

const isShow = ref(false);
const versionList = ref<any>([]);
const formRef = ref(null);
const logDetailsRef = ref(null);
const selectVersionRef = ref(null);
const isRollback = ref<boolean>(true);

interface FormData {
  resource_version_id: number | undefined;
  comment: string;
};
// 提交数据
const formData = reactive<FormData>({
  resource_version_id: undefined,
  comment: '',
});
// 差异数据
const diffData = ref({
  add: [],
  delete: [],
  update: [],
});

const stepsConfig = ref({
  objectSteps: [{ title: '发布信息' }, { title: '差异确认' }],
  curStep: 1,
  controllable: true,
});

const rules = {
  resource_version_id: [
    {
      required: true,
      message: '请选择',
      trigger: 'change',
    },
  ],
};
const publishId = ref();

const showPublishDia = () => {
  if (isRollback.value) {
    InfoBox({
      infoType: 'warning',
      title: t('确认回滚 {version} 版本至 {stage} 环境？', { version: resourceVersion.value, stage: props.currentAssets.name }),
      subTitle: t('发布后，将会覆盖原来的资源版本，请谨慎操作！'),
      confirmText: t('确认回滚'),
      cancelText: t('取消'),
      onConfirm: () => {
        handlePublish();
      },
    });
  } else {
    InfoBox({
      infoType: 'warning',
      title: t('确认发布 {version} 版本至 {stage} 环境？', { version: resourceVersion.value, stage: props.currentAssets.name }),
      subTitle: t('发布后，将会覆盖原来的资源版本，请谨慎操作！'),
      confirmText: t('确认发布'),
      cancelText: t('取消'),
      onConfirm: () => {
        handlePublish();
      },
    });
  }
};

const handlePublish = async () => {
  try {
    const params = {
      stage_id: props.currentAssets.id,
      ...formData,
    };
    const res = await createReleases(apigwId.value, params);

    publishId.value = res?.id;
    isShow.value = false;
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

// 获取资源版本列表
const getResourceVersions = async () => {
  try {
    const res = await getResourceVersionsList(apigwId.value, { offset: 0, limit: 1000 });
    res.results?.forEach((item: any, index: number) => {
      if (item.id === props.currentAssets?.resource_version?.id) {
        item.disabled = true;
      }
      item.isLatestVersion = index === 0;
    });
    versionList.value = res.results;
  } catch (e) {
    console.log(e);
  };
};

const handleVersionChange = async (payload: Record<string, string>) => {
  const curVersion = versionList.value?.filter((item: any) => item.id === props.currentAssets?.resource_version?.id)[0];
  if (curVersion) {
    const curDate = dayjs(curVersion.created_time);
    const chooseDate = dayjs(payload.created_time);
    if (curDate.isBefore(chooseDate)) {
      isRollback.value = false;
    } else {
      isRollback.value = true;
    }
  }
  if (payload.disabled) {
    return;
  }
  if (!payload.id) {
    diffData.value = {
      add: [],
      delete: [],
      update: [],
    };
    selectVersionRef.value.hidePopover();
    return;
  };
  try {
    const query = {
      source_resource_version_id: props.currentAssets?.resource_version?.id,
      target_resource_version_id: payload.id,
    };
    const res: any = await resourceVersionsDiff(apigwId.value, query);
    diffData.value = res;
    formData.resource_version_id = payload?.id;
    selectVersionRef.value.hidePopover();
  } catch (e) {
    console.log(e);
  };
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
      await getResourceVersions();
      if (props.version?.id) {
        const curVersion = versionList.value.find(item => item.id === props.version?.id);
        if (curVersion) {
          formData.resource_version_id = curVersion?.id;
          handleVersionChange({
            disabled: curVersion.disabled,
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
          .version-options {
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
</style>
