<template>
  <div class="release-sideslider">
    <bk-sideslider
      v-model:isShow="isShow"
      :width="1050"
      :title="`${t('资源详情')}【${info.version}】`"
      quick-close
    >
      <template #default>
        <div class="sideslider-content">
          <div class="sideslider-lf">
            <bk-input class="mb12" type="search" />
            <div class="sideslider-lf-title mb8">版本日志</div>
            <div class="sideslider-lf-ul">
              <div
                :class="[
                  'sideslider-lf-li',
                  'mb8',
                  currentSource.name === item.name ? 'active' : '',
                ]"
                v-for="item in info.resources"
                :key="item.name"
                @click="changeCurrentSource(item)"
              >
                <bk-overflow-title type="tips">
                  {{ item.name }}
                </bk-overflow-title>
              </div>
            </div>
          </div>
          <div class="sideslider-rg">
            <div class="sideslider-rg-version-collapse">
              <bk-collapse
                v-model="activeIndex"
                header-icon="right-shape"
                class="bk-collapse-source"
              >
                <bk-collapse-panel :name="1">
                  <span><span class="log-name">版本日志</span></span>
                  <!-- <template #header>
                    <div class="bk-collapse-header">
                      <right-shape v-show="!activeIndex.includes(1)" />
                      <angle-up-fill v-show="activeIndex.includes(1)" />
                      <span class="log-name">版本日志</span>
                    </div>
                  </template> -->
                  <template #content>
                    <div style="padding-left: 32px">
                      <p>{{ info.comment }}</p>
                    </div>
                  </template>
                </bk-collapse-panel>
                <bk-collapse-panel :name="2">
                  <span>
                    <bk-tag theme="success">{{ currentSource.method }}</bk-tag>
                    <span class="log-name">{{ currentSource.name }}</span>
                  </span>
                  <template #content>
                    <div class="sideslider-rg-content">
                      <div class="sideslider-rg-info">
                        <div class="sideslider-item-title">基本信息</div>
                        <div class="sideslider-item-content">
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              资源名称：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{ currentSource.name }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              资源地址：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{ currentSource.path }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              描述：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{ currentSource.description }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              标签：
                            </div>
                            <div
                              class="sideslider-item-content-value"
                              v-if="currentSource.gateway_label_ids?.length"
                            >
                              <bk-tag
                                v-for="tag in currentSource.gateway_label_ids"
                                :key="tag"
                              >{{ tag }}</bk-tag
                              >
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              认证方式：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{
                                getResourceAuth(
                                  currentSource?.contexts?.resource_auth?.config
                                )
                              }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              校验应用权限：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{
                                getPermRequired(
                                  currentSource?.contexts?.resource_auth?.config
                                )
                              }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              是否公开：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{ currentSource?.is_public ? "是" : "否" }}
                              {{
                                currentSource?.allow_apply_permission
                                  ? "(允许申请权限)"
                                  : "(不允许申请权限)"
                              }}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="sideslider-rg-info">
                        <div class="sideslider-item-title">前端配置</div>
                        <div class="sideslider-item-content">
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              请求方法：
                            </div>
                            <div class="sideslider-item-content-value">
                              <bk-tag theme="success">{{
                                currentSource.method
                              }}</bk-tag>
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              请求路径：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{ currentSource.path }}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="sideslider-rg-info">
                        <div class="sideslider-item-title">后端配置</div>
                        <div class="sideslider-item-content">
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              后端服务地址：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{
                                getRequestConfig(currentSource?.proxy?.config)
                                  ?.method
                              }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              服务：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{
                                getRequestConfig(currentSource?.proxy?.config)
                                  ?.method
                              }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              请求方法：
                            </div>
                            <div class="sideslider-item-content-value">
                              <bk-tag theme="success">
                                {{
                                  getRequestConfig(currentSource?.proxy?.config)
                                    ?.method
                                }}
                              </bk-tag>
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              自定义超时时间：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{
                                getRequestConfig(currentSource?.proxy?.config)
                                  ?.timeout
                              }}
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              请求路径：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{
                                getRequestConfig(currentSource?.proxy?.config)
                                  ?.path
                              }}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="sideslider-rg-info">
                        <div class="sideslider-item-title">文档</div>
                        <div class="sideslider-item-content">
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              文档更新时间：
                            </div>
                            <div class="sideslider-item-content-value">
                              {{ currentSource.doc_updated_time }}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="sideslider-rg-info">
                        <div class="sideslider-item-title">插件：频率控制</div>
                        <div class="sideslider-item-content">
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              默认频率控制：
                            </div>
                            <div class="sideslider-item-content-value">
                              60次/s
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              特殊应用频率控制：
                            </div>
                            <div class="sideslider-item-content-value">
                              <p>70次/s（蓝鲸应用 ID：889090）</p>
                              <p>80次/s（蓝鲸应用 ID：889090）</p>
                              <p>1000次/s（蓝鲸应用 ID：32232）</p>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="sideslider-rg-info">
                        <div class="sideslider-item-title">
                          插件：IP 访问保护
                        </div>
                        <div class="sideslider-item-content">
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              类型：
                            </div>
                            <div class="sideslider-item-content-value">
                              白名单
                            </div>
                          </div>
                          <div class="sideslider-item-content-li">
                            <div class="sideslider-item-content-label">
                              IP：
                            </div>
                            <div class="sideslider-item-content-value">
                              <p>（IPv6）192.169.1.10</p>
                              <p>（IPv6）192.169.1.10</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                </bk-collapse-panel>
              </bk-collapse>
            </div>
          </div>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
// import { RightShape, AngleUpFill } from "bkui-vue/lib/icon";
import { getResourceVersionsInfo } from '@/http';

const { t } = useI18n();
const route = useRoute();
// 网关id
const apigwId = +route.params.id;

const props = defineProps<{
  id: number;
}>();

const isShow = ref(false);
const activeIndex = ref([1, 2]);
const info = ref<any>({});
const currentSource = ref<any>({});

// 获取详情数据
const getInfo = async () => {
  if (!props.id || !apigwId) return;

  try {
    const res = await getResourceVersionsInfo(apigwId, props.id);
    console.log('res:  ', res);
    info.value = res;
    currentSource.value = res.resources[0] || {};
  } catch (e) {
    console.log(e);
  }
};
getInfo();

const getResourceAuth = (authStr: string) => {
  if (!authStr) return '';

  const auth = JSON.parse(authStr);
  const tmpArr: string[] = [];

  if (auth?.auth_verified_required) {
    tmpArr.push('用户认证');
  }
  if (auth?.app_verified_required) {
    tmpArr.push('蓝鲸应用认证');
  }
  return tmpArr.join(', ');
};

const getPermRequired = (authStr: string) => {
  if (!authStr) return '';

  const auth = JSON.parse(authStr);
  if (auth?.resource_perm_required) {
    return '校验';
  }
  return '不校验';
};

const getRequestConfig = (configStr: string) => {
  if (!configStr) return {};
  return JSON.parse(configStr);
};

// 显示侧边栏
const showSideslider = () => {
  isShow.value = true;
};

// 切换资源
const changeCurrentSource = (source: any) => {
  currentSource.value = source;
};

watch(
  () => props.id,
  () => {
    getInfo();
  },
);

defineExpose({
  showSideslider,
});
</script>

<style lang="scss" scoped>
.sideslider-content {
  width: 100%;
  display: flex;
  align-items: flex-start;
  .sideslider-lf {
    width: 320px;
    background-color: #f5f7fb;
    height: calc(100vh - 52px);
    padding: 20px 16px 0px;
    box-sizing: border-box;
    .sideslider-lf-title {
      background-color: #ffffff;
      color: #63656e;
      padding: 8px 12px;
      border-radius: 2px;
      font-size: 12px;
    }
    .sideslider-lf-ul {
      height: calc(100% - 94px);
      overflow-y: scroll;
    }
    .sideslider-lf-li {
      cursor: pointer;
      background: #ffffff;
      border-radius: 2px;
      padding: 8px 12px;
      color: #63656e;
      font-size: 12px;
      box-sizing: border-box;
      border: 1px solid #ffffff;
      &:hover {
        border: 1px solid #3a84ff;
      }
      &.active {
        border: 1px solid #3a84ff;
        color: #3a84ff;
        font-weight: 700;
      }
    }
  }
  .sideslider-rg {
    flex: 1;
    padding: 24px 24px 0px;
    box-sizing: border-box;
    height: calc(100vh - 52px);
    overflow-y: scroll;
    .log-name {
      font-size: 12px;
      color: #63656e;
      font-weight: 700;
    }
    .sideslider-rg-info {
      margin-bottom: 12px;
      .sideslider-item-title {
        font-size: 12px;
        color: #63656e;
        font-weight: 700;
        line-height: 40px;
        border-bottom: 1px solid #dddee5;
      }
      .sideslider-item-content {
        padding-top: 8px;
        .sideslider-item-content-li {
          display: flex;
          align-items: flex-start;
          .sideslider-item-content-label {
            font-size: 12px;
            color: #63656e;
            text-align: right;
            line-height: 32px;
            width: 120px;
          }
          .sideslider-item-content-value {
            font-size: 12px;
            color: #313238;
            line-height: 32px;
          }
        }
      }
    }
  }
}
</style>
<style lang="scss">
.sideslider-rg-version-collapse .bk-collapse-source {
  .bk-collapse-header {
    background-color: #f0f1f5;
  }
  .bk-collapse-content {
    padding: 12px 0px 24px;
  }
}
</style>
