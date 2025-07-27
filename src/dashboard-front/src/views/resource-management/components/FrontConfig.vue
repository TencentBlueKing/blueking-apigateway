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
        :input-search="false"
        :clearable="false"
        class="method"
        @change="clearValidate"
      >
        <BkOption
          v-for="item in HTTP_METHODS"
          :key="item.id"
          :value="item.id"
          :label="item.name"
        />
      </BkSelect>
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
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          class="w-70% max-w-700px"
          @input="clearValidate"
        />
        <BkCheckbox
          v-model="frontConfigData.match_subpath"
          class="ml-12px!"
        >
          {{ t('匹配所有子路径') }}
        </BkCheckbox>
      </div>
    </BkFormItem>
    <BkFormItem
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
// import mitt from '@/common/event-bus';
import { HTTP_METHODS } from '@/constants';

interface IProps {
  detail?: any
  isClone?: boolean
}

const { detail = {}, isClone = false } = defineProps<IProps>();

const { t } = useI18n();

const frontRef = ref();
const cloneTips = ref(t('请求方法+请求路径在网关下唯一，请至少调整其中一项'));
const frontConfigData = ref({
  path: '',
  method: 'GET',
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
        if (!value) return true;
        return value !== cloneData.value.method || frontConfigData.value.path !== cloneData.value.path;
      },
      message: cloneTips.value,
      trigger: 'blur',
    },
  ],
  path: [
    {
      validator: (value: string) => {
        console.log('value', value);
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
      validator: (value: string) => /^\/[\w{}/.-]*$/.test(value),
      message: t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名'),
      trigger: 'blur',
    },
  ],
});

// 错误表单项的 #id
const invalidFormElementIds = ref<string[]>([]);

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
  () => frontConfigData.value,
  // (val: any) => {
  () => {
    // mitt.emit('front-config', val);
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
