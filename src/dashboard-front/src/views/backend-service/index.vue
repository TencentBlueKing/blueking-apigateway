<template>
  <div class="backend-service-container page-wrapper-padding">
    <div class="header flex-row justify-content-between mb15">
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
          :row-class="isNewCreate"
          class="table-layout" :data="tableData" remote-pagination :pagination="pagination" show-overflow-tooltip
          @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange" row-hover="auto">
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
                v-if="data?.resource_count !== 0"
                v-bk-tooltips="{
                  content: t(`${data?.name === 'default' ? '默认后端服务，且' : '服务'}被${data?.resource_count}个资源引用了，不能删除`),
                  disabled: data?.resource_count === 0
                }">
                <bk-button
                  theme="primary" text
                  :disabled="data?.resource_count !== 0 || data?.name === 'default'" @click="handleDelete(data)">
                  {{ t('删除') }}
                </bk-button>
              </span>
              <span
                v-else
                v-bk-tooltips="{
                  content: t('默认后端服务，不能删除'),
                  disabled: data?.name !== 'default'
                }">
                <bk-button
                  theme="primary" text
                  :disabled="data?.name === 'default'" @click="handleDelete(data)">
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
        <div class="content">
          <bk-alert theme="warning" :title="editTitle" class="mb20" v-if="curOperate === 'edit' && isPublish" />
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
            </div>
            <div class="stage mt20">
              <bk-collapse :list="stageConfig" header-icon="right-shape" v-model="activeIndex">
                <template #title="slotProps">
                  <span class="fw700 stage-name">
                    {{ slotProps.name || slotProps.configs.stage.name}}
                  </span>
                </template>
                <template #content="slotProps">
                  <bk-form
                    :ref="getSatgeConfigRef"
                    class="stage-config-form " :model="slotProps" form-type="vertical">
                    <bk-form-item
                      :label="t('负载均衡类型')" property="configs.loadbalance" required :rules="configRules.loadbalance">
                      <bk-select
                        v-model="slotProps.configs.loadbalance" class="w150" :clearable="false"
                      >
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
                        <bk-input :placeholder="t('格式如：host:port')" v-model="hostItem.host" :key="i">
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
      </template>
      <template #footer>
        <div class="pl30">
          <bk-button theme="primary" class="mr5 w80" @click="handleConfirm" :loading="isSaveLoading">
            {{ t('确定') }}
          </bk-button>
          <bk-button class="w80" @click="handleCancel">{{ t('取消') }}</bk-button>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { InfoBox, Message } from 'bkui-vue';
import { useRouter } from 'vue-router';
import { useCommon } from '@/store';
import { timeFormatter } from '@/common/util';
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
const isSaveLoading = ref<boolean>(false);
const isPublish = ref<boolean>(false);
const baseInfoRef = ref(null);
const stageConfigRef = ref([]);
const curOperate = ref<string>('add');
const editTitle = ref<string>(t('如果环境和资源已经发布，服务配置修改后，将立即对所有已发布资源生效'));
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
  name: '',
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
      message: t('请输入合法Host，如：example.com'),
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


const isNewCreate = (row: any) => {
  return isWithinTime(row?.updated_time) ? 'new-created' : '';
};

// 判断后端服务新建时间是否在24h之内
const isWithinTime = (date: string) => {
  const str = timeFormatter(date);
  const targetTime = new Date(str);
  const currentTime = new Date();
  // 计算两个时间之间的毫秒差
  const diff = currentTime.getTime() - targetTime.getTime();
  // 24 小时的毫秒数
  const twentyFourHours = 24 * 60 * 60 * 1000;
  return diff < twentyFourHours;
};

// 获取所有stage服务配置的ref
const getSatgeConfigRef = (el: any) => {
  console.log(el);
  if (el !== null) {
    stageConfigRef.value.push(el);
  }
};

// 新建btn
const handleAdd = () => {
  curOperate.value = 'add';
  baseInfo.value = {
    name: '',
    description: '',
  };
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
  const isAddItem = stageConfig.value;
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
  const isDeleteItem = stageConfig.value;
  isDeleteItem.forEach((item) => {
    if (item.name === name && item.configs.hosts.length !== 1) {
      item.configs.hosts.splice(index, 1);
    }
  });
};

// 点击名称/编辑
const handleEdit = async (data: any) => {
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
      return { configs: item, name: item?.stage?.name, id: item?.stage?.id };
    });
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
    query: {
      backend_id: data.id,
    },
  };
  router.push(params);
};

// 点击删除
const handleDelete = (item: any) => {
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
  const isAdd = curOperate.value === 'add';

  console.log(stageConfigRef.value);

  // 逐个stage服务配置的校验
  for (const item of stageConfigRef.value) {
    if (item === null) break;
    await item.validate();
  }
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

  const { name, description } = baseInfo.value;
  const params = {
    name,
    description,
    configs: finaConfigs.value,
  };
  isSaveLoading.value = true;
  try {
    if (isAdd) {
      await createBackendService(apigwId, params);
    } else {
      await updateBackendService(apigwId, curServiceDetail.value.id, params);
    }
    if (isPublish.value && !isAdd) {
      sidesliderConfi.isShow = false;
      InfoBox({
        title: t('内容保存成功，正在发布至环境中'),
        infoType: 'success',
        subTitle: t('如果编辑的后端服务绑定的环境有发布就会立即发布到对应环境当中'),
        confirmText: t('去查看'),
        cancelText: t('关闭'),
        onConfirm: () => {
          router.push({
            name: 'apigwReleaseHistory',
          });
        },
      });
    } else {
      Message({
        message: isAdd ? t('新建成功') : t('更新成功'),
        theme: 'success',
      });
      sidesliderConfi.isShow = false;
    }
    stageConfigRef.value = [];
    getList();
  } catch (error) {
    console.log('error', error);
  } finally {
    isSaveLoading.value = false;
  }
};

// 取消btn
const handleCancel = () => {
  sidesliderConfi.isShow = false;
  stageConfigRef.value = [];
};

const init = async () => {
  try {
    const res = await getStageList(apigwId);
    stageList.value = res;
    console.log(stageList.value);
    res.forEach((item: any, index: number) => {
      activeIndex.value.push(index);
    });
    isPublish.value = stageList.value.some((item: any) => item.publish_id !== 0);
    console.log(isPublish.value);
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
.mb24{
  margin-bottom: 24px;
}
.w500 {
  width: 500px;
}
:deep(.new-created){
  background-color: #f1fcf5 !important;
}
.content{
  padding: 20px 30px 30px;
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
:deep(.table-layout){
  .bk-table-body{
    table{
      tbody{
        tr{
          td{
            background-color: rgba(0,0,0,0);
          }
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


