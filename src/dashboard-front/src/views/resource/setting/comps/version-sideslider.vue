<template>
  <div class="release-sideslider">
    <bk-sideslider v-model:isShow="isShow" :width="960" :title="t('生成资源版本')" quick-close>
      <template #default>
        <div class="sideslider-content">
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
                  于 ${versionList[0]?.created_time || '--'} ${t('创建')}`"
                  class="mt15 mb15"
                />

                <bk-form ref="formRef" :model="formData" :rules="rules" form-type="vertical">
                  <bk-form-item
                    property="version"
                    :label="t('版本号')"
                    :description="t('版本号须符合 Semver 规范，例如：1.1.1，1.1.1-alpha.1')"
                    class="mt20"
                    required>
                    <bk-input v-model="formData.version" :placeholder="t('由数字、字母、中折线（-）、点号（.）组成，长度小于64个字符')" />
                    <!-- <div class="form-tips">
                      <i class="apigateway-icon icon-ag-info"></i>
                      {{ t('版本号须符合 Semver 规范，例如：1.1.1，1.1.1-alpha.1') }}
                    </div> -->
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
      </template>
    </bk-sideslider>

    <!-- 确认发布弹窗 -->
    <custom-dialog
      :title="t('版本生成成功')"
      :sub-title="t('接下来，可以前往 “资源发布” 发布到不同的环境')"
      :is-show="dialogShow"
      @comfirm="handleComfirm"
      @cancel="handleCancel">
    </custom-dialog>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { ref, reactive, watch, computed } from 'vue';
import semver from 'semver';
import { useRoute, useRouter } from 'vue-router';

import { getResourceVersionsList, createResourceVersion, resourceVersionsDiff } from '@/http';
import versionDiff from '@/components/version-diff/index.vue';
import CustomDialog from '@/components/custom-dialog/index.vue';

const route = useRoute();
const router = useRouter();
const apigwId = computed(() => +route.params.id);

const { t } = useI18n();

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

interface FormData {
  version: string;
  comment: string;
};
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
      message: '请选择',
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
        if (semver.valid(value) === null) {
          return false;
        }
        return true;
      },
    },
  ],
};

// 生成版本成功并弹窗
const handleBuildVersion = async () => {
  try {
    await formRef.value?.validate();
    loading.value = true;
    await createResourceVersion(apigwId.value, formData);
    // 弹窗并关闭侧栏
    dialogShow.value = true;
    isShow.value = false;
  } catch (e) {
    console.log(e);
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
      source_resource_version_id: diffSourceId.value,
      target_resource_version_id: diffTargetId.value,
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
  try {
    const res = await getResourceVersionsList(apigwId.value, { offset: 0, limit: 999 });
    versionList.value = res.results;
    diffSourceId.value = versionList.value[0]?.id || '';
  } catch (e) {
    console.log(e);
  }
};

// 下一步
const handleNext = async () => {
  await formRef.value?.validate();
  stepsConfig.value.curStep = 2;
  getDiffData();
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

// 版本生成成功确认
const handleComfirm = () => {
  router.push({
    name: 'apigwResourceVersion',
  });
};

watch(
  () => isShow.value,
  (val) => {
    if (val) {
      getResourceVersions();
    } else {
      stepsConfig.value.curStep = 1;
      formData.version = '';
      formData.comment = '';
    };
  },
);

defineExpose({
  showReleaseSideslider,
});
</script>

  <style lang="scss" scoped>
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
  </style>

  <style lang="scss">
  .custom-option-disabled {
    color: #c4c6cc !important;
    cursor: not-allowed !important;
  }
  </style>
