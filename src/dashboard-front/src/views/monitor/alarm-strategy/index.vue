<template>
  <div class="page-wrapper-padding alarm-strategy-container">
    <div class="header flex-row justify-content-between mb24">
      <div class="header-btn flex-row ">
        <span class="mr10">
          <bk-button theme="primary" class="mr5 w80" @click="handleAdd">
            {{ t('新建') }}
          </bk-button>
        </span>
      </div>
      <div class="header-search">
        <bk-input class="search-input w300" :placeholder="t('请输入告警策略名称，按Enter搜索')" v-model="filterData.keyword" />
      </div>
    </div>
    <div class="alarm-strategy-content">
      <bk-loading :loading="isLoading">
        <bk-table
          class="alarm-strategy-table" :data="tableData" remote-pagination :pagination="pagination"
          @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange" row-hover="auto">
          <bk-table-column :label="t('告警策略名称')" prop="name" width="150"></bk-table-column>
          <bk-table-column :label="t('标签')" prop="gateway_labels">
            <template #default="{ data }">
              <template v-if="data?.gateway_labels.length">
                <div class="pt10 label-box" v-bk-tooltips.top="labelTooltip(data?.gateway_labels)">
                  <template v-for="(label, index) of data?.gateway_labels">
                    <span class="ag-label  mb5" v-if="index < 4" :key="index">
                      {{ label.name }}
                    </span>
                  </template>
                  <template v-if="data?.gateway_labels.length > 4">
                    <span class="ag-label mb5">
                      ...
                    </span>
                  </template>
                </div>
              </template>
              <template v-else>
                --
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('是否启用')" width="150">
            <template #default="{ row }">
              <bk-switcher
                v-model="row.enabled"
                :true-value="true"
                :false-value="false"
                theme="primary"
                :disabled="statusSwitcherDisabled"
                @change="handleIsEnable(row)">
              </bk-switcher>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('更新时间')" prop="updated_time" width="230"></bk-table-column>
          <bk-table-column :label="t('操作')" width="150">
            <template #default="{ data }">
              <bk-button class="mr25" theme="primary" text @click="handleEdit(data)">
                {{ t('编辑') }}
              </bk-button>
              <bk-button theme="primary" text @click="handleDelete(data)">
                {{ t('删除') }}
              </bk-button>
            </template>
          </bk-table-column>
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </bk-table>
      </bk-loading>
    </div>
  </div>

  <!-- 新建/编辑sideslider -->
  <bk-sideslider
    ext-cls="alarm-strategy-slider" v-model:isShow="sidesliderConfig.isShow" :title="sidesliderConfig.title"
    width="750">
    <template #default>
      <div class="strategy-form p30">
        <bk-form ref="strategyFormRef" :label-width="160" :model="formData">
          <div class="form-bd">
            <dl class="form-content">
              <div class="content-panel single">
                <bk-form-item
                  class="mb0"
                  :label="t('告警策略名称')" :required="true" :rules="rules.name" :property="'name'"
                  :error-display-type="'normal'">
                  <bk-input :placeholder="t('请输入')" :maxlength="128" v-model="formData.name"></bk-input>
                </bk-form-item>
              </div>
              <div class="content-panel">
                <dt class="panel-title"> {{ t('触发条件') }} </dt>
                <dd class="panel-content">
                  <bk-form-item
                    class="mb20"
                    :label="t('告警规则')" :required="true" :rules="rules.alarm_subtype"
                    :property="'alarm_subtype'" :error-display-type="'normal'">
                    <bk-select :clearable="false" v-model="formData.alarm_subtype">
                      <bk-option
                        v-for="option in alarmStrategyOptions.alarmSubType" :key="option.value"
                        :value="option.value" :label="option.name">
                      </bk-option>
                    </bk-select>
                  </bk-form-item>
                  <bk-form-item :label="t('告警范围')" class="mb20">
                    <div class="flex-group">
                      <span class="item label"> {{ t('资源标签包含') }} </span>
                      <span class="item w328 flex-none">
                        <bk-select v-model="formData.gateway_label_ids" filterable multiple :input-search="false">
                          <bk-option
                            v-for="option in labelList" :key="option.id" :value="option.id" :label="option.name">
                          </bk-option>
                        </bk-select>
                      </span>
                    </div>
                  </bk-form-item>
                  <bk-form-item :label="t('检测算法')" class="mb20">
                    <div class="flex-groups">
                      <div class="flex-group flex-2">
                        <span class="item">
                          <bk-select
                            disabled :clearable="false" :popover-min-width="120"
                            v-model="formData.config.detect_config.duration">
                            <bk-option
                              v-for="option in alarmStrategyOptions.detectConfig.duration" :key="option.value"
                              :value="option.value" :label="option.name">
                            </bk-option>
                          </bk-select>
                        </span>
                        <span class="item label"> {{ t('内命中规则次数') }} </span>
                        <span class="item flex-none w70">
                          <bk-select disabled :clearable="false" v-model="formData.config.detect_config.method">
                            <bk-option
                              v-for="option in alarmStrategyOptions.detectConfig.method" :key="option.value"
                              :value="option.value" :label="option.name">
                            </bk-option>
                          </bk-select>
                        </span>
                      </div>
                      <div class="flex-group flex-1">
                        <span class="item">
                          <bk-input
                            disabled :placeholder="t('请输入')" type="number" :min="0"
                            v-model="formData.config.detect_config.count">
                          </bk-input>
                        </span>
                        <span class="item label"> {{ t('时触发') }} </span>
                      </div>
                    </div>
                  </bk-form-item>
                  <bk-form-item :label="t('告警收敛')" class="mb0">
                    <div class="flex-group">
                      <span class="item label"> {{ t('告警产生后') }}， </span>
                      <span class="item flex-0-0 w122">
                        <bk-select disabled :clearable="false" v-model="formData.config.converge_config.duration">
                          <bk-option
                            v-for="option in alarmStrategyOptions.convergeConfig.duration" :key="option.value"
                            :value="option.value" :label="option.name">
                          </bk-option>
                        </bk-select>
                      </span>
                      <span class="item label flex-1-1"> {{ t('内不再发送告警') }} </span>
                    </div>
                  </bk-form-item>
                </dd>
              </div>
              <div class="content-panel">
                <dt class="panel-title"> {{ t('通知方式') }} </dt>
                <dd class="panel-content">
                  <bk-form-item :label="t('通知方式')" :required="true">
                    <bk-checkbox-group v-model="formData.config.notice_config.notice_way" class="checkbox-group">
                      <bk-checkbox :label="'wechat'">
                        <span class="icon apigateway-icon icon-ag-wechat-color"></span>
                        {{ t('微信') }}
                      </bk-checkbox>
                      <bk-checkbox :label="'im'">
                        <span class="icon apigateway-icon icon-ag-qw"></span>
                        {{ t('企业微信') }}
                      </bk-checkbox>
                      <bk-checkbox :label="'mail'">
                        <span class="icon apigateway-icon icon-ag-email-color"></span>
                        {{ t('邮箱') }}
                      </bk-checkbox>
                    </bk-checkbox-group>
                  </bk-form-item>
                  <bk-form-item :label="t('通知对象')">
                    <bk-checkbox-group v-model="formData.config.notice_config.notice_role" class="checkbox-group">
                      <bk-checkbox :label="'maintainer'"> {{ t('网关维护者') }} </bk-checkbox>
                    </bk-checkbox-group>
                  </bk-form-item>
                  <bk-form-item :label="t('其他通知对象')" class="mb0">
                    <!-- <bk-input
                      :placeholder="t('请输入用户')"
                      :maxlength="128"
                      v-model="formData.config.notice_config.notice_extra_receiver">
                    </bk-input> -->
                    <bk-tag-input
                      v-model="formData.config.notice_config.notice_extra_receiver" :placeholder="t('请输入用户')"
                      allow-create has-delete-icon collapse-tags />
                    <p class="ag-tip mt5">
                      <i class="apigateway-icon icon-ag-info"></i> {{ t('通知对象、其他通知对象至少一个有效') }}
                    </p>
                  </bk-form-item>
                </dd>
              </div>
            </dl>
          </div>
          <div class="form-ft">
            <bk-button theme="primary" class="mr10" :loading="isSaveLoading" @click="handleSave"> {{ t('保存') }}
            </bk-button>
            <bk-button @click="handleCancel"> {{ t('取消') }} </bk-button>
          </div>
        </bk-form>
      </div>

    </template>
  </bk-sideslider>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon, useAccessLog } from '@/store';
import { InfoBox, Message } from 'bkui-vue';
import { useQueryList } from '@/hooks';
import {
  getGatewayLabels,
  getStrategyList,
  getStrategyDetail,
  deleteStrategy,
  createStrategy,
  updateStrategy,
  updateStrategyStatus,
} from '@/http';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const common = useCommon();
const accessLog = useAccessLog();
const { apigwId } = common; // 网关id
const { alarmStrategyOptions } = accessLog; // 触发条件的option
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});
const filterData = ref({ keyword: '' });
const curOperate = ref<string>('add');
const statusSwitcherDisabled = ref<boolean>(false);
const isSaveLoading = ref<boolean>(false);
const strategyFormRef = ref(null);
const curStrategyId = ref<number>(-1);
const labelList = ref([]);
const sidesliderConfig = reactive({
  isShow: false,
  title: '',
});
// 新建初始数据
const formData = ref({
  name: '',
  alarm_type: 'resource_backend',
  alarm_subtype: '',
  gateway_label_ids: [],
  config: {
    detect_config: {
      duration: 300,
      method: 'gte',
      count: 3,
    },
    converge_config: {
      duration: 86400,
    },
    notice_config: {
      notice_way: ['wechat', 'im'],
      notice_role: ['maintainer'],
      notice_extra_receiver: [],
    },
  },

});
const rules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  alarm_subtype: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
};

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getStrategyList, filterData);

// table 标签的tooltip
const labelTooltip = computed(() => {
  return function (labels: any) {
    const labelNameList = labels.map((item: any) => {
      return item.name;
    });
    return labelNameList.join('; ');
  };
});

// 新建
const handleAdd = () => {
  curOperate.value = 'add';
  sidesliderConfig.isShow = true;
  sidesliderConfig.title = t('新建告警策略');
  formData.value = {
    name: '',
    alarm_type: 'resource_backend',
    alarm_subtype: '',
    gateway_label_ids: [],
    config: {
      detect_config: {
        duration: 300,
        method: 'gte',
        count: 3,
      },
      converge_config: {
        duration: 86400,
      },
      notice_config: {
        notice_way: ['wechat', 'im'],
        notice_role: ['maintainer'],
        notice_extra_receiver: [],
      },
    },
  };
};

// 是否启用
const handleIsEnable = async (item: any) => {
  const { enabled, id } = item;
  try {
    await updateStrategyStatus(apigwId, id, { enabled });
    Message({
      message: enabled ? t('启用成功') : t('禁用成功'),
      theme: 'success',
    });
    getList();
  } catch (error) {
    console.log('error', error);
  }
};

// 编辑
const handleEdit = async (data: any) => {
  console.log(data);
  curOperate.value = 'edit';
  sidesliderConfig.isShow = true;
  sidesliderConfig.title = t('编辑告警策略');
  try {
    const res = await getStrategyDetail(apigwId, data.id);
    curStrategyId.value = res.id;
    formData.value = res;
    console.log(formData.value);
  } catch (error) {
    console.log('error', error);
  }
};

// 删除
const handleDelete = (item: any) => {
  console.log(item);
  InfoBox({
    title: t(`确定要删除告警策略【${item.name}】?`),
    infoType: 'warning',
    subTitle: t('策略删除后，将不再接收相关通知'),
    onConfirm: async () => {
      try {
        await deleteStrategy(apigwId, item.id);
        Message({
          message: t('删除成功'),
          theme: 'success',
        });
        getList();
      } catch (error) {
        console.log('error', error);
      }
    },
  });
};

// 保存
const handleSave = async () => {
  console.log(formData.value);
  const isAdd = curOperate.value === 'add';
  await strategyFormRef.value.validate();
  isSaveLoading.value = true;
  try {
    if (isAdd) {
      await createStrategy(apigwId, formData.value);
    } else {
      await updateStrategy(apigwId, curStrategyId.value, formData.value);
    }
    Message({
      message: isAdd ? t('新建成功') : t('编辑成功'),
      theme: 'success',
    });
    getList();
    sidesliderConfig.isShow = false;
  } catch (error) {
    console.log('error', error);
  } finally {
    isSaveLoading.value = false;
  }
};

// 取消
const handleCancel = () => {
  sidesliderConfig.isShow = false;
};

const init = async () => {
  try {
    labelList.value = await getGatewayLabels(apigwId);
    console.log(labelList.value);
  } catch (error) {
    console.log('error', error);
  }
};
init();

const handleClearFilterKey = () => {
  filterData.value = { keyword: '' };
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = {
    ...filterData.value,
  };
  const list = Object.values(searchParams).filter(item => item !== '');
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (list.length && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

watch(
  () => tableData.value, () => {
    updateTableEmptyConfig();
  },
  {
    deep: true,
  },
);
</script>

<style lang="scss" scoped>
.flex-0-0{
  flex:0 0 auto !important;
}
.flex-1-1{
  flex:1 1 0% !important;
}
.mb0{
  margin-bottom: 0px !important;
}
.w70{
  width: 70px;
}
.w80 {
  width: 80px
}

.w88 {
  width: 88px;
}
.w122{
  width: 122px;
}
.w300 {
  width: 300px
}
.w328{
  width: 328px;
}
.mb24{
  margin-bottom: 24px;
}
:deep(.alarm-strategy-table) {
  .bk-table-body {
    table {
      tbody {
        tr {
          td {
            .cell {
              height: auto !important;
              line-height: normal;
            }
          }
        }
      }

    }
  }
}

.strategy-form {
  .form-content {
    .content-panel {
      overflow: hidden;
      border: 1px solid #DCDEE5;
      margin-bottom: 16px;
      border-radius: 2px;

      &.single {
        border: none;

        :deep(.bk-form-item) {
          .bk-form-label {
            height: 40px;
            line-height: 40px;
            font-size: 14px;
            font-weight: 700;
            border: 1px solid #DCDEE5;
            border-right: none;
            background: #FAFBFD;
          }

          .bk-input {
            height: 40px;
            line-height: 40px;
            border-bottom-left-radius: unset;
            border-top-left-radius: unset;
          }

          .tooltips-icon {
            top: 11px;
          }
        }
      }

      .panel-title {
        height: 40px;
        line-height: 40px;
        padding-left: 20px;
        font-size: 14px;
        font-weight: 700;
        color: #63656E;
        background: #FAFBFD;
      }

      :deep(.panel-content) {
        padding: 30px 90px 30px 0;
        border-top: 1px solid #DCDEE5;

        .bk-form-item {
          .bk-form-content {
            line-height: 30px;
          }
        }
      }
    }
  }
}

.flex-group {
  display: flex;

  .item {
    flex: 1;

    &.label {
      flex: none;
      font-size: 14px;
      color: #313238;
      padding: 0 12px;
      border: 1px solid #C4C6CC;
      background: #FAFBFD;
    }

    &+.item {
      margin-left: -1px;
    }
  }
}

.flex-groups {
  display: flex;

  .flex-group {
    &+.flex-group {
      margin-left: 8px;
    }
  }
}

.checkbox-group {
  .bk-checkbox {
    min-width: 122px;

    .apigateway-icon {
      margin-right: 4px;
    }
  }
}

.attention-dialog {
  width: 400px;

  :deep(.bk-dialog-header) {
    padding: 5px !important;
  }

  :deep(.bk-modal-footer) {
    background-color: #fff;
    border-top: none;
  }

  .title {
    font-size: 20px;
    text-align: center;
    color: #313238;
  }

  .sub-title {
    font-size: 14px;
    color: #63656e;
    line-height: 1.5;
    text-align: center;
    margin-bottom: 21px;
    margin-top: 14px;
  }

  .btn {
    text-align: center;
  }
}
.label-box{
  display: inline-block;
}
.ag-label {
  height: 24px;
  line-height: 22px;
  border: 1px solid #DCDEE5;
  text-align: center;
  padding: 0 10px;
  max-width: 90px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: normal;
  display: inline-block;
  margin-right: 4px;
  border-radius: 2px;
  white-space: nowrap;
}
:deep(.alarm-strategy-content){
  .bk-exception{
    height: 280px;
    max-height: 280px;
    justify-content: center;
  }
}
</style>


