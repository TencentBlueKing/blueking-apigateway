<template>
  <table class="config-display-table">
    <thead>
      <tr>
        <th
          v-for="(col, index) in columns"
          :key="index"
          :style="{width: index === 0 ? `${col.width}px` : 'auto'}"
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
          :style="{width: index === 0 ? `${col.width}px` : 'auto', backgroundColor: index === 0 ? '#fafbfd' : ''}"
          :rowspan="row.rowspan"
        >
          {{ renderValue(row, col) }}
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import type { IBaseTableRow, IColumn } from './types';

interface IProps {
  columns: any[]
  data: any[]
}

const { columns, data } = defineProps<IProps>();

const renderValue = (row: IBaseTableRow, col: IColumn) => {
  const rowField = row[col.field]?.valueRender?.({ row }) || row[col.field];
  if (['boolean', 'number'].includes(typeof rowField)) {
    return String(rowField);
  }
  return rowField || '--';
};

</script>

<style scoped lang="scss">
.config-display-table {
  width: 100%;
  font-size: 12px;
  border: 1px solid #dcdee5;
  border-collapse: collapse;

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
    }

    th, td {
      padding: 0 16px;
      border: 1px solid #dcdee5;
    }

    td {
      color: #63656E;
    }
  }
}
</style>
