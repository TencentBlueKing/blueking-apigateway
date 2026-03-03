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
          <EditMember
            v-if="!featureFlagStore.isTenantMode"
            ref="selectorRef"
            mode="edit"
            width="600px"
            field="contacts"
            is-required
            :exclude-self-tips="false"
            :placeholder="t('请选择联系人')"
            :content="docForm.contacts"
            :is-error-class="'maintainers-error-tip'"
            @on-change="(e:Record<string, any>) => handleContactsChange(e)"
          />
          <TenantUserSelector
            v-else
            ref="selectorRef"
            :content="docForm.contacts"
            :is-error-class="'maintainers-error-tip'"
            is-required
            :placeholder="t('请选择联系人')"
            field="contacts"
            mode="edit"
            width="600px"
            @on-change="(e:Record<string, any>) => handleContactsChange(e)"
          />
          <div class="form-item-tip lh-32px">
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
                  name="qiye-weixin"
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
              <div class="value break-all">
                {{ data?.description || '--' }}
              </div>
            </div>

            <div class="li">
              <div class="title">
                {{ t('网关负责人') }}
              </div>
              <div class="value">
                <div class="mt--8px">
                  <EditMember
                    v-if="!featureFlagStore.isTenantMode"
                    mode="detail"
                    width="600px"
                    field="maintainers"
                    :content="data?.maintainers"
                  />
                  <TenantUserSelector
                    v-else
                    :content="data?.maintainers"
                    field="maintainers"
                    mode="detail"
                    width="600px"
                  />
                </div>
              </div>
            </div>

            <div class="li">
              <div class="title">
                {{ t('文档联系人') }}
              </div>
              <div class="value">
                <div
                  v-show="docForm.type === 'user'"
                  class="mt--8px"
                >
                  <EditMember
                    v-if="!featureFlagStore.isTenantMode"
                    mode="detail"
                    width="600px"
                    field="contacts"
                    :content="docForm.contacts"
                  />
                  <TenantUserSelector
                    v-else
                    :content="docForm.contacts"
                    field="contacts"
                    mode="detail"
                    width="600px"
                  />
                </div>
                <div v-show="docForm.type === 'service_account'">
                  {{ docForm.service_account.name || '--' }}
                </div>
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
import { useFeatureFlag } from '@/stores';
import { cloneDeep } from 'lodash-es';
import { Form, Message } from 'bkui-vue';
import { patchGateway } from '@/services/source/gateway';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';

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
const featureFlagStore = useFeatureFlag();

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

const formRef = ref<InstanceType<typeof Form> & { clearValidate: () => void }>();
const selectorRef = ref<InstanceType<typeof EditMember | typeof TenantUserSelector>>();
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
  'contacts': [
    {
      required: true,
      message: t('联系人不能为空'),
      trigger: 'blur',
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
  // setTimeout(() => {
  //   docForm.value = InitForm();
  // }, 200);
  handleUpdateIsShow(false);
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
      if (!contacts.length) {
        return;
      }
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
    handleUpdateIsShow(false);
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
  nextTick(() => {
    formRef.value?.clearValidate();
    if (selectorRef.value) {
      selectorRef.value.isShowError = false;
      selectorRef.value.isEditable = false;
    }
  });
  emit('update:modelValue', value);
};

const handleContactsChange = ({ contacts }: { contacts: string[] }) => {
  docForm.value.contacts = contacts;
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
