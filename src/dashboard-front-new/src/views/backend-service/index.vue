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
              ref="baseInfoRef" class="base-info-form mt20" :model="baseInfo" :rules="baseInfoRules"
              form-type="vertical">
              <bk-form-item :label="t('服务名称')" property="name" required>
                <bk-input v-model="baseInfo.name" :placeholder="t('请输入 2-20 字符的字母、数字、连字符(-)、下划线(_)，以字母开头')" />
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
              <div class="switch">
                <bk-switcher
                  v-model="isBatchSet" :true-value="true" :false-value="false" theme="primary" size="small"
                  class="mr5" />
                {{ t('批量设置') }}
              </div>
            </div>
            <div class="stage mt20">
              <bk-collapse v-if="!isBatchSet" :list="stageList" header-icon="right-shape" v-model="activeIndex">
                <template #title="slotProps">
                  <span class="fw700 stage-name">
                    {{ slotProps.name }}
                    <span class="ml5">
                      {{ slotProps.description.trim() === '' ? '' : `(${slotProps.description})` }}
                    </span>
                  </span>
                </template>
                <template #content="slotProps">
                  <bk-form
                    :ref="`stageConfigRef${slotProps.anme}`" class="stage-config-form " :model="baseInfo"
                    form-type="vertical" :rules="configRules">
                    <bk-form-item :label="t('负载均衡类型')" property="loadbalance" required>
                      <bk-select
                        v-model="slotProps.loadbalance" class="w150" :clearable="false"
                        @change="handleChange(slotProps)">
                        <bk-option
                          v-for="option of loadbalanceList" :key="option.id" :value="option.id"
                          :label="option.name">
                        </bk-option>
                      </bk-select>
                    </bk-form-item>
                    <bk-form-item :label="t('后端服务地址')" property="description" required>
                      <bk-input v-model="baseInfo.description" :placeholder="t('请输入描述')" />
                    </bk-form-item>
                  </bk-form>
                </template>
              </bk-collapse>
              <div v-else>批量设置</div>
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
import { ref, reactive, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { InfoBox, Message } from 'bkui-vue';
import { useRouter } from 'vue-router';
import { useCommon } from '@/store';
// import { timeFormatter } from '@/common/util';
import { useQueryList } from '@/hooks';
import {
  getStageList,
  getBackendServiceList,
  // createBackendService,
  // getBackendServiceDetail,
  // updateBackendService,
  deleteBackendService,
} from '@/http';

const { t } = useI18n();
const common = useCommon();
const router = useRouter();
const { apigwId } = common; // 网关id


const filterData = ref({ name: '', type: '' });
const isBatchSet = ref(false);
const stageList = ref([]);
const activeIndex = ref([]);
const sidesliderConfi = reactive({
  isShow: false,
  title: '',
});
const loadbalanceList = reactive([
  { id: 'roundrobin', name: t('轮询(Round-Robin)') },
  { id: 'weighted-roundrobin', name: t('加权轮询(Weighted Round-Robin)') },
]);
const baseInfo = ref({
  name: 'default',
  description: '',
});

const baseInfoRules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9_-]{0,19}$/;
        return reg.test(value);
      },
      message: t('由字母、数字、连接符（-）、下划线（_）组成，首字符必须是字母，长度小于20个字符'),
      trigger: 'blur',
    },
  ],
};
const configRules = {
  loadbalance: [
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
} = useQueryList(getBackendServiceList, filterData);

// 监听是否批量设置
watch(
  () => isBatchSet.value,
  (v: boolean) => {
    console.log(v);
  },
  { immediate: true },
);
const handleChange = (curItem: any) => {
  console.log(curItem);
  stageList.value.forEach((item: any) => {
    if (item.name === curItem.name) {
      item.loadbalance = curItem.loadbalance;
      return;
    }
  });
  console.log(stageList.value);
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
  sidesliderConfi.isShow = true;
  baseInfo.value.name = 'default';
  sidesliderConfi.title = t('新建后端服务');
};
// // 新建btn
// const handleChange = (e: any) => {
//   console.log(stageList);
//   console.log(e);
// };

// 点击名称
const handleEdit = (data: any) => {
  console.log(data);
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
const handleConfirm = () => {
  sidesliderConfi.isShow = false;
};

// 取消btn
const handleCancel = () => {
  sidesliderConfi.isShow = false;
};


const init = async () => {
  console.log(tableData);
  try {
    const res = await getStageList(apigwId);
    stageList.value = res.map((item: any) => {
      const { name, id, description } = item;
      const newItem = {
        name,
        id,
        description,
        loadbalance: 'roundrobin',
        timeout: 1,
        hosts: [{
          scheme: '',
          host: '',
          weight: '1',
        }],
        stage_id: id,
      };
      return newItem;
    });
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

      // .rotate-icon{
      //   transform: rotate(90deg);
      //   transition: all linear .3s;
      // }
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
</style>


