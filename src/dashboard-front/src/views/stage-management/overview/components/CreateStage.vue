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
  <div class="sideslider-wrapper">
    <BkSideslider
      v-model:is-show="isShow"
      render-directive="if"
      quick-close
      :width="960"
      ext-cls="stage-sideslider-cls"
      transfer
      @animation-end="handleAnimationEnd"
      @hidden="emit('hidden')"
    >
      <template #header>
        <div class="custom-side-header">
          <div class="title">
            {{ title }}
          </div>
          <template v-if="!isAdd">
            <span />
            <div class="subtitle">
              {{ curStageData.name }}
            </div>
          </template>
        </div>
      </template>
      <template #default>
        <BkLoading :loading="isDialogLoading">
          <div
            v-if="actionType !== 'check'"
            class="sideslider-content"
          >
            <BkCollapse
              v-model="activeKey"
              class="bk-collapse-service"
            >
              <BkCollapsePanel name="base-info">
                <template #header>
                  <div class="panel-header">
                    <AgIcon
                      name="down-shape"
                      :class="[activeKey?.includes('base-info') ? 'panel-header-show' : 'panel-header-hide']"
                    />
                    <div class="title">
                      {{ t('基础信息') }}
                    </div>
                  </div>
                </template>
                <template #content>
                  <div class="content">
                    <BkForm
                      ref="baseInfoRef"
                      :label-width="180"
                      :model="curStageData"
                      form-type="vertical"
                    >
                      <BkFormItem
                        :label="t('环境名称')"
                        required
                        property="name"
                        :rules="rules.name"
                      >
                        <BkInput
                          v-model="curStageData.name"
                          :placeholder="t('请输入 2-20 字符的字母、数字、连字符(-)、下划线(_)，以字母开头')"
                          :disabled="!isAdd"
                        />
                        <p class="color-#979ba5 line-height-20px text-12px mt-2px">
                          {{ t('环境唯一标识，创建后不可修改。创建网关成功后可新增环境') }}
                        </p>
                      </BkFormItem>
                      <BkFormItem label="">
                        <div class="address">
                          <label>{{ t('访问地址') }}：</label>
                          <!-- 网关名/环境名 -->
                          <span>{{ stageAddress || '--' }}</span>
                          <CopyButton :source="stageAddress" />
                        </div>
                      </BkFormItem>
                      <BkFormItem
                        :label="t('描述')"
                        class="last-form-item"
                      >
                        <BkInput
                          v-model="curStageData.description"
                          :placeholder="t('请输入描述')"
                        />
                      </BkFormItem>
                    </BkForm>
                  </div>
                </template>
              </BkCollapsePanel>

              <BkCollapsePanel name="stage-config">
                <template #header>
                  <div class="panel-header">
                    <AgIcon
                      name="down-shape"
                      :class="[activeKey?.includes('stage-config') ? 'panel-header-show' : 'panel-header-hide']"
                    />
                    <div class="title">
                      {{ t('环境的后端服务配置') }}
                    </div>
                  </div>
                </template>
                <template #content>
                  <div class="stage">
                    <BkCollapse
                      v-model="activeIndex"
                      :list="curStageData.backends"
                      header-icon="right-shape"
                    >
                      <template #title="backend">
                        <span class="stage-name">
                          {{ backend.name }}
                        </span>
                      </template>
                      <template #content="backend">
                        <BkForm
                          :ref="setBackendConfigRef"
                          :label-width="180"
                          :model="backend"
                          form-type="vertical"
                        >
                          <BkFormItem
                            required
                            :label="t('负载均衡类型')"
                            class="mt-20px relative"
                            property="config.loadbalance"
                          >
                            <BkSelect
                              v-model="backend.config.loadbalance"
                              :clearable="false"
                              :placeholder="t('负载均衡类型')"
                              @change="(value: string) => handleLoadBalanceChange(value, backend.id)"
                            >
                              <BkOption
                                v-for="option in loadbalanceList"
                                :id="option.id"
                                :key="option.id"
                                :name="option.name"
                              />
                            </BkSelect>
                            <BkLink
                              class="absolute right-0 top--30px"
                              theme="primary"
                              :href="envStore.env.DOC_LINKS.LOADBALANCE"
                              target="_blank"
                            >
                              <AgIcon
                                name="jump"
                                size="12"
                                class="mr-4px"
                              />
                              <span class="text-12px">{{ t('帮助文档') }}</span>
                            </BkLink>
                          </BkFormItem>

                          <!-- hash_on -->
                          <BkFormItem
                            v-if="backend.config.loadbalance === 'chash'"
                            :label="t('哈希位置')"
                            property="config.hash_on"
                            required
                          >
                            <BkSelect
                              v-model="backend.config.hash_on"
                              :clearable="false"
                              :filterable="false"
                              @change="(value: string) => handleHashOnChange(value, backend.id)"
                            >
                              <BkOption
                                v-for="type in hashOnOptions"
                                :id="type.id"
                                :key="type.id"
                                :name="type.name"
                              />
                            </BkSelect>
                          </BkFormItem>

                          <KeyFormItem
                            v-if="backend.config.loadbalance === 'chash'"
                            :stage-config="backend"
                            label="Key"
                            property="config.key"
                            required
                            config-field="config"
                            @change="handleHashOnKeyChange"
                          />

                          <BkFormItem
                            v-for="(hostItem, index) of backend.config.hosts"
                            :key="index"
                            :label="t('后端服务地址')"
                            required
                            :property="`config.hosts.${index}.host`"
                            :rules="rules.host"
                            class="backend-item-cls"
                            :class="[{ 'form-item-special': index !== 0 }]"
                          >
                            <div class="host-item">
                              <BkInput
                                :key="backend.config.loadbalance"
                                v-model="hostItem.host"
                                :placeholder="t('格式: host:port')"
                              >
                                <template #prefix>
                                  <BkSelect
                                    v-model="hostItem.scheme"
                                    class="scheme-select-cls"
                                    :clearable="false"
                                  >
                                    <BkOption
                                      v-for="(item, index1) in schemeList"
                                      :key="index1"
                                      :value="item.value"
                                      :label="item.value"
                                    />
                                  </BkSelect>
                                  <div class="slash">
                                    ://
                                  </div>
                                </template>
                                <template
                                  v-if="backend.config.loadbalance === 'weighted-roundrobin'"
                                  #suffix
                                >
                                  <BkFormItem
                                    :rules="rules.weight"
                                    :property="`config.hosts.${index}.weight`"
                                    label=""
                                    class="weight-input"
                                  >
                                    <BkInput
                                      v-model="hostItem.weight"
                                      class="suffix-slot-cls weights-input"
                                      :class="[{ 'is-error': hostItem.isRoles }]"
                                      :placeholder="t('权重')"
                                      type="number"
                                      :min="1"
                                      :max="10000"
                                    />
                                  </BkFormItem>
                                </template>
                              </BkInput>

                              <AgIcon
                                name="plus-circle-shape"
                                class="ml-13px"
                                @click="() => handleAddServiceAddress(backend.name)"
                              />
                              <AgIcon
                                name="minus-circle-shape"
                                class="ml-10px"
                                :class="{ disabled: backend.config.hosts.length < 2 }"
                                @click="
                                  backend.config.hosts.length < 2 ?
                                    '' :
                                    handleDeleteServiceAddress(backend.name, index)"
                              />
                            </div>
                          </BkFormItem>

                          <BkFormItem
                            :label="t('超时时间')"
                            required
                            :property="'config.timeout'"
                            class="timeout-item-cls"
                            :rules="rules.timeout"
                            :error-display-type="'normal'"
                          >
                            <BkInput
                              v-model="backend.config.timeout"
                              type="number"
                              :min="1"
                              :max="300"
                            >
                              <template #suffix>
                                <div
                                  class="group-text group-text-style"
                                  :class="locale === 'en' ? 'long' : ''"
                                >
                                  {{ t('秒') }}
                                </div>
                              </template>
                            </BkInput>
                            <p
                              class="timeout-tip"
                              :class="locale === 'en' ? 'long' : ''"
                            >
                              {{ t('最大 300 秒') }}
                            </p>
                          </BkFormItem>

                          <HealthChecks
                            v-if="featureFlagStore.flags.ENABLE_HEALTH_CHECK"
                            :ref="(el) => setHealthChecksRef(el, backend)"
                            :checks="backend.config.checks"
                          />
                        </BkForm>
                      </template>
                    </BkCollapse>
                  </div>
                </template>
              </BkCollapsePanel>
            </BkCollapse>
          </div>
          <div
            v-else
            class="sideslider-content check-mode"
          >
            <div class="title">
              {{ t("基本信息") }}
            </div>
            <BkContainer
              class="ag-kv-box"
              :col="14"
            >
              <BkRow>
                <BkCol :span="2">
                  <label class="ag-key">{{ t("环境名称") }}: </label>
                </BkCol>
                <BkCol :span="12">
                  <div class="ag-value">
                    {{ curStageData.name }}
                  </div>
                </BkCol>
              </BkRow>

              <BkRow>
                <BkCol
                  :span="2"
                  class="mt-8px"
                >
                  <label class="ag-key">{{ t("访问地址") }}:</label>
                </BkCol>
                <BkCol :span="12">
                  <div class="ag-value address">
                    <span>{{ stageAddress || '--' }}</span>
                    <CopyButton :source="stageAddress" />
                  </div>
                </BkCol>
              </BkRow>
            </BkContainer>

            <template
              v-for="backend in curStageData.backends"
              :key="backend.name"
            >
              <div
                class="title truncate w-full"
                :class="{ highlighted: backend.name === selectedBackendName }"
              >
                <span>{{ `${t('后端服务')}:` }}</span>
                <span class="ml-8px">{{ backend.name }}</span>
              </div>
              <BkContainer
                class="ag-kv-box"
                :class="{ highlighted: backend.name === selectedBackendName }"
                :col="14"
              >
                <template v-if="backend.config.hosts?.length > 1">
                  <BkRow>
                    <BkCol :span="2">
                      <label class="ag-key">{{ t("负载均衡类型") }}:</label>
                    </BkCol>
                    <BkCol :span="8">
                      <div class="ag-value">
                        {{ getLoadBalanceText(backend.config.loadbalance) }}
                      </div>
                    </BkCol>
                  </BkRow>
                  <BkRow>
                    <BkCol :span="2">
                      <label class="ag-key">{{ t('哈希位置') }}:</label>
                    </BkCol>
                    <BkCol :span="8">
                      <div class="ag-value">
                        {{ backend.config.hash_on || '--' }}
                      </div>
                    </BkCol>
                  </BkRow>
                  <BkRow>
                    <BkCol :span="2">
                      <label class="ag-key">Key:</label>
                    </BkCol>
                    <BkCol :span="8">
                      <div class="ag-value">
                        {{ backend.config.key || '--' }}
                      </div>
                    </BkCol>
                  </BkRow>
                </template>
                <template
                  v-for="host in backend.config.hosts"
                  :key="host.host"
                >
                  <BkRow>
                    <BkCol :span="2">
                      <label class="ag-key">{{ t("后端服务地址") }}:</label>
                    </BkCol>
                    <BkCol :span="12">
                      <div class="ag-value">
                        {{ `${host.scheme}://${host.host}` }}
                      </div>
                    </BkCol>
                  </BkRow>
                  <BkRow v-if="backend.config.loadbalance === 'weighted-roundrobin'">
                    <BkCol :span="2">
                      <label class="ag-key">{{ t("权重") }}:</label>
                    </BkCol>
                    <BkCol :span="12">
                      <div class="ag-value">
                        {{ host.weight }}
                      </div>
                    </BkCol>
                  </BkRow>
                </template>
                <BkRow>
                  <BkCol :span="2">
                    <label class="ag-key">{{ t("超时时间") }}:</label>
                  </BkCol>
                  <BkCol :span="12">
                    <div class="ag-value">
                      {{ `${backend.config.timeout}秒` }}
                    </div>
                  </BkCol>
                </BkRow>

                <template v-if="Object.keys(backend.config.checks || {}).length">
                  <template v-if="backend.config.checks.active">
                    <BkRow>
                      <BkCol :span="2" />
                      <BkCol
                        :span="12"
                        :offset="2"
                      >
                        <div class="ag-value font-bold">
                          {{ `${t('健康检查')} - ${t('主动检查')}` }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('类型') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.type }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow v-if="backend.config.checks.active.type === 'https'">
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('是否检查证书') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.https_verify_certificate ? t('是') : t('否') }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('超时时间(s)') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.timeout }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('并行数量') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.concurrency }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow v-if="backend.config.checks.active.type !== 'tcp'">
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('健康检查.请求路径') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.http_path }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2" />
                      <BkCol
                        :span="12"
                        :offset="2"
                      >
                        <div class="ag-value font-bold">
                          {{ t('健康状态') }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('间隔时间(s)') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.healthy.interval }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow v-if="backend.config.checks.active.type !== 'tcp'">
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('状态码') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.healthy.http_statuses }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('成功次数') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.healthy.successes }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2" />
                      <BkCol
                        :span="12"
                        :offset="2"
                      >
                        <div class="ag-value font-bold">
                          {{ t('不健康状态') }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('间隔时间(s)') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.unhealthy.interval }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow v-if="backend.config.checks.active.type !== 'tcp'">
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('状态码') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.unhealthy.http_statuses }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('失败次数') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{
                            backend.config.checks.active.type === 'tcp'
                              ? backend.config.checks.active.unhealthy.tcp_failures
                              : backend.config.checks.active.unhealthy.http_failures
                          }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('超时时间(s)') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.active.unhealthy.timeouts }}
                        </div>
                      </BkCol>
                    </BkRow>
                  </template>
                  <template v-if="backend.config.checks.passive">
                    <BkRow>
                      <BkCol :span="2" />
                      <BkCol
                        :span="12"
                        :offset="2"
                      >
                        <div class="ag-value font-bold">
                          {{ `${t('健康检查')} - ${t('被动检查')}` }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('类型') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.passive.type }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2" />
                      <BkCol
                        :span="12"
                        :offset="2"
                      >
                        <div class="ag-value font-bold">
                          {{ t('健康状态') }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow v-if="backend.config.checks.passive.type !== 'tcp'">
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('状态码') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.passive.healthy.http_statuses }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('成功次数') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.passive.healthy.successes }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow>
                      <BkCol :span="2" />
                      <BkCol
                        :span="12"
                        :offset="2"
                      >
                        <div class="ag-value font-bold">
                          {{ t('不健康状态') }}
                        </div>
                      </BkCol>
                    </BkRow>

                    <BkRow v-if="backend.config.checks.passive.type !== 'tcp'">
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('状态码') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.passive.unhealthy.http_statuses }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('失败次数') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{
                            backend.config.checks.passive.type === 'tcp'
                              ? backend.config.checks.passive.unhealthy.tcp_failures
                              : backend.config.checks.passive.unhealthy.http_failures
                          }}
                        </div>
                      </BkCol>
                    </BkRow>
                    <BkRow>
                      <BkCol :span="2">
                        <label class="ag-key">{{ t('超时时间(s)') }}:</label>
                      </BkCol>
                      <BkCol :span="12">
                        <div class="ag-value">
                          {{ backend.config.checks.passive.unhealthy.timeouts }}
                        </div>
                      </BkCol>
                    </BkRow>
                  </template>
                </template>
              </BkContainer>
            </template>
          </div>

          <div
            v-if="actionType !== 'check'"
            class="footer-btn-wrapper"
          >
            <BkButton
              theme="primary"
              class="w-90px"
              @click="handleConfirm"
            >
              {{ t('确定') }}
            </BkButton>
            <BkButton
              class="w-90px ml-8px"
              @click="handleCancel"
            >
              {{ t('取消') }}
            </BkButton>
          </div>

          <div
            v-show="isAdsorb"
            class="fixed-footer-btn-wrapper"
          >
            <BkButton
              theme="primary"
              class="w-88px"
              @click="handleConfirm"
            >
              {{ t('确定') }}
            </BkButton>
            <BkButton
              class="w-88px ml-8px"
              @click="handleCancel"
            >
              {{ t('取消') }}
            </BkButton>
          </div>
        </BkLoading>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import {
  createStage,
  getStageBackends,
  getStageDetail,
  putStage,
} from '@/services/source/stage';
import { getBackendServiceList } from '@/services/source/backend-services.ts';
import { Form, Message } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
} from '@/stores';
import KeyFormItem from '@/views/backend-services/components/KeyFormItem.vue';
import HealthChecks from '@/views/backend-services/components/health-checks/Index.vue';

interface IProps { stageId?: number }

const { stageId = 0 } = defineProps<IProps>();

const emit = defineEmits<{
  hidden: [void]
  done: [void]
}>();

const { t, locale } = useI18n();
const route = useRoute();
const envStore = useEnv();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

const isShow = ref(false);
const isAdsorb = ref(false);
const activeKey = ref(['base-info', 'stage-config']);
const activeIndex = ref([0]);
const actionType = ref('add');
// 需要高亮的后端服务名称
const selectedBackendName = ref('');

const curStageData = ref({
  name: '',
  description: '',
  backends: [
    {
      name: '',
      config: {
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
      },
    },
  ],
});

// 侧边loading
const isDialogLoading = ref(true);

// 获取对应Ref
const baseInfoRef = ref();

// 默认为新建
const isAdd = ref(true);

// 负载均衡类型
const loadbalanceList = [
  {
    id: 'roundrobin',
    name: t('轮询（Round-Robin）'),
  },
  {
    id: 'weighted-roundrobin',
    name: t('加权轮询（Weighted Round-Robin）'),
  },
  {
    id: 'chash',
    name: t('一致性哈希（CHash）'),
  },
  {
    id: 'ewma',
    name: t('指数加权移动平均法（EWMA）'),
  },
  {
    id: 'least_conn',
    name: t('最小连接数（least_conn）'),
  },
];

const hashOnOptions = [
  {
    id: 'vars',
    name: 'vars',
  },
  {
    id: 'header',
    name: 'header',
  },
  {
    id: 'cookie',
    name: 'cookie',
  },
];

// scheme 类型
const schemeList = [{ value: 'http' }, { value: 'https' }];

// slider 标题
const titleTextMap: { [key: string]: string } = {
  add: t('新建环境'),
  edit: t('编辑环境'),
  check: t('查看环境'),
};

// 正则校验
const rules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(value: string) {
        const reg = /^[a-zA-Z][a-zA-Z0-9_-]{1,19}$/;
        return reg.test(value);
      },
      message: t('请输入 2-20 字符的字母、数字、连字符(-)、下划线(_)，以字母开头'),
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

  weight: [
    {
      required: true,
      message: t('必填项'),
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
      validator: (val: number) => !(val < 0 || val > 300),
      message: t('超时时间不能小于1且不能大于300'),
      trigger: 'blur',
    },
  ],
};

const backendConfigFormRefs: InstanceType<typeof Form>[] = [];

const healthCheckRefMap: Record<number, InstanceType<typeof HealthChecks>> = {};

// 网关id
const gatewayId = computed(() => Number(route.params.id));

const title = computed(() => {
  return titleTextMap[actionType.value] ?? t('环境');
});

// 访问地址
const stageAddress = computed(() => {
  const keys: any = {
    api_name: gatewayStore.currentGateway!.name,
    stage_name: curStageData.value.name,
    resource_path: '',
  };

  let url = envStore.env.BK_API_RESOURCE_URL_TMPL;
  for (const name of Object.keys(keys)) {
    const reg = new RegExp(`{${name}}`);
    url = url?.replace(reg, keys[name]);
  }
  return url;
});

watch(
  isShow,
  (v) => {
    if (v) {
      setTimeout(() => {
        controlToggle();
        observerBtnScroll();
      }, 200);
    }
    else {
      destroyEvent();
    }
  },
);

// 默认值
const defaultConfig = () => {
  return {
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
};

const setBackendConfigRef = (el: InstanceType<typeof Form>) => {
  if (el !== null) {
    backendConfigFormRefs.push(el);
  }
};

const setHealthChecksRef = (el: InstanceType<typeof HealthChecks>, backend: { id: number }) => {
  if (el && backend.id) {
    healthCheckRefMap[backend.id] = el;
  }
};

// 新建初始化（新建）
const addInit = async () => {
  isDialogLoading.value = true;
  // 获取当前网关下的backends(获取后端服务列表)
  const res = await getBackendServiceList(gatewayId.value);
  // console.log('获取all后端服务列表', res);
  activeIndex.value = [];
  curStageData.value.backends = res.results.map((item: any, index: number) => {
    activeIndex.value.push(index);
    // 后端服务配置默认值
    return {
      id: item.id,
      name: item.name,
      config: defaultConfig(),
    };
  });
  isDialogLoading.value = false;
  // initSidebarFormData(curStageData.value);
};

// 查看态初始化
const checkInit = async () => {
  isDialogLoading.value = true;
  try {
    const data = await getStageDetail(gatewayId.value, stageId!);
    curStageData.value.name = data.name;
    curStageData.value.backends = await getStageBackends(gatewayId.value, stageId!);
  }
  finally {
    isDialogLoading.value = false;
  }
};

// 获取环境详情（编辑）
const getStageDetailFun = async () => {
  const data = await getStageDetail(gatewayId.value, stageId!);
  curStageData.value.name = data.name;
  curStageData.value.description = data.description;
};

// 获取环境后端服务详情（编辑）
const getStageBackendList = async () => {
  isDialogLoading.value = true;
  const backendList = await getStageBackends(gatewayId.value, stageId!);
  curStageData.value.backends = backendList;
  activeIndex.value = [];
  backendList?.forEach((item: any, index: number) => {
    activeIndex.value.push(index);
  });
  // 数据转换
  isDialogLoading.value = false;
};

// 关闭侧边栏回调
const handleCloseSideSlider = () => {
  // 数据重置
  curStageData.value = {
    name: '',
    description: '',
    backends: [
      {
        name: '',
        config: defaultConfig(),
      },
    ],
  };
  activeIndex.value = [0];
};

// 显示侧边栏
const handleShowSideslider = async (type: string, { backendName = '' } = {}) => {
  // 数据重置
  handleCloseSideSlider();
  actionType.value = type || 'add';
  // 新建环境获取当前网关下的所有后端服务进行配置
  if (type === 'add') {
    isAdd.value = true;
    addInit();
  }
  else if (type === 'edit') {
    isAdd.value = false;
    // 编辑环境
    await Promise.all([
      getStageDetailFun(),
      // 获取对应环境下的后端服务列表
      getStageBackendList(),
    ]);
    // initSidebarFormData(curStageData.value);
  }
  else if (type === 'check') {
    isAdd.value = false;
    await checkInit();
    selectedBackendName.value = backendName;
  }
  isShow.value = true;
};

const handleLoadBalanceChange = (value: string, stageId: number) => {
  const stage = curStageData.value.backends.find(item => item.id === stageId);
  if (stage) {
    if (value === 'chash') {
      stage.config.hash_on = 'vars';
      stage.config.key = 'remote_addr';
    }
    else {
      delete stage.config.hash_on;
      delete stage.config.key;
    }
  }
};

const handleHashOnChange = (value: string, stageId: number) => {
  const stage = curStageData.value.backends.find(item => item.id === stageId);
  if (stage) {
    if (value === 'vars') {
      stage.config.key = 'remote_addr';
    }
    else {
      stage.config.key = '';
    }
  }
};

const handleHashOnKeyChange = (config: any) => {
  const stage = curStageData.value.backends.find(item => item.id === config.id);
  if (stage) {
    stage.config.key = config.config.key;
  }
};

// 确定
const handleConfirm = async () => {
  // 表单校验
  await baseInfoRef.value.validate();
  for (const item of backendConfigFormRefs) {
    item?.validate();
  }
  if (isAdd.value) {
    await handleConfirmCreate();
  }
  else {
    await handleConfirmEdit();
  }
};

// 新建环境
const handleConfirmCreate = async () => {
  const params = cloneDeep(curStageData.value);
  if (featureFlagStore.flags.ENABLE_HEALTH_CHECK && Object.keys(healthCheckRefMap).length) {
    Object.entries(healthCheckRefMap).forEach(([backendId, healthCheckRef]) => {
      const backend = params.backends.find(backend => backend.id === Number(backendId));
      if (backend) {
        const checks = healthCheckRef.getValue();
        if (checks) {
          Object.assign(backend.config, { checks });
        }
      }
    });
  }
  // 删除冗余参数
  params.backends.forEach((v: any) => {
    delete v.name;
  });
  await createStage(gatewayId.value, params);
  Message({
    message: t('创建成功'),
    theme: 'success',
  });
  emit('done');
  // 数据重置
  handleCloseSideSlider();
  // 关闭dialog
  isShow.value = false;
};

// 编辑环境
const handleConfirmEdit = async () => {
  const params = cloneDeep(curStageData.value);
  if (featureFlagStore.flags.ENABLE_HEALTH_CHECK && Object.keys(healthCheckRefMap).length) {
    Object.entries(healthCheckRefMap).forEach(([backendId, healthCheckRef]) => {
      const backend = params.backends.find(backend => backend.id === Number(backendId));
      if (backend) {
        const checks = healthCheckRef.getValue();
        if (checks) {
          Object.assign(backend.config, { checks });
        }
      }
    });
  }
  // 删除冗余参数
  params.backends.forEach((v: any) => {
    delete v.name;
  });
  await putStage(gatewayId.value, stageId!, params);
  Message({
    message: t('更新成功'),
    theme: 'success',
  });
  emit('done');
  // 关闭dialog
  isShow.value = false;
};

const handleAnimationEnd = () => {
  handleCancel();
};

// 取消关闭侧边栏
const handleCancel = () => {
  isShow.value = false;
  // 数据重置
  handleCloseSideSlider();
};

// 添加服务地址
const handleAddServiceAddress = (name: string) => {
  curStageData.value.backends.forEach((v) => {
    if (v.name === name) {
      v.config.hosts.push({
        scheme: 'http',
        host: '',
        weight: 100,
      });
    }
  });
  controlToggle();
};

// 删除服务地址
const handleDeleteServiceAddress = (name: string, index: number) => {
  curStageData.value.backends.forEach((v) => {
    if (v.name === name) {
      v.config.hosts.splice(index, 1);
    }
  });
  controlToggle();
};

// 获取按钮底部距离
const getDistanceToBottom = (element: any) => {
  const rect = element?.getBoundingClientRect();
  return Math.max(0, window?.innerHeight - rect?.bottom);
};

// 元素滚动判断元素是否吸顶
const controlToggle = () => {
  const el = document.querySelector('.footer-btn-wrapper');
  const bottomDistance = getDistanceToBottom(el);
  const maxDistance = 1000;
  // 是否吸附
  if (bottomDistance < 25 || bottomDistance > maxDistance) {
    isAdsorb.value = true;
    el?.classList.add('is-pinned');
  }
  else {
    isAdsorb.value = false;
    el?.classList?.remove('is-pinned');
  }
};

const getLoadBalanceText = (value: string) => {
  return loadbalanceList.find(item => item.id === value)?.name ?? '--';
};

const observerBtnScroll = () => {
  const container = document.querySelector('.bk-modal-content');
  container?.addEventListener('scroll', controlToggle);
};

const destroyEvent = () => {
  const container = document.querySelector('.bk-modal-content');
  container?.removeEventListener('scroll', controlToggle);
};

// 暴露属性
defineExpose({ handleShowSideslider });
</script>

<style lang="scss" scoped>
.stage-sideslider-cls {

  :deep(.bk-sideslider-footer) {
    position: absolute;
    bottom: 0;
    box-shadow: 0 -1px 0 0 #dcdee5;
  }

  :deep(.bk-modal-content) {
    overflow-y: auto;
    scrollbar-gutter: stable;

    .bk-form-label {
      line-height: 22px;
    }
  }
}

.sideslider-content {
  padding: 20px 34px 32px 40px;

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

  .address {
    height: 40px;
    padding: 0 12px;
    line-height: 40px;
    background-color: #f5f7fa;

    label {
      height: 22px;
      font-size: 14px;
      font-weight: 700;
      line-height: 22px;
      color: #63656e;
    }

    span {
      font-size: 14px;
      color: #63656e;
    }

    i {
      padding: 3px;
      margin-left: 4px;
      color: #3a84ff;
      cursor: pointer;
    }
  }

  // .weights-input {
  //   :deep(.bk-input--number-control) {
  //     display: none;
  //   }
  // }

  &.check-mode {

    .title {
      height: 40px;
      padding: 0 8px;
      font-size: 12px;
      font-weight: 700;
      line-height: 40px;
      color: #63656e;
      border-bottom: 1px solid #dcdee5;

      &.highlighted {
        color: #4d4f56;
        background-color: #cddffe;
        border-bottom: none;
        box-shadow: inset 0 -1px 0 0 #a3c5fd;
      }
    }

    .ag-kv-box {
      padding-top: 12px;
      padding-right: 24px;
      padding-left: 0 !important;
      margin-bottom: 24px;

      .bk-grid-row {
        padding-bottom: 12px;
        margin-bottom: 0;

        .bk-grid-col {
          padding-right: 16px !important;
          padding-left: 0 !important;
        }
      }

      .ag-key {
        font-size: 12px;
        color: #4d4f56;
        text-align: right;
      }

      .ag-value {
        font-size: 12px;
        color: #313238;
      }

      &.highlighted {
        background-color: #f0f5ff;
      }
    }
  }
}

.weight-input {
  margin-bottom: 0;
  border-left: 1px solid #c4c6cc !important;

  // :deep(.bk-form-content) {
  //   margin-top: -1px;
  // }
}

.suffix-slot-cls {
  width: 80px;
  height: 28px;
  font-size: 12px;
  line-height: 28px;
  color: #63656e;
  text-align: center;
  border: none;
  box-shadow: none !important;

  :deep(.bk-input--text) {
    border-radius: 0;
  }
}

.group-text-style {
  width: 20px;
  color: #63656e;
  text-align: left;
  background: #f5f7fa;

  &.long {
    width: 50px;
  }
}

.scheme-select-cls {
  width: 120px;
  overflow: hidden;
  color: #63656e;

  :deep(.bk-input--default) {
    border: none;
    border-right: 1px solid #c4c6cc;
  }
}

.slash {
  padding: 0 10px;
  color: #63656e;
  background: #fafbfd;
  border-right: 1px solid #c4c6cc;
}

.timeout-item-cls {
  position: relative;
  width: 240px;

  :deep(.bk-form-content) {

    .timeout-tip {
      position: absolute;
      top: 1px;
      right: -77px;
      margin-left: 13px;
      font-size: 12px;
      color: #63656e;
      white-space: nowrap;

      &.long {
        right: -110px;
      }
    }
  }
}

.form-item-special {

  :deep(.bk-form-label) {
    display: none;
  }
}

.backend-item-cls {
  margin-bottom: 18px;

  :deep(.bk-form-error) {
    position: relative;
  }

  &:last-child {
    margin-bottom: 50px !important;
    background: #3a84ff;
  }
}

.footer-btn-wrapper {
  bottom: 0;
  height: 48px;
  padding-left: 40px;
}

.fixed-footer-btn-wrapper {
  position: fixed;
  right: 0;
  bottom: 0;
  z-index: 9;
  width: 100%;
  max-width: 960px;
  padding: 10px 0 10px 40px;
  background-color: #fff;
  box-shadow: 0 -1px 0 0 #dcdee5;
  transition: .2s;
}

.is-pinned {
  opacity: 0%;
}

.bk-collapse-service {

  .panel-header {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    line-height: 22px;
    cursor: pointer;

    .title {
      margin-left: 8px;
      font-size: 14px;
      font-weight: 700;
      color: #313238;
    }

    .panel-header-show,
    .panel-header-hide {
      color: #63656e;
      transform: rotate(0deg);
      transition: .2s;
    }

    .panel-header-hide {
      transform: rotate(-90deg);
    }
  }

  :deep(.bk-collapse-content) {
    padding: 0;
  }

  .stage {

    :deep(.bk-collapse-title) {
      margin-left: 24px;
      font-size: 14px;
      font-weight: 700;
      color: #63656e;
    }

    :deep(.bk-collapse-item) {
      margin-bottom: 16px;
      background-color: #f5f7fb;

      .bk-collapse-header {
        height: 40px;
        line-height: 40px;
        background-color: #f0f1f5;
        border-radius: 2px;
      }

      .bk-collapse-content {
        padding: 0 32px;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }

    .stage-name {
      font-size: 14px;
      font-weight: 700;
      color: #63656E;
    }

    :deep(.bk-collapse-icon) {
      left: 17px;
      color: #979aa2;

      svg {
        font-size: 13px;
      }
    }
  }

  .last-form-item {
    margin-bottom: 32px;
  }
}
</style>
