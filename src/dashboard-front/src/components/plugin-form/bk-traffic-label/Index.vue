<template>
  <BkForm
    ref="formRef"
    :model="form"
    :rules="formRules"
    label-position="left"
    form-type="vertical"
  >
    <BkFormItem property="match">
      <template #label>
        <div class="flex justify-between items-center">
          <div>{{ t('bk-traffic-label.染色条件') }}<span class="pl-4px color-#ea3636">*</span></div>
          <div class="flex items-center">
            <div class="pr-8px">
              {{ t('bk-traffic-label.条件关系') }}
            </div>
            <div
              class="w-120px"
            >
              <BkRadioGroup
                v-model="matchRelation"
                type="card"
                :disabled="form.match.length <= 1"
              >
                <BkRadioButton
                  v-bk-tooltips="t('bk-traffic-label.满足全部条件')"
                  label="AND"
                >
                  AND
                </BkRadioButton>
                <BkRadioButton
                  v-bk-tooltips="t('bk-traffic-label.满足任意条件')"
                  label="OR"
                >
                  OR
                </BkRadioButton>
              </BkRadioGroup>
            </div>
          </div>
        </div>
      </template>
      <table class="match-table">
        <thead class="table-head">
          <tr class="table-head-row">
            <th class="table-head-row-cell arg-on-col">
              {{ t('bk-traffic-label.参数位置') }}
              <span class="pl-4px color-#ea3636">*</span>
            </th>
            <th
              :style="readonly ? 'width: 250px' : ''"
              class="table-head-row-cell name-col"
            >
              {{ t('bk-traffic-label.参数名') }}
              <span class="pl-4px color-#ea3636">*</span>
            </th>
            <th class="table-head-row-cell operator-col">
              {{ t('bk-traffic-label.关系') }}
              <span class="pl-4px color-#ea3636">*</span>
            </th>
            <th
              :style="readonly ? 'width: 250px' : ''"
              class="table-head-row-cell value-col"
            >
              {{ t('bk-traffic-label.参数值') }}
              <span class="pl-4px color-#ea3636">*</span>
            </th>
            <th
              v-if="!readonly"
              class="table-head-row-cell actions-col"
            >
              {{ t('操作') }}
            </th>
          </tr>
        </thead>
        <tbody class="table-body">
          <tr
            v-for="row in form.match"
            :key="row.id"
            class="table-body-row"
          >
            <!-- 参数位置 -->
            <td class="table-body-row-cell arg-on-col">
              <div
                v-if="readonly"
                class="readonly-value-wrapper"
              >
                {{ argOnList.find(item => item.value === row.operator)?.label || '--' }}
              </div>
              <BkSelect
                v-else
                v-model="row.arg_on"
                :clearable="false"
                :filterable="false"
              >
                <BkOption
                  v-for="item in argOnList"
                  :id="item.value"
                  :key="item.value"
                  :name="item.label"
                />
              </BkSelect>
            </td>
            <!-- 参数名 -->
            <td
              class="table-body-row-cell name-col"
              :class="{ 'max-w-250px w-250px': readonly }"
            >
              <div
                v-if="readonly"
                class="readonly-value-wrapper"
              >
                <BkOverflowTitle type="tips">
                  {{ row.name || '--' }}
                </BkOverflowTitle>
              </div>
              <BkInput
                v-else
                v-model="row.name"
                :placeholder="t('bk-traffic-label.参数名')"
              />
            </td>
            <!-- 字段类型 -->
            <td class="table-body-row-cell operator-col">
              <div
                v-if="readonly"
                class="readonly-value-wrapper"
              >
                {{ operatorList.find(item => item.value === row.operator)?.label || '--' }}
              </div>
              <BkSelect
                v-else
                v-model="row.operator"
                :clearable="false"
                :filterable="false"
              >
                <BkOption
                  v-for="item in operatorList"
                  :id="item.value"
                  :key="item.value"
                  :name="item.label"
                />
              </BkSelect>
            </td>
            <!-- 字段备注 -->
            <td
              class="table-body-row-cell value-col"
              :class="{ 'max-w-250px w-250px': readonly }"
            >
              <div
                v-if="readonly"
                class="readonly-value-wrapper"
              >
                <BkOverflowTitle type="tips">
                  {{ row.value || '--' }}
                </BkOverflowTitle>
              </div>
              <BkInput
                v-else
                v-model="row.value"
                :placeholder="t('bk-traffic-label.参数值')"
              />
            </td>
            <!-- 字段操作 -->
            <td
              v-if="!readonly"
              class="table-body-row-cell actions-col"
            >
              <AgIcon
                v-bk-tooltips="t('添加字段')"
                class="tb-btn add-btn"
                name="plus-circle-shape"
                @click="() => addMatchRow(row)"
              />
              <AgIcon
                v-bk-tooltips="t('删除字段')"
                class="tb-btn delete-btn"
                :class="{ 'is-disabled': form.match.length <= 1 }"
                name="minus-circle-shape"
                @click="() => removeMatchRow(row)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </BkFormItem>
    <BkFormItem
      property="actions"
      required
      :label="t('bk-traffic-label.设置 Header')"
    >
      <BkForm
        v-for="action in form.actions"
        :key="action.id"
        ref="action-form"
        :model="action"
        :rules="actionFormRules"
        class="flex items-center gap-12px mb-12px"
      >
        <BkFormItem
          class="flex-1"
          property="key"
          required
        >
          <BkInput
            v-model="action.key"
            prefix="key"
          />
        </BkFormItem>
        <BkFormItem
          class="flex-1"
          property="value"
          required
        >
          <BkInput
            v-model="action.value"
            prefix="value"
          />
        </BkFormItem>
        <BkFormItem
          class="flex-1"
          property="weight"
          required
        >
          <BkInput
            v-model="action.weight"
            prefix="weight"
            suffix="%"
            type="number"
            :step="1"
            :precision="0"
            :min="1"
            :max="100"
            @input="handleWeightInput"
          />
        </BkFormItem>
        <BkFormItem>
          <div>
            <AgIcon
              v-bk-tooltips="t('添加字段')"
              class="tb-btn add-btn"
              :class="{ 'is-disabled': form.actions.length == 20 }"
              name="plus-circle-shape"
              @click="() => addActionRow(action)"
            />
            <AgIcon
              v-bk-tooltips="t('删除字段')"
              class="tb-btn delete-btn"
              :class="{ 'is-disabled': form.actions.length <= 1 }"
              name="minus-circle-shape"
              @click="() => removeActionRow(action)"
            />
          </div>
        </BkFormItem>
      </BkForm>
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { Form } from 'bkui-vue';
import {
  sumBy,
  uniqueId,
} from 'lodash-es';

interface IAction {
  set_headers?: Record<string, string>
  weight?: number
}

interface IRules {
  match?: (string | string[])[]
  actions?: IAction[] // 最少 1 项，最多 20 项
}

interface ITrafficLabelConfig { rules: IRules[] }

interface IFormModel {
  match: {
    arg_on: string
    name: string
    operator: string
    value: string
    id?: string
  }[]
  actions: {
    key: string
    value: string
    weight: number
    id?: string
  }[]
}

interface IProps { data: ITrafficLabelConfig }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref();
const actionFormRefs = useTemplateRef<InstanceType<typeof Form>>('action-form');

const form = ref<IFormModel>({
  match: [
    {
      arg_on: 'header',
      name: '',
      operator: '==',
      value: '',
      id: uniqueId('row_'),
    },
  ],
  actions: [
    {
      key: '',
      value: '',
      weight: 100,
      id: uniqueId('action_row_'),
    },
  ],
});

const readonly = ref(false);
const matchRelation = ref('AND');

const formRules = {
  match: [
    {
      validator: () => !!form.value.match.length,
      message: t('bk-traffic-label.match 不能为空'),
      trigger: 'change',
    },
    {
      validator: () => form.value.match.every(item => item.name && item.operator && item.value),
      message: t('bk-traffic-label.每条 match 的每一项都需要填写'),
      trigger: 'blur',
    },
  ],
  actions: [
    {
      validator: () => !!form.value.actions.length,
      message: t('bk-traffic-label.actions 不能为空'),
      trigger: 'change',
    },
  ],
};

const actionFormRules = {
  weight: [
    {
      validator: () => sumBy(form.value.actions, item => Number(item.weight)) == 100,
      message: t('bk-traffic-label.weight 总和不等于 100'),
      trigger: 'blur',
    },
  ],
};

const argOnList = [
  {
    label: 'Arg',
    value: 'arg',
  },
  {
    label: 'Post',
    value: 'post',
  },
  {
    label: 'HTTP',
    value: 'http',
  },
  {
    label: 'Cookie',
    value: 'cookie',
  },
  {
    label: t('bk-traffic-label.内置变量'),
    value: 'built_in',
  },
];

const operatorList = [
  {
    label: t('bk-traffic-label.=（等于）'),
    value: '==',
  },
  {
    label: t('bk-traffic-label.≠（不等于）'),
    value: '!=',
  },
  {
    label: t('bk-traffic-label.>（大于）'),
    value: '>',
  },
  {
    label: t('bk-traffic-label.≧（大于等于）'),
    value: '>=',
  },
  {
    label: t('bk-traffic-label.<（小于）'),
    value: '<',
  },
  {
    label: t('bk-traffic-label.≦（小于等于）'),
    value: '<=',
  },
  {
    label: t('bk-traffic-label.~~（正则）'),
    value: '~~',
  },
];

const parseArgOnAndName = (str: string): {
  arg_on: string
  name: string
} => {
  const prefixes = argOnList.map(item => item.value);
  for (const prefix of prefixes) {
    if (str.startsWith(`${prefix}_`)) {
      return {
        arg_on: prefix,
        name: str.slice(prefix.length + 1),
      };
    }
  }
  return {
    arg_on: 'built_in',
    name: str,
  };
};

watch(() => data, () => {
  if (data && data.rules?.length) {
    if (data.rules[0].match?.length) {
      const match = data.rules[0].match;
      matchRelation.value = typeof match[0] === 'string' ? match[0] : 'AND';
      form.value.match = match.filter(item => typeof item !== 'string').map((item) => {
        const [argOnAndName, operator, value] = item;
        const { arg_on, name } = parseArgOnAndName(argOnAndName);
        return {
          arg_on,
          name,
          operator,
          value,
          id: uniqueId('row_'),
        };
      });
    }

    if (data.rules[0].actions?.length) {
      const actions = data.rules[0].actions;
      form.value.actions = actions.map(item => ({
        key: Object.keys(item.set_headers!)[0],
        value: item.set_headers![Object.keys(item.set_headers!)[0]],
        weight: item.weight || 1,
        id: uniqueId('action_row_'),
      }));
    }
  }
}, {
  immediate: true,
  deep: true,
});

const addMatchRow = (row: IFormModel['match'][number]) => {
  const index = form.value.match.findIndex(item => item.id === row.id);
  form.value.match.splice(index + 1, 0, {
    arg_on: 'header',
    name: '',
    operator: '==',
    value: '',
    id: uniqueId('row_'),
  });
};

const removeMatchRow = (row: IFormModel['match'][number]) => {
  const index = form.value.match.findIndex(item => item.id === row.id);
  if (index !== -1) {
    form.value.match.splice(index, 1);
  }
};

const addActionRow = (action: IFormModel['actions'][number]) => {
  const index = form.value.actions.findIndex(item => item.id === action.id);
  form.value.actions.splice(index + 1, 0, {
    key: '',
    value: '',
    weight: 100,
    id: uniqueId('action_row_'),
  });
};

const removeActionRow = (action: IFormModel['actions'][number]) => {
  const index = form.value.actions.findIndex(item => item.id === action.id);
  if (index !== -1) {
    form.value.actions.splice(index, 1);
  }
};

const handleWeightInput = () => {
  if (Array.isArray(actionFormRefs.value)) {
    actionFormRefs.value.forEach((item) => {
      item.validate('weight');
    });
  }
  else {
    actionFormRefs.value?.validate('weight');
  }
};

const genRules = () => {
  formRef.value.validate();
  const finalRule: IRules = {
    match: form.value.match.map(item => [
      item.arg_on === 'built_in' ? item.name : `${item.arg_on}_${item.name}`,
      item.operator,
      item.value,
    ]),
    actions: form.value.actions.map(item => ({
      set_headers: { [item.key]: item.value },
      weight: item.weight,
    })),
  };
  if (form.value.match.length > 1) {
    finalRule.match?.unshift(matchRelation.value);
  }
  return { rules: [finalRule] };
};

const validateActions = async () => {
  try {
    if (Array.isArray(actionFormRefs.value)) {
      for (const item of actionFormRefs.value) {
        await item.validate();
      }
    }
    else {
      await actionFormRefs.value?.validate();
    }
    return Promise.resolve(true);
  }
  catch {
    return Promise.reject(false);
  }
};

const validate = () => Promise.all([
  formRef.value.validate(),
  validateActions(),
]);

defineExpose<{ getValue: () => Promise<ITrafficLabelConfig> }>({ getValue: () => validate().then(() => genRules()) });

</script>

<style scoped lang="scss">

.match-table {
  width: 100%;
  border: 1px solid #dcdee5;
  border-collapse: collapse;
  border-bottom: none;
  border-spacing: 0;

  .table-head-row-cell,
  .table-body-row-cell {
    height: 42px;
    font-size: 12px;

    &.arg-on-col {
      border-left: none;
    }

    &.name-col {
      width: 200px;
    }

    &.operator-col {
      width: 160px;
    }

    &.value-col {
      width: 200px;
    }

    &.actions-col {
      width: 110px;
    }
  }

  .table-head-row-cell {
    padding-left: 16px;
    font-weight: normal;
    color: #313238;
    background-color: #fafbfd;
    border-bottom: 1px solid #dcdee5;

    &:hover {
      background-color: #f0f1f5;
    }
  }

  .table-body {

    .readonly-value-wrapper {
      padding-left: 16px;
      font-size: 12px;
      cursor: auto;
    }

    .table-body-row {
      border-bottom: 1px solid #dcdee5;

      .table-body-row-cell {
        height: 42px;

        &.arrow-col {
          text-align: center;
        }

        &.actions-col {
          width: 110px;
          padding-left: 16px;
        }

        :deep(.bk-select),
        :deep(.bk-select-trigger),
        :deep(.bk-input),
        :deep(.bk-input--text) {
          height: 100%;
          border: none;
        }

        // 输入框和 placeholder 样式

        :deep(.bk-input) {

          &:hover {
            border: 1px solid #a3c5fd;
          }

          &.is-disabled {
            background-color: #fff;

            &:hover {
              border: none;
            }
          }

          &.is-focused:not(.is-readonly) {
            border: 1px solid #a3c5fd;
            box-shadow: none;
          }

          .bk-input--text {
            font-size: 12px !important;
            background-color: #fff;
            padding-inline: 16px;

            &::placeholder {
              font-size: 12px !important;
            }
          }
        }
      }
    }
  }
}

.tb-btn {
  font-size: 14px;
  color: #c4c6cc;
  cursor: pointer;

  &:hover {
    color: #979ba5;
  }

  &.add-btn {
    margin-right: 16px;
  }

  &.is-disabled {
    color: #dcdee5;
    pointer-events: none;
  }
}

</style>
