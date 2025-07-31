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
  <div class="release-sideslider">
    <BkSideslider
      v-model:is-show="isShow"
      :width="960"
      :title="t('生成资源版本')"
      quick-close
      class="scroll"
      @hidden="handleCancel"
    >
      <template #default>
        <div
          v-if="!dialogShow"
          class="sideslider-content"
        >
          <div class="top-steps">
            <BkSteps
              :controllable="stepsConfig.controllable"
              :cur-step="stepsConfig.curStep"
              :steps="stepsConfig.objectSteps"
            />
          </div>
          <div>
            <template v-if="stepsConfig.curStep === 1">
              <div class="resource-diff-main">
                <VersionDiff
                  :source-id="diffSourceId"
                  :target-id="diffTargetId"
                  page-type="createVersion"
                  :source-switch="false"
                  :target-switch="false"
                />
              </div>
            </template>
            <template v-else>
              <div class="main">
                <!-- <BkAlert
                  theme="info"
                  :title="t('尚未发布')"
                  v-if="!versionList?.length"
                  class="mt-15px mb15" /> -->
                <BkAlert
                  v-if="versionList.length && versionList[0].version"
                  theme="info"
                  :title="`${t('最新版本号')}: ${versionList[0]?.version || '--'},
                  ${t('于')} ${versionList[0]?.created_time || '--'} ${t('创建')}`"
                  class="mb-15px"
                />

                <BkForm
                  ref="formRef"
                  :model="formData"
                  :rules="rules"
                  form-type="vertical"
                >
                  <BkFormItem
                    property="version"
                    :label="t('版本号')"
                    :description="t('版本号须符合 Semver 规范，例如：1.1.1，1.1.1-alpha.1')"
                    class="form-item-version mt-20px mb-15px"
                    required
                  >
                    <!-- <BkPopover
                      :content="t('由数字、字母、中折线（-）、点号（.）组成，长度小于64个字符')"
                      theme="light"
                      >
                      </BkPopover> -->
                    <BkInput
                      v-model="formData.version"
                      :placeholder="t('由数字、字母、中折线（-）、点号（.）组成，长度小于64个字符')"
                    />
                  </BkFormItem>
                  <BkFormItem>
                    <section class="text-12px">
                      <span>
                        {{ t("新增") }}
                        <strong class="font-bold color-#2dcb56">{{ diffData.add.length }}</strong>
                        {{ t("个资源") }}，
                      </span>
                      <span>
                        {{ t("更新") }}
                        <strong class="font-bold color-#ff9c01">{{ diffData.update.length }}</strong>
                        {{ t("个资源") }}，
                      </span>
                      <span>
                        {{ t("删除") }}
                        <strong class="font-bold color-#ea3636">{{ diffData.delete.length }}</strong>
                        {{ t("个资源") }}
                      </span>
                    </section>
                  </BkFormItem>
                  <BkFormItem
                    property="comment"
                    :label="t('版本日志')"
                  >
                    <BkInput
                      v-model="formData.comment"
                      type="textarea"
                      :rows="4"
                      :maxlength="100"
                    />
                  </BkFormItem>
                </BkForm>
              </div>
            </template>
            <div :class="stepsConfig.curStep === 1 ? 'operate2' : 'operate1'">
              <BkButton
                v-if="stepsConfig.curStep === 1"
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
                  :loading="loading"
                  @click="handleBuildVersion"
                >
                  {{ t('确定') }}
                </BkButton>
                <BkButton
                  class="ml-10px w-100px"
                  @click="handleBack"
                >
                  {{ t('上一步') }}
                </BkButton>
              </template>
              <BkButton
                class="ml-10px w-100px"
                @click="handleCancel"
              >
                {{ t('取消') }}
              </BkButton>
            </div>
          </div>
        </div>

        <div
          v-else
          class="version-create-status"
        >
          <div
            v-if="loading"
            class="create-status"
          >
            <Spinner
              class="status-icon"
              fill="#3A84FF"
            />
            <p class="create-status-title">
              {{ t('版本正在生成中...') }}
            </p>
            <p class="create-status-subtitle">
              {{ t('请稍等') }}
            </p>
          </div>

          <div
            v-if="!loading && !createError"
            class="create-status"
          >
            <Success
              class="status-icon large-icon"
              fill="#2DCB56"
            />
            <p class="create-status-title">
              {{ t('版本生成成功') }}
            </p>
            <p class="create-status-subtitle">
              {{ t('接下来你可以直接发布至环境，或跳转资源版本') }}
            </p>
            <div class="create-status-btns">
              <BkButton
                theme="primary"
                @click="handlePublish"
              >
                {{ t('立即发布') }}
              </BkButton>
              <BkButton
                class="ml-8px"
                @click="handleSkip"
              >
                {{ t('跳转资源版本') }}
              </BkButton>
            </div>
          </div>

          <!--          <div class="create-status" v-if="!loading && createError"> -->
          <!--            <close class="status-icon large-icon" fill="#EA3636" /> -->
          <!--            <p class="create-status-title"> -->
          <!--              {{ t('版本生成失败') }} -->
          <!--            </p> -->
          <!--            <p class="create-status-subtitle"> -->
          <!--              {{ t('接下来你可以重试或关闭弹窗') }} -->
          <!--            </p> -->
          <!--            <div class="create-status-btns"> -->
          <!--              <BkButton theme="primary" @click="handleBuildVersion"> -->
          <!--                {{ t('重试') }} -->
          <!--              </BkButton> -->
          <!--              <BkButton class="ml-8px" @click="handleCancel"> -->
          <!--                {{ t('关闭') }} -->
          <!--              </BkButton> -->
          <!--            </div> -->
          <!--          </div> -->
        </div>
      </template>
    </BkSideslider>

    <!-- 确认发布弹窗 -->
    <!-- <custom-dialog
      :title="t('版本生成成功')"
      :sub-title="t('接下来，可以前往 “资源发布” 发布到不同的环境')"
      :is-show="dialogShow"
      @comfirm="handleSkip"
      @cancel="handleCancel">
      </custom-dialog> -->

    <!-- 发布资源 -->
    <ReleaseStage
      ref="releaseSidesliderRef"
      :current-assets="stageData"
      :version="versionData"
      @release-success="handleSkip"
    />
  </div>
</template>

<script setup lang="ts">
import semver from 'semver';
import {
  Spinner,
  Success,
} from 'bkui-vue/lib/icon';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import ReleaseStage from '@/components/release-stage/Index.vue';
import {
  createResourceVersion,
  getNextVersion,
  getVersionDiff,
  getVersionList,
} from '@/services/source/resource';
import { getStageList } from '@/services/source/stage';
import { useGetStageList } from '@/hooks';
import VersionDiff from '@/components/version-diff/Index.vue';

type VersionType = {
  id: number
  version: string
  isLatestVersion: boolean
};

const emit = defineEmits<{ done: [void] }>();

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
const formRef = ref();
const diffSourceId = ref('');
const diffTargetId = ref('');
const loading = ref(false);
const createError = ref(false);
const hasDuplicateVersionError = ref(false);
const duplicateVersionErrorMsg = ref('');
const releaseSidesliderRef = ref();
const versionData = ref<any>();
const stageData = ref<any>();

interface FormData {
  version: string
  comment: string
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
  }
  catch (e) {
    const error = e as Error;
    const errMsg = error?.message?.toLowerCase() || t('版本号已存在');
    if (
      (errMsg.includes('版本') && errMsg.includes('已存在'))
      || (errMsg.includes('resource version') && errMsg.includes('already exists'))
    ) {
      hasDuplicateVersionError.value = true;
      duplicateVersionErrorMsg.value = errMsg;
      await formRef.value!.validate('version');
    }
    else {
      // createError.value = true;
      InfoBox({
        'ext-cls': 'version-publish-error-infobox',
        'infoType': 'danger',
        'title': t('版本生成失败'),
        'subTitle': t('版本号创建失败，请联系管理员'),
        'confirmText': t('关闭'),
      });
    }
  }
  finally {
    loading.value = false;
  }
};

const getDiffData = async () => {
  diffData.value.add = [];
  diffData.value.delete = [];
  diffData.value.update = [];

  const res = await getVersionDiff(apigwId.value, {
    source_resource_version_id: diffSourceId.value.replace('current', ''),
    target_resource_version_id: diffTargetId.value.replace('current', ''),
  });

  diffData.value.add = res.add;
  diffData.value.delete = res.delete;
  diffData.value.update = res.update;
};

// 显示侧边栏
const showReleaseSideslider = () => {
  isShow.value = true;
};

// 获取资源版本列表
const getResourceVersions = async () => {
  const response = await getVersionList(apigwId.value, {
    offset: 0,
    limit: 10,
  });
  versionList.value = response.results;
  if (!response.results.length) {
    diffSourceId.value = 'current';
  }
  else {
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
    router.push({ name: 'ResourceVersion' });
  }, 300);
};

const handlePublish = async () => {
  try {
    const { results } = await getVersionList(apigwId.value, {
      offset: 0,
      limit: 10,
    });
    const newVersion = results.filter((item: VersionType) => item.version === formData.version)[0];
    if (newVersion?.id) {
      versionData.value = newVersion;
    }
    const stages = await getStageList(apigwId.value);
    const [defaultStage] = stages;
    stageData.value = defaultStage;
    releaseSidesliderRef.value.showReleaseSideslider();
    handleCancel();
  }
  catch {
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
  isShow,
  (val) => {
    if (val) {
      getResourceVersions();
      getSuggestionVersion();
    }
    else {
      stepsConfig.value.curStep = 1;
      formData.version = '';
      formData.comment = '';
    }
  },
);

watch(
  () => formData.version,
  () => {
    hasDuplicateVersionError.value = false;
    duplicateVersionErrorMsg.value = '';
  });

defineExpose({ showReleaseSideslider });
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
    padding: 15px 100px 0;

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
    padding: 0 100px 24px;
  }

  .operate2 {
    padding: 0 24px 24px;
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
  display: flex;
  margin-top: 238px;
  text-align: center;
  flex-direction: column;
  justify-content: center;

  .create-status-title {
    margin-bottom: 16px;
    font-size: 24px;
    color: #313238;
  }

  .create-status-subtitle {
    margin-bottom: 28px;
    font-size: 14px;
    color: #63656e;
  }

  .status-icon {
    font-size: 56px;

    &.large-icon {
      font-size: 74px;
    }
  }
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
    background-color: #fff;
    border: none;
  }

  .bk-modal-wrapper .bk-dialog-footer {
    padding-bottom: 24px;
    background-color: #fff;
    border: none;

    .bk-dialog-cancel {
      display: none;
    }
  }
}
</style>
