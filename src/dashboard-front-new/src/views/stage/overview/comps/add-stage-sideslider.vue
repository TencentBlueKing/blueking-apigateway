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
        <div
          class="sideslider-content"
        >
          <section class="stage-form-item">
            <div class="title">
              <i class="apigateway-icon icon-ag-down-shape"></i>
              基本信息
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
                    <span>https://www.api.com</span>
                    <i class="apigateway-icon icon-ag-copy-info"></i>
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
          <section class="stage-form-item">
            <div class="title">
              <i class="apigateway-icon icon-ag-down-shape"></i>
              环境的后端服务配置
            </div>
            <div class="content">
              <section
                class="backend-config-item"
                v-for="(item, index) in curStageData.backends"
                :key="index"
              >
                <div class="item-title">default</div>
                <div class="item-content">
                  <bk-form
                    ref="backendConfigRef"
                    :label-width="180"
                    :model="curStageData"
                    form-type="vertical"
                  >
                    <bk-form-item :label="t('负载均衡类型')">
                      <bk-select
                        :clearable="false"
                        :placeholder="t('负载均衡类型')"
                        v-model="item.config.loadbalance"
                      >
                        <bk-option
                          v-for="option in loadbalanceList"
                          :key="option.id"
                          :id="option.id"
                          :name="option.name"
                        ></bk-option>
                      </bk-select>
                    </bk-form-item>

                    <!-- 后端服务地址 -->
                    <bk-form-item
                      label="后端服务地址"
                      v-for="(hostItem, index) of item.config.hosts"
                      :required="true"
                      :property="'curStageData.backends.' + index + '.host'"
                      :key="index"
                      :class="{ 'form-item-special': index !== 0 }"
                      :error-display-type="'normal'"
                    >
                      <div class="host-item mb10">
                        <!-- <bk-input
                            :placeholder="$t('格式: http(s)://host:port')"
                            v-model="hostItem.host"
                            v-if="curStageData.loadbalance === 'weighted-roundrobin'"
                            :key="curStage.proxy_http.upstreams.loadbalance">
                            <div class="append-wrapper" slot="append">
                                <bk-input
                                :class="['ag-host-input', 'weights-input', { 'is-error': hostItem.isRoles }]"
                                type="number"
                                :placeholder="$t('权重')"
                                style="border: none !important;"
                                :min="1"
                                :max="10000"
                                :show-controls="false"
                                v-model="hostItem.weight"
                                @input="weightValidate(hostItem)">
                                </bk-input>
                                <i v-if="hostItem.isRoles" class="bk-icon icon-exclamation-circle-shape tooltips-icon" v-bk-tooltips="hostItem.message"></i>
                            </div>
                            </bk-input> -->

                        <bk-input
                          :placeholder="$t('格式: http(s)://host:port')"
                          v-model="hostItem.host"
                          :key="item.config.loadbalance"
                        ></bk-input>

                        <i
                          class="add-host-btn apigateway-icon icon-ag-plus-circle-shape ml10"
                          @click="handleAddServiceAddress"
                        ></i>
                        <i
                          class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape ml10"
                          :class="{ disabled: item.config.hosts.length <= 1 }"
                          @click="handleDeleteServiceAddress(hostItem, index)"
                        ></i>
                      </div>
                    </bk-form-item>

                    <!-- <bk-form-item
                      :label="$t('超时时间')"
                      :required="true"
                      :property="'proxy_http.timeout'"
                      :icon-offset="220"
                      style="width: 500px"
                      :error-display-type="'normal'"
                    >
                      <bk-input
                        type="number"
                        :min="1"
                        :show-controls="false"
                        v-model="curStage.proxy_http.timeout"
                        class="time-input"
                      >
                        <template slot="append">
                          <div class="group-text group-text-style">{{ $t('秒') }}</div>
                        </template>
                      </bk-input>
                      <span
                        class="ag-text"
                        style="line-height: 32px"
                      >
                        {{ $t('最大300秒') }}
                      </span>
                    </bk-form-item> -->
                  </bk-form>
                </div>
              </section>
            </div>
          </section>
        </div>
      </template>
      <template #footer>
        <div style="padding-left: 20px">
          <bk-button
            theme="primary"
            style="padding: 0 30px"
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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
const { t } = useI18n();

interface IHostItem {
  scheme: string;
  host: string;
  weight: number;
}

const isShow = ref(false);
const curStageData = ref({
  name: '',
  description: '',
  backends: [
    {
      config: {
        type: 'node',
        timeout: 600,
        loadbalance: 'roundrobin',
        hosts: [
          {
            scheme: 'http',
            host: '',
            weight: 1,
          },
        ],
      },
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

// 关闭侧边栏回调
const closeSideslider = () => {
  console.log('关闭');
};

// 显示侧边栏
const handleShowSideslider = () => {
  isShow.value = true;
};

// 取消关闭侧边栏
const handleCancel = () => {
  isShow.value = false;
  //   数据重置
  curStageData.value.name = '';
  curStageData.value.description = '';
};

// 添加服务地址
const handleAddServiceAddress = () => {
  console.log('add');
  //   curStageData.value.backends
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
}
</style>
