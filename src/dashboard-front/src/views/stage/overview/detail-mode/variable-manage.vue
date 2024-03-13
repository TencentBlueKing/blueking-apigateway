<template>
  <div class="">
    <div class="title">
      <span class="title-name">
        变量列表
      </span>
      <span class="title-tips">（可在资源配置中使用）</span>
      <span class="title-edit">
        <edit-line @click="editTable" />
      </span>
    </div>

    <bk-loading :loading="isLoading" style="width: 740px;">
      <bk-table
        class="variable-table mt15"
        :data="tableData"
        show-overflow-tooltip
        row-hover="auto"
        :cell-class="getCellClass"
        border="outer"
      >
        <bk-table-column :label="t('变量名称')" prop="name" :show-overflow-tooltip="false">
          <template #default="{ row, index }">
            <span v-show="!row.isEdit" class="no-edit-value">{{ row?.name }}</span>
            <template v-if="row.isEdit">
              <bk-popover
                placement="top-start"
                trigger="click"
                theme="light"
                :is-show="isShowVarPopover"
                :content="t('变量名由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符') "
                :popover-delay="[300, 0]"
              >
                <bk-form :ref="(el: HTMLElement) => setRefs(el, `name-${index}`)" :model="row" label-width="0">
                  <bk-form-item
                    :rules="varRules.name"
                    property="name"
                    error-display-type="tooltips"
                    class="table-form-item">
                    <bk-input
                      :autofocus="row.isEdit"
                      v-model="row.name"
                      :clearable="false"
                      :max-length="50"
                    />
                  </bk-form-item>
                </bk-form>
              </bk-popover>
            </template>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('变量值')" prop="value" :show-overflow-tooltip="false">
          <template #default="{ row, index }">
            <span v-show="!row.isEdit" class="no-edit-value">{{ row?.value }}</span>
            <template v-if="row.isEdit">
              <bk-form :ref="(el: HTMLElement) => setRefs(el, `value-${index}`)" :model="row" label-width="0">
                <bk-form-item
                  :rules="varRules.value"
                  property="value"
                  error-display-type="tooltips"
                  class="table-form-item">
                  <bk-input
                    v-model="row.value"
                    :clearable="false"
                  />
                </bk-form-item>
              </bk-form>
            </template>
          </template>
        </bk-table-column>
        <!-- <bk-table-column :label="t('应用资源数')" prop="sourceNumber">
          <template #default="{ row }">
            <span>{{row?.sourceNumber}}</span>
            <bk-input
              v-model="row.sourceNumber"
              type="number"
              clearable
            />
          </template>
        </bk-table-column> -->
        <bk-table-column
          :label="t('操作')"
          v-if="tableIsEdit"
        >
          <template #default="{ row, index }">
            <div class="normal-status" v-show="!row.isEdit">
              <i class="apigateway-icon icon-ag-plus-circle-shape" @click="addRow(index)" />
              <i class="apigateway-icon icon-ag-minus-circle-shape" @click="delRow(index)" />
            </div>
            <div class="edit-status" v-show="row.isEdit">
              <bk-button
                text
                theme="primary"
                class="mr10"
                @click="confirmRowEdit(index)"
              >
                {{ t('确定') }}
              </bk-button>
              <bk-button
                text
                theme="primary"
                @click="cancelRowEdit(index)"
              >
                {{ t('取消') }}
              </bk-button>
            </div>

          </template>

        </bk-table-column>
      </bk-table>
    </bk-loading>

    <!-- <div class="tips">
      <i class="apigateway-icon icon-ag-info"></i>
      {{ t('变量名由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符') }}
    </div> -->

    <div class="footer-btn" v-show="tableIsEdit">
      <bk-button
        theme="primary"
        @click="handleSave"
      >
        {{ t('保存') }}
      </bk-button>
      <bk-button @click="cancelTableEdit" v-bk-tooltips="{ content: '取消编辑' }">
        {{ t('取消') }}
      </bk-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { EditLine } from 'bkui-vue/lib/icon';
import { useI18n } from 'vue-i18n';
import { getStageVars, updateStageVars } from '@/http';
import { useCommon } from '@/store';
import { Message, InfoBox } from 'bkui-vue';

const common = useCommon();
const { t } = useI18n();

const props = defineProps({
  stageId: Number,
});

const tableIsEdit = ref<boolean>(false);
const isShowVarPopover = ref(false);
const getVars = () => {
  return {
    name: '',
    value: '',
    // sourceNumber: 0,
    isEdit: true,
  };
};

const isLoading = ref<boolean>(false);
const tableData = ref<any>([]);

const getCellClass = (payload: any) => {
  if (payload.index !== 2) {
    return 'custom-table-cell';
  }
  return '';
};

const getData = async () => {
  if (!common.apigwId || !props.stageId) return;

  try {
    const res = await getStageVars(common.apigwId, props.stageId);
    const list: any = [];
    for (const key of Object.keys(res?.vars)) {
      list.push({
        name: key,
        value: res?.vars[key],
        isEdit: false,
      });
    };
    tableData.value = list;
  } catch (e) {
    console.error(e);
  };
};

onMounted(() => {
  getData();
});

const formRefs = ref(new Map());
const setRefs = (el: any, name: string) => {
  if (el) {
    formRefs.value?.set(name, el);
  }
};

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
        if (alikeArr?.length > 1) {
          return false;
        }
        return true;
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

const validateName = async (index: number) => {
  let flag = true;
  await formRefs.value?.get(`name-${index}`)?.validate()
    .then(() => {}, () => { // 校验不通过
      flag = false;
    });
  await formRefs.value?.get(`value-${index}`)?.validate()
    .then(() => {}, () => { // 校验不通过
      flag = false;
    });

  return flag;
};

const confirmRowEdit = async (index: number) => {
  if (await validateName(index)) {
    tableData.value[index].isEdit = false;
  };
};

const cancelRowEdit = async (index: number) => {
  // if (!tableData.value[index]?.name) {
  //   tableData.value?.splice(index, 1);
  //   return;
  // }
  // if (await validateName(index)) {
  //   tableData.value[index].isEdit = false;
  // }
  tableData.value?.splice(index, 1);
};

const editTable = () => {
  tableIsEdit.value = true;
  tableData.value?.forEach((row: any) => {
    row.isEdit = true;
  });
  if (tableData.value?.length === 0) {
    tableData.value?.push(getVars());
  }
};

const cancelTableEdit = () => {
  getData();
  tableIsEdit.value = false;
  // tableData.value?.forEach((row: any) => {
  //   row.isEdit = false;
  // });
};

const addRow = (index: number) => {
  tableData.value?.splice(index + 1, 0, getVars());
};

const delRow = (index: number) => {
  tableData.value?.splice(index, 1);
};

const handleSave = () => {
  InfoBox({
    infoType: 'warning',
    title: t('确认修改变量配置？'),
    subTitle: t('将会立即应用在环境上，请谨慎操作！'),
    confirmText: t('确认修改'),
    cancelText: t('取消'),
    onConfirm: async () => {
      try {
        let flag = true;
        for (let i = 0; i < tableData.value?.length; i++) {
          if (!(await validateName(i))) {
            flag = false;
            break;
          }
        }
        if (!flag) return;

        const data: any = {};
        tableData.value?.forEach((item: any) => {
          data[item.name] = item.value;
        });

        await updateStageVars(common.apigwId, props.stageId, { vars: data });
        Message({
          theme: 'success',
          message: t('更新成功'),
        });
        getData();
        tableIsEdit.value = false;
      } catch (e) {
        console.error(e);
      };
    },
  });
};

watch(
  () => props.stageId,
  (v) => {
    if (v) {
      getData();
    }
  },
);

</script>

<style lang="scss" scoped>
.title {
  display: flex;
  align-items: center;
  .title-name {
    font-weight: 700;
    font-size: 14px;
    color: #313238;
  }
  .title-tips {
    font-size: 14px;
    color: #979BA5;
    font-weight: normal;
  }
  .title-edit {
    color: #3A84FF;
    font-size: 18px;
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
  // .bk-form-error-tips {
  //   display: none;
  // }
  .bk-table-body-content {
    .custom-table-cell {
      // height: 42px;
      // line-height: 42px;
      .cell {
        padding: 0;
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
                &.is-focused {
                  border: 1px solid #3A84FF;
                }
                &--text {
                  padding: 0 16px;
                }
              }
            }
          }
        }
      }
    }
  }
}
</style>
