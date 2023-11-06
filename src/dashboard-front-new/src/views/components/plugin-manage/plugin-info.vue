<template>
  <div class="plugin-info">
    <div class="info-alert mb20" v-if="!isAdd && isStage">
      <bk-alert theme="warning" :title="t(editAlert)"></bk-alert>
    </div>
    <div class="info-header">
      <span class="cur-icon">{{ pluginCodeFirst(curPluginInfo.code) }}</span>
      <div class="cur-text">
        <p class="cur-name">{{ curPluginInfo.name }}</p>
        <ul class="cur-binding-info">
          <li>
            {{ t('当前版本：') }}
            <span class="cur-version">{{ t('1.0.0') }}</span>
          </li>
          <li>
            {{ t('已绑定的资源：') }}
            <span :class="[curPluginInfo.related_scope_count.resource === 0 ? 'empty' : 'bound',]">
              {{ curPluginInfo.related_scope_count.resource }}
            </span>
          </li>
          <li>
            {{ t('已绑定的环境：') }}
            <span :class="[curPluginInfo.related_scope_count.stage === 0 ? 'empty' : 'bound',]">
              {{ curPluginInfo.related_scope_count.stage }}
            </span>
          </li>
        </ul>
      </div>
    </div>
    <div class="info-form-container mt20">
      <bk-form ref="formRef" class="info-form" :model="configFormData" :rules="rules" form-type="vertical">
        <bk-form-item :label="t('名称')" property="name" required>
          <bk-input v-model="configFormData.name" :placeholder="t('请输入')" />
        </bk-form-item>
        <bk-loading :loading="isPluginFormLoading">
          <bk-form-item class="mt20" v-if="infoNotes">
            <bk-alert theme="info" :title="t(infoNotes)"></bk-alert>
          </bk-form-item>
        </bk-loading>
      </bk-form>
    </div>
    <div class="info-btn">
      <div class="last-step">
        <bk-button theme="primary" @click="handleAdd">{{ t('确定') }}</bk-button>
        <bk-button @click="handlePre" class="ml8" v-if="isAdd">{{ t('上一步') }}</bk-button>
        <bk-button @click="handleCancel" class="ml8">{{ t('取消') }}</bk-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, defineEmits } from 'vue';
import { useI18n } from 'vue-i18n';
import { getPluginForm, creatPlugin, updatePluginConfig } from '@/http';
import { Message } from 'bkui-vue';

const { t } = useI18n();
const emit = defineEmits(['on-change']);

const props = defineProps({
  curPlugin: {
    type: Object,
  },
  scopeInfo: {
    type: Object,
  },
  editPlugin: {
    type: Object,
  },
  type: {
    type: String,
  },
});
// 添加插件interface
interface IPluginForm {
  name: string
  yaml: string
  type_id: number
}
const formRef = ref(null);
const curPluginInfo = ref<any>({});
const isPluginFormLoading = ref(false);
const infoNotes = ref('');
const isAdd = ref(false);
const isStage = ref(false);
const editAlert = ref(t('修改插件配置将会直接影响线上环境，请谨慎操作'));
const configFormData: IPluginForm = reactive({
  name: '',
  yaml: '',
  type_id: -1,
});
const rules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
};
const pluginCodeFirst = computed(() => (code: string) => {
  console.log(code);
  return code.charAt(3).toUpperCase();
});

// 上一页
const handlePre = () => {
  emit('on-change', 'pre');
};
// 确认添加
const handleAdd = async () => {
  const { scopeInfo: { scopeType, scopeId, apigwId } } = props;
  const { curPlugin: { code, id } } = props;
  configFormData.type_id = id;
  console.log(configFormData);
  await formRef.value?.validate();
  try {
    if (isAdd.value) {
      await creatPlugin(apigwId, scopeType, scopeId, code, configFormData);
      emit('on-change', 'addSuccess');
    } else {
      await updatePluginConfig(apigwId, scopeType, scopeId, code, props.editPlugin.id, configFormData);
      emit('on-change', 'editSuccess');
    }
    Message({
      message: isAdd.value ? t('添加成功') : t('修改成功'),
      theme: 'success',
    });
  } catch (error) {
    console.log('error', error);
  }
};
// 取消添加
const handleCancel = () => {
  if (isAdd.value) {
    emit('on-change', 'addCancel');
  }
  emit('on-change', 'editCancel');
};
const init = async () => {
  isStage.value = props.scopeInfo.scopeType === 'stage';
  console.log(isStage.value);

  console.log(props.editPlugin);
  isAdd.value = props.type === 'add';
  if (!isAdd.value) {
    configFormData.name = props.editPlugin.name;
  }
  curPluginInfo.value = props.curPlugin;
  configFormData.type_id = props.curPlugin.id;
  const { scopeInfo: { apigwId } } = props;
  const { curPlugin: { code } } = props;
  try {
    isPluginFormLoading.value = true;
    const res = await getPluginForm(apigwId, code);
    isPluginFormLoading.value = false;
    infoNotes.value = res.notes;
    console.log(res);
  } catch (error) {
    console.log('error', error);
  } finally {

  }
  switch (props.curPlugin.id) {
    case 1:
      configFormData.yaml = 'allow_origins: https://example.com:8081\nallow_origins_by_regex: []\nallow_methods: \' ** \'\nallow_headers: \' ** \'\nexpose_headers: \'\'\nmax_age: 86400';
      break;
    case 2:
      configFormData.yaml = 'set:\n- key: appenv\n  value: ieod\nremove: []\n';
      break;
    case 3:
      configFormData.yaml = 'whitelist: |-\n  1.1.1.1\n  2.2.2.2';
      break;
    case 4:
      configFormData.yaml = 'rates:\n  default:\n    period: 1\n    tokens: 100\n  specials: []\n';
      break;
    default:
      break;
  }
};
init();
</script>

<style lang="scss" scoped>
.info-header {
  background-color: #f5f7fb;
  padding: 15px 20px;
  display: flex;

  .cur-icon {
    display: inline-block;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-color: #eff1f5;
    color: #3a84f6;
    text-align: center;
    line-height: 60px;
    font-weight: 700;
    font-size: 30px;
    margin-right: 18px;
  }

  .cur-name {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 5px;
    margin-top: 10px;
  }

  .cur-binding-info {
    display: flex;
    width: 370px;
    justify-content: space-between;
    color: #b9bac1;

    .cur-version {
      color: #333539;
      font-weight: 700;
    }

    .empty {
      color: #646569;
      font-weight: 700;
    }

    .bound {
      color: #4b8ceb;
      font-weight: 700;
    }
  }
}
</style>
