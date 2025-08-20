/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<template>
  <div class="basic-info-wrapper">
    <BkAlert
      v-if="!basicInfoData.status"
      theme="warning"
      :title="`${t('当前网关已停用，如需使用，请先启用')}`"
      class="mb-15px"
    />
    <BkLoading :loading="basicInfoDetailLoading">
      <section class="header-info">
        <div
          class="header-info-left"
          :class="[
            { 'header-info-left-disabled': !basicInfoData.status }
          ]"
        >
          <span class="name">{{ basicInfoData?.name?.[0]?.toUpperCase() }}</span>
        </div>
        <div class="header-info-right">
          <div class="header-info-name">
            <span class="name">{{ basicInfoData.name }}</span>
            <div class="header-info-tag">
              <BkTag
                v-if="basicInfoData.kind === 0"
                theme="info"
              >
                {{ t('普通网关') }}
              </BkTag>
              <BkTag
                v-else
                theme="success"
              >
                {{ t('可编程网关') }}
              </BkTag>
              <BkTag
                v-if="basicInfoData.is_official"
                class="website"
              >
                {{ t('官网') }}
              </BkTag>
              <div v-if="basicInfoData.status > 0">
                <BkTag class="enabling">
                  <AgIcon name="yiqiyong" />
                  {{ t('启用中') }}
                </BkTag>
              </div>
              <BkTag
                v-if="!basicInfoData.status"
                class="deactivated"
              >
                <AgIcon name="minus-circle" />
                {{ t('已停用') }}
              </BkTag>
            </div>
          </div>
          <div class="header-info-description">
            <EditDesc
              field="description"
              width="600px"
              :placeholder="t('请输入描述')"
              :content="basicInfoData.description"
              @on-change="(e:Record<string, any>) => handleInfoChange(e)"
            />
          </div>
          <div class="header-info-button">
            <div>
              <BkButton
                v-if="basicInfoData.status > 0"
                class="deactivate-btn operate-btn"
                @click="() => handleOperate('enable')"
              >
                {{ t('停用') }}
              </BkButton>
              <BkButton
                v-else
                theme="primary"
                class="operate-btn"
                @click="() => handleOperate('deactivate')"
              >
                {{ t('立即启用') }}
              </BkButton>
            </div>
            <template v-if="basicInfoData.status > 0">
              <BkPopover :content="t('请先停用才可删除')">
                <BkButton
                  class="operate-btn"
                  :disabled="basicInfoData.status > 0"
                >
                  {{ t('删除') }}
                </BkButton>
              </BkPopover>
            </template>
            <template v-else>
              <BkButton
                class="operate-btn"
                @click="() => handleOperate('delete')"
              >
                {{ t('删除') }}
              </BkButton>
            </template>
            <template v-if="basicInfoData.kind === 1">
              <span class="btn-line" />
              <BkButton
                class="operate-btn"
                @click="showGuide"
              >
                <AgIcon
                  name="help-document-fill"
                  class="icon-help"
                />
                {{ t('查看开发指引') }}
              </BkButton>
            </template>
          </div>
        </div>
      </section>
      <section class="basic-info-detail">
        <div class="basic-info-detail-item">
          <div class="detail-item-title">
            {{ t('基础信息') }}
            <div
              class="area-edit"
              @click.stop="() => handleOperate('edit')"
            >
              <AgIcon name="edit-line" />
              <BkButton
                theme="primary"
                text
                class="operate-btn"
              >
                {{ t('编辑') }}
              </BkButton>
            </div>
          </div>
          <div class="detail-item-content">
            <template v-if="featureFlagStore.isTenantMode">
              <div class="detail-item-content-item">
                <div class="label">
                  {{ `${t('租户模式')}：` }}
                </div>
                <div class="value">
                  <span>{{ TENANT_MODE_TEXT_MAP[basicInfoData.tenant_mode] || '--' }}</span>
                </div>
              </div>
              <div class="detail-item-content-item">
                <div class="label">
                  {{ `${t('租户 ID')}：` }}
                </div>
                <div class="value url">
                  <span>{{ basicInfoData.tenant_id || '--' }}</span>
                  <CopyButton :source="basicInfoData.tenant_id" />
                </div>
              </div>
            </template>
            <div
              v-if="basicInfoData.kind === 1"
              class="detail-item-content-item"
            >
              <div class="label">
                {{ `${t('开发语言')}：` }}
              </div>
              <div class="value">
                <span>{{ basicInfoData.extra_info?.language || '--' }}</span>
              </div>
            </div>
            <div
              v-if="basicInfoData.kind === 1"
              class="detail-item-content-item"
            >
              <div class="label">
                {{ `${t('代码仓库')}：` }}
              </div>
              <div class="value">
                <span>{{ basicInfoData.extra_info?.repository || '--' }}</span>
                <AgIcon
                  name="jump"
                  @click.stop="() => handleOpenNav(basicInfoData.extra_info.repository)"
                />
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">
                {{ `${t('是否公开')}：` }}
              </div>
              <div class="value">
                <BkSwitcher
                  v-model="basicInfoData.is_public"
                  theme="primary"
                  size="small"
                  class="min-w-28px"
                  @change="handleChangePublic"
                />
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">
                {{ `${t('访问域名')}：` }}
              </div>
              <div class="value url">
                <span>{{ basicInfoData.api_domain || '--' }}</span>
                <CopyButton :source="basicInfoData.api_domain" />
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">
                {{ `${t('维护人员')}：` }}
              </div>
              <div class="value">
                <EditMember
                  v-if="!featureFlagStore.isTenantMode"
                  mode="edit"
                  width="600px"
                  field="maintainers"
                  is-required
                  :placeholder="t('请选择维护人员')"
                  :content="basicInfoData.maintainers"
                  :is-error-class="'maintainers-error-tip'"
                  :error-value="t('维护人员不能为空')"
                  @on-change="(e:Record<string, any>) => handleMaintainerChange(e)"
                />
                <TenantUserSelector
                  v-else
                  :content="basicInfoData.maintainers"
                  :error-value="t('维护人员不能为空')"
                  :is-error-class="'maintainers-error-tip'"
                  is-required
                  :placeholder="t('请选择维护人员')"
                  field="maintainers"
                  mode="edit"
                  width="600px"
                  @on-change="(e:Record<string, any>) => handleMaintainerChange(e)"
                />
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">
                {{ `${t('创建人')}：` }}
              </div>
              <div class="value">
                <span v-if="!featureFlagStore.isEnableDisplayName">{{ basicInfoData.created_by }}</span>
                <span v-else><bk-user-display-name :user-id="basicInfoData.created_by" /></span>
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label">
                {{ `${t('创建时间')}：` }}
              </div>
              <div class="value">
                <span class="link">{{ basicInfoData.created_time || '--' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="basic-info-detail-item">
          <div class="detail-item-title">
            {{ t('API文档') }}
            <div
              class="area-edit"
              @click.stop="showApiDocEdit"
            >
              <AgIcon name="edit-line" />
              <BkButton
                theme="primary"
                text
                class="operate-btn"
              >
                {{ t('编辑') }}
              </BkButton>
            </div>
          </div>
          <div class="detail-item-content">
            <div class="detail-item-content-item">
              <div class="label">
                {{ `${t('联系人类型')}：` }}
              </div>
              <div class="value">
                <span class="link">{{ basicInfoData.doc_maintainers?.type === 'user' ? t('用户') : t('服务号') }}</span>
              </div>
            </div>

            <div
              v-show="basicInfoData.doc_maintainers?.type === 'user'"
              class="detail-item-content-item contact"
            >
              <div class="label">
                {{ `${t('联系人')}：` }}
              </div>
              <div class="value contact">
                <span>
                  <EditMember
                    v-if="!featureFlagStore.isEnableDisplayName"
                    mode="detail"
                    width="600px"
                    field="contacts"
                    :content="basicInfoData.doc_maintainers?.contacts"
                  />
                  <TenantUserSelector
                    v-else
                    :content="basicInfoData.doc_maintainers?.contacts"
                    field="contacts"
                    mode="detail"
                    width="600px"
                  />
                </span>
                <div class="sub-explain">
                  {{ t('文档页面上展示出来的文档咨询接口人') }}
                </div>
              </div>
            </div>

            <div
              v-show="basicInfoData.doc_maintainers?.type === 'service_account'"
              class="detail-item-content-item"
            >
              <div class="label">
                {{ `${t('服务号名称')}：` }}
              </div>
              <div class="value">
                <span class="link">{{ basicInfoData.doc_maintainers?.service_account?.name || '--' }}</span>
              </div>
            </div>

            <div
              v-show="basicInfoData.doc_maintainers?.type === 'service_account'"
              class="detail-item-content-item"
            >
              <div class="label">
                {{ `${t('服务号链接')}：` }}
              </div>
              <div class="value">
                <span class="link">{{ basicInfoData.doc_maintainers?.service_account?.link || '--' }}</span>
              </div>
            </div>

            <div class="detail-item-content-item">
              <div class="label">
                {{ `${t('文档地址')}：` }}
              </div>
              <div class="value url">
                <span
                  v-bk-tooltips="{
                    content: t('网关未开启或公开，暂无文档地址'),
                    placement: 'right',
                    disabled: !!basicInfoData.docs_url,
                  }"
                  class="link"
                >
                  {{ basicInfoData.docs_url || '--' }}
                </span>
                <template v-if="basicInfoData.docs_url">
                  <AgIcon
                    name="jump"
                    @click.stop="handleOpenNav(basicInfoData.docs_url)"
                  />
                  <CopyButton :source="basicInfoData.docs_url" />
                </template>
              </div>
            </div>
          </div>
        </div>

        <div class="basic-info-detail-item">
          <div class="detail-item-title">
            {{ t('API公钥（指纹）') }}
          </div>
          <div class="detail-item-content">
            <div class="detail-item-content-item">
              <div class="label w-0px" />
              <div class="value public-key-content">
                <div class="value-icon-lock">
                  <AgIcon name="lock-fill1" />
                </div>
                <div class="value-public-key">
                  <span class="link">
                    {{ basicInfoData.public_key_fingerprint }}
                  </span>
                  <div>
                    <CopyButton :source="basicInfoData.public_key" />
                    <AgIcon
                      name="download"
                      size="16"
                      @click.stop="handleDownload"
                    />
                  </div>
                </div>
              </div>
            </div>
            <div class="detail-item-content-item">
              <div class="label w-0px" />
              <div class="value more-tip">
                <AgIcon name="info" />
                <span>{{ t('可用于解密传入后端接口的请求头 X-Bkapi-JWT') }}，</span>
                <a
                  :href="envStore.env.DOC_LINKS.JWT"
                  target="_blank"
                  class="more-detail"
                >{{ t(' 更多详情') }}</a>
              </div>
            </div>
          </div>
        </div>
        <div
          v-if="basicInfoData.kind === 1"
          class="basic-info-detail-item"
        >
          <div class="detail-item-title">
            {{ t('可编程网关工作流') }}
          </div>
          <div class="detail-item-content">
            <img
              class="process-img"
              :src="ProgramProcess"
              :alt="t('可编程网关的流程图')"
            >
          </div>
        </div>
        <div
          v-if="basicInfoData.kind === 1"
          class="basic-info-detail-item"
        >
          <div class="detail-item-title">
            {{ t('关联操作指引') }}
          </div>
          <div class="detail-item-content">
            <div class="explain">
              {{ t('可编程网关发布后，系统将在蓝鲸开发者中心部署一个 SaaS 来提供 API 的后端服务，与蓝鲸 SaaS 开发相关的操作均可在蓝鲸开发者中心完成') }}
            </div>
            <div class="guide-wrapper">
              <div class="guide-item">
                <div class="item-name">
                  {{ t('开发 API') }}
                </div>
                <div class="item-values">
                  <div
                    v-for="(item, index) in basicInfoData.links?.develop"
                    :key="item.name"
                    class="item"
                  >
                    <a
                      class="value"
                      :href="item.link"
                      target="_blank"
                    >{{ item.name }}</a>
                    <span
                      v-if="index !== basicInfoData.links?.develop?.length - 1"
                      class="line"
                    />
                  </div>
                </div>
              </div>

              <div class="guide-item">
                <div class="item-name">
                  {{ t('查询日志') }}
                </div>
                <div class="item-values">
                  <div
                    v-for="(item, index) in basicInfoData.links?.logging"
                    :key="item.name"
                    class="item"
                  >
                    <a
                      class="value"
                      :href="item.link"
                      target="_blank"
                    >{{ item.name }}</a>
                    <span
                      v-if="index !== basicInfoData.links?.logging?.length - 1"
                      class="line"
                    />
                  </div>
                </div>
              </div>

              <div class="guide-item">
                <div class="item-name">
                  {{ t('更多操作') }}
                </div>
                <div class="item-values">
                  <div
                    v-for="(item, index) in basicInfoData.links?.more"
                    :key="item.name"
                    class="item"
                  >
                    <a
                      class="value"
                      :href="item.link"
                      target="_blank"
                    >{{ item.name }}</a>
                    <span
                      v-if="index !== basicInfoData.links?.more?.length - 1"
                      class="line"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </BkLoading>

    <BkDialog
      width="540"
      :is-show="delApigwDialog.isShow"
      :title="t(`确认删除网关【{basicInfoDataName}】？`, { basicInfoDataName: basicInfoData.name })"
      :theme="'primary'"
      :loading="delApigwDialog.loading"
      @closed="delApigwDialog.isShow = false"
    >
      <div class="ps-form">
        <div
          v-dompurify-html="delTips"
          class="form-tips"
        />
        <div class="mt-15px">
          <BkInput v-model="formRemoveConfirmApigw" />
        </div>
      </div>
      <template #footer>
        <BkButton
          theme="primary"
          :disabled="!formRemoveApigw"
          class="mr-8px"
          @click="handleDeleteApigw"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton @click="delApigwDialog.isShow = false">
          {{ t('取消') }}
        </BkButton>
      </template>
    </BkDialog>
    <EditAPIDoc
      v-model="isShowApiDoc"
      :data="basicInfoData"
      @done="getBasicInfo"
    />
    <CreateGateway
      v-model="createGatewayShow"
      :init-data="basicInfoDetailData"
      @done="getBasicInfo"
    />
    <AgSideslider
      v-model="isShowMarkdown"
      :title="t('查看开发指引')"
      :width="960"
    >
      <section class="markdown-box">
        <Guide :markdown-html="markdownHtml" />
      </section>
    </AgSideslider>
  </div>
</template>

<script setup lang="ts">
import { cloneDeep } from 'lodash-es';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import {
  deleteGateway,
  getGatewayDetail,
  getGuideDocs,
  patchGateway,
  putGatewayBasics,
  toggleStatus,
} from '@/services/source/gateway.ts';
import EditDesc from './components/EditDesc.vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import ProgramProcess from '@/images/program-process.png';
import EditMember from './components/EditMember.vue';
import CreateGateway from '@/components/create-gateway/Index.vue';
import AgSideslider from '@/components/ag-sideslider/Index.vue';
import Guide from '@/components/guide/Index.vue';
import { TENANT_MODE_TEXT_MAP } from '@/enums';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
} from '@/stores';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import EditAPIDoc from '@/views/basic-info/components/EditAPIDoc.vue';

type BasicInfoType = Awaited<ReturnType<typeof getGatewayDetail>>;

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
const gatewayStore = useGateway();

// 网关id
const apigwId = ref(0);
const formRemoveConfirmApigw = ref('');
const basicInfoDetailLoading = ref(false);
const createGatewayShow = ref(false);
const isShowMarkdown = ref(false);
const markdownHtml = ref('');
const isShowApiDoc = ref(false);

// 当前网关基本信息
const basicInfoData = ref<BasicInfoType>({
  status: 1,
  name: '',
  description: '',
  description_en: '',
  public_key_fingerprint: '',
  bk_app_codes: [],
  related_app_codes: [],
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
const basicInfoDetailData = ref(cloneDeep(basicInfoData.value));
const delApigwDialog = ref({
  isShow: false,
  loading: false,
});
const statusChanging = ref(false);

const formRemoveApigw = computed(() => {
  return basicInfoData.value.name === formRemoveConfirmApigw.value;
});

const delTips = computed(() => {
  return t(`请完整输入<code class="gateway-del-tips">${basicInfoData.value.name}</code> 来确认删除网关！`);
});

// 获取网关基本信息
const getBasicInfo = async () => {
  basicInfoData.value = await getGatewayDetail(apigwId.value);
};

watch(
  () => route.params,
  () => {
    if (route.params?.id) {
      apigwId.value = Number(route.params.id);
      getBasicInfo();
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

const showApiDocEdit = () => {
  isShowApiDoc.value = true;
};

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
      }
    }
    catch {
      return str;
    }
    return str;
  },
});

const showGuide = async () => {
  const data = await getGuideDocs(apigwId.value);
  markdownHtml.value = md.render(data.content);
  isShowMarkdown.value = true;
};

const handleDeleteApigw = async () => {
  await deleteGateway(apigwId.value);
  Message({
    theme: 'success',
    message: t('删除成功'),
    width: 'auto',
  });
  delApigwDialog.value.isShow = false;
  setTimeout(() => {
    router.push({ name: 'Home' });
    gatewayStore.clearCurrentGateway();
    gatewayStore.setApigwId(0);
    gatewayStore.setApigwName('');
  }, 200);
};

const handleChangePublic = async (value: boolean) => {
  basicInfoData.value.is_public = value;
  await patchGateway(apigwId.value, basicInfoData.value);
  Message({
    message: t('更新成功'),
    theme: 'success',
    width: 'auto',
  });
};

const handleChangeApigwStatus = async () => {
  const status = basicInfoData.value.status === 1 ? 0 : 1;
  try {
    statusChanging.value = true;
    const res = await toggleStatus(apigwId.value, { status });
    if (res) {
      basicInfoData.value = Object.assign(basicInfoData.value, { status });
      Message({
        theme: 'success',
        message: status === 1 ? t('启用网关成功') : t('停用网关成功'),
        width: 'auto',
      });
    }
    await getBasicInfo();
  }
  catch (e) {
    console.error(e);
  }
  finally {
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
    basicInfoDetailData.value = cloneDeep(basicInfoData.value);
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
  }
  else {
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
  const blob: any = new Blob([public_key], { type: 'text/plain' });
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
  await patchGateway(apigwId.value, params);
  basicInfoData.value = Object.assign(basicInfoData.value, params);
  Message({
    message: t('编辑成功'),
    theme: 'success',
    width: 'auto',
  });
};

const handleMaintainerChange = async (payload: { maintainers?: string[] }) => {
  await putGatewayBasics(apigwId.value, payload);
  basicInfoData.value = Object.assign(basicInfoData.value, payload);
  Message({
    message: t('编辑成功'),
    theme: 'success',
    width: 'auto',
  });
};

</script>

<style lang="scss" scoped>
.markdown-box {
  padding: 20px 24px;
}

.basic-info-wrapper {
  padding: 24px;
  font-size: 12px;

  .header-info {
    display: flex;
    padding: 24px;
    background: #fff;
    box-shadow: 0 2px 4px 0 #1919290d;

    &-left {
      position: relative;
      display: flex;
      width: 80px;
      height: 80px;
      background: #f0f5ff;
      border-radius: 8px;
      align-items: center;
      justify-content: center;

      // .kind {
      //   content: ' ';
      //   position: absolute;
      //   width: 20px;
      //   height: 20px;
      //   border-radius: 2px;
      //   top: 0;
      //   left: 0;
      //   font-size: 12px;
      //   line-height: 18px;
      //   text-align: center;
      //   &.normal {
      //     color: #1768EF;
      //     background: #E1ECFF;
      //     border: 1px solid #699DF4;
      //   }
      //   &.program {
      //     color: #299E56;
      //     background: #EBFAF0;
      //     border: 1px solid #A1E3BA;
      //   }
      // }

      .name {
        font-size: 40px;
        font-weight: 700;
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
      flex: 1;
      padding: 16px 16px 0;

      .header-info-name {
        display: flex;

        .name {
          font-size: 16px;
          font-weight: 700;
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
            padding: 8px;
            color: #3a84ff;
            background-color: #EDF4FF;
          }

          .vip {
            color: #FE9C00;
            background-color: #FFF1DB;
          }

          .enabling {
            color: #14A568;
            background-color: #E4FAF0;
          }

          .deactivated {
            color: #63656E;
            background-color: #F0F1F5;
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
          margin-top: 8px;
          margin-right: 8px;
          background-color: #DCDEE5;
        }

        .operate-btn {
          min-width: 88px;
          margin-right: 8px;

          .icon-help {
            margin-right: 2px;
            color: #c4c6cc;
          }
        }

        .deactivate-btn {

          &:hover {
            color: #fff;
            background-color: #ff5656;
            border-color: #ff5656;
          }
        }
      }
    }
  }

  .basic-info-detail {
    padding: 24px;
    margin-top: 16px;
    background: #fff;
    box-shadow: 0 2px 4px 0 #1919290d;

    &-item {

      &:not(&:first-child) {
        padding-top: 40px;
      }

      .detail-item-title {
        display: flex;
        font-size: 14px;
        font-weight: 700;
        color: #313238;
        align-items: center;

        .area-edit {
          margin-left: 14px;
          color: #3A84FF;
          cursor: pointer;

          .operate-btn {
            font-size: 12px;
          }
        }
      }

      .detail-item-content {
        padding-top: 24px;
        padding-left: 100px;

        .detail-item-content-item {
          display: flex;
          align-items: center;
          line-height: 32px;

          &.contact {
            align-items: flex-start;
          }

          .label {
            min-width: 70px;
            color: #63656E;
            text-align: right;

            &.w-0px {
              min-width: 0;
            }
          }

          .value {
            display: flex;
            margin-left: 8px;
            color: #313238;
            vertical-align: middle;
            align-items: center;
            flex: 1;

            &.contact {
              display: block;

              .sub-explain {
                margin-bottom: 6px;
                font-size: 12px;
                line-height: 12px;
                color: #979BA5;
              }
            }

            .icon-ag-copy-info,
            .icon-ag-jump {
              padding: 3px;
              margin-left: 3px;
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
                margin-right: 5px;
                color: #63656E;
              }
            }

            &.public-key-content {
              width: 912px;
              height: 40px;
              margin-left: 0;
              line-height: 40px;
              color: #63656E;
              background-color: #F5F7FA;
              flex: none;

              .value-icon-lock {
                width: 40px;
                text-align: center;
                background-color: #F0F1F5;
                border-radius: 2px 0 0 2px;
              }

              .value-public-key {
                display: flex;
                width: calc(100% - 40px);
                padding-right: 12px;
                padding-left: 32px;
                justify-content: space-between;
              }
            }
          }
        }

        .explain {
          margin-bottom: 14px;
          font-size: 12px;
          color: #4D4F56;
        }

        .guide-wrapper {
          width: 912px;
          border-top: 1px solid #DCDEE5;

          .guide-item {
            display: flex;
            height: 42px;
            padding-left: 16px;
            line-height: 42px;
            border-bottom: 1px solid #DCDEE5;

            .item-name {
              font-size: 12px;
              font-weight: bold;
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

        .process-img {
          width: 912px;
          height: 223px;
          background: #F5F7FA;
        }
      }
    }
  }
}

.gateways-name-tip {
  font-size: 14px;
  color: #979BA5;
}

:deep(.ag-markdown-view pre) {
  background: #F5F7FA;
}

:deep(.ag-markdown-view code) {
  color: #4D4F56;
}

:deep(.ag-markdown-view .ag-copy-btn) {
  color: #3A84FF;
  background: #F5F7FA;
}
</style>

<style>
.gateway-del-tips {
  padding: 3px 4px;
  margin: 0;
  color: #c7254e;
  background-color: rgb(0 0 0 / 4%);
  border-radius: 3px;
}
</style>
