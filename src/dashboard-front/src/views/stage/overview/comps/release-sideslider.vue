<template>
  <div class="release-sideslider">
    <bk-sideslider
      v-model:isShow="isShow"
      :width="960"
      :title="`发布资源至环境【${currentAssets.name}】`"
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
                  <bk-form-item
                    property="resource_version_id"
                    :label="`发布的资源版本(当前版本: ${currentAssets.resource_version.version})`">
                    <bk-select
                      v-model="formData.resource_version_id"
                      :input-search="false"
                      filterable
                      @change="handleVersionChange"
                    >
                      <bk-option
                        v-for="(item) in versionList"
                        :key="item.id"
                        :value="item.id"
                        :label="item.version"
                        :disabled="item.disabled"
                      >
                      </bk-option>
                    </bk-select>
                    <p>
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
                  <bk-form-item property="comment" :label="$t('版本日志')">
                    <bk-input v-model="formData.comment" type="textarea" :rows="4" :maxlength="100" />
                  </bk-form-item>
                </bk-form>
              </div>
            </template>
            <template v-else>
              <div class="resource-diff-main">
                <version-diff
                  ref="diffRef"
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
                  {{ $t('确认发布') }}
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
    <bk-dialog
      :is-show="dialogConfig.isShow"
      :title="dialogConfig.title"
      :is-loading="dialogConfig.loading"
      :theme="'primary'"
      quick-close
      @closed="() => (dialogConfig.isShow = false)"
      @confirm="handlePublish"
    >
      将发布资源 {{ resourceVersion }} 版本至【{{ currentAssets.name }}】环境
    </bk-dialog>

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
import versionDiff from '@/components/version-diff';
import logDetails from '@/components/log-details/index.vue';
import { Message } from 'bkui-vue';
import { useSidebar } from '@/hooks';

const route = useRoute();
const router = useRouter();
const { initSidebarFormData, isSidebarClosed } = useSidebar();

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

const dialogConfig: IDialog = reactive({
  isShow: false,
  title: t('确认发布资源?'),
  loading: false,
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

const showPublishDia = () => {
  dialogConfig.isShow = true;
};

const publishId = ref();
const handlePublish = async () => {
  try {
    const params = {
      stage_id: props.currentAssets.id,
      ...formData,
    };
    const res = await createReleases(apigwId.value, params);

    publishId.value = res?.id;
    isShow.value = false;
    dialogConfig.isShow = false;
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
    res.results?.forEach((item: any) => {
      if (item.id === props.currentAssets?.resource_version?.id) {
        item.disabled = true;
      }
    });
    versionList.value = res.results;
  } catch (e) {
    console.log(e);
  };
};

const handleVersionChange = async (val: number) => {
  if (!val) {
    diffData.value = {
      add: [],
      delete: [],
      update: [],
    };
    return;
  };

  try {
    const query = {
      source_resource_version_id: props.currentAssets?.resource_version?.id,
      target_resource_version_id: val,
    };

    const res: any = await resourceVersionsDiff(apigwId.value, query);

    diffData.value = res;
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

watch(
  () => isShow.value,
  (val) => {
    if (val) {
      getResourceVersions();
      if (props.version?.id) {
        formData.resource_version_id = props.version?.id;
        handleVersionChange(props.version?.id);
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
    padding: 0px 100px 24px;
  }
  .operate2 {
    padding: 0px 24px 24px;
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
</style>
