<template>
  <div class="tab-content function-overview">
    <div class="tab-description">
      {{ t('覆盖蓝鲸生态核心系统，一个 CLI 工具打通所有能力。') }}
    </div>

    <table class="overview-table">
      <thead>
        <tr>
          <th>{{ t('蓝鲸服务') }}</th>
          <th>{{ t('能力描述') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in overviewList"
          :key="item.service"
        >
          <td>{{ item.service }}</td>
          <td>{{ item.title }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { useEnv } from '@/stores';

const { t } = useI18n();
const envStore = useEnv();

const overviewList = computed(() => envStore.env.CLI.OVERVIEW ?? []);

</script>

<style scoped lang="scss">
.function-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .tab-description {
    font-size: 12px;
    line-height: 20px;
    color: #4d4f56;
  }

  .overview-table {
    width: 100%;
    border: 1px solid #dcdee5;
    border-collapse: collapse;

    th,
    td {
      padding: 12px 24px;
      font-size: 12px;
      line-height: 20px;
      text-align: left;
      border-bottom: 1px solid #dcdee5;
    }

    th {
      font-weight: 700;
      color: #313238;
      background: #fafbfd;
    }

    td {
      color: #63656e;
    }

    td:first-child {
      width: 200px;
    }

    tbody tr:last-child td {
      border-bottom: none;
    }

    tbody tr:hover {
      background: #f5f7fa;
    }
  }
}
</style>
