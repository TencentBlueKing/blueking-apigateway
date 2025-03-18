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
          <span class="name">{{ basicInfoData?.name?.[0]?.toUpperCase() }}</span>
        </div>
        <div class="header-info-right">
          <div class="header-info-name">
            <span class="name">{{ basicInfoData.name }}</span>
            <div class="header-info-tag">
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
          </div>
        </div>
      </section>
      <section class="basic-info-detail">
        <div class="basic-info-detail-item">
          <div class="detail-item-title">{{ t('基础信息') }}</div>
          <div class="detail-item-content">
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

    <bk-dialog
      width="600"
      theme="primary"
      :is-show="dialogEditData.isShow"
      :title="dialogEditData.title"
      quick-close>
      <bk-form ref="formRef" form-type="vertical" :model="basicInfoDetailData" :rules="rules">
        <bk-form-item
          :label="t('名称')"
          property="name"
          required
        >
          <bk-input
            v-model="basicInfoDetailData.name"
            :maxlength="30"
            :disabled="true"
            :placeholder="t('请输入小写字母、数字、连字符(-)，以小写字母开头')"
          />
          <div class="gateways-name-tip">
            <span>{{ t('网关唯一标识，创建后不可修改') }}</span>
          </div>
        </bk-form-item>
        <bk-form-item
          :label="t('维护人员')"
          property="maintainers"
          required
        >
          <MemberSelect v-model="basicInfoDetailData.maintainers" :placeholder="t('请选择维护人员')" :has-delete-icon="true" />
        </bk-form-item>
        <bk-form-item
          :label="t('描述')"
          property="description"
        >
          <bk-input
            type="textarea"
            v-model="basicInfoDetailData.description"
            :placeholder="t('请输入网关描述')"
            :maxlength="500"
            :rows="5"
            clearable
          />
        </bk-form-item>
        <bk-form-item
          :label="t('是否公开')"
          property="is_public"
          required
        >
          <bk-switcher v-model="basicInfoDetailData.is_public" theme="primary" />
          <span class="common-form-tips">{{ t('公开，则用户可查看资源文档、申请资源权限；不公开，则网关对用户隐藏') }}</span>
        </bk-form-item>
        <bk-form-item
          :label="t('关联蓝鲸应用')"
          property="bk_app_codes"
          v-if="user?.featureFlags?.GATEWAY_APP_BINDING_ENABLED"
        >
          <bk-tag-input
            v-model="basicInfoDetailData.bk_app_codes"
            :placeholder="t('请输入蓝鲸应用ID，并按enter确认')"
            allow-create
            has-delete-icon
            collapse-tags
            :list="[]"
          />
          <span class="common-form-tips">{{ t('仅影响 HomePage 中运维开发分数的计算') }}</span>
        </bk-form-item>
        <bk-form-item
          :label="t('管理网关的应用列表 ')"
          property="related_app_codes"
        >
          <bk-tag-input
            v-model="basicInfoDetailData.related_app_codes"
            :placeholder="t('请输入蓝鲸应用ID，并按enter确认')"
            allow-create
            has-delete-icon
            collapse-tags
          />
          <span class="common-form-tips">{{ t('允许列表中的应用使用 sdk 或者开放 API 调用网关接口，同步环境/资源以及发布版本') }}</span>
        </bk-form-item>
      </bk-form>
      <template #footer>
        <bk-pop-confirm
          width="288"
          :content="t('您已将自己从维护人员列表中移除，移除后您将失去查看和编辑网关的权限。请确认！')"
          trigger="click"
          @confirm="handleConfirmEdit"
          @cancel="handleCloseEdit"
          v-if="!basicInfoDetailData.maintainers?.includes(user.user.username)"
        >
          <bk-button theme="primary" :loading="dialogEditData.loading">
            {{ t('确定') }}
          </bk-button>
        </bk-pop-confirm>
        <bk-button v-else theme="primary" @click="handleConfirmEdit" :loading="dialogEditData.loading">
          {{ t('确定') }}
        </bk-button>
        <bk-button @click="handleCloseEdit" class="ml8">
          {{ t('取消') }}
        </bk-button>
      </template>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import {  ref, computed, watch } from 'vue';
import _ from 'lodash';
import { Message, InfoBox } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useUser } from '@/store';
import {  copy } from '@/common/util';
import { useGetGlobalProperties } from '@/hooks';
// import { useStage } from '@/store';
import { BasicInfoParams, DialogParams } from './common/type';
import { getGateWaysInfo, toggleGateWaysStatus, deleteGateWays, editGateWays } from '@/http';
import GateWaysEditTextarea from '@/components/gateways-edit/textarea.vue';
import GateWaysEditMemberSelector from '@/components/gateways-edit/member-selector.vue';
import MemberSelect from '@/components/member-select';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const user = useUser();

const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length >= 3,
      message: t('不能小于3个字符'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length <= 30,
      message: t('不能多于30个字符'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-z][a-z0-9-]*$/;
        return reg.test(value);
      },
      message: '由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符',
      trigger: 'blur',
    },
  ],
};

// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

// 网关id
const apigwId = ref(0);
const formRef = ref(null);
const formRemoveConfirmApigw = ref('');
const basicInfoDetailLoading = ref(false);
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
});
const basicInfoDetailData = ref(_.cloneDeep(basicInfoData.value));
const delApigwDialog = ref<DialogParams>({
  isShow: false,
  loading: false,
});
const dialogEditData = ref<DialogParams>({
  isShow: false,
  loading: false,
  title: t('编辑网关'),
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
    }, 300);
  } catch (e) {
    console.error(e);
  }
};

const handleConfirmEdit = async () => {
  try {
    await formRef.value.validate();
    dialogEditData.value.loading = true;
    const params = _.cloneDeep(basicInfoDetailData.value);
    if (!user?.featureFlags?.GATEWAY_APP_BINDING_ENABLED) {
      params.bk_app_codes = undefined;
    }
    await editGateWays(apigwId.value, params);
    Message({
      message: t('编辑成功'),
      theme: 'success',
      width: 'auto',
    });
    dialogEditData.value.isShow = false;
    await getBasicInfo();
  } catch (error) {
  } finally {
    setTimeout(() => {
      dialogEditData.value.loading = false;
    }, 200);
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
    console.log('basicInfoDetailData.value', basicInfoDetailData.value);
    setTimeout(() => {
      dialogEditData.value.isShow = true;
    }, 500);
    return;
  }

  if (['delete'].includes(type)) {
    delApigwDialog.value.isShow = true;
    formRemoveConfirmApigw.value = '';
    return;
  }
};

const handleCloseEdit =  () => {
  dialogEditData.value.isShow = false;
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

        .operate-btn {
          min-width: 88px;
          margin-right: 8px;
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

            .icon-ag-copy-info {
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
