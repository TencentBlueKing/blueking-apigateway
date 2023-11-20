<template>
  <div class="backend-service-container p20">
    <div class="header flex-row justify-content-between">
      <div class="header-btn flex-row ">
        <span class="mr10">
          <bk-button theme="primary" class="mr5 w80" @click="handleAdd">
            {{ t('新建') }}
          </bk-button>
        </span>
      </div>
      <div class="header-search">
        <bk-input class="search-input w500" :placeholder="t('请输入服务名称')" v-model="filterData.name"></bk-input>
      </div>
    </div>
    <div class="backend-service-content">
      <bk-loading :loading="isLoading">
        <bk-table
          class="table-layout" :data="tableData" remote-pagination :pagination="pagination" show-overflow-tooltip
          @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange" row-hover="auto">
          <!-- <bk-table-column type="selection" width="60" align="center"></bk-table-column> -->
          <bk-table-column :label="t('后端服务名称')" prop="name">
            <template #default="{ data }">
              <bk-button text theme="primary" @click="handleEdit(data)">
                {{ data?.name }}
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('描述')" prop="description">
            <template #default="{ data }">
              {{ data?.description || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('关联的资源')" prop="resource_count">
            <template #default="{ data }">
              <span v-if="data?.resource_count === 0">{{ data?.resource_count }}</span>
              <bk-button v-else text theme="primary" @click="handleResource(data)">
                {{ data?.resource_count }}
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('更新时间')" prop="updated_time"></bk-table-column>
          <bk-table-column :label="t('操作')" width="150">
            <template #default="{ data }">
              <bk-button class="mr25" theme="primary" text @click="handleEdit(data)">
                {{ t('编辑') }}
              </bk-button>
              <span
                v-bk-tooltips="{
                  content: t(`服务被${data?.resource_count}个资源引用了，不能删除`),
                  disabled: data?.resource_count === 0
                }">
                <bk-button theme="primary" text :disabled="data?.resource_count !== 0" @click="handleDelete(data)">
                  {{ t('删除') }}
                </bk-button>
              </span>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-loading>
    </div>
    <!-- 新建/编辑sideslider -->
    <bk-sideslider
      v-model:isShow="sidesliderConfi.isShow" :title="sidesliderConfi.title" :quick-close="false"
      ext-cls="backend-service-slider" width="800">
      <template #default>
        <div class="content p30">
          <div class="base-info mb20">
            <p class="title"><span class="icon apigateway-icon icon-ag-down-shape"></span>{{ t('基础信息') }}</p>
            <bk-form
              ref="baseInfoRef" class="base-info-form mt20" :model="baseInfo"
              form-type="vertical">
              <bk-form-item :label="t('服务名称')" property="name" required :rules="baseInfoRules.name">
                <bk-input
                  v-model="baseInfo.name" :placeholder="t('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头')"
                  :disabled="curOperate === 'edit'" />
                <p class="aler-text">{{ t('后端服务唯一标识，创建后不可修改') }}</p>
              </bk-form-item>
              <bk-form-item :label="t('描述')" property="description">
                <bk-input v-model="baseInfo.description" :placeholder="t('请输入描述')" />
              </bk-form-item>
            </bk-form>
          </div>
          <div class="stage-config">
            <div class="header-title flex-row justify-content-between">
              <p class="title"><span class="icon apigateway-icon icon-ag-down-shape"></span>{{ t('各环境的服务配置') }}</p>
              <div class="switch" v-if="stageList.length > 1">
                <bk-switcher
                  v-model="isBatchSet" :true-value="true" :false-value="false" theme="primary" size="small"
                  class="mr5" />
                {{ t('批量设置') }}
              </div>
            </div>
            <div class="stage mt20">
              <bk-collapse v-if="!isBatchSet" :list="stageConfig" header-icon="right-shape" v-model="activeIndex">
                <template #title="slotProps">
                  <span class="fw700 stage-name">
                    {{ slotProps.name || slotProps.configs.stage.name}}
                  </span>
                </template>
                <template #content="slotProps">
                  <bk-form ref="stageConfigRef" class="stage-config-form " :model="slotProps" form-type="vertical">
                    <bk-form-item
                      :label="t('负载均衡类型')" property="configs.loadbalance" required :rules="configRules.loadbalance">
                      <bk-select
                        v-model="slotProps.configs.loadbalance" class="w150" :clearable="false"
                        @change="handleChange(slotProps)">
                        <bk-option
                          v-for="option of loadbalanceList" :key="option.id" :value="option.id"
                          :label="option.name">
                        </bk-option>
                      </bk-select>
                    </bk-form-item>
                    <bk-form-item
                      :label="t('后端服务地址')" v-for="(hostItem, i) in slotProps.configs.hosts" :key="i"
                      :rules="configRules.host" :property="`configs.hosts.${i}.host`"
                      :class="['backend-item-cls', { 'form-item-special': i !== 0 }]" required>
                      <div class="host-item">
                        <bk-input :placeholder="t('格式如 ：http(s)://host:port')" v-model="hostItem.host" :key="i">
                          <template #prefix>
                            <bk-select v-model="hostItem.scheme" class="scheme-select-cls w80" :clearable="false">
                              <bk-option
                                v-for="(item, index) in schemeList" :key="index" :value="item.value"
                                :label="item.value" />
                            </bk-select>
                            <div class="slash">://</div>
                          </template>
                          <template #suffix v-if="slotProps.configs.loadbalance === 'weighted-roundrobin'">
                            <bk-input
                              class="suffix-slot-cls weights-input" :placeholder="t('权重')" type="number" :min="1"
                              :max="10000" v-model="hostItem.weight"></bk-input>
                          </template>
                        </bk-input>
                        <i
                          class="add-host-btn apigateway-icon icon-ag-plus-circle-shape ml10"
                          @click="handleAddServiceAddress(slotProps.name)"></i>
                        <i
                          class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape ml10"
                          :class="{ disabled: slotProps.configs.hosts.length < 2 }"
                          @click="handleDeleteServiceAddress(slotProps.name, i)"></i>
                      </div>
                    </bk-form-item>
                    <bk-form-item
                      :label="t('超时时间')" :required="true" :property="'configs.timeout'" class="timeout-item"
                      :rules="configRules.timeout" :error-display-type="'normal'">
                      <bk-input
                        type="number" :min="1" :max="300"
                        v-model="slotProps.configs.timeout" class="time-input">
                        <template #suffix>
                          <div class="group-text group-text-style">{{ t('秒') }}</div>
                        </template>
                      </bk-input>
                      <span class="timeout-tip"> {{ t('最大300秒') }} </span>
                    </bk-form-item>
                  </bk-form>
                </template>
              </bk-collapse>
              <div v-else>
                <bk-collapse :list="batchConfig" header-icon="right-shape" v-model="activeIndex">
                  <template #title>
                    <span class="fw700 stage-name">
                      {{ t(`全部环境（${getAllStageName}）`) }}
                    </span>
                  </template>
                  <template #content="slotProps">
                    <bk-form
                      ref="stageBatchConfigRef" class="stage-config-form " :model="slotProps" form-type="vertical">
                      <bk-form-item
                        :label="t('负载均衡类型')" property="configs.loadbalance" required :rules="configRules.loadbalance">
                        <bk-select
                          v-model="slotProps.configs.loadbalance" class="w150" :clearable="false"
                          @change="handleChange(slotProps)">
                          <bk-option
                            v-for="option of loadbalanceList" :key="option.id" :value="option.id"
                            :label="option.name">
                          </bk-option>
                        </bk-select>
                      </bk-form-item>
                      <bk-form-item
                        :label="t('后端服务地址')" v-for="(hostItem, i) in slotProps.configs.hosts" :key="i"
                        :rules="configRules.host" :property="`configs.hosts.${i}.host`"
                        :class="['backend-item-cls', { 'form-item-special': i !== 0 }]" required>
                        <div class="host-item">
                          <bk-input :placeholder="t('格式如 ：http(s)://host:port')" v-model="hostItem.host" :key="i">
                            <template #prefix>
                              <bk-select v-model="hostItem.scheme" class="scheme-select-cls w80" :clearable="false">
                                <bk-option
                                  v-for="(item, index) in schemeList" :key="index" :value="item.value"
                                  :label="item.value" />
                              </bk-select>
                              <div class="slash">://</div>
                            </template>
                            <template #suffix v-if="slotProps.configs.loadbalance === 'weighted-roundrobin'">
                              <bk-input
                                class="suffix-slot-cls weights-input" :placeholder="t('权重')" type="number" :min="1"
                                :max="10000" v-model="hostItem.weight"></bk-input>
                            </template>
                          </bk-input>
                          <i
                            class="add-host-btn apigateway-icon icon-ag-plus-circle-shape ml10"
                            @click="handleAddServiceAddress(slotProps.name)"></i>
                          <i
                            class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape ml10"
                            :class="{ disabled: slotProps.configs.hosts.length < 2 }"
                            @click="handleDeleteServiceAddress(slotProps.name, i)"></i>
                        </div>
                      </bk-form-item>
                      <bk-form-item
                        :label="t('超时时间')" :required="true" :property="'configs.timeout'" class="timeout-item"
                        :rules="configRules.timeout" :error-display-type="'normal'">
                        <bk-input
                          type="number" :min="1" :max="300"
                          v-model="slotProps.configs.timeout" class="time-input">
                          <template #suffix>
                            <div class="group-text group-text-style">{{ t('秒') }}</div>
                          </template>
                        </bk-input>
                        <span class="timeout-tip"> {{ t('最大300秒') }} </span>
                      </bk-form-item>
                    </bk-form>
                  </template>
                </bk-collapse>
              </div>
            </div>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="pl30">
          <bk-button theme="primary" class="mr5 w80" @click="handleConfirm">
            {{ t('确定') }}
          </bk-button>
          <bk-button class="w80" @click="handleCancel">{{ t('取消') }}</bk-button>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { InfoBox, Message } from 'bkui-vue';
import { useRouter } from 'vue-router';
import { useCommon } from '@/store';
// import { timeFormatter } from '@/common/util';
import { useQueryList } from '@/hooks';
import {
  getStageList,
  getBackendServiceList,
  createBackendService,
  getBackendServiceDetail,
  updateBackendService,
  deleteBackendService,
} from '@/http';

const { t } = useI18n();
const common = useCommon();
const router = useRouter();
const { apigwId } = common; // 网关id


const filterData = ref({ name: '', type: '' });
const isBatchSet = ref<boolean>(false);
const baseInfoRef = ref(null);
const stageConfigRef = ref(null);
const stageBatchConfigRef = ref(null);
const curOperate = ref<string>('add');
const finaConfigs = ref([]);
const curServiceDetail = ref({
  id: 0,
  name: '',
  description: '',
  configs: [],
});
const stageList = ref([]);
const stageConfig = ref([]);
const activeIndex = ref([]);
const batchConfig = ref([{
  configs: {
    loadbalance: 'roundrobin',
    timeout: 30,
    hosts: [{
      scheme: 'http',
      host: '',
      weight: 100,
    }],
  },
}]);
const sidesliderConfi = reactive({
  isShow: false,
  title: '',
});
// 负载均衡类型
const loadbalanceList = reactive([
  { id: 'roundrobin', name: t('轮询(Round-Robin)') },
  { id: 'weighted-roundrobin', name: t('加权轮询(Weighted Round-Robin)') },
]);
// scheme 类型
const schemeList = [{ value: 'http' }, { value: 'https' }];

// 基础信息
const baseInfo = ref({
  name: 'default',
  description: '',
});
// 基础信息校验规则
const baseInfoRules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9-]{0,19}$/;
        return reg.test(value);
      },
      message: t('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头'),
      trigger: 'blur',
    },
  ],
};
// 服务配置校验规则
const configRules = {
  loadbalance: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'change',
    },
  ],
  host: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(value: string) {
        const reg = /^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?$|^\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?$/;
        return reg.test(value);
      },
      message: t('请输入合法Host，如：http://example.com'),
      trigger: 'blur',
    },
  ],
  timeout: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(val: number) {
        if (val < 0 || val > 300) {
          return false;
        }
        return true;
      },
      message: t('超时时间不能小于1且不能大于300'),
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
} = useQueryList(getBackendServiceList, filterData);

// 监听是否批量设置
watch(
  () => isBatchSet.value,
  (v: boolean) => {
    console.log(v);
  },
  { immediate: true },
);

const getAllStageName = computed(() => {
  const newTitle = stageList.value.map(item => item.name).join('，');
  return newTitle;
});


const handleChange = (curItem: any) => {
  console.log(curItem);
  console.log(stageList.value);
  console.log(batchConfig.value);
};


// 判断后端服务新建时间是否在24h之内
// const isWithinTime = (date: string) => {
//   const str = timeFormatter(date);
//   const targetTime = new Date(str);
//   const currentTime = new Date();
//   // 计算两个时间之间的毫秒差
//   const diff = currentTime.getTime() - targetTime.getTime();
//   // 24 小时的毫秒数
//   const twentyFourHours = 24 * 60 * 60 * 1000;
//   return diff < twentyFourHours;
// };

// 新建btn
const handleAdd = () => {
  isBatchSet.value = false;
  curOperate.value = 'add';
  baseInfo.value = {
    name: 'default',
    description: '',
  };
  batchConfig.value = [{
    configs: {
      loadbalance: 'roundrobin',
      timeout: 30,
      hosts: [{
        scheme: 'http',
        host: '',
        weight: 100,
      }],
    },
  }];
  stageConfig.value = stageList.value.map((item: any) => {
    const { name, id, description } = item;
    const newItem = {
      name,
      id,
      description,
      configs: {
        loadbalance: 'roundrobin',
        timeout: 30,
        hosts: [{
          scheme: 'http',
          host: '',
          weight: 100,
        }],
        stage_id: id,
      },
    };
    return newItem;
  });
  sidesliderConfi.isShow = true;
  sidesliderConfi.title = t('新建后端服务');
};

// 增加服务地址
const handleAddServiceAddress = (name: string) => {
  console.log(name);
  console.log(stageConfig.value);
  const isAddItem = isBatchSet.value ? batchConfig.value : stageConfig.value;
  isAddItem.forEach((item) => {
    if (item.name === name) {
      item.configs.hosts.push({
        scheme: 'http',
        host: '',
        weight: 100,
      });
    }
  });
};

// 删除服务地址
const handleDeleteServiceAddress = (name: string, index: number) => {
  const isDeleteItem = isBatchSet.value ? batchConfig.value : stageConfig.value;
  isDeleteItem.forEach((item) => {
    if (item.name === name && item.configs.hosts.length !== 1) {
      item.configs.hosts.splice(index, 1);
    }
  });
};

// 点击名称/编辑
const handleEdit = async (data: any) => {
  isBatchSet.value = false;
  curOperate.value = 'edit';
  baseInfo.value = {
    name: data.name,
    description: data.description,
  };
  sidesliderConfi.title = t(`编辑后端服务【${data.name}】`);
  try {
    const res = await getBackendServiceDetail(apigwId, data.id);
    curServiceDetail.value = res;
    stageConfig.value = res.configs.map((item: any) => {
      return { configs: item };
    });
    console.log(res);
    console.log(stageConfig.value);
    sidesliderConfi.isShow = true;
  } catch (error) {
    console.log('error', error);
  }
};

// 点击关联的资源数
const handleResource = (data: any) => {
  console.log(data);
  const params = {
    name: 'apigwResource',
    params: {
      id: apigwId,
    },
  };
  router.push(params);
};

// 点击删除
const handleDelete = (item: any) => {
  console.log(item);
  InfoBox({
    title: t(`确定删除【${item.name}】该服务?`),
    infoType: 'warning',
    subTitle: t('删除操作无法撤回，请谨慎操作'),
    onConfirm: async () => {
      try {
        await deleteBackendService(apigwId, item.id);
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

// 确认btn
const handleConfirm = async () => {
  // 基础信息校验
  await baseInfoRef.value.validate();
  console.log(baseInfo.value);
  console.log('stageConfig', stageConfig.value);
  console.log('batchConfig', batchConfig.value);
  const isAdd = curOperate.value === 'add';
  if (isBatchSet.value) {
    finaConfigs.value = stageList.value.map((item: any) => {
      const { configs } = batchConfig.value[0];
      const newItem = {
        timeout: configs.timeout,
        loadbalance: configs.loadbalance,
        hosts: configs.hosts,
        stage_id: item.id,
      };
      return newItem;
    });
  } else {
    finaConfigs.value = stageConfig.value.map((item) => {
      const id =  isAdd ? item.id : item.configs.stage.id;
      const newItem = {
        timeout: item.configs.timeout,
        loadbalance: item.configs.loadbalance,
        hosts: item.configs.hosts,
        stage_id: id,
      };
      return newItem;
    });
  }

  const { name, description } = baseInfo.value;
  const params = {
    name,
    description,
    configs: finaConfigs.value,
  };
  console.log(params);
  try {
    if (isAdd) {
      await createBackendService(apigwId, params);
    } else {
      await updateBackendService(apigwId, curServiceDetail.value.id, params);
    }
    Message({
      message: isAdd ? t('新建成功') : t('更新成功'),
      theme: 'success',
    });
    sidesliderConfi.isShow = false;
    getList();
  } catch (error) {
    console.log('error', error);
  }
};

// 取消btn
const handleCancel = () => {
  sidesliderConfi.isShow = false;
};


const init = async () => {
  console.log(tableData);
  try {
    const res = await getStageList(apigwId);
    stageList.value = res;
    res.forEach((item: any) => {
      activeIndex.value.push(item.name);
    });
    console.log(stageList.value);
    console.log(activeIndex.value);
  } catch (error) {
    console.log('error', error);
  }
};
init();
</script>

<style lang="scss" scoped>
.w80 {
  width: 80px;
}

.w500 {
  width: 500px;
}

.backend-service-slider {
  :deep(.bk-modal-content) {
    min-height: calc(100vh - 104px) !important;
  }

  .base-info {
    .base-info-form {
      .aler-text {
        color: #A5A4A7;
      }
    }
  }

  .stage-config {
    .header-title {
      .switch {
        color: #6E6F74;
        font-size: 14px;
      }
    }

    .stage {
      :deep(.bk-collapse-item) {
        background-color: #F5F7FB;
        margin-bottom: 25px;

        .bk-collapse-content {
          padding: 5px 40px;
        }
      }

      .stage-name {
        color: #6D6F75;
      }

      :deep(.bk-collapse-icon) {
        left: 17px;
        top: 17px;
        color: #979AA2;

        svg {
          font-size: 13px;
        }
      }
    }
  }
}

.host-item {
  display: flex;
  align-items: center;

  i {
    font-size: 14px;
    color: #979ba5;
    cursor: pointer;

    &.disabled {
      color: #dcdee5;
    }
  }

  :deep(.bk-form-error) {
    position: relative;
  }
}

.form-item-special {
  :deep(.bk-form-label) {
    display: none;
  }
}

.suffix-slot-cls {
  width: 60px;
  line-height: 30px;
  font-size: 12px;
  color: #63656e;
  text-align: center;
  height: 100%;
  border: none;
  border-left: 1px solid #c4c6cc !important;
}

.scheme-select-cls {
  color: #63656e;
  overflow: hidden;

  :deep(.bk-input--default) {
    border: none;
    border-right: 1px solid #c4c6cc;
  }
}

.timeout-item {
  width: 200px;
  position: relative;

  .timeout-tip {
    position: absolute;
    top: 0px;
    right: -70px;
  }

  .group-text {
    width: 30px;
    text-align: center;
  }
}

.slash {
  color: #63656e;
  background: #fafbfd;
  padding: 0 10px;
  border-right: 1px solid #c4c6cc;
}

.ag-host-input {
  width: 80px;
  line-height: 30px;
  font-size: 12px;
  color: #63656E;
  outline: none;
  padding: 0 10px;
  text-align: center;
}

.title {
  font-size: 15px;
  font-weight: 700;
  color: #323237;

  .icon {
    color: #62666B;
    font-size: 18px;
    margin-right: 10px;
  }
}

:deep(.bk-input--number-control) {
  display: none;
}

.backend-config-item {
  .item-title {
    height: 40px;
    line-height: 40px;
    background: #f0f1f5;
    border-radius: 2px;
    font-weight: 700;
    font-size: 14px;
    color: #63656e;
    padding: 0 16px;
  }

  .item-content {
    background: #f5f7fa;
    padding: 20px 32px;

    .host-item {
      display: flex;
      align-items: center;

      i {
        font-size: 14px;
        color: #979ba5;
        cursor: pointer;

        &.disabled {
          color: #dcdee5;
        }
      }

      :deep(.bk-form-error) {
        position: relative;
      }
    }
  }
}
</style>


