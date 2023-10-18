<template>
  <div class="sideslider-wrapper">
    <bk-sideslider
      v-model:isShow="isShow"
      :title="t('新建环境')"
      quick-close
      width="960"
      ext-cls="stage-sideslider-cls"
      @hidden="closeSideslider"
    >
      <template #default>
        <bk-loading :loading="isDialogLoading">
          <div class="sideslider-content">
            <section class="stage-form-item">
              <div class="title">
                <i class="apigateway-icon icon-ag-down-shape"></i>
                {{ t('基本信息') }}
              </div>
              <div class="content">
                <bk-form
                  ref="nameForm"
                  :label-width="180"
                  :model="curStageData"
                  form-type="vertical"
                >
                  <bk-form-item
                    :label="t('环境名称')"
                    :required="true"
                    :property="'name'"
                    :error-display-type="'normal'"
                  >
                    <bk-input
                      :placeholder="t('请输入 2-20 字符的字母、数字、连字符(-)、下划线(_)，以字母开头')"
                      v-model="curStageData.name"
                    ></bk-input>
                    <p
                      slot="tip"
                      class="ag-tip mt5"
                    >
                      <i class="apigateway-icon icon-ag-info"></i>
                      {{ t('环境唯一标识，创建后不可修改。创建网关成功后可新增环境') }}
                    </p>
                  </bk-form-item>
                  <bk-form-item label="">
                    <div class="address">
                      <label>{{ t('访问地址') }}：</label>
                      <!-- 网关名/环境名 -->
                      <span>{{ stageAddress }}</span>
                      <i
                        class="apigateway-icon icon-ag-copy-info"
                        @click.self="copy(stageAddress)"
                      ></i>
                    </div>
                  </bk-form-item>
                  <bk-form-item :label="t('描述')">
                    <bk-input
                      v-model="curStageData.description"
                      :placeholder="t('请输入描述')"
                    ></bk-input>
                  </bk-form-item>
                </bk-form>
              </div>
            </section>
            <!-- 根据配置来 -->
            <section
              class="stage-form-item"
              v-for="(backend, backendIndex) in curStageData.backends"
              :key="backend.name"
            >
              <div class="title">
                <i class="apigateway-icon icon-ag-down-shape"></i>
                {{ t('后端服务配置') }}
              </div>
              <div class="content">
                <section class="backend-config-item">
                  <div class="item-title">{{ backend.name }}</div>
                  <div class="item-content">
                    <bk-form
                      ref="backendConfigRef"
                      :label-width="180"
                      :model="backend"
                      form-type="vertical"
                    >
                      <bk-form-item
                        :required="true"
                        :label="t('负载均衡类型')"
                      >
                        <bk-select
                          :clearable="false"
                          :placeholder="t('负载均衡类型')"
                          v-model="backend.config.loadbalance"
                        >
                          <bk-option
                            v-for="option in loadbalanceList"
                            :key="option.id"
                            :id="option.id"
                            :name="option.name"
                          ></bk-option>
                        </bk-select>
                      </bk-form-item>

                      <!-- :icon-offset="curStage.proxy_http.upstreams.loadbalance === 'weighted-roundrobin' ? 90 : 10" -->
                      <bk-form-item
                        label="后端服务地址"
                        v-for="(hostItem, index) of backend.config.hosts"
                        :required="true"
                        :property="'backend.' + index + '.host'"
                        :key="index"
                        class="backend-item-cls"
                        :class="[{ 'form-item-special': index !== 0 }]"
                        :error-display-type="'normal'"
                      >
                        <div class="host-item mb10">
                          <bk-input
                            :placeholder="$t('格式: http(s)://host:port')"
                            v-model="hostItem.host"
                            :key="backend.config.loadbalance"
                          >
                            <template #prefix>
                              <bk-select
                                v-model="hostItem.scheme"
                                class="scheme-select-cls"
                                style="width: 120px"
                                :clearable="false"
                              >
                                <bk-option
                                  v-for="(item, index) in schemeList"
                                  :key="index"
                                  :value="item.value"
                                  :label="item.value"
                                />
                              </bk-select>
                              <div class="slash">://</div>
                            </template>
                            <template
                              #suffix
                              v-if="backend.config.loadbalance === 'weighted-roundrobin'"
                            >
                              <bk-input
                                :class="['suffix-slot-cls', 'weights-input', { 'is-error': hostItem.isRoles }]"
                                :placeholder="$t('权重')"
                                type="number"
                                :min="1"
                                :max="10000"
                                v-model="hostItem.weight"
                              ></bk-input>
                              <!-- <i
                                v-if="hostItem.isRoles"
                                class="bk-icon icon-exclamation-circle-shape tooltips-icon"
                                v-bk-tooltips="hostItem.message"
                              ></i> -->
                            </template>
                          </bk-input>

                          <!-- <bk-input
                            :placeholder="$t('格式: http(s)://host:port')"
                            v-model="hostItem.host"
                            :key="backend.config.loadbalance"
                            v-else
                          ></bk-input> -->

                          <i
                            class="add-host-btn apigateway-icon icon-ag-plus-circle-shape ml10"
                            @click="handleAddServiceAddress(backend.name, index)"
                          ></i>
                          <i
                            class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape ml10"
                            :class="{ disabled: backend.config.hosts.length < 2 }"
                            @click="handleDeleteServiceAddress(hostItem, index)"
                          ></i>
                        </div>
                      </bk-form-item>

                      <bk-form-item
                        :label="$t('超时时间')"
                        :required="true"
                        :property="'config.timeout'"
                        class="timeout-item-cls"
                        :rules="rules.timeout"
                        :error-display-type="'normal'"
                      >
                        <bk-input
                          type="number"
                          :min="1"
                          :show-controls="false"
                          v-model="backend.config.timeout"
                          class="time-input"
                        >
                          <template #suffix>
                            <div class="group-text group-text-style">{{ $t('秒') }}</div>
                          </template>
                        </bk-input>
                        <p class="timeout-tip">
                          {{ $t('最大300秒') }}
                        </p>
                      </bk-form-item>
                    </bk-form>
                  </div>
                </section>
              </div>
            </section>
          </div>
        </bk-loading>
      </template>
      <template #footer>
        <div style="padding-left: 20px">
          <bk-button
            theme="primary"
            style="padding: 0 30px"
            @click="handleConfirm"
          >
            {{ t('确定') }}
          </bk-button>
          <bk-button
            style="padding: 0 30px"
            @click="handleCancel"
          >
            {{ t('取消') }}
          </bk-button>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { getBackendsListData, createStage } from '@/http';
import { Message } from 'bkui-vue';
import { cloneDeep } from 'lodash';
import { useCommon } from '@/store';
import { copy } from '@/common/util';
import { SrvRecord } from 'dns';

const { t } = useI18n();
const common = useCommon();

interface IHostItem {
  scheme: string;
  host: string;
  weight: number;
}

const route = useRoute();

const isShow = ref(true);

// 默认值
const defaultConfig = {
  type: 'node',
  timeout: 30,
  loadbalance: 'weighted-roundrobin',
  hosts: [
    {
      scheme: 'http',
      host: '',
      weight: 100,
    },
  ],
};

const curStageData = ref({
  name: '',
  description: '',
  backends: [
    {
      name: '',
      config: defaultConfig,
    },
  ],
});

// 负载均衡类型
const loadbalanceList = [
  {
    id: 'roundrobin',
    name: t('轮询(Round-Robin)'),
  },
  {
    id: 'weighted-roundrobin',
    name: t('加权轮询(Weighted Round-Robin)'),
  },
];

// scheme 类型
const schemeList = [{ value: 'http' }, { value: 'https' }];

// 访问地址
const stageAddress = computed(() => {
  return `http://${common.apigwName}/${curStageData.value.name}`;
});

// 正则校验
const rules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      max: 20,
      message: t('不能多于20个字符'),
      trigger: 'blur',
    },
    {
      validator(value: string) {
        const reg = /^[a-zA-Z][a-zA-Z0-9_-]{0,19}$/;
        return reg.test(value);
      },
      message: t('由字母、数字、连接符（-）、下划线（_）组成，首字符必须是字母，长度小于20个字符'),
      trigger: 'blur',
    },
  ],

  host: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      regex:
        /^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?$|^\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?$/,
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

// 权重校验
const weightValidate = (hostItem: any) => {
  if (!hostItem.weight) {
    hostItem.isRoles = true;
    hostItem.message = t('请输入合法的整数值');
  } else {
    hostItem.isRoles = false;
  }
};

const isDialogLoading = ref(true);

// 网关id
const apigwId = +route.params.id;

// 后端服务列表
const allBackends = ref([]);

const init = async () => {
  // 获取当前网关下的backends(获取后端服务列表)
  const res = await getBackendsListData(apigwId);
  allBackends.value = res.results;
  curStageData.value.backends = allBackends.value.map((item) => {
    // 后端服务配置默认值
    return {
      id: item.id,
      name: item.name,
      config: defaultConfig,
    };
  });
  isDialogLoading.value = false;
};
init();

// 关闭侧边栏回调
const closeSideslider = () => {
  // 数据重置
  curStageData.value = {
    name: '',
    description: '',
    backends: [
      {
        name: '',
        config: defaultConfig,
      },
    ],
  };
};

// 显示侧边栏
const handleShowSideslider = () => {
  isShow.value = true;
};

// 确定
const handleConfirm = () => {
  // 表单校验
  // 请求接口
  handleConfirmCreate();
};

const handleConfirmCreate = async () => {
  try {
    const params = cloneDeep(curStageData.value);
    // 删除冗余参数
    params.backends.forEach((v: any) => {
      delete v.name;
    });
    console.log('params--', params);
    await createStage(apigwId, params);
    Message({
      message: t('创建成功'),
      theme: 'success',
    });
    // 重新获取环境列表(全局事件总线实现)
    // dialog表单数据重置
    closeSideslider();
  } catch (error) {
    console.error(error);
  }
};

// 取消关闭侧边栏
const handleCancel = () => {
  isShow.value = false;
  //   数据重置
  curStageData.value.name = '';
  curStageData.value.description = '';
};

// 添加服务地址
const handleAddServiceAddress = (name: string, index: number) => {
  console.log('add');
  curStageData.value.backends.forEach((v) => {
    if (v.name === name) {
      console.log(v);
      v.config.hosts.push({
        scheme: 'http',
        host: '',
        weight: 100,
      });
    }
  });
};

// 删除服务地址
const handleDeleteServiceAddress = (host: IHostItem, index: string | number) => {
  console.log('del');
};

// 暴露属性
defineExpose({
  handleShowSideslider,
});
</script>

<style lang="scss" scoped>
.stage-sideslider-cls {
  :deep(.bk-sideslider-footer) {
    position: absolute;
    bottom: 0;
  }
}
.sideslider-content {
  padding: 20px 40px;
  .stage-form-item {
    .title {
      height: 54px;
      line-height: 54px;
      font-weight: 700;
      font-size: 14px;
      color: #313238;
    }
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
      }
    }
  }
  .address {
    height: 40px;
    line-height: 40px;
    background: #f5f7fa;
    border-radius: 2px;
    padding: 0 16px;

    label {
      height: 22px;
      font-weight: 700;
      font-size: 14px;
      color: #63656e;
      line-height: 22px;
    }
    span {
      font-size: 14px;
      color: #63656e;
    }
    i {
      cursor: pointer;
      color: #3a84ff;
      margin-left: 5px;
      padding: 3px;
    }
  }

  :deep(.bk-input--number-control) {
    display: none;
  }
}

.suffix-slot-cls {
  width: 80px;
  line-height: 30px;
  font-size: 12px;
  color: #63656e;
  text-align: center;
  height: 100%;
  border: none;
  border-left: 1px solid #c4c6cc !important;
}
.group-text-style {
  width: 32px;
  color: #63656e;
  text-align: center;
  background: #fafbfd;
  border-left: 1px solid #c4c6cc;
}
.scheme-select-cls {
  :deep(.bk-input--text) {
    background: #fafbfd;
  }
  color: #63656e;
  width: 120px;
  overflow: hidden;
  :deep(.bk-input--default) {
    border: none;
    border-right: 1px solid #c4c6cc;
  }
}
.slash {
  color: #63656e;
  background: #fafbfd;
  padding: 0 10px;
  border-right: 1px solid #c4c6cc;
}
.timeout-item-cls {
  width: 240px;
  position: relative;
  :deep(.bk-form-content) {
    .timeout-tip {
      position: absolute;
      top: 0;
      right: -70px;
      color: #63656e;
      margin-left: 13px;
      white-space: nowrap;
    }
  }
}
.form-item-special {
  :deep(.bk-form-label) {
    display: none;
  }
}
.backend-item-cls {
  margin-bottom: 8px;
}
</style>
