<template>
  <div class="release-sideslider">
    <bk-sideslider
      v-model:is-show="isShow"
      :width="960"
      :title="t('生成资源版本')"
      quick-close
      @hidden="handleCancel"
      class="scroll">
      <template #default>
        <div class="sideslider-content" v-if="!dialogShow">
          <div class="top-steps">
            <bk-steps
              :controllable="stepsConfig.controllable" :cur-step="stepsConfig.curStep"
              :steps="stepsConfig.objectSteps" />
          </div>
          <div>
            <template v-if="stepsConfig.curStep === 1">
              <div class="resource-diff-main">
                <version-diff
                  ref="diffRef"
                  :source-id="diffSourceId"
                  :target-id="diffTargetId"
                  page-type="createVersion"
                  :source-switch="false"
                  :target-switch="false"
                >
                </version-diff>
              </div>
            </template>
            <template v-else>
              <div class="main">
                <!-- <bk-alert
                  theme="info"
                  :title="$t('尚未发布')"
                  v-if="!versionList?.length"
                  class="mt15 mb15" /> -->
                <bk-alert
                  v-if="versionList.length && versionList[0].version"
                  theme="info"
                  :title="`${t('最新版本号')}: ${versionList[0]?.version || '--'},
                  ${t('于')} ${versionList[0]?.created_time || '--'} ${t('创建')}`"
                  class="mb15"
                />

                <bk-form ref="formRef" :model="formData" :rules="rules" form-type="vertical">
                  <bk-form-item
                    property="version"
                    :label="t('版本号')"
                    :description="t('版本号须符合 Semver 规范，例如：1.1.1，1.1.1-alpha.1')"
                    class="form-item-version mt-20 mb15"
                    required>
                    <!-- <bk-popover
                      :content="t('由数字、字母、中折线（-）、点号（.）组成，长度小于64个字符')"
                      theme="light"
                    >
                    </bk-popover> -->
                    <bk-input
                      v-model="formData.version"
                      :placeholder="t('由数字、字母、中折线（-）、点号（.）组成，长度小于64个字符')"
                    />
                  </bk-form-item>
                  <bk-form-item>
                    <section class="ft12">
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
                    </section>
                  </bk-form-item>
                  <bk-form-item property="comment" :label="$t('版本日志')">
                    <bk-input v-model="formData.comment" type="textarea" :rows="4" :maxlength="100" />
                  </bk-form-item>
                </bk-form>
              </div>
            </template>
            <div :class="stepsConfig.curStep === 1 ? 'operate2' : 'operate1'">
              <bk-button v-if="stepsConfig.curStep === 1" theme="primary" style="width: 100px" @click="handleNext">
                {{ $t('下一步') }}
              </bk-button>
              <template v-else-if="stepsConfig.curStep === 2">
                <bk-button theme="primary" style="width: 100px" @click="handleBuildVersion" :loading="loading">
                  {{ $t('确定') }}
                </bk-button>
                <bk-button class="ml10" style="width: 100px" @click="handleBack">
                  {{ $t('上一步') }}
                </bk-button>
              </template>
              <bk-button class="ml10" style="width: 100px" @click="handleCancel">
                {{ $t('取消') }}
              </bk-button>
            </div>
          </div>
        </div>

        <div class="version-create-status" v-else>

          <div class="create-status" v-if="loading">
            <spinner class="status-icon" fill="#3A84FF" />
            <p class="create-status-title">
              {{ t('版本正在生成中...') }}
            </p>
            <p class="create-status-subtitle">
              {{ t('请稍等') }}
            </p>
          </div>

          <div class="create-status" v-if="!loading && !createError">
            <success class="status-icon large-icon" fill="#2DCB56" />
            <p class="create-status-title">
              {{ t('版本生成成功') }}
            </p>
            <p class="create-status-subtitle">
              {{ t('接下来你可以直接发布至环境，或跳转资源版本') }}
            </p>
            <div class="create-status-btns">
              <bk-button theme="primary" @click="handlePublish">
                {{ t('立即发布') }}
              </bk-button>
              <bk-button class="ml8" @click="handleSkip">
                {{ t('跳转资源版本') }}
              </bk-button>
            </div>
          </div>

          <!--          <div class="create-status" v-if="!loading && createError">-->
          <!--            <close class="status-icon large-icon" fill="#EA3636" />-->
          <!--            <p class="create-status-title">-->
          <!--              {{ t('版本生成失败') }}-->
          <!--            </p>-->
          <!--            <p class="create-status-subtitle">-->
          <!--              {{ t('接下来你可以重试或关闭弹窗') }}-->
          <!--            </p>-->
          <!--            <div class="create-status-btns">-->
          <!--              <bk-button theme="primary" @click="handleBuildVersion">-->
          <!--                {{ t('重试') }}-->
          <!--              </bk-button>-->
          <!--              <bk-button class="ml8" @click="handleCancel">-->
          <!--                {{ t('关闭') }}-->
          <!--              </bk-button>-->
          <!--            </div>-->
          <!--          </div>-->
        </div>
      </template>
    </bk-sideslider>

    <!-- 确认发布弹窗 -->
    <!-- <custom-dialog
      :title="t('版本生成成功')"
      :sub-title="t('接下来，可以前往 “资源发布” 发布到不同的环境')"
      :is-show="dialogShow"
      @comfirm="handleSkip"
      @cancel="handleCancel">
    </custom-dialog> -->

    <!-- 发布资源 -->
    <release-sideslider
      :current-assets="stageData"
      :version="versionData"
      ref="releaseSidesliderRef"
      @release-success="handleSkip()"
    />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import {
  computed,
  reactive,
  ref,
  watch,
} from 'vue';
import semver from 'semver';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import {
  Spinner,
  Success,
} from 'bkui-vue/lib/icon';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import releaseSideslider from '@/views/stage/overview/comps/release-sideslider.vue';
import {
  createResourceVersion,
  getNextVersion,
  getResourceVersionsList,
  getStageList,
  resourceVersionsDiff,
} from '@/http';
import { useGetStageList } from '@/hooks';
import versionDiff from '@/components/version-diff/index.vue';

type VersionType = {
  id: number
  version: string
  isLatestVersion: boolean
};

const emit  = defineEmits(['done']);
const route = useRoute();
const router = useRouter();
const apigwId = computed(() => +route.params.id);

const { t } = useI18n();
const { getStagesStatus } = useGetStageList();
// const resourceVersion = computed(() => {
//   let version = '';
//   versionList.value?.forEach((item: any) => {
//     if (item.id === formData.resource_version_id) {
//       version = item.version;
//     }
//   });
//   return version;
// });

// 侧边栏sildslider
const isShow = ref(false);
// 弹窗dialog
const dialogShow = ref(false);
const versionList = ref<any>([]);
const formRef = ref(null);
const diffSourceId = ref('');
const diffTargetId = ref('');
const loading = ref(false);
const createError = ref(false);
const hasDuplicateVersionError = ref(false);
const duplicateVersionErrorMsg = ref('');
const releaseSidesliderRef = ref(null);
const versionData = ref<any>();
const stageData = ref<any>();

interface FormData {
  version: string;
  comment: string;
}

// 提交数据
const formData = reactive<FormData>({
  version: '',
  comment: '',
});
  // 差异数据
const diffData = ref({
  add: [],
  delete: [],
  update: [],
});

const stepsConfig = ref({
  objectSteps: [{ title: t('差异确认') }, { title: t('版本信息') }],
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
  version: [
    {
      required: true,
      message: t('请输入版本号'),
      trigger: 'change',
    },
    {
      message: t('版本号须符合 Semver 规范'),
      trigger: 'change',
      validator: (value: any) => {
        if (value?.indexOf('v') !== -1) {
          return false;
        }
        if (semver.valid(value) === null) {
          return false;
        }
        return true;
      },
    },
    {
      message: () => duplicateVersionErrorMsg.value,
      trigger: 'change',
      validator: () => !hasDuplicateVersionError.value,
    },
  ],
};

// 生成版本
const handleBuildVersion = async () => {
  try {
    await formRef.value?.validate();
    loading.value = true;
    await createResourceVersion(apigwId.value, formData);
    dialogShow.value = true;
    emit('done');
    getStagesStatus();
    createError.value = false;
    hasDuplicateVersionError.value = false;
    duplicateVersionErrorMsg.value = '';
  } catch (e) {
    const error = e as Error;
    const errMsg = error?.message?.toLowerCase() || t('版本号已存在');
    if (
      (errMsg.includes('版本') && errMsg.includes('已存在'))
      || (errMsg.includes('resource version') && errMsg.includes('already exists'))
    ) {
      hasDuplicateVersionError.value = true;
      duplicateVersionErrorMsg.value = errMsg;
      await formRef.value!.validate('version');
    } else {
      // createError.value = true;
      InfoBox({
        'ext-cls': 'version-publish-error-infobox',
        infoType: 'danger',
        title: t('版本生成失败'),
        subTitle: t('版本号创建失败，请联系管理员'),
        confirmText: t('关闭'),
      });
    }
  } finally {
    loading.value = false;
  }
};

const getDiffData = async () => {
  diffData.value.add = [];
  diffData.value.delete = [];
  diffData.value.update = [];

  try {
    const res = await resourceVersionsDiff(apigwId.value, {
      source_resource_version_id: diffSourceId.value.replace('current', ''),
      target_resource_version_id: diffTargetId.value.replace('current', ''),
    });

    diffData.value.add = res.add;
    diffData.value.delete = res.delete;
    diffData.value.update = res.update;
  } catch (e) {
    console.log(e);
  }
};

// 显示侧边栏
const showReleaseSideslider = () => {
  isShow.value = true;
};

// 获取资源版本列表
const getResourceVersions = async () => {
  const response = await getResourceVersionsList(apigwId.value, { offset: 0, limit: 10 });
  versionList.value = response.results;
  if (!response.results.length) {
    diffSourceId.value = 'current';
  } else {
    diffSourceId.value = String(versionList.value[0]?.id || '');
  }
};

// 下一步
const handleNext = async () => {
  await formRef.value?.validate();
  stepsConfig.value.curStep = 2;
  await getDiffData();
};

// 上一步
const handleBack = () => {
  stepsConfig.value.curStep = 1;
};

// 取消
const handleCancel = () => {
  isShow.value = false;
  dialogShow.value = false;
};

const handleSkip = () => {
  handleCancel();
  setTimeout(() => {
    router.push({
      name: 'apigwResourceVersion',
    });
  }, 300);
};

const handlePublish = async () => {
  try {
    const { results } = await getResourceVersionsList(apigwId.value, { offset: 0, limit: 10 });
    const newVersion = results.filter((item: VersionType) => item.version === formData.version)[0];
    if (newVersion?.id) {
      versionData.value = newVersion;
    }
    const stages = await getStageList(apigwId.value);
    const [defaultStage] = stages;
    stageData.value = defaultStage;
    releaseSidesliderRef.value.showReleaseSideslider();
    handleCancel();
  } catch (e) {
    Message({
      theme: 'error',
      message: t('系统错误，请稍后重试'),
    });
  }
};

const getSuggestionVersion = async () => {
  const res = await getNextVersion(apigwId.value);
  if (res?.version) {
    formData.version = res.version;
  }
};

watch(
  () => isShow.value,
  (val) => {
    if (val) {
      getResourceVersions();
      getSuggestionVersion();
    } else {
      stepsConfig.value.curStep = 1;
      formData.version = '';
      formData.comment = '';
    }
  },
);

watch(() => formData.version, () => {
  hasDuplicateVersionError.value = false;
  duplicateVersionErrorMsg.value = '';
});

defineExpose({
  showReleaseSideslider,
});
</script>

<style lang="scss" scoped>
.sideslider-content {
  width: 100%;

  .top-steps {
    width: 100%;
    padding: 16px 300px;
    border-bottom: 1px solid #dcdee5;
  }

  .main {
    padding: 15px 100px 0px;

    .add {
      color: #34d97b;
    }

    .update {
      color: #ffb400;
    }

    .delete {
      color: #ff5656;
    }

    .ft12 {
      color: #63656e;
    }
  }

  .resource-diff-main {
    padding: 18px 24px 24px;
  }

  .operate1 {
    padding: 0px 100px 24px;
  }

  .operate2 {
    padding: 0px 24px 24px;
  }
}

.form-tips {
  font-size: 12px;
  color: #63656e;
}

.form-item-version {
  margin-bottom: 0;

  &.is-error {
    margin-bottom: 12px;
  }
}

.version-create-status {
  margin-top: 238px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;

  .create-status-title {
    font-size: 24px;
    color: #313238;
    margin-bottom: 16px;
  }

  .create-status-subtitle {
    font-size: 14px;
    color: #63656e;
    margin-bottom: 28px;
  }

  .status-icon {
    font-size: 56px;

    &.large-icon {
      font-size: 74px;
    }
  }
}

.ml8 {
  margin-left: 8px;
}
</style>

<style lang="scss">
.custom-option-disabled {
  color: #c4c6cc !important;
  cursor: not-allowed !important;
}

.scroll {
  .bk-modal-content {
    overflow-y: auto;
  }
}

.version-publish-error-infobox {

  .bk-modal-wrapper .bk-modal-footer {
    border: none;
    background-color: #fff;
  }

  .bk-modal-wrapper .bk-dialog-footer {
    border: none;
    background-color: #fff;
    padding-bottom: 24px;

    .bk-dialog-cancel {

      display: none;
    }
  }
}
</style>
