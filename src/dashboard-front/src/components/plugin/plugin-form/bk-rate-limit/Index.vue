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
    autocomplete="off"
    @validate="handleValidate"
  >
    <section class="rate-limit-card">
      <h3 class="rate-limit-title">
        {{ t('默认应用频率限制') }}
      </h3>
      <div class="rate-limit-row">
        <BkFormItem
          :label="t('次数')"
          :label-width="90"
          property="default.tokens"
          :rules="positiveIntegerRules"
          required
        >
          <BkInput
            :model-value="formData.default.tokens"
            type="number"
            :min="1"
            :precision="0"
            @update:model-value="(value: string | number | null) => formData.default.tokens = Number(value)"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('时间范围')"
          :label-width="90"
          property="default.period"
          :rules="positiveIntegerRules"
          required
        >
          <BkSelect
            v-model="formData.default.period"
            :clearable="false"
          >
            <BkOption
              v-for="option in getPeriodOptions(formData.default.period)"
              :id="option.value"
              :key="option.value"
              :name="option.label"
            />
          </BkSelect>
        </BkFormItem>
      </div>
    </section>

    <section class="rate-limit-card">
      <h3 class="rate-limit-title">
        {{ t('特殊应用频率限制') }}
      </h3>
      <div
        v-for="(row, index) in formData.specials"
        :key="row.id"
        class="rate-limit-row special-rate-limit-row"
      >
        <BkFormItem
          :label="t('次数')"
          :label-width="90"
          :property="`specials[${index}].tokens`"
          :rules="positiveIntegerRules"
          required
        >
          <BkInput
            :model-value="row.tokens"
            type="number"
            :min="1"
            :precision="0"
            @update:model-value="(value: string | number | null) => row.tokens = Number(value)"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('时间范围')"
          :label-width="90"
          :property="`specials[${index}].period`"
          :rules="positiveIntegerRules"
          required
        >
          <BkSelect
            v-model="row.period"
            :clearable="false"
          >
            <BkOption
              v-for="option in getPeriodOptions(row.period)"
              :id="option.value"
              :key="option.value"
              :name="option.label"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem
          :label="t('蓝鲸应用 ID')"
          :label-width="100"
          :property="`specials[${index}].bk_app_code`"
          :rules="getAppCodeRules(row)"
          required
        >
          <BkInput
            v-model="row.bk_app_code"
            @update:model-value="() => revalidateAppCodes(row)"
          />
        </BkFormItem>
        <div class="row-actions">
          <AgIcon
            v-bk-tooltips="t('克隆')"
            name="copy"
            class="row-action"
            @click="() => cloneRow(row)"
          />
          <AgIcon
            v-bk-tooltips="t('删除')"
            name="delet"
            class="row-action"
            @click="() => removeRow(index)"
          />
        </div>
      </div>
      <BkButton
        class="text-14px!"
        text
        theme="primary"
        @click="addRow"
      >
        <i class="mr-5px apigateway-icon icon-ag-plus-circle-shape" />
        <span>{{ t('添加') }}</span>
      </BkButton>
    </section>
  </BkForm>
</template>

<script setup lang="ts">
import { isPlainObject } from 'lodash-es';
import type { Form } from 'bkui-vue';

interface IRateLimitRule {
  tokens: number
  period: number
}

interface ISpecialRateLimitRow extends IRateLimitRule {
  id: number
  bk_app_code: string
}

interface IFormData {
  default: IRateLimitRule
  specials: ISpecialRateLimitRow[]
}

interface IProps {
  data: Record<string, any>
}

const { data } = defineProps<IProps>();

const { t } = useI18n();

const APP_CODE_PATTERN = /^[a-z][a-z0-9_-]{0,31}$/;

let nextRowId = 0;

const createRow = (tokens: unknown = 200, period: unknown = 1, bkAppCode: unknown = ''): ISpecialRateLimitRow => ({
  id: nextRowId++,
  tokens: tokens as number,
  period: period as number,
  bk_app_code: typeof bkAppCode === 'string' ? bkAppCode : '',
});

// 回显时保留原值，非法值交给表单校验提示，不在初始化时静默修正
const getFormData = (config: Record<string, any>): IFormData => {
  const rates = isPlainObject(config.rates) ? config.rates : {};
  const defaultRule = isPlainObject(rates.default) ? rates.default : {};
  const specials = Array.isArray(rates.specials) ? rates.specials : [];
  return {
    default: {
      tokens: defaultRule.tokens ?? 100,
      period: defaultRule.period ?? 1,
    },
    specials: specials.map((item: Record<string, unknown> | null) =>
      createRow(item?.tokens, item?.period, item?.bk_app_code)),
  };
};

const formData = ref<IFormData>(getFormData(data));
const formRef = ref<InstanceType<typeof Form>>();
// 已展示过应用 ID 校验结果的行，按行 id 记录，删除行导致下标变化后仍能对应
const validatedRowIds = new Set<number>();

const isPositiveInteger = (value: unknown) => typeof value === 'number' && Number.isSafeInteger(value) && value > 0;

const positiveIntegerRules = computed(() => [
  {
    required: true,
    message: t('请输入正整数'),
    trigger: 'change',
    validator: isPositiveInteger,
  },
]);

const getAppCodeRules = (row: ISpecialRateLimitRow) => [
  {
    required: true,
    message: t('请输入{inputValue}', { inputValue: t('蓝鲸应用 ID') }),
    trigger: 'change',
    validator: () => !!row.bk_app_code.trim(),
  },
  {
    message: t('format_bk_rate_limit_bk_app_code'),
    trigger: 'change',
    validator: () => APP_CODE_PATTERN.test(row.bk_app_code),
  },
  {
    message: t('{inputKey}存在重复项', { inputKey: row.bk_app_code }),
    trigger: 'change',
    validator: () => !formData.value.specials.some(item =>
      item.id !== row.id && item.bk_app_code === row.bk_app_code),
  },
];

const getPeriodOptions = (period: number) => {
  const options = [
    {
      label: t('秒'),
      value: 1,
    },
    {
      label: t('分'),
      value: 60,
    },
    {
      label: t('时'),
      value: 3600,
    },
    {
      label: t('天'),
      value: 86400,
    },
  ];
  // 回显时保留已有的自定义时间窗口，避免将其替换为预设值
  if (isPositiveInteger(period) && !options.some(option => option.value === period)) {
    options.push({
      label: `${period} ${t('秒')}`,
      value: period,
    });
  }
  return options;
};

const handleValidate = (property: string) => {
  const index = /^specials\[(\d+)\]\.bk_app_code$/.exec(property)?.[1];
  const row = index === undefined ? undefined : formData.value.specials[Number(index)];
  if (row) {
    validatedRowIds.add(row.id);
  }
};

// 应用 ID 不能重复：修改或删除某一行后，同步刷新已校验过的其他行，清除或补充重复提示
const revalidateAppCodes = async (currentRow?: ISpecialRateLimitRow) => {
  await nextTick();
  const fields = formData.value.specials.flatMap((row, index) =>
    row.id !== currentRow?.id && validatedRowIds.has(row.id) ? [`specials[${index}].bk_app_code`] : []);
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

const clearValidate = () => {
  validatedRowIds.clear();
  formRef.value?.clearValidate();
};

const addRow = () => {
  formData.value.specials.push(createRow());
};

const cloneRow = (row: ISpecialRateLimitRow) => {
  formData.value.specials.push(createRow(row.tokens, row.period));
};

// 只刷新剩余行中已校验过的应用 ID，不清空其他字段的错误提示
const removeRow = (index: number) => {
  const [removed] = formData.value.specials.splice(index, 1);
  if (removed) {
    validatedRowIds.delete(removed.id);
  }
  void revalidateAppCodes();
};

const getValue = async () => {
  await formRef.value?.validate();
  const { default: defaultRule, specials } = formData.value;
  return {
    rates: {
      default: {
        tokens: defaultRule.tokens,
        period: defaultRule.period,
      },
      specials: specials.map(row => ({
        tokens: row.tokens,
        period: row.period,
        bk_app_code: row.bk_app_code,
      })),
    },
  };
};

defineExpose({
  getValue,
  clearValidate,
});
</script>

<style lang="scss" scoped>
.rate-limit-card {
  padding: 10px 20px 20px 16px;
  margin-bottom: 24px;
  background: #f5f7fa;
}

.rate-limit-title {
  display: flex;
  height: 50px;
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #63656e;
  align-items: center;
}

.rate-limit-row {
  position: relative;
  display: grid;
  padding: 10px 56px 10px 10px;
  margin-bottom: 24px;
  grid-template-columns: 250px 200px;
  gap: 24px;

  &.special-rate-limit-row {
    background: #fff;
    grid-template-columns: 250px 200px 250px;
  }

  :deep(.bk-form-item) {
    min-width: 0;
    margin-top: 0;
    margin-bottom: 0;
  }
}

.row-actions {
  position: absolute;
  top: 18px;
  right: 8px;
  display: flex;
  gap: 12px;
}

.row-action {
  color: #979ba5;
  cursor: pointer;

  &:hover {
    color: #3a84ff;
  }
}
</style>
