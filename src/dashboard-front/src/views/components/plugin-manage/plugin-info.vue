<template>
  <div class="plugin-info">
    <main class="plugin-form-content" :class="{ 'pr20': isExampleVisible }">
      <div class="info-alert mb20" v-if="!isAdd && isStage">
        <bk-alert theme="warning" :title="t(editAlert)"></bk-alert>
      </div>
      <div class="info-header">
        <header class="choose-plugin">
          <div v-if="pluginIconList.includes(curPluginInfo?.code)" class="cur-icon">
            <i :class="`apigateway-icon icon-ag-plugin-${curPluginInfo?.code}`" class="f48"></i>
          </div>
          <div v-else class="cur-icon">{{ pluginCodeFirst(curPluginInfo?.code) }}</div>
          <div v-show="isAdd" @click="showChoosePlugin = true">{{ t('切换插件') }}</div>
          <bk-select
            v-show="showChoosePlugin"
            v-model="choosePlugin"
            :clearable="false"
            ref="pluginSelectRef"
            class="choose-plugin-select"
            @change="handleChoosePlugin"
            @blur="() => showChoosePlugin = false"
          >
            <bk-option
              v-for="item in pluginList"
              :id="item.code"
              :key="item.code"
              :name="item.name"
              :disabled="isBound(item)"
            />
          </bk-select>
        </header>
        <main class="cur-text">
          <div class="cur-info">
            <span class="cur-name">{{ curPluginInfo?.name }}</span>
            <ul class="cur-binding-info">
              <li>
                {{ t('当前版本：') }}
                <span class="cur-version">{{ t('1.0.0') }}</span>
              </li>
              <li>
                {{ t('已绑定的资源：') }}
                <span :class="[curPluginInfo?.related_scope_count?.resource === 0 ? 'empty' : 'bound',]">
                  {{ curPluginInfo?.related_scope_count?.resource }}
                </span>
              </li>
              <li>
                {{ t('已绑定的环境：') }}
                <span :class="[curPluginInfo?.related_scope_count?.stage === 0 ? 'empty' : 'bound',]">
                  {{ curPluginInfo?.related_scope_count?.stage }}
                </span>
              </li>
            </ul>
          </div>
          <div class="cur-describe">
            {{ curPluginInfo?.notes || infoNotes }}
          </div>
        </main>
        <aside class="plugin-example-btn" @click="toggleShowExample">{{ t('查看填写示例') }}</aside>
      </div>
      <div class="info-form-container mt20">
        <!-- <bk-form ref="formRef" class="info-form" :model="configFormData" :rules="rules" form-type="vertical">
          <bk-form-item :label="t('名称')" property="name" required>
            <bk-input v-model="configFormData.name" :placeholder="t('请输入')" />
          </bk-form-item>
          <bk-loading :loading="isPluginFormLoading">
            <bk-form-item class="mt20" v-if="infoNotes">
              <bk-alert theme="info" :title="t(infoNotes)"></bk-alert>
            </bk-form-item>
          </bk-loading>
        </bk-form> -->

        <bk-alert
          theme="warning"
          :title="t('allow_origins 与 allow_origins_by_regex 不能同时为空')"
          v-show="typeId === 1"
        />

        <!-- 免用户认证应用白名单策略 -->
        <div v-if="formStyle === 'raw'">
          <div class="white-list">
            <whitelist-table
              ref="whitelist"
              :type="type"
              :yaml-str="editPlugin?.yaml || ''"
            >
            </whitelist-table>
          </div>
        </div>
        <BkSchemaForm
          v-else
          class="mt20 plugin-form"
          v-model="schemaFormData"
          :schema="formConfig.schema"
          :layout="formConfig.layout"
          :rules="formConfig.rules"
          ref="formRef">
        </BkSchemaForm>
      </div>
      <div class="info-btn mt20">
        <div class="last-step">
          <bk-pop-confirm
            :title="t('确认{optType}插件（{name}）到 {stage} 环境？',
                      { optType: isAdd ? t('添加') : t('修改'),
                        name: curPluginInfo?.name,
                        stage: stageStore?.curStageData?.name })"
            :content="t('插件配置变更后，将立即影响线上环境，请确认。')"
            trigger="click"
            @confirm="handleAdd"
            v-if="isStage"
          >
            <bk-button theme="primary" class="default-btn">{{ t('确定') }}</bk-button>
          </bk-pop-confirm>
          <bk-button v-else @click="handleAdd" theme="primary" class="default-btn">{{ t('确定') }}</bk-button>
          <bk-button @click="handlePre" class="prev-btn ml8" v-if="isAdd">{{ t('上一步') }}</bk-button>
          <bk-button @click="handleCancel" class="default-btn ml8">{{ t('取消') }}</bk-button>
        </div>
      </div>
    </main>
    <!--  右侧插件使用示例  -->
    <aside v-if="isExampleVisible" class="plugin-example-content">
      <header class="example-content-header">
        <span class="header-title">{{ t('插件配置示例') }}</span>
        <i
          class="close-btn apigateway-icon icon-ag-icon-close f24"
          @click="toggleShowExample"
        ></i>
      </header>
      <main class="example-main">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <pre class="example-pre" v-dompurify-html="exampleHtml"></pre>
      </main>
    </aside>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  onBeforeUnmount,
  ref,
  toRefs,
} from 'vue';
import { useI18n } from 'vue-i18n';
import { getPluginForm, creatPlugin, updatePluginConfig } from '@/http';
import { Message } from 'bkui-vue';
// @ts-ignore
import createForm from '@blueking/bkui-form';
import { json2yaml, yaml2json } from '@/common/util';
import whitelistTable from './whitelist-table.vue';
import { useStage } from '@/store';
import { onClickOutside } from '@vueuse/core';
import pluginIconList from '@/common/plugin-icon-list';

const stageStore = useStage();
const BkSchemaForm = createForm();

const { t } = useI18n();
const emit = defineEmits(['on-change', 'choose-plugin', 'show-example']);

const schemaFormData = ref({});
const formConfig = ref({
  schema: {},
  layout: {},
  rules: {},
});

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
  pluginList: {
    type: Array<any>,
    default: () => [],
  },
  bindingPlugins: {
    type: Array<any>,
    default: () => [],
  },
});

const { curPlugin } = toRefs(props);
const formRef = ref(null);
const whitelist = ref(null);
const curPluginInfo = ref<any>(curPlugin);
const choosePlugin = ref<string>(curPluginInfo.value?.code);
const showChoosePlugin = ref<boolean>(false);
const isPluginFormLoading = ref(false);
const infoNotes = ref('');
const isAdd = ref(false);
const isStage = ref(false);
const editAlert = ref(t('修改插件配置将会直接影响线上环境，请谨慎操作'));
const pluginCodeFirst = computed(() => {
  return function (code: string) {
    return code?.charAt(3)?.toUpperCase();
  };
});
const typeId = ref<number>();
const formStyle = ref<string>();
// 右侧插件使用示例是否可见
const isExampleVisible = ref(false);
// 右侧插件使用示例内容
const exampleContent = ref('');
// 插件切换 select
const pluginSelectRef = ref<HTMLElement | null>(null);

const isBound = computed(() => {
  return function (obj: any) {
    return props?.bindingPlugins?.some((item: { code: string; }) => item.code === obj.code);
  };
});

// 把后端返回的带 \n 的文本块转换成换行标签，当做 html 渲染
const exampleHtml = computed(() => {
  return exampleContent.value.replace(/\\n/gm, '<br/>');
});

// 上一页
const handlePre = () => {
  emit('on-change', 'pre');
};
// 确认
const handleAdd = async () => {
  const { scopeInfo: { scopeType, scopeId, apigwId } } = props;
  const { curPlugin: { code } } = props;

  const doSubmit = async (data: any) => {
    try {
      if (isAdd.value) {
        data.name = props.curPlugin?.name;
        data.type_id = typeId.value;
        await creatPlugin(apigwId, scopeType, scopeId, code, data);
        emit('on-change', 'addSuccess');
      } else {
        data.name = props.editPlugin?.name;
        data.type_id = props.editPlugin?.type_id;
        await updatePluginConfig(apigwId, scopeType, scopeId, code, props.editPlugin.id, data);
        emit('on-change', 'editSuccess');
      }
      Message({
        message: isAdd.value ? t('添加成功') : t('修改成功'),
        theme: 'success',
        width: 'auto',
      });
    } catch (error) {
      console.log('error', error);
    }
  };

  // 免用户认证应用白名单
  if (formStyle.value === 'raw') {
    const data: any = { ...schemaFormData.value };
    const yamlData = whitelist.value?.sendPolicyData();
    data.yaml = yamlData.data;
    await doSubmit(data);
  } else {
    formRef.value?.validate().then(async () => {
      const data: any = { ...schemaFormData.value };
      data.yaml = json2yaml(JSON.stringify(schemaFormData.value)).data;
      await doSubmit(data);
    })
      .catch((e: any) => {
        console.error(e);
      });
  }
};

// 取消
const handleCancel = () => {
  if (isAdd.value) {
    emit('on-change', 'addCancel');
  }
  emit('on-change', 'editCancel');
};

const getSchemaFormData = async (code: string) => {
  try {
    const { scopeInfo: { apigwId } } = props;

    isPluginFormLoading.value = true;
    const res = await getPluginForm(apigwId, code);
    // const res = {
    //   id: 7,
    //   language: '',
    //   notes: '默认频率限制，表示单个应用的默认频率限制；特殊应用频率限制，对指定应用设置单独的频率限制。频率控制插件，绑定环境时，表示应用对环境下所有资源的总频率限制；绑定资源时，表示应用对单个资源的频率限制',
    //   style: 'dynamic',
    //   default_value: '',
    //   config: {
    //     schema: {
    //       title: '频率控制',
    //       type: 'object',
    //       properties: {
    //         rates: {
    //           type: 'object',
    //           properties: {
    //             default: {
    //               type: 'object',
    //               title: '默认频率限制',
    //               'ui:group': {
    //                 type: 'card',
    //                 showTitle: true,
    //                 style: {
    //                   background: '#F5F7FA',
    //                   padding: '10px 20px 10px 30px',
    //                 },
    //               },
    //               required: [
    //                 'tokens',
    //                 'period',
    //               ],
    //               properties: {
    //                 tokens: {
    //                   type: 'integer',
    //                   title: '次数',
    //                   default: 100,
    //                   'ui:rules': [
    //                     'required',
    //                   ],
    //                   'ui:component': {
    //                     name: 'bfInput',
    //                     min: 1,
    //                   },
    //                   'ui:props': {
    //                     labelWidth: 100,
    //                   },
    //                 },
    //                 period: {
    //                   type: 'integer',
    //                   title: '时间范围',
    //                   default: 1,
    //                   'ui:rules': [
    //                     'required',
    //                   ],
    //                   'ui:component': {
    //                     name: 'select',
    //                     datasource: [
    //                       {
    //                         label: '秒',
    //                         value: 1,
    //                       },
    //                       {
    //                         label: '分',
    //                         value: 60,
    //                       },
    //                       {
    //                         label: '时',
    //                         value: 3600,
    //                       },
    //                       {
    //                         label: '天',
    //                         value: 86400,
    //                       },
    //                     ],
    //                     clearable: false,
    //                   },
    //                   'ui:props': {
    //                     labelWidth: 100,
    //                   },
    //                 },
    //               },
    //             },
    //             specials: {
    //               type: 'array',
    //               title: '特殊应用频率限制',
    //               'ui:group': {
    //                 type: 'card',
    //                 showTitle: true,
    //                 style: {
    //                   background: '#F5F7FA',
    //                   padding: '10px 20px 20px 20px',
    //                 },
    //               },
    //               items: {
    //                 type: 'object',
    //                 required: [
    //                   'tokens',
    //                   'period',
    //                   'bk_app_code',
    //                 ],
    //                 'ui:group': {
    //                   style: {
    //                     background: '#FFF',
    //                     padding: '10px 10px 10px 10px',
    //                   },
    //                 },
    //                 properties: {
    //                   tokens: {
    //                     type: 'integer',
    //                     title: '次数',
    //                     default: 1,
    //                     'ui:rules': [
    //                       'required',
    //                     ],
    //                     'ui:component': {
    //                       name: 'bfInput',
    //                       min: 1,
    //                     },
    //                     'ui:props': {
    //                       labelWidth: 100,
    //                     },
    //                   },
    //                   period: {
    //                     type: 'integer',
    //                     title: '时间范围',
    //                     default: 1,
    //                     'ui:rules': [
    //                       'required',
    //                     ],
    //                     'ui:component': {
    //                       name: 'select',
    //                       datasource: [
    //                         {
    //                           label: '秒',
    //                           value: 1,
    //                         },
    //                         {
    //                           label: '分',
    //                           value: 60,
    //                         },
    //                         {
    //                           label: '时',
    //                           value: 3600,
    //                         },
    //                         {
    //                           label: '天',
    //                           value: 86400,
    //                         },
    //                       ],
    //                       clearable: false,
    //                     },
    //                     'ui:props': {
    //                       labelWidth: 100,
    //                     },
    //                   },
    //                   bk_app_code: {
    //                     type: 'string',
    //                     title: '蓝鲸应用ID',
    //                     pattern: '^[a-z0-9][a-z0-9_-]{0,31}$',
    //                     'ui:rules': [
    //                       'required',
    //                     ],
    //                   },
    //                 },
    //               },
    //             },
    //           },
    //         },
    //       },
    //     },
    //     layout: [
    //       [
    //         {
    //           prop: 'rates',
    //           group: [
    //             [
    //               {
    //                 prop: 'default',
    //                 container: {
    //                   'grid-template-columns': '250px 200px',
    //                 },
    //                 group: [
    //                   [
    //                     'tokens',
    //                     'period',
    //                   ],
    //                 ],
    //               },
    //             ],
    //             [
    //               {
    //                 prop: 'specials',
    //                 container: {
    //                   'grid-template-columns': '250px 200px 250px',
    //                 },
    //                 group: [
    //                   [
    //                     'tokens',
    //                     'period',
    //                     'bk_app_code',
    //                   ],
    //                 ],
    //               },
    //             ],
    //           ],
    //         },
    //       ],
    //     ],
    //     formData: {},
    //     rules: {},
    //   },
    //   type_id: 4,
    //   type_code: 'bk-rate-limit',
    //   type_name: '频率控制',
    // };

    // 当使用 select 组件切换到 ip 访问保护插件时，schemaFormData 没有被正确地设置
    // 需要手动重置 schemaFormData
    if (code === 'bk-ip-restriction') {
      schemaFormData.value = { whitelist: '' };
    }

    isPluginFormLoading.value = false;
    infoNotes.value = res.notes;
    formConfig.value = res.config;
    typeId.value = res.type_id;
    formStyle.value = res.style;
    exampleContent.value = res.example || '';

    if (!isAdd.value) {
      const yamlData = yaml2json(props.editPlugin.yaml).data;
      schemaFormData.value = { ...(yamlData as {}) };
    }
  } catch (error) {
    console.log('error', error);
  }
};

const handleChoosePlugin = () => {
  const plugin = props?.pluginList?.filter((item: any) => item.code === choosePlugin.value)[0];
  if (plugin) {
    curPluginInfo.value = plugin;
    getSchemaFormData(choosePlugin.value);
    emit('choose-plugin', plugin);
  }
};

// 切换使用示例可见状态
// 初次渲染若内容为空就去请求一次内容
const toggleShowExample = async () => {
  if (!exampleContent.value) {
    await getSchemaFormData(choosePlugin.value);
  }
  isExampleVisible.value = !isExampleVisible.value;
  emit('show-example', { isVisible: isExampleVisible.value });
};

const init = async () => {
  isStage.value = props.scopeInfo.scopeType === 'stage';
  isAdd.value = props.type === 'add';
  curPluginInfo.value = props.curPlugin;
  const { curPlugin: { code } } = props;
  getSchemaFormData(code);
};
init();

// 点击了插件 select 区域外且未 focus 到该组件时，隐藏整个 select
onClickOutside(pluginSelectRef, () => {
  if (pluginSelectRef.value?.isFocus === false) {
    showChoosePlugin.value = false;
  }
});

// 离开时重置使用示例可见状态恢复父组件的宽度
onBeforeUnmount(() => {
  emit('show-example', { isVisible: false });
});
</script>

<style lang="scss" scoped>
.plugin-info {
  display: flex;

  .plugin-form-content {
    flex-grow: 1;
  }

  .plugin-example-content {
    flex-shrink: 0;
    padding: 0 0 20px 20px;
    width: 400px;
    border-left: 1px solid #dcdee5;

    .example-content-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;

      .header-title {
        height: 24px;
        font-size: 16px;
        color: #313238;
        line-height: 24px;
      }

      .close-btn {
        color: #979BA5;
        cursor: pointer;

        &:hover {
          color: #63656e;
        }
      }
    }

    .example-main {

      .example-pre {
        line-height: 22px;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-family: inherit;
        color: #4D4F56;
      }
    }
  }
}

.info-header {
  background-color: #f5f7fa;;
  border-radius: 2px;
  padding: 12px 24px;
  display: flex;
  align-items: flex-start;
  gap: 24px;

  .choose-plugin {
    flex-shrink: 0;
    position: relative;
    display: flex;
    flex-direction: column;
    align-content: center;
    gap: 4px;
    font-size: 14px;
    color: #3A84FF;
    cursor: pointer;

    .cur-icon {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #EAEBF0;
      color: #3a84f6;
      text-align: center;
      line-height: 56px;
      font-weight: 700;
      font-size: 28px;
    }
  }

  .cur-text {
    flex-grow: 1;

    .cur-info {
      margin-top: 12px;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      .cur-name {
        font-size: 16px;
        font-weight: 700;
        color: #313238;
        margin-right: 24px;
      }
      .cur-binding-info {
        display: flex;
        align-items: center;
        color: #979ba5;
        font-size: 12px;
        li:not(:nth-last-child(1)) {
          margin-right: 32px;
        }
        .cur-version {
          color: #313238;
          font-weight: 700;
        }

        .empty {
          color: #3a84ff;
          font-weight: 700;
        }

        .bound {
          color: #3a84ff;
          font-weight: 700;
        }
      }
    }
    .cur-describe {
      font-size: 12px;
      color: #63656E;
    }
  }

  .plugin-example-btn {
    margin-top: 16px;
    flex-shrink: 0;
    color: #3A84FF;
    cursor: pointer;
  }
}
.plugin-form {
  :deep(.bk-schema-form-group-delete) {
    top: 18px !important;
  }
  :deep(.bk-switcher.is-checked) {
    background: #3a84ff;
  }
}

.last-step {
  font-size: 0;
  .default-btn {
    min-width: 88px;
  }
  .prev-btn {
    min-width: 74px;
  }
  .ml8 {
    margin-left: 8px;
  }
}

.choose-plugin-select {
  position: absolute;
  left: 0;
  top: 85px;
  width: 300px;
  z-index: 1;

  :deep(.bk-input) {
    border: 1px solid #DCDEE5;
    .angle-up {
      color: #DCDEE5;;
    }
  }
}
</style>
