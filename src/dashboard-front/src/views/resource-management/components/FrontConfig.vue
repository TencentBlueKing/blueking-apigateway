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
  <BkForm
    ref="frontRef"
    :model="frontConfigData"
    :rules="rules"
    class="front-config-container"
    @validate="setInvalidPropId"
  >
    <BkFormItem
      id="front-config-method"
      :label="t('请求方法')"
      property="method"
      required
    >
      <BkSelect
        v-model="frontConfigData.method"
        class="method"
        :input-search="false"
        :clearable="false"
        :disabled="isModelProxy"
        @change="clearValidate"
      >
        <BkOption
          v-for="item in HTTP_METHODS"
          :key="item.id"
          :value="item.id"
          :label="item.name"
        />
      </BkSelect>
      <div
        v-if="isModelProxy"
        class="text-12px color-#979ba5"
      >
        {{ t('模型代理API请求方法固定为POST，不可更改') }}
      </div>
    </BkFormItem>
    <BkFormItem
      :label="t('请求路径')"
      property="path"
      required
    >
      <div class="flex items-center">
        <BkInput
          id="front-config-path"
          v-model="frontConfigData.path"
          :placeholder="renderPathPlaceholder"
          clearable
          class="w-70% max-w-700px"
          @input="clearValidate"
        />
        <BkCheckbox
          v-if="!isModelProxy"
          v-model="frontConfigData.match_subpath"
          class="ml-12px!"
        >
          {{ t('匹配所有子路径') }}
        </BkCheckbox>
      </div>
      <div class="text-12px color-#979ba5">
        {{ renderPathDesc }}
      </div>
    </BkFormItem>
    <BkFormItem
      v-if="!isModelProxy"
      :label="t('启用 WebSocket')"
      property="enable_websocket"
      required
    >
      <BkSwitcher
        v-model="frontConfigData.enable_websocket"
        theme="primary"
        size="small"
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { useRouteQuery } from '@vueuse/router';
import { HTTP_METHODS } from '@/constants';

interface IProps {
  detail?: any
  isClone?: boolean
}

const { detail = {}, isClone = false } = defineProps<IProps>();

const emit = defineEmits<{ change: [data: typeof frontConfigData.value] }>();

const { t } = useI18n();
const queryKind = useRouteQuery('kind');

const standardPathPlaceholder = t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名');

// 是否是模型代理 API
const isModelProxy = computed(() => queryKind.value === 'ai');

const frontRef = ref();
const cloneTips = ref(t('请求方法+请求路径在网关下唯一，请至少调整其中一项'));
const frontConfigData = ref({
  path: '',
  method: isModelProxy.value ? 'POST' : 'GET',
  match_subpath: false,
  enable_websocket: false,
});

const cloneData = ref({
  path: '',
  method: '',
});

const rules = ref<any>({
  method: [
    {
      validator: (value: string) => {
        if (!value || isModelProxy.value) return true;
        return value !== cloneData.value.method || frontConfigData.value.path !== cloneData.value.path;
      },
      message: cloneTips.value,
      trigger: 'blur',
    },
  ],
  path: [
    {
      validator: (value: string) => {
        if (!value) return true;
        return value !== cloneData.value.path || frontConfigData.value.method !== cloneData.value.method;
      },
      message: cloneTips.value,
      trigger: 'blur',
    },
    {
      required: true,
      message: t('请求路径不能为空'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => /^\/[\w{}/.!-]*$/.test(value),
      message: standardPathPlaceholder,
      trigger: 'blur',
    },
  ],
});

// 错误表单项的 #id
const invalidFormElementIds = ref<string[]>([]);

const renderPathPlaceholder = computed(() => isModelProxy.value
  ? t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名，如/ai/chat/completions')
  : standardPathPlaceholder,
);

const renderPathDesc = computed(() => isModelProxy.value
  ? t('网关对外暴露的调用路径：模型代理API不支持「匹配所有子路径」与WebSocket')
  : t('资源请求路径支持路径变量，包含在{\'{}\'}中，如：/users/{id}/', { id: '{id}' }),
);

watch(
  () => detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { path, method, match_subpath, enable_websocket } = val;
      frontConfigData.value = {
        path,
        method,
        match_subpath,
        enable_websocket,
      };
      if (isClone) {
        cloneData.value = {
          path,
          method,
        };
        setTimeout(() => {
          validate();
        }, 500);
      }
    }
  },
  { immediate: true },
);

watch(
  frontConfigData,
  () => {
    // mitt.emit('front-config', val);
    emit('change', frontConfigData.value);
  },
  { deep: true },
);

// 监听表单校验时间，收集 #id
const setInvalidPropId = (property: string, result: boolean) => {
  if (!result) {
    invalidFormElementIds.value.push(`front-config-${property}`);
  }
};

const validate = async () => {
  invalidFormElementIds.value = [];
  await frontRef.value?.validate();
};

// 清除表单验证
const clearValidate = () => {
  frontRef.value?.clearValidate();
};

defineExpose({
  frontConfigData,
  invalidFormElementIds,
  validate,
});
</script>

<style lang="scss" scoped>
.front-config-container {

  .method {
    max-width: 700px;
  }

  .public-switch {
    height: 32px;
  }

  .w700 {
    width: 70%;
    max-width: 700px;
  }

  :deep(.bk-checkbox-label) {
    white-space: nowrap;
  }
}
</style>
