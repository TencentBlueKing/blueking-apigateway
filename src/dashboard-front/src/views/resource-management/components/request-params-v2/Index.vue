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
  <div class="request-params-v2">
    <!-- 编辑态工具栏：控制“无请求参数”状态，并提供 JSON 批量生成入口。 -->
    <div
      v-if="!readonly"
      class="request-params-v2__toolbar"
    >
      <BkCheckbox
        v-model="disabled"
        class="no-params-checkbox"
      >
        {{ t('该资源无请求参数') }}
      </BkCheckbox>

      <IconButton
        v-if="!disabled"
        theme="primary"
        @click="handleOpenJsonEditor"
      >
        {{ t('通过 JSON 生成') }}
      </IconButton>
    </div>

    <!--
      主体区域按以下顺序互斥展示：
      只读空态 → 只读参数详情 → 编辑器 → “无请求参数”编辑空态。
    -->
    <div
      v-if="readonly && isEmpty"
      class="request-params-v2__empty"
    >
      {{ t('该资源无请求参数') }}
    </div>

    <div
      v-else-if="readonly"
      class="request-params-v2__readonly"
    >
      <!-- Header、Query、Path 仅在存在参数时分栏展示。 -->
      <template
        v-for="location in PARAMETER_LOCATIONS"
        :key="location"
      >
        <section
          v-if="state.parameters[location].length"
          class="readonly-section"
        >
          <div class="readonly-section__header">
            <span class="readonly-section__title">
              {{ getLocationLabel(location) }}
            </span>
            <span class="readonly-section__count">
              {{ state.parameters[location].length }}
            </span>
          </div>
          <ScalarParameterTable
            :location="location"
            :model-value="state.parameters[location]"
            readonly
          />
        </section>
      </template>

      <!-- Body 使用树形表格单独展示，与基础参数分区保持一致。 -->
      <section
        v-if="state.body"
        class="readonly-section"
      >
        <div class="readonly-section__header">
          <span class="readonly-section__title">Body</span>
          <span class="readonly-section__count">
            {{ state.body ? 1 : 0 }}
          </span>
        </div>
        <BodyParameterTable
          :model-value="bodyState"
          readonly
        />
      </section>
    </div>

    <div
      v-else-if="!disabled"
      class="request-params-v2__editor"
    >
      <!-- 编辑态通过页签隔离 Header、Query、Path、Body 四类参数。 -->
      <BkTab
        v-model:active="activeTab"
        class="request-params-tabs"
        type="unborder-card"
      >
        <BkTabPanel
          :label="getTabLabel('header')"
          name="header"
        >
          <ScalarParameterTable
            v-model="state.parameters.header"
            :errors="validationErrors"
            location="header"
            @clear-error="clearValidationError"
          />
        </BkTabPanel>

        <BkTabPanel
          :label="getTabLabel('query')"
          name="query"
        >
          <ScalarParameterTable
            v-model="state.parameters.query"
            :errors="validationErrors"
            location="query"
            @clear-error="clearValidationError"
          />
        </BkTabPanel>

        <BkTabPanel
          :label="getTabLabel('path')"
          name="path"
        >
          <ScalarParameterTable
            v-model="state.parameters.path"
            :errors="validationErrors"
            location="path"
            @clear-error="clearValidationError"
          />
        </BkTabPanel>

        <BkTabPanel
          :label="getTabLabel('body')"
          name="body"
        >
          <!-- Body 已存在时展示编辑表格，否则展示创建请求体的空态。 -->
          <div
            v-if="state.body"
            class="body-editor"
          >
            <div class="body-editor__toolbar">
              <div class="body-editor__media-type">
                <span>Content-Type</span>
                <span class="body-editor__media-type-value">
                  application/json
                </span>
              </div>
              <BkButton
                text
                theme="danger"
                @click="removeBody"
              >
                {{ t('删除参数') }}
              </BkButton>
            </div>
            <BodyParameterTable
              v-model="bodyState"
              :errors="validationErrors"
              @clear-error="clearValidationError"
            />
          </div>
          <div
            v-else
            class="body-editor-empty"
          >
            <div class="body-editor-empty__description">
              {{ t('暂无数据') }}
            </div>
            <BkButton
              theme="primary"
              @click="addBody"
            >
              {{ t('新增参数') }}
            </BkButton>
          </div>
        </BkTabPanel>
      </BkTab>
    </div>

    <div
      v-else
      class="request-params-v2__disabled"
    >
      <!-- 用户勾选“该资源无请求参数”后的编辑空态。 -->
      {{ t('该资源无请求参数') }}
    </div>
  </div>

  <!-- JSON 侧栏独立于主区域渲染，用于批量导入并回填四类参数。 -->
  <RequestParamsJsonSlider
    v-model="jsonEditorVisible"
    v-model:source="jsonSource"
    @confirm="handleJsonConfirm"
  />
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import BodyParameterTable from './components/BodyParameterTable.vue';
import {
  cloneRequestParamsState,
  createEmptyRequestParamsState,
  createRequestBody,
  createRequestParameter,
  flattenRequestFields,
  openApiSchemaToState,
  requestJsonToState,
  requestParamsStateToEditorJson,
  requestParamsStateToValue,
} from './utils';
import RequestParamsJsonSlider from './components/RequestParamsJsonSlider.vue';
import ScalarParameterTable from './components/ScalarParameterTable.vue';
import {
  type IRequestBodyState,
  type IRequestFieldRow,
  type IRequestParamsDetail,
  type IRequestParamsState,
  PARAMETER_LOCATIONS,
  type ParameterLocation,
} from './types';

interface IProps {
  detail?: IRequestParamsDetail
  readonly?: boolean
}

type RequestParamsTab = ParameterLocation | 'body';

const disabled = defineModel<boolean>('is-no-params', { default: false });

const {
  detail = {},
  readonly = false,
} = defineProps<IProps>();

const { t } = useI18n();

const activeTab = ref<RequestParamsTab>('header');
const jsonEditorVisible = ref(false);
const jsonSource = ref('{}');
const state = ref<IRequestParamsState>(createEmptyRequestParamsState());
const validationErrors = ref<Record<string, string>>({});

const bodyState = computed<IRequestBodyState>({
  get: () => state.value.body ?? createRequestBody(),
  set: (value) => {
    state.value.body = value;
  },
});

const isEmpty = computed(() => {
  return !state.value.body
    && PARAMETER_LOCATIONS.every(location => !state.value.parameters[location].length);
});

watch(
  () => detail,
  () => {
    const operation = detail.schema ?? detail.openapi_schema;
    const nextState = openApiSchemaToState(operation);

    if (!operation) {
      nextState.parameters.header.push(createRequestParameter('header'));
    }

    state.value = nextState;
    validationErrors.value = {};
  },
  {
    deep: true,
    immediate: true,
  },
);

/** 获取参数位置对应的页签与只读分区名称。 */
const getLocationLabel = (location: ParameterLocation) => {
  const labels: Record<ParameterLocation, string> = {
    header: 'Header',
    path: 'Path',
    query: 'Query',
  };

  return labels[location];
};

/** 生成带当前参数数量的页签标题。 */
const getTabLabel = (tab: RequestParamsTab) => {
  const count = tab === 'body'
    ? Number(Boolean(state.value.body))
    : state.value.parameters[tab].length;
  const label = tab === 'body' ? 'Body' : getLocationLabel(tab);

  return `${label} (${count})`;
};

/** 清除指定参数或字段的校验错误。 */
const clearValidationError = (id: string) => {
  delete validationErrors.value[id];
};

/** 创建默认的 application/json 请求体。 */
const addBody = () => {
  state.value.body = createRequestBody();
};

/** 删除请求体，并同步清理请求体字段的校验错误。 */
const removeBody = () => {
  if (state.value.body) {
    flattenRequestFields(state.value.body.root).forEach(({ row }) => {
      clearValidationError(row.id);
    });
  }

  delete state.value.body;
};

/** 将当前请求参数序列化后打开 JSON 编辑侧栏。 */
const handleOpenJsonEditor = () => {
  jsonSource.value = JSON.stringify(
    requestParamsStateToEditorJson(state.value),
    null,
    2,
  );
  jsonEditorVisible.value = true;
};

/** 查找导入结果中第一个有数据的页签，便于导入后直接定位内容。 */
const getFirstPopulatedTab = (nextState: IRequestParamsState): RequestParamsTab => {
  const location = PARAMETER_LOCATIONS.find((item) => {
    return nextState.parameters[item].length > 0;
  });

  if (location) {
    return location;
  }

  return nextState.body ? 'body' : 'header';
};

/** 将 JSON 编辑器确认的数据解析并回填到四类请求参数中。 */
const handleJsonConfirm = (json: unknown) => {
  try {
    const nextState = requestJsonToState(json);
    state.value = cloneRequestParamsState(nextState);
    validationErrors.value = {};
    disabled.value = false;
    activeTab.value = getFirstPopulatedTab(nextState);
  }
  catch {
    Message({
      message: t('生成 JSON Schema 失败'),
      theme: 'error',
    });
  }
};

/** 递归校验 Body 对象字段名是否为空或在同级重复。 */
const validateFieldRows = (
  row: IRequestFieldRow,
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

/** 校验全部请求参数，并自动切换到第一个存在错误的页签。 */
const validate = () => {
  const errors: Record<string, string> = {};
  let firstErrorTab: RequestParamsTab | undefined;

  PARAMETER_LOCATIONS.forEach((location) => {
    const names = new Set<string>();

    state.value.parameters[location].forEach((row) => {
      const name = row.name.trim();

      if (!name) {
        errors[row.id] = t('字段名不能为空');
      }
      else if (names.has(name)) {
        errors[row.id] = t('字段名“{name}”已存在', { name });
      }
      else {
        names.add(name);
      }

      if (errors[row.id] && !firstErrorTab) {
        firstErrorTab = location;
      }

      if (location === 'path') {
        row.required = true;
      }
    });
  });

  if (state.value.body) {
    validateFieldRows(state.value.body.root, errors);

    if (!firstErrorTab && flattenRequestFields(state.value.body.root).some(({ row }) => errors[row.id])) {
      firstErrorTab = 'body';
    }
  }

  validationErrors.value = errors;

  if (firstErrorTab) {
    activeTab.value = firstErrorTab;
  }

  return Object.keys(errors).length === 0;
};

defineExpose({
  /** 校验并返回 OpenAPI 请求参数；无请求参数时返回空结构。 */
  getValue: async () => {
    if (!disabled.value && !validate()) {
      Message({
        message: t('请填写完整的请求参数'),
        theme: 'warning',
      });
      throw new Error('invalid request params');
    }

    if (disabled.value) {
      return {
        parameters: [],
        requestBody: null,
      };
    }

    return requestParamsStateToValue(state.value);
  },
});
</script>

<style lang="scss" scoped>
.request-params-v2 {
  padding-bottom: 22px;

  &__toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 34px;
    margin-bottom: 16px;

    .no-params-checkbox {
      font-size: 12px;
    }
  }

  &__editor {
    min-width: 0;
  }

  &__empty,
  &__disabled {
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
}

.request-params-tabs {

  :deep(.bk-tab-content) {
    padding: 16px 0 0;
  }
}

.readonly-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }

  &__header {
    display: flex;
    gap: 8px;
    align-items: center;
    height: 36px;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: #313238;
  }

  &__count {
    display: inline-flex;
    height: 20px;
    min-width: 20px;
    padding: 0 6px;
    font-size: 11px;
    color: #63656E;
    background: #F0F1F5;
    border-radius: 10px;
    align-items: center;
    justify-content: center;
  }
}

.body-editor {

  &__toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 42px;
    padding: 0 12px;
    background: #F5F7FA;
    border: 1px solid #DCDEE5;
    border-bottom: 0;
    border-radius: 3px 3px 0 0;
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

  :deep(.body-parameter-table) {
    border-radius: 0 0 3px 3px;
  }
}

.body-editor-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  background: #FAFBFD;
  border: 1px dashed #DCDEE5;
  border-radius: 3px;

  &__description {
    margin-bottom: 12px;
    font-size: 12px;
    color: #979BA5;
  }
}
</style>
