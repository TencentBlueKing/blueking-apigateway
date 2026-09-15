<template>
  <div class="config-display-table-wrapper">
    <table class="config-display-table">
      <thead>
        <tr>
          <th
            v-for="(col, index) in columns"
            :key="index"
            :style="index === 0 ? { width: firstColWidth, minWidth: firstColWidth } : undefined"
            :rowspan="col.rowspan"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in data"
          :key="row.key"
        >
          <td
            v-for="(col, index) in columns"
            :key="index"
            :style="index === 0 ? { width: firstColWidth, minWidth: firstColWidth } : undefined"
            :rowspan="row.rowspan"
          >
            {{ renderValue(row, col) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { IBaseTableRow, IColumn } from './types';

interface IProps {
  columns: any[]
  data: any[]
}

const { columns, data } = defineProps<IProps>();

// auto 使用统一的基础列宽，长字段仍可通过自动表格布局撑宽第一列。
const firstColWidth = computed(() => {
  const width = columns[0]?.width;
  if (width === undefined || width === 'auto') {
    return '200px';
  }
  return typeof width === 'number' || /^\d+(\.\d+)?$/.test(width) ? `${width}px` : width;
});

const renderValue = (row: IBaseTableRow, col: IColumn) => {
  // @ts-ignore
  const rowField = row[col.field]?.valueRender?.({ row }) || row[col.field];
  if (['boolean', 'number'].includes(typeof rowField)) {
    return String(rowField);
  }
  return rowField || '--';
};

</script>

<style scoped lang="scss">
.config-display-table-wrapper {
  min-width: 0;
  overflow-x: auto;
}

.config-display-table {
  width: 100%;
  font-size: 12px;
  border: 1px solid #dcdee5;
  border-collapse: collapse;
  table-layout: auto;

  tr {
    height: 40px;

    th {
      font-weight: normal;
      color: #313238;
      text-align: left;
      background-color: #fafbfd;
    }

    th:first-of-type, td:first-child {
      text-align: right;
      white-space: nowrap;
      background-color: #fafbfd;
    }

    th, td {
      padding: 0 16px;
      border: 1px solid #dcdee5;
      box-sizing: border-box;
      overflow-wrap: anywhere;
    }

    td {
      color: #63656E;
    }
  }
}
</style>
