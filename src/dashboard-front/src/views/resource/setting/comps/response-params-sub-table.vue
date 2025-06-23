<template>
  <div>
    <table v-for="row in tableData" :key="row.id" class="response-table">
      <tbody class="table-body">
        <tr class="table-body-row">
          <td class="table-body-row-cell arrow-col">
            <AgIcon name="right-shape" />
          </td>
          <!-- 字段名 -->
          <td class="table-body-row-cell name-col">
            <bk-input v-model="row.name" :placeholder="t('字段名')" />
          </td>
          <!-- 字段类型 -->
          <td class="table-body-row-cell type">
            <bk-select
              v-model="row.type"
              :clearable="false"
              :filterable="false"
              @change="() => handleTypeChange(row)"
            >
              <bk-option
                v-for="item in typeList"
                :id="item.value"
                :key="item.value"
                :name="item.label"
              />
            </bk-select>
          </td>
          <!-- 字段备注 -->
          <td class="table-body-row-cell description">
            <bk-input v-model="row.description" :placeholder="t('备注')" />
          </td>
          <!-- 字段操作 -->
          <td class="table-body-row-cell actions">
            <AgIcon
              v-if="row.type === 'object'"
              v-bk-tooltips="t('添加字段')"
              class="tb-btn add-btn"
              name="plus-circle-shape"
              @click="() => addField(row)"
            />
            <AgIcon
              v-bk-tooltips="t('删除字段')"
              class="tb-btn delete-btn"
              name="minus-circle-shape"
              @click="() => removeField(row)"
            />
          </td>
        </tr>
      </tbody>
      <tfoot v-if="row?.properties?.length">
        <tr>
          <td colspan="5" style="padding-left: 16px;">
            <ResponseParamsSubTable v-model="row.properties" />
          </td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script lang="ts" setup>
import {
  onMounted,
  ref,
} from 'vue';
import { useI18n } from 'vue-i18n';
import AgIcon from '@/components/ag-icon.vue';
import _ from 'lodash';
import { JSONSchema7TypeName } from 'json-schema';

interface ITableRow {
  id: string;
  name: string;
  type: JSONSchema7TypeName;
  description: string;
  properties?: ITableRow[];
}

const tableData = defineModel<ITableRow[]>();

const { t } = useI18n();

const tableRef = ref();


const typeList = ref([
  {
    label: 'String',
    value: 'string',
  },
  {
    label: 'Number',
    value: 'number',
  },
  {
    label: 'Boolean',
    value: 'boolean',
  },
  {
    label: 'Array',
    value: 'array',
  },
  {
    label: 'Object',
    value: 'object',
  },
]);

const genRow = () => {
  return {
    id: _.uniqueId(),
    name: '',
    type: 'string' as JSONSchema7TypeName,
    description: '',
  };
};

const addField = (row: ITableRow) => {
  const targetRow = tableData.value.find(data => data.id === row.id);
  if (targetRow) {
    if (targetRow.properties) {
      targetRow.properties.push(genRow());
    } else {
      targetRow.properties = [genRow()];
    }
  }
};

const removeField = (row: ITableRow) => {
  const index = tableData.value.findIndex(data => data.id === row.id);
  if (index !== -1) {
    tableData.value.splice(index, 1);
  }
};

const handleTypeChange = (row: ITableRow) => {
  const targetRow = tableData.value.find(data => data.id === row.id);
  if (targetRow) {
    if (row.type === 'object') {
      targetRow.properties = [genRow()];
    } else {
      targetRow.properties = [];
    }
  }
};

onMounted(() => {
  tableRef.value?.setAllRowExpand(true);
});
</script>

<style lang="scss" scoped>

.response-table {
  border-collapse: collapse;
  border-spacing: 0;

  .table-body-row-cell {
    height: 42px;
    font-size: 12px;

    &.arrow-col {
      border-right: none;
    }

    &.name-col {
      border-left: none;
    }
  }

  .table-body {
    .table-body-row {
      .table-body-row-cell {

        &:first-child {
          width: 32px;
          text-align: center;
        }

        &.type {
          width: 100px;
        }

        &.description {
          width: 120px;
        }

        &.actions {
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

        :deep(.bk-input):hover {
          border: 1px solid #a3c5fd;
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
        }
      }
    }
  }
}

</style>
