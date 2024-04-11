<template>
  <div>
    <bk-dialog
      :is-show="dialogConfig.isShow"
      :title="dialogConfig.title"
      :is-loading="dialogConfig.loading"
      :theme="'primary'"
      quick-close
      @closed="() => (dialogConfig.isShow = false)"
      @confirm="handleCreate"
      width="600"
      class="dialog-scroll-y"
    >
      <bk-alert
        theme="info"
        class="mb15"
        :title="$t('SDK仅包含公开资源，生成后会上传到pypi源')"
      />
      <bk-form ref="baseInfoRef" form-type="vertical" :model="formData" :rules="rules">
        <bk-form-item :label="$t('资源版本')" property="resource_version_id" required>
          <bk-select v-model="formData.resource_version_id">
            <bk-option
              v-for="item in versionOpts"
              :key="item.id"
              :value="item.id"
              :label="item.version"
            />
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('SDK 版本号')" required property="version">
          <bk-input
            :placeholder="$t('请输入 SDK 版本号')"
            v-model="formData.version"
            clearable
          />
        </bk-form-item>
        <bk-form-item :label="$t('生成语言')" required property="language">
          <bk-radio-group v-model="formData.language" type="card">
            <bk-radio-button label="python">Python</bk-radio-button>
            <bk-radio-button label="golang">Golang</bk-radio-button>
          </bk-radio-group>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { IDialog } from '@/types';
import { createSdks, getResourceVersionsList } from '@/http';
import { useRoute } from 'vue-router';
import { Message } from 'bkui-vue';

const { t } = useI18n();
const route = useRoute();

// 网关id
const apigwId = computed(() => +route.params.id);

const props = defineProps<{
  versionList?: Array<any>;
  resourceVersionId?: string;
}>();

const baseInfoRef = ref(null);
// 版本列表
const versionOpts = ref<any[]>([]);

interface CreateDialog {
  resource_version_id: string;
  version: string;
  language: string;
}

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

const emit = defineEmits(['done']);

// 生成sdk
const handleCreate = async () => {
  try {
    await baseInfoRef.value?.validate();
    dialogConfig.loading = true;

    await createSdks(apigwId.value, formData);

    Message({
      message: t('创建成功'),
      theme: 'success',
    });
    dialogConfig.isShow = false;
    setTimeout(() => {
      emit('done');
    }, 300);
  } catch (e) {
    console.log(e);
  } finally {
    dialogConfig.loading = false;
  }
};

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

// 显示弹窗
const showCreateSdk = () => {
  dialogConfig.isShow = true;
};

// 获取版本列表
const getResourceVersions = async () => {
  try {
    const query = {
      offset: 0,
      limit: 1000,
    };
    const res = await getResourceVersionsList(apigwId.value, query);
    versionOpts.value = res.results;
  } catch (e) {
    console.log(e);
  }
};

watch(
  () => [props.resourceVersionId, props.versionList, dialogConfig.isShow],
  (newArr: any[]) => {
    let [id] = newArr;
    const [, opts, show] = newArr;

    if (show) {
      if (id && opts) {
        id = Number(id);
        versionOpts.value = opts;
        formData.resource_version_id = id;
        formData.version = opts?.filter((item: any) => item.id === id)[0]?.version;
      } else {
        getResourceVersions();
      }
    } else {
      setTimeout(() => {
        formData.resource_version_id = '';
        formData.version = '';
        formData.language = 'python';
      }, 1000);
    }
  },
  {
    immediate: true,
  },
);

defineExpose({
  showCreateSdk,
});
</script>
