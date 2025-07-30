<template>
  <BkDialog
    width="640"
    :is-show="modelValue"
    :title="t('编辑API文档')"
    @update:is-show="handleUpdateIsShow"
  >
    <div class="doc-form">
      <BkForm
        ref="formRef"
        form-type="vertical"
        :model="docForm"
        :rules="rules"
      >
        <BkFormItem
          :label="t('联系人类型')"
          property="type"
        >
          <BkRadioGroup v-model="docForm.type">
            <BkRadio label="user">
              {{ t('用户') }}
            </BkRadio>
            <BkRadio label="service_account">
              {{ t('服务号') }}
            </BkRadio>
          </BkRadioGroup>
        </BkFormItem>

        <BkFormItem
          v-if="docForm.type === 'user'"
          :label="t('联系人')"
          property="contacts"
          required
        >
          <MemberSelector
            v-model="docForm.contacts"
            :placeholder="t('请选择')"
            has-delete-icon
          />
          <div class="form-item-tip">
            <span>{{ t('文档页面上展示出来的文档咨询接口人') }}</span>
          </div>
        </BkFormItem>

        <BkFormItem
          v-if="docForm.type === 'service_account'"
          :label="t('服务号名称')"
          property="service_account.name"
          required
        >
          <BkInput
            v-model="docForm.service_account.name"
            :placeholder="t('请输入服务号名称，如BK助手')"
          />
        </BkFormItem>
        <BkFormItem
          v-if="docForm.type === 'service_account'"
          :label="t('服务号链接')"
          property="service_account.link"
          required
        >
          <BkInput
            v-model="docForm.service_account.link"
            :placeholder="t('如 wxwork://message?uin=00000')"
          />
        </BkFormItem>

        <BkFormItem
          :label="t('文档地址')"
          class="virtual-required"
        >
          <span class="link">{{ data?.docs_url || '--' }}</span>
        </BkFormItem>
      </BkForm>
    </div>
    <template #footer>
      <BkPopover
        width="280"
        placement="top"
        theme="light"
        trigger="click"
      >
        <BkButton class="mr-4px">
          {{ t('预览') }}
        </BkButton>
        <template #content>
          <div class="preview-content">
            <div class="header li">
              <div class="title">
                {{ t('网关详情') }}
              </div>
              <div
                v-bk-tooltips="{
                  content: docForm.type === 'user' ? docForm.contacts?.join(',') : t('联系服务号'),
                  theme: 'light',
                  placement: 'bottom',
                }"
                class="opt"
              >
                <AgIcon
                  name="doc-icon"
                  size="16"
                  class="doc-qw icon-ag-qw"
                />
                {{ docForm.type === 'user' ? t('一键拉群') : docForm.service_account.name }}
              </div>
            </div>

            <div class="li">
              <div class="title">
                {{ t('网关描述') }}
              </div>
              <div class="value">
                {{ data?.description || '--' }}
              </div>
            </div>

            <div class="li">
              <div class="title">
                {{ t('网关负责人') }}
              </div>
              <div class="value">
                {{ data?.maintainers?.join(',') || '--' }}
              </div>
            </div>

            <div class="li">
              <div class="title">
                {{ t('网关访问地址') }}
              </div>
              <div class="value">
                {{ data?.api_domain || '--' }}
              </div>
            </div>
          </div>
        </template>
      </BkPopover>

      <BkButton
        theme="primary"
        :loading="loading"
        class="mr-4px"
        @click="handleCommit"
      >
        {{ t('确定') }}
      </BkButton>
      <BkButton @click="handleCancel">
        {{ t('取消') }}
      </BkButton>
    </template>
  </BkDialog>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import { Message } from 'bkui-vue';
import MemberSelector from '@/components/member-selector';
import { patchGateway } from '@/services/source/gateway';

interface IForm {
  type: string
  contacts: string[]
  service_account: {
    name: string
    link: string
  }
}

interface IProps {
  modelValue?: boolean
  data?: any
}

const {
  modelValue = false,
  data = {},
} = defineProps<IProps>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'done': [void]
}>();

const { t } = useI18n();

const InitForm = (): IForm => {
  return {
    type: 'user',
    contacts: [],
    service_account: {
      name: '',
      link: '',
    },
  };
};

const formRef = ref();
const loading = ref<boolean>(false);
const docForm = ref<IForm>(InitForm());

const rules = {
  'service_account.link': [
    {
      required: true,
      message: t('请填写服务号链接'),
      trigger: 'change',
    },
    {
      validator: (value: string) => {
        const reg = /^wxwork:\/\//;
        return reg.test(value);
      },
      message: t('请输入正确的服务号链接，支持以下协议：wxwork://'),
      trigger: 'change',
    },
  ],
};

watch(
  () => modelValue,
  () => {
    if (modelValue) {
      const { doc_maintainers } = data;
      docForm.value = cloneDeep(doc_maintainers);
    }
  },
);

const handleCancel = () => {
  emit('update:modelValue', false);
  // setTimeout(() => {
  //   docForm.value = InitForm();
  // }, 200);
};

const handleCommit = async () => {
  try {
    await formRef.value.validate();

    loading.value = true;

    const payload: any = { ...data };

    const { type, contacts, service_account } = docForm.value;
    if (type === 'user') {
      payload.doc_maintainers = {
        type,
        contacts,
        service_account: {
          name: '',
          link: '',
        },
      };
    }
    else {
      payload.doc_maintainers = {
        type,
        contacts: [],
        service_account,
      };
    }

    await patchGateway(data.id, payload);

    emit('done');
    emit('update:modelValue', false);
    Message({
      message: t('更新成功'),
      theme: 'success',
      width: 'auto',
    });
  }
  finally {
    loading.value = false;
  }
};

const handleUpdateIsShow = (value: boolean) => {
  emit('update:modelValue', value);
};

</script>

<style lang="scss" scoped>
.form-item-tip {
  font-size: 12px;
  color: #979BA5;
}

.doc-form {

  :deep(.bk-form-item) {
    margin-bottom: 16px;
  }

  .virtual-required {
    position: relative;

    &::before {
      position: absolute;
      top: 2px;
      left: 62px;
      color: #EA3636;
      content: '*';
    }

    .link {
      font-size: 14px;
      color: #313238;
    }
  }
}

.preview-content {
  padding: 4px;

  .header {
    display: flex;
    justify-content: space-between;
  }

  .li {

    &:not(:nth-last-child(1)) {
      margin-bottom: 16px;
    }

    .title {
      margin-bottom: 4px;
      font-size: 12px;
      color: #4D4F56;
    }

    .value {
      font-size: 12px;
      color: #4D4F56;
    }
  }

  .opt {
    font-size: 12px;
    color: #3A84FF;
    cursor: pointer;
  }
}
</style>
