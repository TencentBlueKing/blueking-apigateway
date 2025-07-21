<template>
  <div class="">
    <div class="title">
      <span class="title-name">
        {{ t('变量列表') }}
      </span>
      <span class="title-tips">{{ t('（可在资源配置中使用）') }}</span>
      <span
        v-if="gatewayStore.currentGateway?.kind !== 1"
        class="title-edit"
      >
        <AgIcon
          v-bk-tooltips="{
            content: t('当前有版本正在发布，请稍后再进行变量修改'),
            disabled: getStageStatus(stage) !== 'doing'
          }"
          class="mx-5px"
          name="edit-line"
          size="15"
          @click.stop="editTable"
        />
      </span>
    </div>

    <BkLoading
      :loading="isLoading"
      class="w-740px!"
    >
      <BkTable
        class="variable-table mt15"
        :data="tableData"
        show-overflow-tooltip
        row-hover="auto"
        :cell-class="getCellClass"
        border="outer"
        @cell-click="handleCellClick"
      >
        <BkTableColumn
          :label="t('变量名称')"
          prop="name"
          :show-overflow-tooltip="false"
          :resizable="false"
        >
          <template #default="{ row, index, column }">
            <span
              v-if="!row.isEdit"
              v-bk-tooltips="{ content: row.name, disabled: !row.name }"
              class="no-edit-value"
            >
              {{ row?.name }}
            </span>
            <template v-if="row.isEdit">
              <BkPopover
                placement="top-start"
                trigger="click"
                theme="light"
                :is-show="isShowVarPopover"
                :content="t('变量名由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符') "
                :popover-delay="[300, 0]"
              >
                <BkForm
                  :ref="(el: HTMLElement) => setRefs(el, `name-${index}`)"
                  :model="row"
                  label-width="0"
                >
                  <BkFormItem
                    :rules="varRules.name"
                    property="name"
                    error-display-type="tooltips"
                    class="table-form-item"
                  >
                    <BkInput
                      :ref="(el: HTMLElement) => setInputRefs(el, `name-input-${index}-${column?.index}`)"
                      v-model="row.name"
                      :clearable="false"
                      :max-length="50"
                      @focus="() => handleInputFocus(index)"
                      @enter="() => handleInputEnter(index)"
                      @blur="() => handleInputBlur(index)"
                    />
                  </BkFormItem>
                </BkForm>
              </BkPopover>
            </template>
          </template>
        </BkTableColumn>
        <BkTableColumn
          :label="t('变量值')"
          prop="value"
          :show-overflow-tooltip="false"
          :resizable="false"
        >
          <template #default="{ row, index, column }">
            <span
              v-show="!row.isEdit"
              v-bk-tooltips="{ content: row.value, disabled: !row.value }"
              class="no-edit-value"
            >
              {{ row?.value }}
            </span>
            <template v-if="row.isEdit">
              <BkForm
                :ref="(el: HTMLElement) => setRefs(el, `value-${index}`)"
                :model="row"
                label-width="0"
              >
                <BkFormItem
                  :rules="varRules.value"
                  property="value"
                  error-display-type="tooltips"
                  class="table-form-item"
                >
                  <BkInput
                    :ref="(el: HTMLElement) => setInputRefs(el, `value-input-${index}-${column?.index}`)"
                    v-model="row.value"
                    :clearable="false"
                    @focus="() => handleInputFocus(index)"
                    @enter="() => handleInputEnter(index)"
                    @blur="() => handleInputBlur(index)"
                  />
                </BkFormItem>
              </BkForm>
            </template>
          </template>
        </BkTableColumn>
        <BkTableColumn
          :label="t('操作')"
          :resizable="false"
        >
          <template #default="{ index, column }">
            <div
              v-if="tableIsEdit"
              class="normal-status"
            >
              <AgIcon
                name="plus-circle-shape"
                @click="() => addRow(index, column.index)"
              />
              <AgIcon
                name="minus-circle-shape"
                @click="() => delRow(index)"
              />
            </div>
            <div
              v-else
              class="normal-status"
            >
              --
            </div>
          </template>
        </BkTableColumn>
      </BkTable>
    </BkLoading>

    <div
      v-show="tableIsEdit"
      class="footer-btn"
    >
      <BkButton
        theme="primary"
        @click.stop="handleSave"
      >
        {{ t('保存') }}
      </BkButton>
      <BkButton
        v-bk-tooltips="{ content: '取消编辑' }"
        @click.stop="cancelTableEdit"
      >
        {{ t('取消') }}
      </BkButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type IStageListItem, getStageVars, putStageVars } from '@/services/source/stage';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import { getStageStatus } from '@/utils';
import { useGateway } from '@/stores';
import { useRouteParams } from '@vueuse/router';

interface IProps {
  stageId: number
  stage: IStageListItem
}

const {
  stageId,
  stage,
} = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();
const gatewayId = useRouteParams('id', 0, { transform: Number });

const tableIsEdit = ref(false);
const isShowVarPopover = ref(false);

const isLoading = ref(false);
const tableData = ref<any>([]);

const formRefs = ref(new Map());
const formInputRef = ref(new Map());

const varRules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(value: any) {
        const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,49}$/;
        return reg.test(value);
      },
      message: t('由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符'),
      trigger: 'blur',
    },
    {
      validator(value: any) {
        // 去重
        const alikeArr: any = tableData.value?.filter((item: any) => item.name === value);
        return alikeArr?.length <= 1;
      },
      message: t('变量名不可重复'),
      trigger: 'blur',
    },
  ],
  value: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
};

watch(
  () => stage,
  (stage) => {
    if (stage) {
      getData();
    }
  },
);

const getVars = () => {
  return {
    name: '',
    value: '',
    // sourceNumber: 0,
    isEdit: true,
    isFocus: true,
  };
};

const getCellClass = (payload: any) => {
  if (payload.index !== 2) {
    return 'custom-table-cell';
  }
  return '';
};

const getData = async () => {
  if (!gatewayId.value || !stageId) return;
  const res = await getStageVars(gatewayId.value, stageId);
  const list: any = [];
  for (const key of Object.keys(res?.vars)) {
    list.push({
      name: key,
      value: res?.vars[key],
      isEdit: false,
      isFocus: false,
    });
  }
  tableData.value = list;
};

const setRefs = (el: any, name: string) => {
  if (el) {
    formRefs.value?.set(name, el);
  }
};

const setInputRefs = (el: any, name: string) => {
  if (el) {
    formInputRef.value?.set(name, el);
  }
};

const validateName = async (index: number) => {
  let flag = true;
  await formRefs.value?.get(`name-${index}`)?.validate()
    .then(() => {
    }, () => { // 校验不通过
      flag = false;
    });
  await formRefs.value?.get(`value-${index}`)?.validate()
    .then(() => {
    }, () => { // 校验不通过
      flag = false;
    });

  return flag;
};

const confirmRowEdit = async (index: number) => {
  if (await validateName(index)) {
    tableData.value[index].isEdit = false;
  }
};

const editTable = () => {
  if (getStageStatus(stage) === 'doing') {
    return;
  }
  tableIsEdit.value = true;
  if (tableData.value.length) {
    tableData.value.forEach((row: any, index: number) => {
      if (index === 0) {
        row.isEdit = true;
        nextTick(() => {
          formInputRef.value?.get(`name-input-${index}-0`)?.focus();
        });
      }
    });
  }
  else {
    tableData.value?.push(getVars());
    nextTick(() => {
      formInputRef.value?.get('name-input-0-0')?.focus();
    });
  }
};

const cancelTableEdit = () => {
  tableIsEdit.value = false;
  getData();
};

const addRow = async (index: number, columnIndex: number) => {
  const nextIndex = index + 1;
  tableData.value?.splice(nextIndex, 0, getVars());
  tableData.value[nextIndex] = Object.assign(tableData.value[nextIndex], {
    isEdit: true,
    isFocus: false,
  });
  nextTick(() => {
    formInputRef.value?.get(`name-input-${nextIndex}-${columnIndex}`)?.focus();
  });
};

const delRow = (index: number) => {
  tableData.value?.splice(index, 1);
};

const handleInputEnter = (index: number) => {
  confirmRowEdit(index);
};

const handleInputFocus = (index: number) => {
  // 处理新增的场景
  tableData.value[index].isFocus = true;
};

const handleInputBlur = (index: number) => {
  tableData.value[index].isFocus = false;
  confirmRowEdit(index);
};

const handleCellClick = async ({ event, column, rowIndex }: any) => {
  if (!tableIsEdit.value) return;

  event.stopPropagation();
  const { field, index } = column;
  if (!field) {
    return;
  }
  tableData.value[rowIndex] = Object.assign(tableData.value[rowIndex], {
    isEdit: true,
    isFocus: true,
  });
  nextTick(() => {
    formInputRef.value?.get(`${field}-input-${rowIndex}-${index}`)?.focus();
  });
};

const handleSave = async () => {
  let flag = true;
  for (let i = 0; i < tableData.value?.length; i++) {
    if (!(await validateName(i))) {
      flag = false;
      break;
    }
  }
  if (flag) {
    InfoBox({
      infoType: 'warning',
      title: t('确认修改变量配置？'),
      subTitle: t('将会立即应用在环境上，请谨慎操作！'),
      confirmText: t('确认修改'),
      cancelText: t('取消'),
      onConfirm: async () => {
        const data: any = {};
        tableData.value?.forEach((item: any) => {
          data[item.name] = item.value;
        });

        await putStageVars(gatewayId.value, stageId, { vars: data });
        Message({
          theme: 'success',
          message: t('更新成功'),
        });
        getData();
        tableIsEdit.value = false;
      },
    });
  }
};

onMounted(() => {
  getData();
});

</script>

<style lang="scss" scoped>
.title {
  display: flex;
  align-items: center;

  .title-name {
    font-size: 14px;
    font-weight: 700;
    color: #313238;
  }

  .title-tips {
    font-size: 14px;
    font-weight: normal;
    color: #979BA5;
  }

  .title-edit {
    font-size: 18px;
    color: #3A84FF;
    cursor: pointer;
  }
}

.tips {
  padding-top: 12px;
}

.footer-btn {
  padding-top: 32px;

  .bk-button {
    min-width: 88px;

    &:not(&:last-child) {
      margin-right: 8px;
    }
  }
}

.normal-status {

  .apigateway-icon {
    font-size: 16px;
    color: #c4c6cc;
    cursor: pointer;
  }

  .icon-ag-plus-circle-shape {
    margin-right: 18px;
  }
}

// .table-form-item {
//   margin-bottom: 12px;
//   padding-top: 12px;
// }

// .edit-status {
//   padding-top: 8px;
// }

.no-edit-value {
  padding: 0 16px;
  line-height: 42px;
}

:deep(.variable-table) {

  .bk-form-error-tips {
    transform: translate(-50%, 4px);
  }

  .bk-table-body-content {

    .custom-table-cell {

      .cell {
        padding: 0;

        &:hover {
          cursor: pointer;
        }

        .bk-form {
          line-height: 42px;

          .table-form-item {
            margin-bottom: 0;

            .bk-form-content {
              line-height: 42px;

              .bk-input {
                height: 42px;
                line-height: 42px;
                border: 0;

                &:hover {
                  border: 1px solid #A3C5FD;
                }

                &.is-focused {
                  border: 1px solid #3A84FF;
                }

                &--text {
                  padding: 0 16px;
                }
              }
            }

            &.is-error {

              .bk-form-content {

                .bk-input--text {
                  background: #FEE;
                }
              }
            }
          }
        }
      }
    }
  }
}

.variable-table {

  :deep(.bk-table-head) {
    scrollbar-color: transparent transparent;
    overflow: visible;
  }

  :deep(.bk-table-body) {
    scrollbar-color: transparent transparent;
    overflow: visible;
  }
}
</style>
