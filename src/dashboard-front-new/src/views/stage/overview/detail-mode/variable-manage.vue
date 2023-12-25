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
        border="outer"
      >
        <bk-table-column :label="t('变量名称')" prop="name">
          <template #default="{ row }">
            <span v-show="!row.isEdit">{{ row?.name }}</span>
            <bk-input
              v-model="row.name"
              clearable
              v-show="row.isEdit"
              maxlength="50"
            />
          </template>
        </bk-table-column>
        <bk-table-column :label="t('变量值')" prop="value">
          <template #default="{ row }">
            <span v-show="!row.isEdit">{{ row?.value }}</span>
            <bk-input
              v-model="row.value"
              clearable
              v-show="row.isEdit"
            />
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
          width="100px"
          align="center"
        >
          <template #default="{ row, index }">
            <div class="normal-status" v-show="!row.isEdit">
              <i class="apigateway-icon icon-ag-plus-circle mr10" @click="addRow(index)" />
              <i class="apigateway-icon icon-ag-minus-circle" @click="delRow(index)" />
            </div>
            <div class="edit-status" v-show="row.isEdit">
              <bk-button
                text
                theme="primary"
                class="mr10"
                @click="confirmRowEdit(index)"
              >
                确定
              </bk-button>
              <bk-button
                text
                theme="primary"
                @click="cancelRowEdit(index)"
              >
                取消
              </bk-button>
            </div>

          </template>

        </bk-table-column>
      </bk-table>
    </bk-loading>

    <div class="tips">
      <i class="apigateway-icon icon-ag-info"></i>
      {{ t('变量名由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符') }}
    </div>

    <div class="footer-btn">
      <bk-button
        theme="primary"
        @click="handleSave"
      >
        保存
      </bk-button>
      <bk-button class="ml10" @click="cancelTableEdit">
        取消
      </bk-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { EditLine } from 'bkui-vue/lib/icon';
import { useI18n } from 'vue-i18n';
import { getStageVars, updateStageVars } from '@/http';
import { useCommon } from '@/store';
import { Message } from 'bkui-vue';

const common = useCommon();
const { t } = useI18n();

const props = defineProps({
  stageId: Number,
});

const tableIsEdit = ref<boolean>(false);

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

const getData = async () => {
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

const validateName = (name: string) => {
  if (!name) {
    Message({
      theme: 'error',
      message: '请填写变量名',
    });
    return false;
  }

  const reg = new RegExp(/^[a-zA-Z][a-zA-Z0-9_]{0,49}$/);
  if (!reg.test(name)) {
    Message({
      theme: 'error',
      message: '变量名由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符',
    });
    return false;
  }

  // 去重
  const alikeArr: any = tableData.value?.filter((item: any) => item.name === name);
  if (alikeArr?.length > 1) {
    Message({
      theme: 'error',
      message: '变量名不能重复',
    });
    return false;
  }

  return true;
};

const confirmRowEdit = (index: number) => {
  if (validateName(tableData.value[index].name)) {
    tableData.value[index].isEdit = false;
  };
};

const cancelRowEdit = (index: number) => {
  if (!tableData.value[index]?.name) {
    tableData.value?.splice(index, 1);
    return;
  }
  if (validateName(tableData.value[index]?.name)) {
    tableData.value[index].isEdit = false;
  }
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
  tableIsEdit.value = false;
  tableData.value?.forEach((row: any) => {
    row.isEdit = false;
  });
};

const addRow = (index: number) => {
  tableData.value?.splice(index + 1, 0, getVars());
};

const delRow = (index: number) => {
  tableData.value?.splice(index, 1);
};

const handleSave = async () => {
  try {
    const flag = tableData.value?.find((item: any) => !validateName(item.name));
    if (flag) return;

    const data: any = {};
    tableData.value?.forEach((item: any) => {
      if (!item.isEdit) {
        data[item.name] = item.value;
      }
    });

    await updateStageVars(common.apigwId, props.stageId, { vars: data });
    Message({
      theme: 'success',
      message: t('更新成功'),
    });
    getData();
  } catch (e) {
    console.error(e);
  };
};

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
}

.normal-status {
  .apigateway-icon {
    font-size: 16px;
    cursor: pointer;
  }
}
</style>
