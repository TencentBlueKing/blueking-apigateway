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
  <div class="body-payload">
    <div class="table-header">
      <div class="body-type">
        <div class="body-type-item active">
          raw
        </div>
        <BkSelect
          v-model="rawType"
          class="raw-select"
          :clearable="false"
          :filterable="false"
        >
          <BkOption
            v-for="(item, index) in datasource"
            :id="item.value"
            :key="index"
            :name="item.label"
            disabled
          />
        </BkSelect>
      </div>
    </div>
    <div class="raw-content">
      <AgCodeEditor
        ref="resourceEditorRef"
        v-model="editorText"
        theme="Visual Studio"
        language="json"
        :minimap="false"
        show-format
        show-copy
        show-full-screen
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgCodeEditor from '@/components/base/ag-code-editor/Index.vue';

interface IProps {
  rawPayload?: any
}

const { rawPayload = {} } = defineProps<IProps>();

const rawType = ref<string>('JSON');
const datasource = ref([
  {
    value: 'JSON',
    label: 'JSON',
  },
  {
    value: 'XML',
    label: 'XML',
  },
  {
    value: 'HTML',
    label: 'HTML',
  },
  {
    value: 'TEXT',
    label: 'TEXT',
  },
]);
const resourceEditorRef = useTemplateRef<InstanceType<typeof AgCodeEditor>>('resourceEditorRef');
const editorText = ref(JSON.stringify(rawPayload, null, 2));

// Body 固定为 raw 模式，无需表格校验
const validate = async () => true;

const getData = () => {
  return {
    type: 'raw',
    raw: editorText.value,
    rawType: rawType.value,
  };
};

watch(
  () => rawPayload,
  (value: any) => {
    editorText.value = JSON.stringify(value, null, 2);
    resourceEditorRef.value?.setValue(editorText.value);
  },
  { deep: true },
);

defineExpose({
  validate,
  getData,
});
</script>

<style lang="scss" scoped>
.body-payload {
  height: 100%;
}

.table-header {
  display: flex;
  width: 100%;
  margin-bottom: 8px;
  align-items: center;
  justify-content: space-between;

  .body-type {
    display: flex;
    align-items: center;
    padding-bottom: 10px;

    .body-type-item {
      padding: 4px 8px;
      font-size: 12px;
      color: #63656E;
      cursor: pointer;
      background: #F0F1F5;
      border-radius: 11px;

      &:not(:nth-last-child(1)) {
        margin-right: 8px;
      }

      &.active {
        position: relative;
        color: #FFF;
        background: #3A84FF;
      }
    }
  }
}

.raw-select {
  width: 120px;
}

.raw-content {
  width: 100%;
  height: calc(100% - 50px);
  background: #FFF;
  border: 1px solid #DCDEE5;
  border-radius: 2px;
}
</style>
