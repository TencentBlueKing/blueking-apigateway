<template>
  <div>
    <!-- 新建/编辑sideslider -->
    <bk-sideslider
      v-model:isShow="sidesliderConfi.isShow"
      :quick-close="true"
      ext-cls="backend-service-slider"
      width="960"
      :before-close="handleBeforeClose"
      @animation-end="handleAnimationEnd"
    >
      <template #header>
        <div class="custom-side-header">
          <div class="title">{{ editId ? t('编辑后端服务') : t('新建后端服务') }}</div>
          <template v-if="editId">
            <span></span>
            <div class="subtitle">{{ baseInfo.name }}</div>
          </template>
        </div>
      </template>
      <template #default>
        <div class="content">
          <bk-alert theme="warning" :title="editTitle" class="service-tips" v-if="editId && isPublish" />

          <bk-collapse v-model="activeKey" class="bk-collapse-service">
            <bk-collapse-panel name="base-info">
              <template #header>
                <div class="panel-header">
                  <angle-up-fill
                    :class="[activeKey?.includes('base-info') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">{{ t('基础信息') }}</div>
                </div>
              </template>
              <template #content>
                <div>
                  <bk-form
                    ref="baseInfoRef" class="base-info-form" :model="baseInfo"
                    form-type="vertical">
                    <bk-form-item :label="t('服务名称')" property="name" required :rules="baseInfoRules.name">
                      <bk-input
                        v-model="baseInfo.name" :placeholder="t('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头')"
                        :disabled="editId" />
                      <p class="aler-text">{{ t('后端服务唯一标识，创建后不可修改') }}</p>
                    </bk-form-item>
                    <bk-form-item :label="t('描述')" property="description" class="last-form-item">
                      <bk-input v-model="baseInfo.description" :placeholder="t('请输入描述')" />
                    </bk-form-item>
                  </bk-form>
                </div>
              </template>
            </bk-collapse-panel>

            <bk-collapse-panel name="stage-config">
              <template #header>
                <div class="panel-header">
                  <angle-up-fill
                    :class="[activeKey?.includes('stage-config') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">{{ t('各环境的服务配置') }}</div>
                </div>
              </template>
              <template #content>
                <div class="stage">
                  <bk-collapse :list="stageConfig" header-icon="right-shape" v-model="activeIndex">
                    <template #title="slotProps">
                      <span class="stage-name">
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
                          :label="t('后端服务地址')"
                          v-for="(hostItem, i) in slotProps.configs.hosts"
                          :key="i"
                          :rules="configRules.host"
                          :property="`configs.hosts.${i}.host`"
                          :class="['backend-item-cls', { 'form-item-special': i !== 0 }]"
                          required>
                          <div class="host-item">
                            <bk-input :placeholder="t('格式如：host:port')" v-model="hostItem.host" :key="i">
                              <template #prefix>
                                <bk-select
                                  v-model="hostItem.scheme"
                                  class="scheme-select-cls w80"
                                  :filterable="false"
                                  :clearable="false">
                                  <bk-option
                                    v-for="(item, index) in schemeList" :key="index" :value="item.value"
                                    :label="item.value" />
                                </bk-select>
                                <div class="slash">://</div>
                              </template>
                              <template #suffix v-if="slotProps.configs.loadbalance === 'weighted-roundrobin'">
                                <bk-form-item
                                  :rules="configRules.weight"
                                  :property="`configs.hosts.${i}.weight`"
                                  label=""
                                  style="margin-bottom: 0px;">
                                  <bk-input
                                    class="suffix-slot-cls weights-input"
                                    :placeholder="t('权重')"
                                    type="number"
                                    :min="1"
                                    :max="10000"
                                    v-model="hostItem.weight"
                                  ></bk-input>
                                </bk-form-item>
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
                              <div class="group-text group-text-style" :class="locale === 'en' ? 'long' : ''">
                                {{ t('秒') }}
                              </div>
                            </template>
                          </bk-input>
                          <span class="timeout-tip" :class="locale === 'en' ? 'long' : ''"> {{ t('最大 300 秒') }} </span>
                        </bk-form-item>
                      </bk-form>
                    </template>
                  </bk-collapse>
                </div>
              </template>
            </bk-collapse-panel>
          </bk-collapse>
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

    <!-- 提示弹窗 -->
    <bk-dialog
      v-model:is-show="publishDialog.isShow"
      class="custom-main-dialog"
      width="500"
    >
      <div class="dialog-content">
        <div class="publish-icon">
          <success fill="#3FC06D" />
        </div>
        <div class="dialog-title">
          {{ t('内容保存成功，正在发布至对应环境...') }}
        </div>
        <div class="dialog-main">
          <div class="publish-tips">
            {{ t('当前服务') }} <span>{{ baseInfo.name }}</span>{{ t('，') }}
            {{ t('已绑定以下') }} <span>{{ publishDialog.stageNames?.length }}</span> {{ t('个环境，所有修改都将发布到这些环境中：') }}
          </div>
          <div class="publish-stages">
            <div class="stage-item" v-for="stage in publishDialog.stageNames" :key="stage">
              {{ stage }}
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <bk-button theme="primary" @click="toPublishLogs">{{ t('去查看发布记录') }}</bk-button>
          <bk-button class="ml10" @click="publishDialog.isShow = false">{{ t('关闭') }}</bk-button>
        </div>
      </div>
    </bk-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch } from 'vue';
import { InfoBox, Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { useCommon } from '@/store';
import { useSidebar } from '@/hooks';
import {
  createBackendService,
  updateBackendService,
  getStageList,
  getBackendServiceDetail,
} from '@/http';
import { useRouter } from 'vue-router';
import { AngleUpFill, Success } from 'bkui-vue/lib/icon';

const props = defineProps({
  editId: {
    type: Number,
  },
  base: {
    type: Object,
  },
});

const router = useRouter();
const common = useCommon();
const { apigwId } = common; // 网关id
const { t, locale } = useI18n();
const { isSidebarClosed, initSidebarFormData } = useSidebar();
const activeKey = ref(['base-info', 'stage-config']);
// 基础信息
const baseInfo = ref({
  name: '',
  description: '',
});
const curServiceDetail = ref({
  id: 0,
  name: '',
  description: '',
  configs: [],
});
const stageConfig = ref([]);
const activeIndex = ref<number[]>([]);
const stageList = ref([]);
const stageConfigRef = ref<any>([]);
const isPublish = ref<boolean>(false);
const isSaveLoading = ref<boolean>(false);
const baseInfoRef = ref<any>(null);
const finaConfigs = ref<any>([]);
const publishDialog = reactive<any>({
  isShow: false,
  stageNames: [],
});
// scheme 类型
const schemeList = [{ value: 'http' }, { value: 'https' }];
const sidesliderConfi = reactive({
  isShow: false,
  title: '',
});
const editTitle = ref<string>(t('如果环境和资源已经发布，服务配置修改后，将立即对所有已发布资源生效'));
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
  weight: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'change',
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
// 负载均衡类型
const loadbalanceList = reactive([
  { id: 'roundrobin', name: t('轮询(Round-Robin)') },
  { id: 'weighted-roundrobin', name: t('加权轮询(Weighted Round-Robin)') },
]);

const emit = defineEmits(['done', 'close']);

const handleBeforeClose = async () => {
  const sliderParams = {
    curServiceDetail: curServiceDetail.value,
    stageConfig: stageConfig.value,
    baseInfo: baseInfo.value,
  };
  return isSidebarClosed(JSON.stringify(sliderParams));
};

const handleAnimationEnd = () => {
  handleCancel();
};

// 获取所有stage服务配置的ref
const getSatgeConfigRef = (el: any) => {
  if (el !== null) {
    stageConfigRef.value.push(el);
  }
};

// 增加服务地址
const handleAddServiceAddress = (name: string) => {
  const isAddItem = stageConfig.value;
  isAddItem.forEach((item: any) => {
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
  isDeleteItem.forEach((item: any) => {
    if (item.name === name && item.configs.hosts.length !== 1) {
      item.configs.hosts.splice(index, 1);
    }
  });
};

// 取消btn
const handleCancel = () => {
  emit('close');
  sidesliderConfi.isShow = false;
  stageConfigRef.value = [];
};

// 确认btn
const handleConfirm = async () => {
  // 基础信息校验
  await baseInfoRef.value?.validate();

  // 逐个stage服务配置的校验
  for (const item of stageConfigRef.value) {
    if (item === null) break;
    await item.validate();
  }
  finaConfigs.value = stageConfig.value.map((item: any) => {
    const id =  !props.editId ? item.id : item.configs.stage.id;
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
    if (!props.editId) {
      await createBackendService(apigwId, params);
    } else {
      await updateBackendService(apigwId, curServiceDetail.value.id, params);
    }
    if (isPublish.value && props.editId) {
      sidesliderConfi.isShow = false;

      const stageNames = stageConfig.value?.map((item: any) => {
        return item.name;
      });

      if (stageNames?.length) {
        publishDialog.isShow = true;
        publishDialog.stageNames = stageNames;
      } else {
        InfoBox({
          title: t('后端服务内容保存成功'),
          infoType: 'success',
          dialogType: 'confirm',
          headerAlign: 'center',
          footerAlign: 'center',
          confirmText: t('关闭'),
        });
      }
    } else {
      Message({
        message: !props.editId ? t('新建成功') : t('更新成功'),
        theme: 'success',
      });
      sidesliderConfi.isShow = false;
    }
    stageConfigRef.value = [];
    emit('done');
  } catch (error) {
    console.log('error', error);
  } finally {
    isSaveLoading.value = false;
  }
};

const toPublishLogs = () => {
  router.push({
    name: 'apigwReleaseHistory',
  });
};

const setInit = () => {
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
  const sliderParams = {
    curServiceDetail: curServiceDetail.value,
    stageConfig: stageConfig.value,
    baseInfo: baseInfo.value,
  };
  initSidebarFormData(sliderParams);
};

const getStageListData = async () => {
  try {
    const res = await getStageList(apigwId);
    res?.forEach((item: any, index: number) => {
      activeIndex.value.push(index);
    });
    isPublish.value = res?.some((item: any) => item.publish_id !== 0);
    stageList.value = res;
  } catch (error) {
    console.log('error', error);
  }
};

const getInfo = async () => {
  try {
    const res = await getBackendServiceDetail(apigwId, props.editId);
    curServiceDetail.value = res;
    stageConfig.value = res.configs.map((item: any) => {
      return { configs: item, name: item?.stage?.name, id: item?.stage?.id };
    });
    const sliderParams = {
      curServiceDetail: curServiceDetail.value,
      stageConfig: stageConfig.value,
      baseInfo: baseInfo.value,
    };
    initSidebarFormData(sliderParams);
  } catch (error) {
    console.log('error', error);
  }
};

const show = async () => {
  await getStageListData();
  if (props.editId) {
    await getInfo();
  } else {
    setInit();
  }
  sidesliderConfi.isShow = true;
};

watch(
  () => props.base,
  (val: any) => {
    baseInfo.value = val;
  },
  { immediate: true },
);

defineExpose({
  show,
});
</script>

<style lang="scss" scoped>
.backend-service-slider {
  :deep(.bk-modal-content) {
    min-height: calc(100vh - 104px) !important;
    overflow-y: auto;
  }

  .base-info {
    .base-info-form {
      .aler-text {
        color: #A5A4A7;
      }
    }
  }
}
.content{
  padding: 20px 40px 30px;
}
.service-tips {
  margin-bottom: 12px;
}
.bk-collapse-service {
  .panel-header {
    display: flex;
    align-items: center;
    padding: 12px 0px;
    cursor: pointer;
    .title {
      font-weight: 700;
      font-size: 14px;
      color: #313238;
      margin-left: 8px;
    }

    .panel-header-show {
      transition: .2s;
      transform: rotate(0deg);
    }
    .panel-header-hide {
      transition: .2s;
      transform: rotate(-90deg);
    }
  }

  :deep(.bk-collapse-content) {
    padding: 0px;
  }

  .stage {
    :deep(.bk-collapse-title) {
      margin-left: 23px;
      font-size: 14px;
      color: #63656E;
      font-weight: 700;
    }
    :deep(.bk-collapse-item) {
      background-color: #F5F7FB;
      margin-bottom: 25px;

      .bk-collapse-content {
        padding: 5px 40px;
      }
    }

    .stage-name {
      color: #63656E;
      font-size: 14px;
      font-weight: 700;
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

  .last-form-item {
    margin-bottom: 12px;
  }
}
.w80 {
  width: 80px;
}
.host-item {
  display: flex;
  align-items: center;

  i {
    font-size: 14px;
    color: #979ba5;
    cursor: pointer;
    &:hover {
      color: #63656e;
    }

    &.disabled {
      color: #dcdee5;
      cursor: not-allowed;
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
  width: 80px;
  line-height: 30px;
  font-size: 12px;
  color: #63656e;
  text-align: center;
  height: 28px;
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
    &.long {
      right: -120px;
    }
  }

  .group-text {
    width: 20px;
    text-align: left;
    &.long {
      width: 50px;
    }
  }
}
.slash {
  color: #63656e;
  background: #fafbfd;
  padding: 0 10px;
  border-right: 1px solid #c4c6cc;
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
.custom-main-dialog {
  :deep(.bk-dialog-title) {
    display: none;
  }
  :deep(.bk-modal-footer) {
    display: none;
  }
  .dialog-content {
    .publish-icon {
      text-align: center;
      margin-bottom: 18px;
      font-size: 42px;
      line-height: 32px;
    }
    .dialog-title {
      font-size: 20px;
      color: #313238;
      text-align: center;
      margin-bottom: 16px;
    }
    .dialog-main {
      background: #F5F6FA;
      border-radius: 2px;
      margin-bottom: 25px;
      padding: 12px 16px 18px;
      .publish-tips {
        font-size: 14px;
        color: #63656E;
        margin-bottom: 10px;
        span {
          font-weight: 700;
        }
      }
      .publish-stages {
        display: flex;
        flex-wrap: wrap;
        .stage-item {
          font-size: 14px;
          color: #63656E;
          position: relative;
          padding-left: 12px;
          width: 33%;
          &::after {
            content: ' ';
            position: absolute;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #63656E;
            top: 10px;
            left: 0;
          }
        }
      }
    }
    .dialog-footer {
      text-align: center;
    }
  }
}
</style>
