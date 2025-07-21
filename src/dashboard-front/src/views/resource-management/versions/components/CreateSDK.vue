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
      @closed="() => (dialogConfig.isShow = false)"
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
          :label="t('SDK 版本号')"
          required
          property="version"
        >
          <BkInput
            v-model="formData.version"
            :placeholder="t('请输入 SDK 版本号')"
            clearable
          />
        </BkFormItem>
        <BkFormItem
          :label="t('生成语言')"
          required
          property="language"
        >
          <BkRadioGroup
            v-model="formData.language"
            type="card"
          >
            <BkRadioButton
              v-for="option in languageOptions"
              :key="option.label"
              :label="option.label"
            >
              {{ option.text }}
            </BkRadioButton>
          </BkRadioGroup>
        </BkFormItem>
      </BkForm>
    </BkDialog>
  </div>
</template>

<script setup lang="ts">
import { type IDialog } from '@/types/common';
import { createSDK } from '@/services/source/sdks';
import {
  type IVersionItem,
  getVersionList,
} from '@/services/source/resource';
import { Message } from 'bkui-vue';

interface CreateDialog {
  resource_version_id: string
  version: string
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

// 网关id
const apigwId = computed(() => +route.params.id);

const baseInfoRef = ref();
// 版本列表
const versionOpts = ref<IVersionItem[]>([]);
const languageOptions = ref([
  {
    label: 'python',
    text: 'Python',
  },
  {
    label: 'golang',
    text: 'Golang',
  },
  {
    label: 'java',
    text: 'Java',
  },
]);

// 导出dialog
const dialogConfig: IDialog = reactive({
  isShow: false,
  title: t('生成 SDK'),
  loading: false,
});

// 提交表单
const formData: CreateDialog = reactive({
  resource_version_id: '',
  version: '',
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
  version: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
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
  versionOpts.value = res.results;
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
        formData.version = opts?.filter((item: any) => item.id === id)[0]?.version;
      }
      else {
        getResourceVersions();
      }
    }
    else {
      setTimeout(() => {
        formData.resource_version_id = '';
        formData.version = '';
        formData.language = 'python';
      }, 1000);
    }
  },
  { immediate: true },
);

// 生成sdk
const handleCreate = async () => {
  try {
    await baseInfoRef.value?.validate();
    dialogConfig.loading = true;

    await createSDK(apigwId.value, formData);

    Message({
      message: t('创建成功'),
      theme: 'success',
    });
    dialogConfig.isShow = false;
    setTimeout(() => {
      emit('done');
    }, 300);
  }
  finally {
    dialogConfig.loading = false;
  }
};

// 显示弹窗
const showCreateSdk = () => {
  dialogConfig.isShow = true;
};

defineExpose({ showCreateSdk });
</script>
