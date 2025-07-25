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
  <div class="tmpl-example-sideslider-wrapper">
    <BkSideslider
      v-model:is-show="renderShow"
      quick-close
      :title="t('模板示例')"
      width="660"
      ext-cls="stage-sideslider-cls"
      @hidden="handleHidden"
    >
      <div class="tmpl-example-monaco-editor">
        <editor-monaco
          v-model="editorText"
          read-only
        />
      </div>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import editorMonaco from '@/components/ag-editor/Index.vue';
import { RESOURCE_IMPORT_EXAMPLE } from '@/constants';

interface IProps { isShow?: boolean }

const { isShow = false } = defineProps<IProps>();

const emits = defineEmits<{ 'on-hidden': [void] }>();

const { t } = useI18n();

const renderShow = ref(isShow);
const editorText = ref<string>(RESOURCE_IMPORT_EXAMPLE.content);

const handleHidden = () => {
  renderShow.value = false;
  emits('on-hidden');
};

watch(() => isShow, (val) => {
  renderShow.value = val;
});

</script>

<style scoped lang="scss">
.tmpl-example-monaco-editor {
  width: 100%;
  height: calc(100vh - 52px);
}
</style>
