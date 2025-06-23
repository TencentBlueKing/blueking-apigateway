<template>
  <div>
    <table v-for="row in tableData" :key="row.id" class="request-body-table">
      <tbody class="table-body">
        <tr class="table-body-row">
          <td class="table-body-row-cell">
            <AgIcon name="right-shape" />
          </td>
          <!-- 字段名 -->
          <td class="table-body-row-cell">
            <bk-input v-model="row.name" :placeholder="t('字段名')" />
          </td>
          <!-- 字段类型 -->
          <td class="table-body-row-cell type">
            <bk-select
              v-model="row.type"
              :clearable="false"
              :filterable="false"
            >
              <bk-option
                v-for="item in typeList"
                :id="item.value"
                :key="item.value"
                :name="item.label"
              />
            </bk-select>
          </td>
          <!-- 字段必填 -->
          <td class="table-body-row-cell required">
            <BkSwitcher
              v-model="row.required"
              :off-text="t('必填')"
              :on-text="t('必填')"
              show-text
              size="small"
              theme="primary"
            />
          </td>
          <!-- 字段默认值 -->
          <td class="table-body-row-cell">
            <bk-input v-model="row.default" :placeholder="t('默认值')" />
          </td>
          <!-- 字段备注 -->
          <td class="table-body-row-cell">
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
      <tfoot v-if="row?.body?.length">
        <tr>
          <td colspan="7" style="padding-left: 16px;">
            <RequestParamsTable v-model="row.body" />
          </td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import AgIcon from '@/components/ag-icon.vue';
import _ from 'lodash';

const tableData = defineModel<IBodyRow[]>();

const { t } = useI18n();

interface IBodyRow {
  id: string,
  name: string,
  type: string,
  required: boolean,
  default: string,
  description: string,
  isEdit: boolean,
  body?: IBodyRow[],
}

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

const genBodyRow = (id?: string) => {
  return {
    id: id || _.uniqueId(),
    name: '',
    type: 'string',
    required: false,
    default: '',
    description: '',
    isEdit: true,
  };
};

const addField = (row: IBodyRow) => {
  const bodyRow = tableData.value.find(data => data.id === row.id);
  if (bodyRow) {
    if (bodyRow.body) {
      bodyRow.body.push(genBodyRow());
    } else {
      bodyRow.body = [genBodyRow()];
    }
  }
};

const removeField = (row: IBodyRow) => {
  const index = tableData.value.findIndex(data => data.id === row.id);
  if (index !== -1) {
    tableData.value.splice(index, 1);
  }
};
</script>

<style lang="scss" scoped>

.request-body-table {
  border-collapse: collapse;
  border-spacing: 0;

  .table-body {
    .table-body-row {
      .table-body-row-cell {
        height: 42px;

        &:first-child {
          width: 32px;
          text-align: center;
        }

        &.type {
          width: 100px;
        }

        &.required {
          width: 100px;
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
