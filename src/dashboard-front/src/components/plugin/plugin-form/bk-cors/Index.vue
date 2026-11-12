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
    ref="formRef"
    :model="formData"
    :rules="formRules"
    :label-width="200"
    class="mt-20px"
    @validate="handleValidate"
  >
    <BkFormItem
      label="allow_origins"
      property="allow_origins"
      :description="t('bk_cors_allow_origins_desc')"
    >
      <BkInput
        v-model="formData.allow_origins"
        :maxlength="4096"
      />
    </BkFormItem>
    <BkFormItem
      label="allow_origins_by_regex"
      :description="t('bk_cors_allow_origins_by_regex_desc')"
    >
      <div
        v-for="(item, index) in formData.allow_origins_by_regex"
        :key="item.id"
        class="regex-row"
      >
        <BkFormItem
          class="regex-item"
          :property="`allow_origins_by_regex[${index}].key`"
          :rules="getRegexRules(item)"
        >
          <BkInput
            v-model="item.key"
            :maxlength="4096"
            :placeholder="t('请输入{inputValue}', { inputValue: 'allow_origins_by_regex' })"
          />
        </BkFormItem>
        <div class="regex-actions">
          <AgIcon
            class="cursor-pointer"
            color="#979BA5"
            name="minus-circle-shape"
            size="18"
            @click="() => removeRegex(index)"
          />
          <AgIcon
            v-if="index === formData.allow_origins_by_regex.length - 1"
            class="cursor-pointer"
            color="#979BA5"
            name="plus-circle-shape"
            size="18"
            @click="addRegex"
          />
        </div>
      </div>
      <AgIcon
        v-if="!formData.allow_origins_by_regex.length"
        class="cursor-pointer"
        color="#979BA5"
        name="plus-circle-shape"
        size="18"
        @click="addRegex"
      />
    </BkFormItem>
    <BkFormItem
      label="allow_methods"
      property="allow_methods"
      :description="t('bk_cors_allow_methods_desc')"
      required
    >
      <BkInput
        v-model="formData.allow_methods"
        :maxlength="100"
      />
    </BkFormItem>
    <BkFormItem
      label="allow_headers"
      property="allow_headers"
      :description="t('bk_cors_allow_headers_desc')"
      required
    >
      <BkInput
        v-model="formData.allow_headers"
        :maxlength="4096"
      />
    </BkFormItem>
    <BkFormItem
      label="expose_headers"
      property="expose_headers"
      :description="t('bk_cors_expose_headers_desc')"
    >
      <BkInput
        v-model="formData.expose_headers"
        :maxlength="4096"
      />
    </BkFormItem>
    <BkFormItem
      label="max_age"
      property="max_age"
      :description="t('bk_cors_max_age_desc')"
      required
    >
      <BkInput
        :model-value="formData.max_age ?? ''"
        type="number"
        :min="-1"
        :precision="0"
        :suffix="t('秒')"
        @update:model-value="handleMaxAgeChange"
      />
    </BkFormItem>
    <BkFormItem
      label="allow_credential"
      property="allow_credential"
      :description="t('bk_cors_allow_credential_desc')"
    >
      <BkSwitcher
        v-model="formData.allow_credential"
        theme="primary"
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { isPlainObject } from 'lodash-es';
import type { Form } from 'bkui-vue';
import { getDuplicateKeys } from '@/utils/duplicateKeys';

interface IRegexRow {
  id: number
  key: string
}

interface IFormData {
  allow_origins: string
  allow_origins_by_regex: IRegexRow[]
  allow_methods: string
  allow_headers: string
  expose_headers: string
  max_age: number | null
  allow_credential: boolean
}

interface IProps {
  data: Record<string, any>
}

const { data } = defineProps<IProps>();

const { t } = useI18n();

const ORIGIN_PATTERN = /^(?:\*|\*\*|null|https?:\/\/[-a-zA-Z0-9:[\]./?&=]+)(?:,\s*https?:\/\/[-a-zA-Z0-9:[\]./?&=]+)*$/;
const ORIGIN_REGEX_PATTERN = /^\^?[-a-zA-Z0-9:/[\]{}().*+?|\\]+\$?$/;
const METHODS_PATTERN = /^(?:\*|\*\*|(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE)(?:,\s*(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE))*)$/;
const HEADERS_PATTERN = /^(\*|\*\*|[-a-zA-Z0-9]+(,[-a-zA-Z0-9]+)*)$/;

let nextRowId = 0;

const createRegexRow = (key = ''): IRegexRow => ({
  id: nextRowId++,
  key,
});

const toText = (value: unknown) => typeof value === 'string' ? value : '';

const getFormData = (config: Record<string, any>): IFormData => {
  // 新增时使用推荐的默认值
  if (!Object.keys(config).length) {
    return {
      allow_origins: '',
      allow_origins_by_regex: [],
      allow_methods: '**',
      allow_headers: '**',
      expose_headers: '',
      max_age: 86400,
      allow_credential: true,
    };
  }
  // 编辑时按已保存的配置回显，缺失的字段不套用新增默认值，避免保存时改变原有行为
  const regexList = Array.isArray(config.allow_origins_by_regex) ? config.allow_origins_by_regex : [];
  return {
    allow_origins: toText(config.allow_origins),
    allow_origins_by_regex: regexList.map((item: unknown) =>
      createRegexRow(toText(isPlainObject(item) ? (item as Record<string, unknown>).key : item))),
    allow_methods: toText(config.allow_methods),
    allow_headers: toText(config.allow_headers),
    expose_headers: toText(config.expose_headers),
    max_age: typeof config.max_age === 'number' ? config.max_age : null,
    allow_credential: config.allow_credential === true,
  };
};

const formRef = ref<InstanceType<typeof Form>>();
const formData = ref<IFormData>(getFormData(data));
const validatedProps = new Set<string>();

// allow_origins 与有效的 allow_origins_by_regex 同时存在；正则有重复项时只提示重复
const hasBothOrigins = () => {
  const { allow_origins: allowOrigins, allow_origins_by_regex: regexList } = formData.value;
  const hasRegex = regexList.some(item => item.key !== '');
  const hasDuplicateRegex = getDuplicateKeys(regexList, 'key').length > 0;
  return !!allowOrigins.trim() && hasRegex && !hasDuplicateRegex;
};

const getRequiredRule = (field: string) => ({
  required: true,
  message: t('请输入{inputValue}', { inputValue: field }),
  trigger: 'change',
  validator: (value: string) => !!value?.trim(),
});

const formRules = computed(() => ({
  allow_origins: [
    {
      message: t('allow_origins 与 allow_origins_by_regex 不能同时为空'),
      trigger: 'change',
      validator: () => !!formData.value.allow_origins.trim() || formData.value.allow_origins_by_regex.length > 0,
    },
    {
      message: t('format_bk_cors_allow_origins'),
      trigger: 'change',
      validator: (value: string) => !value || ORIGIN_PATTERN.test(value),
    },
    {
      message: t('allow_origins 与 allow_origins_by_regex 只能一个有效'),
      trigger: 'change',
      validator: () => !hasBothOrigins(),
    },
  ],
  allow_methods: [
    getRequiredRule('allow_methods'),
    {
      message: t('format_bk_cors_allow_methods'),
      trigger: 'change',
      validator: (value: string) => METHODS_PATTERN.test(value),
    },
  ],
  allow_headers: [
    getRequiredRule('allow_headers'),
    {
      message: t('format_bk_cors_allow_headers'),
      trigger: 'change',
      validator: (value: string) => HEADERS_PATTERN.test(value),
    },
  ],
  max_age: [
    {
      required: true,
      message: t('请输入{inputValue}', { inputValue: 'max_age' }),
      trigger: 'change',
      validator: (value: number | null) => typeof value === 'number' && Number.isInteger(value) && value >= -1,
    },
  ],
  allow_credential: [
    {
      // 开启 allow_credential 时，其他字段不能使用 *
      message: t('format_bk_cors_allow_credential'),
      trigger: 'change',
      validator: () => {
        const { allow_credential, allow_origins, allow_methods, allow_headers, expose_headers } = formData.value;
        return !allow_credential || ![allow_origins, allow_methods, allow_headers, expose_headers].includes('*');
      },
    },
  ],
}));

const getRegexRules = (item: IRegexRow) => [
  {
    required: true,
    message: t('请输入{inputValue}', { inputValue: 'allow_origins_by_regex' }),
    trigger: 'change',
    validator: () => !!item.key,
  },
  {
    message: t('format_bk_cors_allow_origins_by_regex'),
    trigger: 'change',
    validator: () => ORIGIN_REGEX_PATTERN.test(item.key),
  },
  {
    message: t('{inputKey}存在重复项', { inputKey: item.key }),
    trigger: 'change',
    validator: () => !getDuplicateKeys(formData.value.allow_origins_by_regex, 'key').includes(item.key),
  },
];

const handleValidate = (property: string) => {
  validatedProps.add(property);
};

// 字段之间存在联动校验：只刷新已经展示过校验结果的字段，未编辑的字段不提前提示
const revalidate = async (match: (property: string) => boolean) => {
  await nextTick();
  const regexCount = formData.value.allow_origins_by_regex.length;
  const fields = [...validatedProps].filter((property) => {
    const regexIndex = /^allow_origins_by_regex\[(\d+)\]/.exec(property)?.[1];
    return match(property) && (regexIndex === undefined || Number(regexIndex) < regexCount);
  });
  if (!fields.length) {
    return;
  }
  try {
    await formRef.value?.validate(fields);
  }
  catch {
    // 校验失败由对应表单项展示
  }
};

watch(
  () => formData.value.allow_origins_by_regex.map(item => item.key),
  () => revalidate(property => property === 'allow_origins' || property.startsWith('allow_origins_by_regex[')),
);

watch(
  () => [
    formData.value.allow_origins,
    formData.value.allow_methods,
    formData.value.allow_headers,
    formData.value.expose_headers,
  ],
  () => revalidate(property => property === 'allow_credential'),
);

const handleMaxAgeChange = (value: string | number | null) => {
  formData.value.max_age = value === '' || value === null ? null : Number(value);
};

const addRegex = () => {
  formData.value.allow_origins_by_regex.push(createRegexRow());
};

const removeRegex = (index: number) => {
  formData.value.allow_origins_by_regex.splice(index, 1);
};

const clearValidate = () => {
  validatedProps.clear();
  formRef.value?.clearValidate();
};

const getValue = async () => {
  await formRef.value?.validate();
  const {
    allow_origins,
    allow_origins_by_regex,
    allow_methods,
    allow_headers,
    expose_headers,
    max_age,
    allow_credential,
  } = formData.value;
  return {
    allow_origins,
    allow_origins_by_regex: allow_origins_by_regex.map(item => item.key),
    allow_methods,
    allow_headers,
    expose_headers,
    max_age,
    allow_credential,
  };
};

defineExpose({
  getValue,
  clearValidate,
});
</script>

<style lang="scss" scoped>
.regex-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;

  // 最后一行的错误提示使用外层表单项的下边距展示
  &:last-child .regex-item {
    margin-bottom: 0;
  }
}

.regex-item {
  flex: 1;
  min-width: 0;
}

.regex-actions {
  display: flex;
  width: 48px;
  padding-top: 7px;
  flex-shrink: 0;
  gap: 12px;
}
</style>
