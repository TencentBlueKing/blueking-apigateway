<template>
  <div class="basic-info-wrapper">
    <bk-alert v-if="!basicInfoData.status" theme="warning" :title="`${t('当前网关已停用，如需使用，请先启用')}`" class="mb15" />
    <bk-loading :loading="basicInfoDetailLoading">
      <section class="header-info">
        <div
          :class="[
            'header-info-left',
            { 'header-info-left-disabled': !basicInfoData.status }
          ]">
          <span
            :class="['kind', basicInfoData.kind === 0 ? 'normal' : 'program']">
            {{ basicInfoData.kind === 0 ? t('普') : t('编') }}
          </span>
          <span class="name">{{ basicInfoData?.name?.[0]?.toUpperCase() }}</span>
        </div>
        <div class="header-info-right">
          <div class="header-info-name">
            <span class="name">{{ basicInfoData.name }}</span>
            <div class="header-info-tag">
              <bk-tag theme="info" v-if="basicInfoData.kind === 0">
                {{ t('普通网关') }}
              </bk-tag>
              <bk-tag theme="success" v-else>
                {{ t('可编程网关') }}
              </bk-tag>
              <bk-tag class="website" v-if="basicInfoData.is_official">{{ t('官网') }}</bk-tag>
              <div v-if="basicInfoData.status > 0">
                <!-- <bk-tag class="vip">{{ t('专享') }}</bk-tag>? -->
                <bk-tag class="enabling">
                  <i class="apigateway-icon icon-ag-yiqiyong" />
                  {{ t('启用中') }}
                </bk-tag>
              </div>
              <bk-tag class="deactivated" v-if="!basicInfoData.status">
                <i class="apigateway-icon icon-ag-minus-circle" />
                {{ t('已停用') }}
              </bk-tag>
            </div>
          </div>
          <div class="header-info-description">
            <GateWaysEditTextarea
              field="description"
              width="600px"
              :placeholder="t('请输入描述')"
              :content="basicInfoData.description"
              @on-change="(e:Record<string, any>) => handleInfoChange(e)"
            />
          </div>
          <div class="header-info-button">
            <bk-button @click="handleOperate('edit')" class="operate-btn">
              {{ t('编辑') }}
            </bk-button>
            <div>
              <bk-button
                v-if="basicInfoData.status > 0" @click="handleOperate('enable')"
                class="deactivate-btn operate-btn"
              >
                {{ t('停用') }}
              </bk-button>
              <bk-button v-else theme="primary" @click="handleOperate('deactivate')" class="operate-btn">
                {{ t('立即启用') }}
              </bk-button>
            </div>
            <template v-if="basicInfoData.status > 0">
              <bk-popover :content="$t('请先停用才可删除')">
                <bk-button class="operate-btn" :disabled="basicInfoData.status > 0">
                  {{ t('删除') }}
                </bk-button>
              </bk-popover>
            </template>
            <template v-else>
              <bk-button @click="handleOperate('delete')" class="operate-btn">
                {{ t('删除') }}
              </bk-button>
            </template>
            <template v-if="basicInfoData.kind === 1">
              <span class="btn-line"></span>
              <bk-button class="operate-btn" @click="showGuide">
                <help-document-fill class="icon-help" />
                {{ t('查看开发指引') }}
              </bk-button>
            </template>
          </div>
        </div>
      </section>
      <section class="basic-info-detail">
        <div class="basic-info-detail-item">
          <div class="detail-item-title">{{ t('基础信息') }}</div>
          <div class="detail-item-content">
            <div class="detail-item-content-item" v-if="basicInfoData.kind === 1">
              <div class="label">{{ `${t('开发语言')}：` }}</div>
              <div class="value">
                <span>{{ basicInfoData.extra_info?.language || '--' }}</span>
              </div>
            </div>
            <div class="detail-item-content-item" v-if="basicInfoData.kind === 1">
              <div class="label">{{ `${t('代码仓库')}：` }}</div>
              <div class="value">
                <span>{{ basicInfoData.extra_info?.repository || '--' }}</span>
                <i
                  class="apigateway-icon icon-ag-jump"
                  @click.stop="handleOpenNav(basicInfoData.extra_info.repository)"></i>
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">{{ `${t('是否公开')}：` }}</div>
              <div class="value">
                <bk-switcher
                  v-model="basicInfoData.is_public"
                  theme="primary"
                  size="small"
                  style="min-width: 28px;"
                  @change="handleChangePublic"
                />
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">{{ `${t('访问域名')}：` }}</div>
              <div class="value url">
                <span>{{ basicInfoData.api_domain || '--' }}</span>
                <i class="apigateway-icon icon-ag-copy-info" @click.self.stop="copy(basicInfoData.api_domain)"></i>
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">{{ `${t('文档地址')}：` }}</div>
              <div class="value url">
                <span
                  class="link"
                  v-bk-tooltips="{
                    content: t('网关未开启或公开，暂无文档地址'),
                    placement: 'right',
                    disabled: !!basicInfoData.docs_url }"
                >
                  {{ basicInfoData.docs_url || '--' }}
                </span>
                <template v-if="basicInfoData.docs_url">
                  <span>
                    <i class="apigateway-icon icon-ag-jump" @click.stop="handleOpenNav(basicInfoData.docs_url)" />
                  </span>
                  <span>
                    <i class="apigateway-icon icon-ag-copy-info" @click.self.stop="copy(basicInfoData.docs_url)" />
                  </span>
                </template>
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">{{ `${t('维护人员')}：` }}</div>
              <div class="value">
                <GateWaysEditMemberSelector
                  mode="edit"
                  width="600px"
                  field="maintainers"
                  :is-required="true"
                  :placeholder="t('请选择维护人员')"
                  :content="basicInfoData.maintainers"
                  :is-error-class="'maintainers-error-tip'"
                  :error-value="t('维护人员不能为空')"
                  @on-change="(e:Record<string, any>) => handleInfoChange(e)"
                />
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">{{ `${t('创建人')}：` }}</div>
              <div class="value">
                <span>{{ basicInfoData.created_by || '--' }}</span>
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">{{ `${t('创建时间')}：` }}</div>
              <div class="value">
                <span class="link">{{ basicInfoData.created_time || '--' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="basic-info-detail-item">
          <div class="detail-item-title">{{ t('API公钥（指纹）') }}</div>
          <div class="detail-item-content">
            <div class="detail-item-content-item">
              <div class="label w0" />
              <div class="value public-key-content">
                <div class="value-icon-lock">
                  <i class="apigateway-icon icon-ag-lock-fill1"></i>
                </div>
                <div class="value-public-key">
                  <span class="link">
                    {{ basicInfoData.public_key_fingerprint }}
                  </span>
                  <div>
                    <span>
                      <i class="apigateway-icon icon-ag-copy-info" @click.self.stop="copy(basicInfoData.public_key)" />
                    </span>
                    <span>
                      <i class="apigateway-icon icon-ag-download" @click.stop="handleDownload" />
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label w0"></div>
              <div class="value more-tip">
                <i class="apigateway-icon icon-ag-info"></i>
                <span>{{ t('可用于解密传入后端接口的请求头 X-Bkapi-JWT') }}，</span>
                <a :href="GLOBAL_CONFIG.DOC.JWT" target="_blank" class="more-detail">{{ t(' 更多详情') }}</a>
              </div>
            </div>
          </div>
        </div>
        <div class="basic-info-detail-item" v-if="basicInfoData.kind === 1">
          <div class="detail-item-title">{{ t('可编程网关工作流') }}</div>
          <div class="detail-item-content">
            <img :src="processImg" :alt="t('可编程网关的流程图')">
          </div>
        </div>
        <div class="basic-info-detail-item" v-if="basicInfoData.kind === 1">
          <div class="detail-item-title">{{ t('关联操作指引') }}</div>
          <div class="detail-item-content">
            <div class="explain">
              {{ t('可编程网关发布后，系统将在蓝鲸开发者中心部署一个 SaaS 来提供 API 的后端服务，与蓝鲸 SaaS 开发相关的操作均可在蓝鲸开发者中心完成') }}
            </div>
            <div class="guide-wrapper">
              <div class="guide-item">
                <div class="item-name">{{ t('开发 API') }}</div>
                <div class="item-values">
                  <div class="item" v-for="(item, index) in basicInfoData.links?.develop" :key="item.name">
                    <a class="value" :href="item.link" target="_blank">{{ item.name }}</a>
                    <span class="line" v-if="index !== basicInfoData.links?.develop?.length - 1"></span>
                  </div>
                </div>
              </div>

              <div class="guide-item">
                <div class="item-name">{{ t('查询日志') }}</div>
                <div class="item-values">
                  <div class="item" v-for="(item, index) in basicInfoData.links?.logging" :key="item.name">
                    <a class="value" :href="item.link" target="_blank">{{ item.name }}</a>
                    <span class="line" v-if="index !== basicInfoData.links?.logging?.length - 1"></span>
                  </div>
                </div>
              </div>

              <div class="guide-item">
                <div class="item-name">{{ t('更多操作') }}</div>
                <div class="item-values">
                  <div class="item" v-for="(item, index) in basicInfoData.links?.more" :key="item.name">
                    <a class="value" :href="item.link" target="_blank">{{ item.name }}</a>
                    <span class="line" v-if="index !== basicInfoData.links?.more?.length - 1"></span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </bk-loading>

    <bk-dialog
      width="540"
      :is-show="delApigwDialog.isShow"
      :title="$t(`确认删除网关【{basicInfoDataName}】？`, { basicInfoDataName: basicInfoData.name })"
      :theme="'primary'"
      :loading="delApigwDialog.loading"
      @closed="delApigwDialog.isShow = false">
      <div class="ps-form">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="form-tips" v-dompurify-html="delTips" />
        <div class="mt15">
          <bk-input v-model="formRemoveConfirmApigw"></bk-input>
        </div>
      </div>
      <template #footer>
        <bk-button theme="primary" :disabled="!formRemoveApigw" @click="handleDeleteApigw">
          {{ t('确定') }}
        </bk-button>
        <bk-button
          @click="delApigwDialog.isShow = false">
          {{ t('取消') }}
        </bk-button>
      </template>
    </bk-dialog>

    <bk-sideslider
      v-model:is-show="isShowMarkdown"
      :title="t('查看开发指引')"
      width="960"
    >
      <section class="markdown-box">
        <guide :markdown-html="markdownHtml" />
      </section>
    </bk-sideslider>

    <create-gateway-com v-model="createGatewayShow" :init-data="basicInfoDetailData" @done="getBasicInfo()" />
  </div>
</template>

<script setup lang="ts">
import {  ref, computed, watch } from 'vue';
import _ from 'lodash';
import { Message, InfoBox } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { HelpDocumentFill } from 'bkui-vue/lib/icon';
import { useRoute, useRouter } from 'vue-router';
import {  copy } from '@/common/util';
import { useGetGlobalProperties } from '@/hooks';
import { BasicInfoParams, DialogParams } from './common/type';
import { getGateWaysInfo, toggleGateWaysStatus, deleteGateWays, editGateWays, getGuideDocs } from '@/http';
import GateWaysEditTextarea from '@/components/gateways-edit/textarea.vue';
import GateWaysEditMemberSelector from '@/components/gateways-edit/member-selector.vue';
import CreateGatewayCom from '@/components/create-gateway.vue';
import guide from '@/components/guide.vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
// @ts-ignore
import programProcess from '@/images/program-process.svg';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

// 网关id
const apigwId = ref(0);
const formRemoveConfirmApigw = ref('');
const basicInfoDetailLoading = ref(false);
const createGatewayShow = ref<boolean>(false);
const isShowMarkdown = ref<boolean>(false);
const markdownHtml = ref<string>('');

// 当前基本信息
const basicInfoData = ref<BasicInfoParams>({
  status: 1,
  name: '',
  url: '',
  description: '',
  description_en: '',
  public_key_fingerprint: '',
  bk_app_codes: '',
  related_app_codes: '',
  docs_url: '',
  api_domain: '',
  created_by: '',
  created_time: '',
  public_key: '',
  maintainers: [],
  developers: [],
  is_public: true,
  is_official: false,
  kind: 0,
  extra_info: {
    language: 'python',
    repository: '',
  },
  programmable_gateway_git_info: {
    repository: '',
    account: '',
    password: '',
  },
});
const basicInfoDetailData = ref(_.cloneDeep(basicInfoData.value));
const delApigwDialog = ref<DialogParams>({
  isShow: false,
  loading: false,
});

const processImg = computed(() => {
  return programProcess;
});

const formRemoveApigw = computed(() => {
  return basicInfoData.value.name === formRemoveConfirmApigw.value;
});

const delTips = computed(() => {
  // return t('请完整输入 <code class="gateway-del-tips">{name}</code> 来确认删除网关！', { name: basicInfoData.value.name });
  return t(`请完整输入<code class="gateway-del-tips">${basicInfoData.value.name}</code> 来确认删除网关！`);
});

// 获取网关基本信息
const getBasicInfo = async () => {
  try {
    const res = await getGateWaysInfo(apigwId.value);
    basicInfoData.value = Object.assign({}, res);
  } catch (e) {
    console.error(e);
  }
};

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, { language: lang, ignoreIllegals: true }).value;
      }
    } catch {
      return str;
    }
    return str;
  },
});

const showGuide = async () => {
  try {
    const data = await getGuideDocs(apigwId.value);
    markdownHtml.value = md.render(data.content);
    isShowMarkdown.value = true;
  } catch (e) {
    console.error(e);
  }
};

const handleDeleteApigw = async () => {
  try {
    await deleteGateWays(apigwId.value);
    Message({
      theme: 'success',
      message: t('删除成功'),
      width: 'auto',
    });
    delApigwDialog.value.isShow = false;
    setTimeout(() => {
      router.push({
        name: 'home',
      });
    }, 200);
  } catch (e) {
    console.error(e);
  }
};

const handleChangePublic = async (value: boolean) => {
  basicInfoData.value.is_public = value;
  await editGateWays(apigwId.value, basicInfoData.value);
  Message({
    message: t('更新成功'),
    theme: 'success',
    width: 'auto',
  });
};

const statusChanging = ref(false);
const handleChangeApigwStatus = async () => {
  const status = basicInfoData.value.status === 1 ? 0 : 1;
  try {
    statusChanging.value = true;
    const res = await toggleGateWaysStatus(apigwId.value, { status });
    if (res) {
      basicInfoData.value = Object.assign(basicInfoData.value, { status });
      Message({
        theme: 'success',
        message: status === 1 ? t('启用网关成功') : t('停用网关成功'),
        width: 'auto',
      });
    }
    await getBasicInfo();
  } catch (e) {
    console.error(e);
  } finally {
    statusChanging.value = false;
  }
};

const handleOperate = async (type: string) => {
  if (['enable', 'deactivate'].includes(type)) {
    let title = t('确认要启用网关？');
    let subTitle = '';
    if (basicInfoData.value.status > 0) {
      title = t('确认是否停用网关？');
      subTitle = t('网关停用后，网关下所有资源不可访问，请确认是否继续操作？');
    }

    InfoBox({
      title,
      subTitle,
      onConfirm: () => {
        if (statusChanging.value) {
          return;
        }
        handleChangeApigwStatus();
      },
    });
    return;
  }

  if (['edit'].includes(type)) {
    basicInfoDetailData.value = _.cloneDeep(basicInfoData.value);
    createGatewayShow.value = true;
    return;
  }

  if (['delete'].includes(type)) {
    delApigwDialog.value.isShow = true;
    formRemoveConfirmApigw.value = '';
    return;
  }
};

const handleOpenNav = (url: string) => {
  if (url) {
    window.open(url, '_blank');
  } else {
    Message({
      theme: 'warning',
      message: t('暂无可跳转链接'),
      width: 'auto',
    });
  }
};

const handleDownload = () => {
  const { name, public_key } = basicInfoData.value;
  const element = document.createElement('a');
  const blob: any = new Blob([public_key], {
    type: 'text/plain',
  });
  element.download = `bk_apigw_public_key_${name}.pub`;
  element.href = URL.createObjectURL(blob);
  element.click();
  URL.revokeObjectURL(blob);
};

const handleInfoChange = async (payload: Record<string, string>) => {
  const params = {
    ...basicInfoData.value,
    ...payload,
  };
  await editGateWays(apigwId.value, params);
  basicInfoData.value = Object.assign(basicInfoData.value, params);
  Message({
    message: t('编辑成功'),
    theme: 'success',
    width: 'auto',
  });
};

watch(
  () => route,
  async (payload: any) => {
    if (payload.params?.id) {
      apigwId.value = Number(payload.params.id);
      await getBasicInfo();
    }
  },
  { immediate: true, deep: true },
);

</script>

<style lang="scss" scoped>
.markdown-box {
  padding: 20px 24px;
}
.basic-info-wrapper {
  padding: 24px;
  font-size: 12px;

  .header-info {
    padding: 24px;
    background: #ffffff;
    box-shadow: 0 2px 4px 0 #1919290d;
    display: flex;

    &-left {
      width: 80px;
      height: 80px;
      background: #f0f5ff;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      .kind {
        content: ' ';
        position: absolute;
        width: 20px;
        height: 20px;
        border-radius: 2px;
        top: 0;
        left: 0;
        font-size: 12px;
        line-height: 18px;
        text-align: center;
        &.normal {
          color: #1768EF;
          background: #E1ECFF;
          border: 1px solid #699DF4;
        }
        &.program {
          color: #299E56;
          background: #EBFAF0;
          border: 1px solid #A1E3BA;
        }
      }

      .name {
        font-weight: 700;
        font-size: 40px;
        color: #3a84ff;
      }

      &-disabled {
        background: #F0F1F5;

        .name {
          color: #C4C6CC;
        }
      }
    }

    &-right {
      width: calc(100% - 50px);
      padding: 0 16px;

      .header-info-name {
        display: flex;

        .name {
          font-weight: 700;
          font-size: 16px;
          color: #313238;
        }

        .header-info-tag {
          display: flex;
          margin-left: 8px;
          font-size: 12px;
          .bk-tag {
            margin: 2px 4px 2px 0;
          }

          .website {
            background-color: #EDF4FF;
            color: #3a84ff;
            padding: 8px;
          }

          .vip {
            background-color: #FFF1DB;
            color: #FE9C00;
          }

          .enabling {
            background-color: #E4FAF0;
            color: #14A568;
          }

          .deactivated {
            background-color: #F0F1F5;
            color: #63656E;
          }

          .icon-ag-yiqiyong,
          .icon-ag-minus-circle {
            font-size: 14px;
          }
        }
      }

      .header-info-description {
        margin-top: 8px;
        margin-bottom: 23px;
      }
      .header-info-button {
        display: flex;

        .btn-line {
          width: 1px;
          height: 16px;
          background-color: #DCDEE5;
          margin-right: 8px;
          margin-top: 8px;
        }
        .operate-btn {
          min-width: 88px;
          margin-right: 8px;
          .icon-help {
            color: #c4c6cc;
            margin-right: 2px;
          }
        }

        .deactivate-btn {
          &:hover {
            background-color: #ff5656;
            border-color: #ff5656;
            color: #ffffff;
          }
        }
      }
    }
  }

  .basic-info-detail {
    padding: 24px;
    margin-top: 16px;
    background: #ffffff;
    box-shadow: 0 2px 4px 0 #1919290d;

    &-item {
      &:not(&:first-child) {
        padding-top: 40px;
      }

      .detail-item-title {
        font-weight: 700;
        font-size: 14px;
        color: #313238;
      }

      .detail-item-content {
        padding-left: 100px;
        padding-top: 24px;

        &-item {
          display: flex;
          align-items: center;
          line-height: 32px;

          .label {
            color: #63656E;
            min-width: 60px;
            text-align: right;
            &.w0 {
              min-width: 0px;
            }
          }

          .value {
            display: flex;
            align-items: center;
            vertical-align: middle;
            margin-left: 8px;
            flex: 1;
            color: #313238;

            .icon-ag-copy-info,
            .icon-ag-jump {
              margin-left: 3px;
              padding: 3px;
              color: #3A84FF;
              cursor: pointer;
            }

            .link {
              margin-right: 14px;
            }

            .more-detail {
              color: #3A84FF;
              cursor: pointer;
            }

            .apigateway-icon {
              font-size: 16px;
              color: #979BA5;
              &:hover {
                color: #3A84FF;
                cursor: pointer;
              }
              &.icon-ag-lock-fill1 {
                &:hover {
                  color: #979BA5;
                  cursor: default;
                }
              }
            }

            &.more-tip {
              display: flex;
              align-items: center;

              .icon-ag-info {
                color: #63656E;
                margin-right: 5px;
              }
            }

            &.public-key-content {
              min-width: 670px;
              height: 40px;
              line-height: 40px;
              background-color: #F5F7FA;
              color: #63656E;
              margin-left: 0;

              .value-icon-lock {
                width: 40px;
                background-color: #F0F1F5;
                border-radius: 2px 0 0 2px;
                text-align: center;
              }

              .value-public-key {
                width: calc(100% - 40px);
                display: flex;
                justify-content: space-between;
                padding: 0 12px;
              }
            }
          }
        }
        .explain {
          font-size: 12px;
          color: #4D4F56;
          margin-bottom: 14px;
        }
        .guide-wrapper {
          width: 912px;
          border-top: 1px solid #DCDEE5;
          .guide-item {
            border-bottom: 1px solid #DCDEE5;
            display: flex;
            height: 42px;
            line-height: 42px;
            padding-left: 16px;
            .item-name {
              font-weight: Bold;
              font-size: 12px;
              color: #4D4F56;
            }
            .item-values {
              display: flex;
              margin-left: 164px;
              .item {
                display: flex;
              }
              .line {
                width: 1px;
                height: 13px;
                margin: 15px 8px 0;
                background-color: #C4C6CC;
              }
              .value {
                font-size: 12px;
                color: #3A84FF;
                cursor: pointer;
              }
            }
          }
        }
      }
    }
  }
}
.gateways-name-tip {
  color: #979BA5;
  font-size: 14px;
}
</style>

<style>
.gateway-del-tips {
  color: #c7254e;
  padding: 3px 4px;
  margin: 0;
  background-color: rgba(0,0,0,.04);
  border-radius: 3px;
}
</style>
