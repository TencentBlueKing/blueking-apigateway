<template>
  <div class="tab-content function-overview">
    <!-- 功能概览标题区 -->
    <div class="overview-header">
      <div class="overview-icon">
        <AgIcon
          name="log-rizhi"
          size="24"
          color="#3A84FF"
        />
      </div>
      <div class="overview-info">
        <div class="overview-title">
          {{ t('功能概览') }}
        </div>
        <div class="overview-desc">
          {{ t('覆盖蓝鲸生态核心系统，一个 CLI 工具打通所有能力。') }}
        </div>
      </div>
    </div>

    <!-- 功能表格 -->
    <div class="overview-table-wrapper">
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
  </div>
</template>

<script setup lang="ts">

const { t } = useI18n();

const overviewList = [
  {
    service: t('API 网关'),
    title: t('发现所有网关及接口，查询日志'),
  },
  {
    service: t('配置平台'),
    title: t('主机管理、业务拓扑、集群模块、动态分组、属性管理、关联查询'),
  },
  {
    service: t('作业平台'),
    title: t('脚本执行、文件分发、作业模板、定时任务、执行历史查询'),
  },
  // {
  //   service: t('监控平台'),
  //   title: t('告警策略、告警事件、自定义指标、仪表盘、通知组管理'),
  // },
  // {
  //   service: t('日志平台'),
  //   title: t('日志检索、日志采集、索引管理、采集配置'),
  // },
  {
    service: t('标准运维'),
    title: t('流程模板、任务执行、任务查询、参数填充、周期任务'),
  },
  {
    service: t('节点管理'),
    title: t('Agent 安装、Agent 状态、插件管理、任务历史、云区域管理'),
  },
  // {
  //   service: t('容器服务'),
  //   title: t('集群管理、命名空间、工作负载、服务发现、配置管理'),
  // },
];

</script>

<style scoped lang="scss">

.function-overview {

  .overview-header {
    display: flex;
    padding: 18px 24px;
    background: #FAFBFD;
    align-items: flex-start;
    gap: 16px;
    border-bottom: 1px solid #DCDEE5;

    .overview-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      background: #fff;
      border-radius: 4px;
      flex-shrink: 0;
      box-shadow: 0 0 8px 0 #374a641a;
    }

    .overview-info {

      .overview-title {
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        color: #313238;
      }

      .overview-desc {
        margin-top: 4px;
        font-size: 12px;
        line-height: 20px;
        color: #979ba5;
      }
    }
  }

  .overview-table-wrapper {
    padding: 24px;

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
}

</style>
