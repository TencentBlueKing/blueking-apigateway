<!--
  TencentBlueKing is pleased to support the open source community by making
  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
  Copyright (C) Tencent. All rights reserved.
  Licensed under the MIT License (the "License"); you may not use this file except
  in compliance with the License. You may obtain a copy of the License at

  http://opensource.org/licenses/MIT

  Unless required by applicable law or agreed to in writing, software distributed under
  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
  either express or implied. See the License for the specific language governing permissions and
  limitations under the License.

  We undertake not to change the open source license (MIT license) applicable
  to the current version of the project delivered to anyone in the future.
-->

<template>
  <div class="response-params-v2">
    <!-- 只读且没有响应定义时展示统一空态，否则展示响应卡片列表。 -->
    <div
      v-if="readonly && !responseList.length"
      class="response-params-v2__empty"
    >
      {{ t('暂无数据') }}
    </div>

    <div
      v-else
      class="response-params-v2__list"
    >
      <!-- 每个状态码对应一张可折叠卡片，内部维护各自的响应字段树。 -->
      <section
        v-for="response in responseList"
        :key="response.id"
        class="response-card"
        :class="{ 'is-collapsed': !response.expanded }"
      >
        <div
          class="response-card__header"
          @click="response.expanded = !response.expanded"
        >
          <AngleUpFill
            class="response-card__arrow"
            :class="{ 'is-collapsed': !response.expanded }"
          />

          <!-- 状态码编辑时使用输入框，非编辑态展示已确认的状态码。 -->
          <div
            v-if="editingResponseId === response.id"
            class="response-card__code-editor"
            @click.stop
          >
            <BkInput
              v-model="codeDraft"
              :placeholder="t('请输入 HTTP 状态码，按 Enter 确认')"
              :status="validationErrors[response.id] ? 'error' : undefined"
              @blur="cancelCodeEdit(response)"
              @enter="finishCodeEdit(response)"
              @input="clearValidationError(response.id)"
            />
          </div>
          <div
            v-else
            class="response-card__code"
            :class="{ 'is-error': validationErrors[response.id] }"
          >
            {{ response.code || '--' }}
          </div>

          <span class="response-card__label">
            {{ t('状态码') }}
          </span>

          <AgIcon
            v-if="validationErrors[response.id]"
            v-bk-tooltips="{ content: validationErrors[response.id] }"
            class="response-card__error"
            name="exclamation-circle-fill"
            size="14"
          />

          <!-- 只读模式隐藏状态码编辑和响应删除操作。 -->
          <div
            v-if="!readonly"
            class="response-card__actions"
            @click.stop
          >
            <BkButton
              v-bk-tooltips="{ content: t('编辑') }"
              text
              @click="startCodeEdit(response)"
            >
              <AgIcon
                name="edit-line"
                size="15"
              />
            </BkButton>
            <BkButton
              v-bk-tooltips="{ content: t('删除') }"
              class="delete-button"
              text
              @click="deleteResponse(response)"
            >
              <AgIcon
                name="delet"
                size="15"
              />
            </BkButton>
          </div>
        </div>

        <div
          v-show="response.expanded"
          class="response-card__content"
        >
          <!-- 编辑态展示固定 Content-Type 和当前响应的 JSON 生成入口。 -->
          <div
            v-if="!readonly"
            class="response-card__toolbar"
          >
            <div class="response-card__media-type">
              <span>Content-Type</span>
              <span class="response-card__media-type-value">
                application/json
              </span>
            </div>
            <IconButton
              theme="primary"
              @click="openJsonEditor(response)"
            >
              {{ t('通过 JSON 生成') }}
            </IconButton>
          </div>

          <!-- 响应字段树在查看态和编辑态共用同一张原生表格。 -->
          <ResponseParameterTable
            v-model="response.root"
            :errors="validationErrors"
            :readonly="readonly"
            @clear-error="clearValidationError"
          />
        </div>
      </section>
    </div>

    <!-- 仅编辑态允许新增状态码响应。 -->
    <BkButton
      v-if="!readonly"
      class="add-response-button"
      text
      theme="primary"
      @click="addResponse"
    >
      <AgIcon name="add-small" />
      {{ t('新增状态码') }}
    </BkButton>
  </div>

  <!-- JSON 侧栏针对当前选中的响应生成并回填字段树。 -->
  <ResponseParamsJsonSlider
    v-model="jsonEditorVisible"
    v-model:source="jsonSource"
    @confirm="handleJsonConfirm"
  />
</template>

<script lang="ts" setup>
import { messageWarn } from '@/utils';
import { Message } from 'bkui-vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';

import ResponseParameterTable from './components/ResponseParameterTable.vue';
import ResponseParamsJsonSlider from './components/ResponseParamsJsonSlider.vue';
import {
  createResponseState,
  flattenResponseFields,
  openApiSchemaToResponses,
  responseFieldToSchema,
  responseJsonToField,
  responseStatesToValue,
} from './utils';
import type {
  IResponseFieldRow,
  IResponseParamsDetail,
  IResponseState,
} from './types';

interface IProps {
  detail?: IResponseParamsDetail
  readonly?: boolean
}

const {
  detail = {},
  readonly = false,
} = defineProps<IProps>();

const { t } = useI18n();

const codeDraft = ref('');
const editingResponseId = ref('');
const jsonEditorResponseId = ref('');
const jsonEditorVisible = ref(false);
const jsonSource = ref('{}');
const responseList = ref<IResponseState[]>([]);
const validationErrors = ref<Record<string, string>>({});

const HTTP_STATUS_CODE_PATTERN = /^[1-5]\d{2}$/;

watch(
  () => detail,
  () => {
    const operation = detail.schema ?? detail.openapi_schema;
    responseList.value = openApiSchemaToResponses(operation);
    validationErrors.value = {};
    editingResponseId.value = '';
    jsonEditorVisible.value = false;
    jsonEditorResponseId.value = '';
  },
  {
    deep: true,
    immediate: true,
  },
);

/** 生成当前响应列表中尚未使用的状态码，默认从 200 开始递增。 */
const getNextResponseCode = () => {
  const usedCodes = new Set(responseList.value.map(response => response.code));
  let code = 200;

  while (usedCodes.has(String(code))) {
    code += 1;
  }

  return String(code);
};

/** 清除指定响应或字段的校验错误。 */
const clearValidationError = (id: string) => {
  delete validationErrors.value[id];
};

/** 新增一个使用未占用状态码的响应。 */
const addResponse = () => {
  responseList.value.push(createResponseState(getNextResponseCode()));
};

/** 删除响应及其字段错误，并关闭该响应正在使用的 JSON 编辑侧栏。 */
const deleteResponse = (response: IResponseState) => {
  flattenResponseFields(response.root).forEach(({ row }) => {
    clearValidationError(row.id);
  });
  clearValidationError(response.id);
  responseList.value = responseList.value.filter(item => item.id !== response.id);

  if (jsonEditorResponseId.value === response.id) {
    jsonEditorVisible.value = false;
    jsonEditorResponseId.value = '';
  }
};

/** 进入状态码编辑态，并使用当前状态码初始化输入值。 */
const startCodeEdit = (response: IResponseState) => {
  codeDraft.value = response.code;
  editingResponseId.value = response.id;
};

/** 校验状态码是否为 100 至 599 的三位 HTTP 状态码。 */
const isValidHttpStatusCode = (code: string) => {
  return HTTP_STATUS_CODE_PATTERN.test(code);
};

/** 取消状态码编辑并恢复原值。 */
const cancelCodeEdit = (response: IResponseState) => {
  if (editingResponseId.value !== response.id) {
    return;
  }

  codeDraft.value = response.code;
  editingResponseId.value = '';
  clearValidationError(response.id);
};

/** 确认状态码编辑，校验失败时保留编辑态并给出提示。 */
const finishCodeEdit = (response: IResponseState) => {
  if (editingResponseId.value !== response.id) {
    return;
  }

  const code = codeDraft.value.trim();

  if (!isValidHttpStatusCode(code)) {
    const message = t('请输入合法的状态码');
    validationErrors.value[response.id] = message;
    messageWarn(message);
    return;
  }

  response.code = code;
  editingResponseId.value = '';
  clearValidationError(response.id);
};

/** 将指定响应的 Schema 序列化后打开 JSON 编辑侧栏。 */
const openJsonEditor = (response: IResponseState) => {
  jsonEditorResponseId.value = response.id;
  jsonSource.value = JSON.stringify(
    responseFieldToSchema(response.root),
    null,
    2,
  );
  jsonEditorVisible.value = true;
};

/** 将 JSON 编辑器确认的数据解析并回填到当前响应字段树。 */
const handleJsonConfirm = (json: unknown) => {
  const response = responseList.value.find(item => item.id === jsonEditorResponseId.value);

  if (!response) {
    return;
  }

  try {
    flattenResponseFields(response.root).forEach(({ row }) => {
      clearValidationError(row.id);
    });
    response.root = responseJsonToField(
      json,
      response.root.description,
      response.code,
    );
    response.expanded = true;
  }
  catch {
    Message({
      message: t('生成 JSON Schema 失败'),
      theme: 'error',
    });
  }
};

/** 递归校验响应对象字段名是否为空或在同级重复。 */
const validateFieldRows = (
  row: IResponseFieldRow,
  errors: Record<string, string>,
) => {
  if (row.type === 'object') {
    const names = new Set<string>();

    row.children?.forEach((child) => {
      const name = child.name.trim();

      if (!name) {
        errors[child.id] = t('字段名不能为空');
      }
      else if (names.has(name)) {
        errors[child.id] = t('字段名“{name}”已存在', { name });
      }
      else {
        names.add(name);
      }

      validateFieldRows(child, errors);
    });
  }
  else if (row.type === 'array') {
    row.children?.slice(0, 1).forEach(child => validateFieldRows(child, errors));
  }
};

/** 校验状态码与字段树，并展开包含字段错误的响应卡片。 */
const validate = () => {
  const errors: Record<string, string> = {};
  const responseCodeMap = new Map<string, IResponseState>();
  let hasDuplicateCode = false;
  let hasIncompleteField = false;
  let hasInvalidStatusCode = false;

  responseList.value.forEach((response) => {
    const code = response.code.trim();

    if (!isValidHttpStatusCode(code)) {
      errors[response.id] = t('请输入合法的状态码');
      hasIncompleteField = true;
      hasInvalidStatusCode = true;
    }
    else if (responseCodeMap.has(code)) {
      const duplicatedResponse = responseCodeMap.get(code);
      const error = t('响应参数中有重复的状态码，请修改');
      errors[response.id] = error;

      if (duplicatedResponse) {
        errors[duplicatedResponse.id] = error;
      }

      hasDuplicateCode = true;
    }
    else {
      responseCodeMap.set(code, response);
    }

    const previousErrorCount = Object.keys(errors).length;
    validateFieldRows(response.root, errors);

    if (Object.keys(errors).length > previousErrorCount) {
      hasIncompleteField = true;
      response.expanded = true;
    }
  });

  validationErrors.value = errors;

  return {
    hasDuplicateCode,
    hasIncompleteField,
    hasInvalidStatusCode,
    valid: Object.keys(errors).length === 0,
  };
};

defineExpose({
  /** 校验并返回以状态码为键的 OpenAPI responses 对象。 */
  getValue: async () => {
    const result = validate();

    if (!result.valid) {
      const message = result.hasInvalidStatusCode
        ? t('请输入合法的状态码')
        : result.hasIncompleteField
          ? t('请填写完整的响应参数')
          : t('响应参数中有重复的状态码，请修改');
      messageWarn(message);
      throw new Error('invalid response params');
    }

    return responseStatesToValue(responseList.value);
  },
});
</script>

<style lang="scss" scoped>
.response-params-v2 {
  padding-bottom: 24px;

  &__list {
    min-width: 0;
  }

  &__empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 96px;
    font-size: 12px;
    color: #979BA5;
    background: #FAFBFD;
    border: 1px dashed #DCDEE5;
    border-radius: 3px;
  }

  :deep(.bk-input),
  :deep(.bk-select),
  :deep(.bk-select-trigger) {
    font-size: 12px;
  }

  :deep(.bk-input--text) {
    font-size: 12px !important;

    &::placeholder {
      font-size: 12px !important;
    }
  }
}

.response-card {
  min-width: 0;
  margin-bottom: 12px;
  overflow: hidden;
  border: 1px solid #DCDEE5;
  border-radius: 3px;

  &__header {
    display: flex;
    align-items: center;
    height: 44px;
    padding: 0 12px;
    cursor: pointer;
    background: #F5F7FA;
    border-bottom: 1px solid #DCDEE5;
  }

  &__arrow {
    flex: 0 0 auto;
    margin-right: 10px;
    color: #979BA5;
    transition: transform .2s;

    &.is-collapsed {
      transform: rotate(-90deg);
    }
  }

  &__code {
    min-width: 48px;
    font-size: 14px;
    font-weight: 600;
    color: #313238;

    &.is-error {
      color: #EA3636;
    }
  }

  &__code-editor {
    flex: 0 1 260px;
    width: 260px;
    height: 30px;
    margin-right: 8px;

    :deep(.bk-input) {
      height: 30px;
    }
  }

  &__label {
    margin-left: 8px;
    font-size: 12px;
    color: #979BA5;
  }

  &__error {
    margin-left: 8px;
    color: #EA3636;
  }

  &__actions {
    display: flex;
    gap: 2px;
    align-items: center;
    margin-left: auto;

    :deep(.bk-button) {
      width: 28px;
      height: 28px;
      min-width: 28px;
      padding: 0;
      color: #63656E;

      &:hover {
        color: #3A84FF;
        background: #E1ECFF;
      }
    }

    .delete-button:hover {
      color: #EA3636;
      background: #FFF0F0;
    }
  }

  &__content {
    min-width: 0;
    padding: 16px;
  }

  &__toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 34px;
    margin-bottom: 12px;
  }

  &__media-type {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 12px;
    color: #63656E;
  }

  &__media-type-value {
    color: #313238;
  }

  &.is-collapsed &__header {
    border-bottom: 0;
  }
}

.add-response-button {
  margin-top: 2px;
  font-size: 12px;
}
</style>
