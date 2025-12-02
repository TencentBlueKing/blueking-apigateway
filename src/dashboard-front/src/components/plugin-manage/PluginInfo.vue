/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <div class="plugin-info">
    <main
      class="plugin-form-content"
      :class="{ 'pr-20px': showExample }"
    >
      <div
        v-if="!isAdd && isStage"
        class="info-alert mb-20px"
      >
        <BkAlert
          theme="warning"
          :title="t(editAlert)"
        />
      </div>
      <div class="info-header">
        <header class="choose-plugin">
          <div
            v-if="PLUGIN_ICONS.includes(curPluginInfo?.code)"
            class="cur-icon"
          >
            <svg class="icon svg-icon">
              <use
                :xlink:href="`#icon-ag-plugin-${curPluginInfo.code}`"
                fill="#3a84f6"
              />
            </svg>
          </div>
          <div
            v-else-if="PLUGIN_ICONS_MIN.includes(curPluginInfo?.code)"
            class="cur-icon"
          >
            <svg class="icon svg-icon small">
              <use
                :xlink:href="`#icon-ag-plugin-${curPluginInfo.code}`"
                fill="#3a84f6"
              />
            </svg>
          </div>
          <div
            v-else
            class="cur-icon"
          >
            {{ pluginCodeFirst(curPluginInfo?.code) }}
          </div>
          <div
            v-show="isAdd"
            @click="showChoosePlugin = true"
          >
            {{ t('切换插件') }}
          </div>
          <BkSelect
            v-show="showChoosePlugin"
            ref="pluginSelectRef"
            v-model="choosePlugin"
            :clearable="false"
            class="choose-plugin-select"
            @change="handleChoosePlugin"
            @blur="() => showChoosePlugin = false"
          >
            <BkOption
              v-for="item in pluginList"
              :id="item.code"
              :key="item.code"
              :name="item.name"
              :disabled="isBound(item)"
            />
          </BkSelect>
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
        <aside
          class="plugin-example-btn"
          @click="toggleShowExample"
        >
          {{ t('查看填写示例') }}
        </aside>
      </div>
      <div class="info-form-container mt-20px">
        <!-- <BkForm ref="formRef" class="info-form" :model="configFormData" :rules="rules" form-type="vertical">
          <BkFormItem :label="t('名称')" property="name" required>
          <BkInput v-model="configFormData.name" :placeholder="t('请输入')" />
          </BkFormItem>
          <BkLoading :loading="isPluginFormLoading">
          <BkFormItem class="mt-20px" v-if="infoNotes">
          <BkAlert theme="info" :title="t(infoNotes)"></BkAlert>
          </BkFormItem>
          </BkLoading>
          </BkForm> -->

        <BkAlert
          v-show="typeId === 1"
          theme="warning"
          :title="t('allow_origins 与 allow_origins_by_regex 不能同时为空')"
        />

        <!-- 免用户认证应用白名单策略 -->
        <div v-if="formStyle === 'raw'">
          <div class="white-list">
            <WhitelistTable
              ref="whitelist"
              :type="type"
              :yaml-str="editPlugin?.yaml || ''"
            />
          </div>
        </div>
        <template
          v-else-if="[
            'proxy-cache',
            'bk-user-restriction',
            'bk-request-body-limit',
            'bk-access-token-source',
            'redirect',
            'bk-mock',
            'response-rewrite',
            'fault-injection',
            'request-validation',
            'api-breaker',
          ].includes(choosePlugin)"
        >
          <Component
            :is="pluginFormCompMap[choosePlugin as keyof typeof pluginFormCompMap]"
            ref="formRef"
            :data="schemaFormData"
          />
        </template>
        <template v-else-if="isDynamicFormPlugin">
          <component
            :is="pluginFormCompMap[choosePlugin as keyof typeof pluginFormCompMap]"
            ref="formRef"
            v-model="schemaFormData"
            :route-mode="choosePlugin"
            :schema="formConfig.schema"
            :layout="formConfig.layout"
          />
        </template>
        <BkSchemaForm
          v-else
          ref="formRef"
          v-model="schemaFormData"
          class="mt-20px plugin-form"
          :schema="formConfig.schema"
          :layout="formConfig.layout"
          :rules="formConfig.rules"
        />
      </div>
      <div class="info-btn mt-20px">
        <div class="last-step">
          <BkPopConfirm
            v-if="isStage"
            :title="t('确认{optType}插件（{name}）到 {stage} 环境？',
                      {
                        optType: isAdd ? t('添加') : t('修改'),
                        name: curPluginInfo?.name,
                        stage: stageStore?.curStageData?.name
                      })"
            :content="t('插件配置变更后，将立即影响线上环境，请确认。')"
            trigger="click"
            @confirm="handleAdd"
          >
            <BkButton
              theme="primary"
              class="default-btn"
            >
              {{ t('确定') }}
            </BkButton>
          </BkPopConfirm>
          <BkButton
            v-else
            theme="primary"
            class="default-btn"
            @click="handleAdd"
          >
            {{ t('确定') }}
          </BkButton>
          <BkButton
            v-if="isAdd"
            class="prev-btn ml-8px"
            @click="handlePre"
          >
            {{ t('上一步') }}
          </BkButton>
          <BkButton
            class="default-btn ml-8px"
            @click="handleCancel"
          >
            {{ t('取消') }}
          </BkButton>
        </div>
      </div>
    </main>
    <!--  右侧插件使用示例  -->
    <aside
      v-if="showExample"
      class="plugin-example-content"
    >
      <header class="example-content-header">
        <span class="header-title">{{ t('插件配置示例') }}</span>
        <AgIcon
          class="close-btn"
          size="24"
          name="icon-close"
          @click="toggleShowExample"
        />
      </header>
      <main class="example-main">
        <pre
          v-dompurify-html="exampleHtml"
          class="example-pre"
        />
      </main>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { cloneDeep } from 'lodash-es';
import { creatPlugin, getPluginForm, updatePluginConfig } from '@/services/source/plugin-manage';
import { Message } from 'bkui-vue';
// @ts-expect-error missing module type
import createForm from '@blueking/bkui-form';
import { json2Yaml, yaml2Json } from '@/utils';
import WhitelistTable from './WhitelistTable.vue';
import { useStage } from '@/stores';
import { onClickOutside } from '@vueuse/core';
import {
  PLUGIN_ICONS,
  PLUGIN_ICONS_MIN,
} from '@/constants';
import ProxyCacheForm from '@/components/plugin-form/proxy-cache/Index.vue';
import BkUserRestriction from '@/components/plugin-form/bk-user-restriction/Index.vue';
import BkRequestBodyLimit from '@/components/plugin-form/bk-request-body-limit/Index.vue';
import BkAccessTokenSource from '@/components/plugin-form/bk-access-token-source/Index.vue';
import BkIpRestriction from '@/components/plugin-form/bk-ip-restriction/Index.vue';
import BkHeaderRewrite from '@/components/plugin-form/bk-header-rewrite/Index.vue';
import BkRateLimit from '@/components/plugin-form/bk-rate-limit/Index.vue';
import BkCors from '@/components/plugin-form/bk-cors/Index.vue';
import Redirect from '@/components/plugin-form/redirect/Index.vue';
import BkMock from '@/components/plugin-form/bk-mock/Index.vue';
import ResponseRewrite from '@/components/plugin-form/response-rewrite/Index.vue';
import FaultInjection from '@/components/plugin-form/fault-injection/Index.vue';
import RequestValidate from '@/components/plugin-form/request-validation/Index.vue';
import ApiBreaker from '@/components/plugin-form/api-breaker/Index.vue';

interface IProps {
  curPlugin: any
  scopeInfo: any
  editPlugin: any
  type: string
  pluginList?: any[]
  bindingPlugins?: any[]
}

// 右侧插件使用示例是否可见
const showExample = defineModel<boolean>('showExample', { default: false });

const {
  curPlugin,
  scopeInfo,
  editPlugin,
  type,
  pluginList = [],
  bindingPlugins = [],
} = defineProps<IProps>();

const emit = defineEmits<{
  'on-change': [type: string]
  'choose-plugin': [plugin: any]
}>();

interface IProps {
  curPlugin: any
  scopeInfo: any
  editPlugin: any
  type: string
  pluginList?: any[]
  bindingPlugins?: any[]
}

const stageStore = useStage();
const BkSchemaForm = createForm();

const { t } = useI18n();
const schemaFormData = ref({});
const formConfig = ref({
  schema: {},
  layout: {},
  rules: {},
});

const formRef = ref();
const whitelist = ref();
const curPluginInfo = ref<any>(curPlugin);
const choosePlugin = ref<string>(curPluginInfo.value?.code);
const showChoosePlugin = ref(false);
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
// 右侧插件使用示例内容
const exampleContent = ref('');
// 插件切换 select
const pluginSelectRef = ref<HTMLElement>();

const pluginFormCompMap = {
  'proxy-cache': ProxyCacheForm,
  'bk-user-restriction': BkUserRestriction,
  'bk-request-body-limit': BkRequestBodyLimit,
  'bk-access-token-source': BkAccessTokenSource,
  'redirect': Redirect,
  'bk-ip-restriction': BkIpRestriction,
  'bk-header-rewrite': BkHeaderRewrite,
  'bk-mock': BkMock,
  'response-rewrite': ResponseRewrite,
  'fault-injection': FaultInjection,
  'request-validation': RequestValidate,
  'api-breaker': ApiBreaker,
  'bk-rate-limit': BkRateLimit,
  'bk-cors': BkCors,
};

const isDynamicFormPlugin = computed(() => {
  return ['bk-cors', 'bk-ip-restriction', 'bk-header-rewrite', 'bk-rate-limit'].includes(choosePlugin.value);
});

const isBound = computed(() => {
  return function (obj: any) {
    return bindingPlugins?.some((item: { code: string }) => item.code === obj.code);
  };
});

// 把后端返回的带 \n 的文本块转换成换行标签，当做 html 渲染
const exampleHtml = computed(() => {
  return exampleContent.value.replace(/\\n/gm, '<br/>');
});

watch(
  () => curPlugin,
  (newVal) => {
    if (newVal) {
      curPluginInfo.value = newVal;
      choosePlugin.value = newVal.code;
      init();
    }
  },
);

const clearValidate = () => {
  formRef.value?.clearValidate?.();
};

// 上一页
const handlePre = () => {
  clearValidate();
  emit('on-change', 'pre');
};
// 确认
const handleAdd = async () => {
  const { scopeType, scopeId, apigwId } = scopeInfo;
  const { code } = curPlugin;

  const doSubmit = async (data: any) => {
    try {
      if (isAdd.value) {
        data.name = curPlugin?.name;
        data.type_id = typeId.value;
        await creatPlugin(apigwId, scopeType, scopeId, code, data);
        emit('on-change', 'addSuccess');
      }
      else {
        data.name = editPlugin?.name;
        data.type_id = editPlugin?.type_id;
        await updatePluginConfig(apigwId, scopeType, scopeId, code, editPlugin.id, data);
        emit('on-change', 'editSuccess');
      }
      Message({
        message: isAdd.value ? t('添加成功') : t('修改成功'),
        theme: 'success',
        width: 'auto',
      });
    }
    catch (error) {
      console.log('error', error);
    }
  };

  // 免用户认证应用白名单
  const data = {};
  try {
    if (formStyle.value === 'raw') {
      Object.assign(data, { yaml: whitelist.value?.sendPolicyData().data });
    }
    else if ([
      'proxy-cache',
      'bk-user-restriction',
      'bk-request-body-limit',
      'bk-access-token-source',
      'redirect',
      'bk-mock',
      'response-rewrite',
      'fault-injection',
      'request-validation',
      'api-breaker',
    ].includes(choosePlugin.value)) {
      const formValue = await formRef.value!.getValue();
      Object.assign(data, { yaml: json2Yaml(JSON.stringify(formValue)).data });
      schemaFormData.value = formValue;
    }
    else {
      const isValidate = await formRef.value?.validate();
      if (!isValidate) {
        return;
      }
      const formValue = await formRef.value!.getValue();
      Object.assign(data, { yaml: json2Yaml(JSON.stringify(formValue)).data });
      schemaFormData.value = formValue;
    }
  }
  catch (err) {
    const error = err as Error;
    Message({
      theme: 'error',
      message: error.message || t('表单校验失败'),
    });
    return;
  }

  if (isAdd.value) {
    Object.assign(data, schemaFormData.value);
  }
  await doSubmit(data);
};

// 取消
const handleCancel = () => {
  clearValidate();
  if (isAdd.value) {
    emit('on-change', 'addCancel');
  }
  emit('on-change', 'editCancel');
};

const getSchemaFormData = async (code: string) => {
  try {
    const { apigwId } = scopeInfo;
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
      const yamlData = yaml2Json(editPlugin?.yaml).data;
      schemaFormData.value = { ...(yamlData as object) };
    }
  }
  catch (error) {
    console.log('error', error);
  }
};

const handleChoosePlugin = () => {
  const plugin = pluginList?.filter((item: any) => item.code === choosePlugin.value)[0];
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
  showExample.value = !showExample.value;
};

const init = async () => {
  isStage.value = scopeInfo.scopeType === 'stage';
  isAdd.value = type === 'add';
  curPluginInfo.value = curPlugin;
  const { code } = curPlugin;
  getSchemaFormData(code);
};
init();

// 设置编辑插件配置数据回显
const setPluginInfo = (plugin) => {
  schemaFormData.value = cloneDeep(plugin?.config);
};

// 点击了插件 select 区域外且未 focus 到该组件时，隐藏整个 select
onClickOutside(pluginSelectRef, () => {
  if (pluginSelectRef.value?.isFocus === false) {
    showChoosePlugin.value = false;
  }
});

defineExpose({
  clearValidate,
  setPluginInfo,
});
</script>

<style lang="scss" scoped>
.plugin-info {
  display: flex;

  .plugin-form-content {
    flex-grow: 1;
  }

  .plugin-example-content {
    width: 400px;
    padding: 0 0 20px 20px;
    border-left: 1px solid #dcdee5;
    flex-shrink: 0;

    .example-content-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;

      .header-title {
        height: 24px;
        font-size: 16px;
        line-height: 24px;
        color: #313238;
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
        overflow-x: auto;
        font-family: inherit;
        font-size: 14px;
        line-height: 22px;
        color: #4D4F56;
        word-wrap: break-word;
        white-space: pre-wrap;
      }
    }
  }
}

.info-header {
  display: flex;
  padding: 12px 24px;
  background-color: #f5f7fa;
  border-radius: 2px;
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
      display: flex;
      width: 56px;
      height: 56px;
      font-size: 28px;
      font-weight: 700;
      line-height: 56px;
      color: #3a84f6;
      background: #EAEBF0;
      border-radius: 50%;
      justify-content: center;
      align-items: center;

      .svg-icon {
        width: 56px;
        height: 56px;

        &.small {
          width: 28px;
          height: 28px;
        }
      }
    }
  }

  .cur-text {
    flex-grow: 1;

    .cur-info {
      display: flex;
      margin-top: 12px;
      margin-bottom: 10px;
      align-items: center;

      .cur-name {
        margin-right: 24px;
        font-size: 16px;
        font-weight: 700;
        color: #313238;
      }

      .cur-binding-info {
        display: flex;
        font-size: 12px;
        color: #979ba5;
        align-items: center;

        li:not(:nth-last-child(1)) {
          margin-right: 32px;
        }

        .cur-version {
          font-weight: 700;
          color: #313238;
        }

        .empty {
          font-weight: 700;
          color: #3a84ff;
        }

        .bound {
          font-weight: 700;
          color: #3a84ff;
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
    font-size: 14px;
    color: #3A84FF;
    cursor: pointer;
    flex-shrink: 0;
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
}

.choose-plugin-select {
  position: absolute;
  top: 85px;
  left: 0;
  z-index: 1;
  width: 300px;

  :deep(.bk-input) {
    border: 1px solid #DCDEE5;

    .angle-up {
      color: #DCDEE5;
    }
  }
}
</style>
