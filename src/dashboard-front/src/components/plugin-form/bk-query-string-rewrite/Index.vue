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
  <BkForm :model="formData">
    <BkFormItem
      label="Add"
      property="add"
    >
      <KeyValuePairs
        ref="addRef"
        v-model="formData.add"
      />
    </BkFormItem>
    <BkFormItem
      label="Set"
      property="set"
    >
      <KeyValuePairs
        ref="setRef"
        v-model="formData.set"
      />
    </BkFormItem>
    <BkFormItem
      label="Remove"
      property="remove"
    >
      <KeysInput
        ref="removeRef"
        v-model="formData.remove"
      />
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import KeyValuePairs from './components/KeyValuePairs.vue';
import KeysInput from './components/KeysInput.vue';

interface KeyValuePair {
  key: string
  value: string | number
}

interface IFormData {
  add: KeyValuePair[]
  set: KeyValuePair[]
  remove: { key: string }[]
}

interface IRawData {
  add?: Record<string, string | number>
  set?: Record<string, string | number>
  remove?: string[]
}

interface IProps { data: IRawData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const addRef = useTemplateRef('addRef');
const setRef = useTemplateRef('setRef');
const removeRef = useTemplateRef('removeRef');

const getDefaultData = () => ({
  add: [],
  set: [],
  remove: [],
});

const formData = ref<IFormData>(getDefaultData());

watch(() => data, () => {
  if (data) {
    if (data.add) {
      formData.value.add = Object.entries(data.add).map(([key, value]) => ({
        key,
        value,
      }));
    }
    if (data.set) {
      formData.value.set = Object.entries(data.set).map(([key, value]) => ({
        key,
        value,
      }));
    }
    if (data.remove) {
      formData.value.remove = data.remove.map(key => ({ key }));
    }
  }
}, {
  immediate: true,
  deep: true,
});

defineExpose({
  getValue: async () => {
    await Promise.all([
      addRef.value!.validate(),
      setRef.value!.validate(),
      removeRef.value!.validate(),
    ]);
    const [add, set, remove] = [addRef.value!.getValue(), setRef.value!.getValue(), removeRef.value!.getValue()];
    // 判断是否全为空
    if (!Object.keys(add).length && !Object.keys(set).length && !remove.length) {
      Message({
        theme: 'error',
        message: t('请填写信息'),
      });
      throw new Error();
    }

    // 构造返回值
    const result: IRawData = {};
    if (Object.keys(add).length) {
      result.add = add;
    }
    if (Object.keys(set).length) {
      result.set = set;
    }
    if (remove.length) {
      result.remove = remove;
    }
    return result;
  },
});

</script>
