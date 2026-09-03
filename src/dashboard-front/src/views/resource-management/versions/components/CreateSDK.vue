/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
    <BkDialog
      :is-show="dialogConfig.isShow"
      :title="dialogConfig.title"
      :is-loading="dialogConfig.loading"
      :theme="'primary'"
      quick-close
      width="600"
      class="dialog-scroll-y"
      @closed="handleClosed"
      @confirm="handleCreate"
    >
      <BkAlert
        theme="info"
        class="mb-15px"
        :title="t('SDK 包含所有资源，生成后会上传到 pypi 源或 bkrepo')"
      />
      <BkForm
        ref="baseInfoRef"
        form-type="vertical"
        :model="formData"
        :rules="rules"
      >
        <BkFormItem
          :label="t('资源版本')"
          property="resource_version_id"
          required
        >
          <BkSelect v-model="formData.resource_version_id">
            <BkOption
              v-for="item in versionOpts"
              :key="item.id"
              :value="item.id"
              :label="item.version"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem
          :label="t('生成语言')"
          required
          property="language"
        >
          <SdkLanguageSelector v-model="formData.language" />
        </BkFormItem>
      </BkForm>
    </BkDialog>
  </div>
</template>

<script setup lang="ts">
import { type IDialog } from '@/types/common';
import { createSDK, getSDKGenerationTask } from '@/services/source/sdks';
import {
  type IVersionItem,
  getVersionList,
} from '@/services/source/resource';
import { Message } from 'bkui-vue';
import SdkLanguageSelector from '@/components/sdk-language-selector/Index.vue';

interface CreateDialog {
  resource_version_id: string
  language: string
}

interface IProps {
  versionList?: IVersionItem[]
  resourceVersionId?: string
}

const {
  versionList = [],
  resourceVersionId = '',
} = defineProps<IProps>();

const emit = defineEmits<{ done: [void] }>();

const { t } = useI18n();
const route = useRoute();
const pollInterval = 2000;
const pollTimeout = 10 * 60 * 1000;
let activePollId = 0;

// 网关id
const apigwId = computed(() => +route.params.id);

const baseInfoRef = ref();
// 版本列表
const versionOpts = ref<IVersionItem[]>([]);

// 导出dialog
const dialogConfig: IDialog = reactive({
  isShow: false,
  title: t('生成 SDK'),
  loading: false,
});

// 提交表单
const formData: CreateDialog = reactive({
  resource_version_id: '',
  language: 'python',
});

// 正则校验
const rules = {
  resource_version_id: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'change',
    },
  ],
  language: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'change',
    },
  ],
};

// 获取版本列表
const getResourceVersions = async () => {
  const query = {
    offset: 0,
    limit: 1000,
  };
  const res = await getVersionList(apigwId.value, query);
  versionOpts.value = res.results as unknown as IVersionItem[];
};

watch(
  () => [resourceVersionId, versionList, dialogConfig.isShow],
  (newArr: any[]) => {
    let [id] = newArr;
    const [, opts, show] = newArr;

    if (show) {
      if (id && opts) {
        id = Number(id);
        versionOpts.value = opts;
        formData.resource_version_id = id;
      }
      else {
        getResourceVersions();
      }
    }
    else {
      setTimeout(() => {
        formData.resource_version_id = '';
        formData.language = 'python';
      }, 500);
    }
  },
  { immediate: true },
);

// 生成sdk
const handleCreate = async () => {
  const pollId = ++activePollId;
  try {
    await baseInfoRef.value?.validate();
    dialogConfig.loading = true;

    const acceptedTask = await createSDK(apigwId.value, {
      resource_version_id: Number(formData.resource_version_id),
      languages: [formData.language],
    });
    if (pollId !== activePollId) {
      return;
    }
    const deadline = Date.now() + pollTimeout;
    let task = await getSDKGenerationTask(apigwId.value, acceptedTask.id);
    if (pollId !== activePollId) {
      return;
    }
    while (['pending', 'running'].includes(task.status)) {
      if (pollId !== activePollId) {
        return;
      }
      if (Date.now() >= deadline) {
        Message({
          message: t('SDK 生成超时，请稍后在 SDK 列表中查看结果'),
          theme: 'warning',
        });
        return;
      }
      await new Promise(resolve => setTimeout(resolve, pollInterval));
      if (pollId !== activePollId) {
        return;
      }
      task = await getSDKGenerationTask(apigwId.value, acceptedTask.id);
      if (pollId !== activePollId) {
        return;
      }
    }

    const requestedItem = task.items.find(item => item.language === formData.language);
    const hasGenericArtifact = requestedItem?.artifacts.some(artifact => (
      artifact.distributor === 'bkrepo_generic'
      && artifact.filename !== 'manifest.json'
      && artifact.status === 'success'
    ));
    if (requestedItem?.status === 'partial' && hasGenericArtifact) {
      Message({
        message: t('SDK 已生成到 BKRepo，但部分仓库发布失败'),
        theme: 'warning',
      });
    }
    else if (requestedItem?.status === 'success') {
      Message({
        message: t('创建成功'),
        theme: 'success',
      });
    }
    else {
      Message({
        message: requestedItem?.error?.message || t('SDK 生成失败'),
        theme: 'error',
      });
      return;
    }

    handleClosed();
    setTimeout(() => {
      emit('done');
    }, 300);
  }
  finally {
    if (pollId === activePollId) {
      dialogConfig.loading = false;
    }
  }
};

const handleClosed = () => {
  activePollId += 1;
  dialogConfig.isShow = false;
  dialogConfig.loading = false;
  baseInfoRef.value?.clearValidate();
};

onBeforeUnmount(() => {
  activePollId += 1;
});

// 显示弹窗
const showCreateSdk = () => {
  dialogConfig.isShow = true;
};

defineExpose({ showCreateSdk });
</script>

<style lang="scss" scoped>

:deep(.bk-button-group) {
  display: flex;
}

</style>
