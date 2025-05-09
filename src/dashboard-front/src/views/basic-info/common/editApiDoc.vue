<template>
  <bk-dialog
    width="640"
    :is-show="modelValue"
    @update:is-show="emit('update:modelValue')"
    :title="t('编辑API文档')">
    <div class="doc-form">
      <bk-form ref="formRef" form-type="vertical" :model="docForm" :rules="rules">
        <bk-form-item
          :label="t('联系人类型')"
          property="type"
        >
          <bk-radio-group v-model="docForm.type">
            <bk-radio label="user">{{ t('用户') }}</bk-radio>
            <bk-radio label="service_account">{{ t('服务号') }}</bk-radio>
          </bk-radio-group>
        </bk-form-item>

        <bk-form-item
          :label="t('联系人')"
          property="contacts"
          required
          v-if="docForm.type === 'user'"
        >
          <MemberSelect v-model="docForm.contacts" :placeholder="t('请选择')" :has-delete-icon="true" />
          <div class="form-item-tip">
            <span>{{ t('文档页面上展示出来的文档咨询接口人') }}</span>
          </div>
        </bk-form-item>

        <bk-form-item
          :label="t('服务号名称')"
          property="service_account.name"
          required
          v-if="docForm.type === 'service_account'"
        >
          <bk-input
            v-model="docForm.service_account.name"
            :placeholder="t('请输入服务号名称，如BK助手')"
          />
        </bk-form-item>
        <bk-form-item
          :label="t('服务号链接')"
          property="service_account.link"
          required
          v-if="docForm.type === 'service_account'"
        >
          <bk-input
            v-model="docForm.service_account.link"
            :placeholder="t('如wxwork：//message？uin=84444455886')"
          />
        </bk-form-item>

        <bk-form-item
          :label="t('文档地址')"
          class="virtual-required"
        >
          <span class="link">{{ data?.docs_url || '--' }}</span>
        </bk-form-item>
      </bk-form>
    </div>
    <template #footer>
      <bk-popover
        width="280"
        placement="top"
        theme="light"
        trigger="click"
      >
        <bk-button>
          {{ t('预览') }}
        </bk-button>
        <template #content>
          <div class="preview-content">
            <div class="header li">
              <div class="title">{{ t('网关详情') }}</div>
              <div
                class="opt"
                v-bk-tooltips="{
                  content: docForm.type === 'user' ? docForm.contacts?.join(',') : t('联系服务号'),
                  theme: 'light',
                  placement: 'bottom' }">
                <i class="ag-doc-icon doc-qw f16 apigateway-icon icon-ag-qw"></i>
                {{ docForm.type === 'user' ? t('一键拉群') : docForm.service_account.name }}
              </div>
            </div>

            <div class="li">
              <div class="title">{{ t('网关描述') }}</div>
              <div class="value">{{ data?.description || '--' }}</div>
            </div>

            <div class="li">
              <div class="title">{{ t('网关负责人') }}</div>
              <div class="value">{{ data?.maintainers?.join(',') || '--' }}</div>
            </div>

            <div class="li">
              <div class="title">{{ t('网关访问地址') }}</div>
              <div class="value">{{ data?.api_domain || '--' }}</div>
            </div>
          </div>
        </template>
      </bk-popover>

      <bk-button theme="primary" @click="handleCommit" :loading="loading">
        {{ t('确定') }}
      </bk-button>
      <bk-button @click="handleCancel">
        {{ t('取消') }}
      </bk-button>
    </template>
  </bk-dialog>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { cloneDeep } from 'lodash';
import { Message } from 'bkui-vue';
import MemberSelect from '@/components/member-select';
import { editGateWays } from '@/http';

const { t } = useI18n();

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  data: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['update:modelValue', 'done']);

interface IForm {
  type: string;
  contacts: string[];
  service_account: {
    name: string;
    link: string;
  };
}

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

const formRef = ref(null);
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

    const payload: any = {
      ...props.data,
    };

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
    } else {
      payload.doc_maintainers = {
        type,
        contacts: [],
        service_account,
      };
    }

    await editGateWays(props.data.id, payload);

    emit('done');
    emit('update:modelValue', false);
    Message({
      message: t('更新成功'),
      theme: 'success',
      width: 'auto',
    });
  } catch (e) {} finally {
    loading.value = false;
  }
};

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      const { doc_maintainers } = props.data;
      docForm.value = cloneDeep(doc_maintainers);
    }
  },
);

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
      content: '*';
      color: #EA3636;
      position: absolute;
      top: 2px;
      left: 62px;
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
    font-size: 12px;
    color: #4D4F56;
    margin-bottom: 4px;
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
