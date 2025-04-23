<template>
  <bk-sideslider
    v-model:is-show="isShow"
    :title="isEdit ? t('编辑网关') : t('新建网关')"
    width="1020"
  >
    <section class="create-gateway">
      <div class="create-form">
        <bk-form ref="formRef" form-type="vertical" class="create-gw-form" :model="formData" :rules="rules">
          <bk-form-item
            :label="t('网关类型')"
            property="kind"
            required
          >
            <bk-radio-group v-model="formData.kind" type="card" :disabled="isEdit">
              <bk-radio-button :label="0">
                <span class="kind normal">{{ t('普') }}</span>
                {{ t('普通网关') }}
              </bk-radio-button>
              <bk-radio-button :label="1">
                <span class="kind program">{{ t('编') }}</span>
                {{ t('可编程网关') }}
              </bk-radio-button>
            </bk-radio-group>
          </bk-form-item>
          <bk-alert theme="info" class="form-item-alert" v-show="formData.kind === 1">
            <template #title>
              <p class="flex-row">
                {{ t('通过编码的方式配置和管理网关的功能，支持接口组合、协议转换和接口编排等功能') }}&nbsp;&nbsp;
                <bk-button theme="primary" text>
                  {{ t('查看指引 >') }}
                </bk-button>
              </p>
            </template>
          </bk-alert>
          <bk-form-item
            class="form-item-name"
            :label="t('名称')"
            property="name"
            required
          >
            <bk-input
              v-model="formData.name"
              :maxlength="30"
              :disabled="isEdit"
              show-word-limit
              :placeholder="t('请输入小写字母、数字、连字符(-)，以小写字母开头')"
              clearable
              autofocus
            />
          </bk-form-item>
          <span class="common-form-tips form-item-name-tips">
            {{ t('网关的唯一标识，创建后不可更改') }}
          </span>
          <bk-form-item
            :label="t('开发语言')"
            property="extra_info.language"
            required
            v-if="formData.kind === 1"
          >
            <bk-select
              class="bk-select"
              :disabled="isEdit"
              v-model="formData.extra_info.language"
            >
              <bk-option
                v-for="item in languageList"
                :key="item.value"
                :id="item.value"
                :name="item.label"
              />
            </bk-select>
          </bk-form-item>
          <bk-form-item
            :label="t('维护人员')"
            property="maintainers"
            required
          >
            <member-select v-model="formData.maintainers" />
          </bk-form-item>
          <bk-form-item
            :label="t('描述')"
            property="description"
          >
            <bk-input
              type="textarea"
              v-model="formData.description"
              :placeholder="t('请输入网关描述')"
              :maxlength="500"
              clearable
            />
          </bk-form-item>

          <template v-if="formData.kind === 1 && BK_APP_VERSION === 'te'">
            <bk-form-item
              :label="t('代码仓库')"
              class="form-item-name"
              property="extra_info.repository"
              required
            >
              <bk-input v-model="formData.extra_info.repository" disabled />
            </bk-form-item>
            <span class="common-form-tips form-item-name-tips">
              {{ t('自动创建开源仓库，将模板代码初始化到仓库中，并将创建者设定为仓库管理员') }}
            </span>
          </template>

          <template v-if="formData.kind === 1 && BK_APP_VERSION === 'ee' && !isEdit">
            <bk-form-item
              :label="t('代码源')"
              required
            >
              <div class="flex-row align-items-center">
                <div class="repository-item active">
                  <img :src="bareGitImg" :alt="t('Git 代码库')">
                  <p class="text">{{ t('Git 代码库') }}</p>
                  <div class="checked-icon">
                    <i class="apigateway-icon icon-ag-check-circle-shape"></i>
                  </div>
                </div>
              </div>
            </bk-form-item>
            <bk-form-item
              :label="t('代码仓库地址')"
              property="programmable_gateway_git_info.repository"
              required
            >
              <bk-input v-model="formData.programmable_gateway_git_info.repository" />
            </bk-form-item>
            <bk-form-item
              :label="t('账号')"
              property="programmable_gateway_git_info.account"
              required
            >
              <bk-input v-model="formData.programmable_gateway_git_info.account" />
            </bk-form-item>
            <bk-form-item
              :label="t('密码')"
              property="programmable_gateway_git_info.password"
              required
            >
              <bk-input v-model="formData.programmable_gateway_git_info.password" />
            </bk-form-item>
          </template>

          <bk-form-item
            :label="t('是否公开')"
            property="is_public"
            required
          >
            <bk-switcher theme="primary" v-model="formData.is_public" />
            <span class="common-form-tips">{{ t('公开，则用户可查看资源文档、申请资源权限；不公开，则网关对用户隐藏') }}</span>
          </bk-form-item>

          <template v-if="isEdit">
            <bk-form-item
              :label="t('关联蓝鲸应用')"
              property="bk_app_codes"
              v-if="user?.featureFlags?.GATEWAY_APP_BINDING_ENABLED"
            >
              <bk-tag-input
                v-model="formData.bk_app_codes"
                :placeholder="t('请输入蓝鲸应用ID，并按enter确认')"
                allow-create
                has-delete-icon
                collapse-tags
                :list="[]"
              />
              <span class="common-form-tips">{{ t('仅影响 HomePage 中运维开发分数的计算') }}</span>
            </bk-form-item>
            <bk-form-item
              :label="t('管理网关的应用列表 ')"
              property="related_app_codes"
            >
              <bk-tag-input
                v-model="formData.related_app_codes"
                :placeholder="t('请输入蓝鲸应用ID，并按enter确认')"
                allow-create
                has-delete-icon
                collapse-tags
              />
              <span class="common-form-tips">{{ t('允许列表中的应用使用 sdk 或者开放 API 调用网关接口，同步环境/资源以及发布版本') }}</span>
            </bk-form-item>
          </template>
        </bk-form>

        <div class="operate-btn">
          <bk-pop-confirm
            width="288"
            :content="t('您已将自己从维护人员列表中移除，移除后您将失去查看和编辑网关的权限。请确认！')"
            trigger="click"
            ext-cls="confirm-custom-btn"
            @confirm="handleConfirmCreate"
            @cancel="handleCancel"
            v-if="!formData.maintainers?.includes(user.user.username) && isEdit"
          >
            <bk-button theme="primary" :loading="submitLoading">
              {{ t('确定') }}
            </bk-button>
          </bk-pop-confirm>
          <bk-button v-else theme="primary" :loading="submitLoading" @click="handleConfirmCreate">
            {{ t('确定') }}
          </bk-button>
          <bk-button @click="handleCancel" class="ml8">
            {{ t('取消') }}
          </bk-button>
        </div>
      </div>

      <div class="progress">
        <div class="title">
          {{ formData.kind === 0 ? t('普通网关发布流程') : t('编程网关发布流程') }}
        </div>
        <bk-timeline :list="progressList" />
      </div>
    </section>
  </bk-sideslider>
</template>

<script lang="ts" setup>
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUser } from '@/store/user';
import { createGateway, getEnvVars, editGateWays } from '@/http';
import { Message } from 'bkui-vue';
import { cloneDeep } from 'lodash';
// @ts-ignore
import { BasicInfoParams } from '@/basic-info/common/type';
import MemberSelect from '@/components/member-select';
// @ts-ignore
import bareGit from '@/images/bare_git.png';

const user = useUser();
const { t } = useI18n();

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  initData: {
    type: Object,
    default: () => ({
      kind: 0,
      extra_info: {
        language: 'python',
        repository: '',
      },
    }),
  },
});

const emit = defineEmits(['update:modelValue', 'done']);

const { BK_APP_VERSION } = window;

// interface IinitDialogData {
//   kind?: number
//   name?: string
//   id?: number
//   maintainers?: string[]
//   description?: string
//   is_public?: boolean
//   bk_app_codes?: string[]
//   extra_info?: {
//     language?: string
//     repository?: string
//   }
//   programmable_gateway_git_info?: {
//     repository: string
//     account: string
//     password: string
//   }
// }

const defaultFormData = {
  name: '',
  description: '',
  is_public: true,
  kind: 0,
  maintainers: [user.user.username],
  extra_info: {
    language: 'python',
    repository: '',
  },
  programmable_gateway_git_info: {
    repository: '',
    account: '',
    password: '',
  },
};

const isShow = ref<boolean>(props.modelValue);
const formRef = ref(null);
const formData = ref<BasicInfoParams>(cloneDeep(defaultFormData));
const submitLoading = ref<boolean>(false);
const repositoryUrl = ref<string>('');
const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'change',
    },
    {
      validator: (value: string) => value.length >= 3,
      message: t('不能小于3个字符'),
      trigger: 'change',
    },
    {
      validator: (value: string) => value.length <= 30,
      message: t('不能多于30个字符'),
      trigger: 'change',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-z][a-z0-9-]*$/;
        return reg.test(value);
      },
      message: t('由小写字母、数字、连接符（-）组成，首字符必须是小写字母，长度大于3小于30个字符'),
      trigger: 'change',
    },
  ],
};
const languageList = [
  {
    value: 'python',
    label: 'Python',
  },
  {
    value: 'go',
    label: 'Go',
  },
];

const bareGitImg = computed(() => {
  return bareGit;
});

const isEdit = computed(() => {
  return !!formData.value?.id;
});

const progressList = computed(() => {
  if (formData.value.kind === 0) {
    return [
      {
        tag: t('创建网关'),
        content: `<span class="progress-subtitle">${t('初始化环境： prod ，并可新增环境')}</span>`,
        color: 'blue',
      },
      {
        tag: t('配置后端服务'),
        content: `<span class="progress-subtitle">${t('每个环境都可以单独配置后端 API 的域名')}</span>`,
      },
      {
        tag: t('资源配置'),
        content: `<span class="progress-subtitle">${t('页面添加或通过 Swagger/OpenAPI 文件导入')}</span>`,
      },
      {
        tag: t('生成版本'),
        content: `<span class="progress-subtitle">${t('资源列表快照可以用于对比差异，并生成 SDK')}</span>`,
      },
      {
        tag: t('发布到环境'),
        content: `<span class="progress-subtitle">${t('发布成后，即可通过网关访问 API')}</span>`,
      },
    ];
  }
  return [
    {
      tag: t('创建网关'),
      content: `<span class="progress-subtitle">
        ${t('自动创建代码仓库并包含代码示例初始化')} <b>2</b> ${t('套环境：stag 和 prod')}
      </span>`,
      color: 'blue',
    },
    {
      tag: t('开发 API'),
      content: `<p class="progress-subtitle progress-p">${t('在代码仓库定义资源配置')}</p>
      <p class="progress-subtitle">${t('同时可对 API 进行')} <b>${t('网络协议转、接口组合编排')}</b> ${t('等')}</p>`,
    },
    {
      tag: t('发布到环境'),
      content: `<p class="progress-subtitle progress-p">${t('自动生成版本')}</p>
      <p class="progress-subtitle">${t('自动部署 web 服务，并将域名到注册后端服务地址')}</p> `,
    },
  ];
});

const getUrlPrefix = async () => {
  const res = await getEnvVars();
  repositoryUrl.value = res.BK_PAAS_APP_REPO_URL_TMPL;
};
if (BK_APP_VERSION === 'te') {
  getUrlPrefix();
}

const handleConfirmCreate = async () => {
  try {
    await formRef.value.validate();

    submitLoading.value = true;
    const payload = cloneDeep(formData.value);
    if (payload.kind === 0) {
      payload.extra_info = undefined;
    }
    if (payload.kind === 1 && BK_APP_VERSION === 'ee' && !isEdit.value) {
      payload.extra_info.repository = payload.programmable_gateway_git_info.repository;
    }

    if (isEdit.value) {
      if (!user?.featureFlags?.GATEWAY_APP_BINDING_ENABLED) {
        payload.bk_app_codes = undefined;
      }
      await editGateWays(payload.id, payload);
      Message({
        message: t('编辑成功'),
        theme: 'success',
        width: 'auto',
      });
    } else {
      await createGateway(payload);
      Message({
        message: t('创建成功'),
        theme: 'success',
      });
    }

    isShow.value = false;
    formData.value = cloneDeep(defaultFormData);
    emit('done');
  } catch (error) {
  } finally {
    submitLoading.value = false;
  }
};

const handleCancel = () => {
  isShow.value = false;
  formData.value = cloneDeep(defaultFormData);
};

watch(
  () => formData.value.name,
  () => {
    if (BK_APP_VERSION === 'te' && formData.value.kind === 1) {
      formData.value.extra_info.repository = `${repositoryUrl.value.replace('{{gateway_name}}', formData.value.name)}`;
    }
  },
);

watch(
  () => props.modelValue,
  (value: boolean) => {
    isShow.value = value;
  },
);

watch(
  () => isShow.value,
  (v) => {
    emit('update:modelValue', v);
  },
);

watch(
  () => props.initData,
  (payload: BasicInfoParams) => {
    if (payload) {
      formData.value = payload;
    }
  },
);

</script>

<style lang="scss" scoped>
.create-gateway {
  display: flex;
  .create-form {
    flex: 1;
    background: #FFFFFF;
    padding: 0 24px;
    height: calc(100vh - 68px);
    overflow-y: auto;
  }
  .form-item-name {
    :deep(.bk-form-error) {
      position: relative;
    }
  }
  .form-item-name-tips {
    position: relative;
    top: -20px;
  }
  .progress {
    width: 400px;
    height: calc(100vh - 52px);
    padding: 24px;
    box-sizing: border-box;
    background: #F5F7FA;
    margin-top: -16px;
    margin-right: -14px;
    .title {
      color: #4D4F56;
      font-size: 14px;
      font-weight: Bold;
      padding-bottom: 16px;
    }
  }
}
.form-item-alert {
  margin-bottom: 16px;
  margin-top: -10px;
}
.kind {
  content: ' ';
  width: 20px;
  height: 20px;
  border-radius: 2px;
  padding: 1px 2px;
  font-size: 12px;
  text-align: center;
  margin-right: 4px;
  &.normal {
    color: #1768EF;
    background: #E1ECFF;
    border: 1px solid #699DF4;
  }
  &.program {
    color: #299E56;
    background: #EBFAF0;
    border: 1px solid #A1E3BA;
  }
}
.repository-item {
  width: 124px;
  height: 88px;
  border: 1px solid #c4c6cc;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  img {
    width: 40px;
    height: 40px;
  }
  .text {
    font-size: 14px;
    color: #63656E;
  }
  &.active {
    border: 1px solid #3A84FF;
    position: relative;
    .checked-icon {
      position: absolute;
      width: 18px;
      height: 18px;
      top: -9px;
      right: -9px;
      background-color: #FFFFFF;
      display: flex;
      align-items: center;
      justify-content: center;
      .apigateway-icon {
        color: #3A84FF;
        width: 14px;
        height: 14px;
      }
    }
  }
}
:deep(.progress-subtitle) {
  font-size: 12px;
  color: #979BA5;
}
:deep(.progress-p) {
  margin-bottom: 4px;
}
:deep(.bk-timeline-content) {
  word-break: normal !important;
}
</style>
