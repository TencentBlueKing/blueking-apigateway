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
  <div class="detail-container">
    <div
      class="detail-container-content"
      :class="[
        { 'has-notice': stageStore.getNotUpdatedStages?.length },
        { 'pb-52px': isStickyFixed }
      ]"
    >
      <div class="mb-30px">
        <div class="title">
          {{ t('基本信息') }}
        </div>
        <div class="label-content-grid">
          <div class="label-content-group">
            <div class="label">
              {{ t('名称') }}
            </div>
            <div class="content">
              <div
                v-if="!nameEdit"
                class="value-container"
              >
                <span class="value-cls">{{ formData.name }}</span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="toggleEdit"
                  />
                  <AgIcon
                    name="copy-info"
                    @click="() => copy(formData.name)"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkInput
                  ref="nameInputRef"
                  v-model="formData.name"
                  size="small"
                  :placeholder="t('名称由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符')"
                  @blur="() => handleNameBlur(formData.name)"
                  @enter="handleEditEnter"
                />
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              {{ t('描述') }}
            </div>
            <div class="content">
              <div
                v-if="!descEdit"
                class="value-container flex items-center"
              >
                <div
                  v-bk-tooltips="{
                    content: formData.description,
                    disabled: !formData.description || formData.description.length <= 50,
                  }"
                  class="value-cls"
                >
                  {{ truncatedDesc }}
                </div>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="descEdit = true"
                  />
                  <AgIcon
                    name="copy-info"
                    @click="() => copy(formData.description)"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkInput
                  v-model="formData.description"
                  size="small"
                  :placeholder="t('请输入描述')"
                  @blur="handleEditSave"
                />
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              {{ t('标签') }}
            </div>
            <div class="content">
              <div
                v-if="!labelsEdit"
                class="value-container"
              >
                <span class="value-cls">
                  <template v-if="formData.labels?.length">
                    <BkTag
                      v-for="item in formData.labels"
                      :key="item.id"
                    >{{ item.name }}</BkTag>
                  </template>
                  <span v-else>--</span>
                </span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="labelsEdit = true"
                  />
                  <AgIcon
                    name="copy-info"
                    @click="() => copy(formData?.labels?.map((item: any) => item.name)?.join(','))"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <section class="w-full">
                  <SelectCheckBox
                    :width="700"
                    :cur-select-label-ids="formData.label_ids"
                    :resource-id="resourceId"
                    :labels-data="labelsData"
                    @close="labelsEdit = false"
                    @update-success="handleUpdateLabelSuccess"
                    @label-add-success="initLabels"
                  />
                </section>
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              <span
                v-bk-tooltips="t('请求方需提供蓝鲸应用身份信息')"
                class="cursor-pointer underline underline-dashed underline-offset-4"
              >{{ t('认证方式') }}</span>
            </div>
            <div class="content">
              <div
                v-if="!verifiedEdit"
                class="value-container"
              >
                <span class="value-cls">
                  {{ t(verifiedRequired(formData.auth_config)) }}
                </span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="verifiedEdit = true"
                  />
                  <AgIcon
                    name="copy-info"
                    @click="() => copy(verifiedRequired(formData.auth_config))"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkPopover
                  disable-outside-click
                  trigger="click"
                  :is-show="verifiedEdit"
                  :component-event-delay="300"
                  :offset="16"
                  placement="bottom"
                  theme="light"
                  width="490"
                >
                  <span class="value-cls">
                    {{ t(verifiedRequired(formData.auth_config)) }}
                  </span>
                  <template #content>
                    <div class="p-4px">
                      <BkForm
                        :model="formData"
                        form-type="vertical"
                      >
                        <BkFormItem :label="t('认证方式')">
                          <BkCheckbox
                            v-model="formData.auth_config.app_verified_required_copy"
                            :disabled="!gatewayStore.currentGateway.allow_update_gateway_auth"
                          >
                            <span
                              v-bk-tooltips="{ content: t('请求方需提供蓝鲸应用身份信息') }"
                              class="bottom-line"
                            >
                              {{ t('蓝鲸应用认证') }}
                            </span>
                          </BkCheckbox>
                          <BkCheckbox
                            v-model="formData.auth_config.auth_verified_required_copy"
                            class="ml-40px"
                          >
                            <span
                              v-bk-tooltips="{ content: t('请求方需提供蓝鲸用户身份信息') }"
                              class="bottom-line"
                            >
                              {{ t('用户认证') }}
                            </span>
                          </BkCheckbox>
                        </BkFormItem>
                        <BkFormItem
                          v-if="formData.auth_config.app_verified_required_copy"
                          :label="t('检验应用权限')"
                        >
                          <BkSwitcher
                            v-model="formData.auth_config.resource_perm_required_copy"
                            :disabled="!gatewayStore.currentGateway.allow_update_gateway_auth"
                            theme="primary"
                            size="small"
                          />
                        </BkFormItem>
                        <BkFormItem class="mb-0 text-right">
                          <BkButton
                            theme="primary"
                            native-type="button"
                            @click="verifiedSubmit"
                          >
                            {{ t('确定') }}
                          </BkButton>
                          <BkButton
                            class="ml-8px"
                            @click="verifiedEdit = false"
                          >
                            {{ t('取消') }}
                          </BkButton>
                        </BkFormItem>
                      </BkForm>
                    </div>
                  </template>
                </BkPopover>
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              {{ t('校验应用权限') }}
            </div>
            <div class="content">
              <div
                v-if="!permEdit"
                class="value-container"
              >
                <span class="value-cls color-#ff9c01!">
                  {{ formData.auth_config?.resource_perm_required ? t('开启') : t('关闭') }}
                </span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="permEdit = true"
                  />
                  <AgIcon
                    name="copy-info"
                    @click="() => copy(formData.auth_config?.resource_perm_required ? t('开启') : t('关闭'))"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkSwitcher
                  v-model="formData.auth_config.resource_perm_required_copy"
                  :disabled="!gatewayStore.currentGateway.allow_update_gateway_auth"
                  theme="primary"
                  size="small"
                  class="mt-8px!"
                  @change="verifiedSubmit"
                />
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              <span
                v-bk-tooltips="t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')"
                class="cursor-pointer underline underline-dashed underline-offset-4"
              >{{ t('是否公开') }}</span>
            </div>
            <div class="content">
              <div
                v-if="!publicEdit"
                class="value-container"
              >
                <span class="color-#ff9c01!">{{ formData.is_public ? t('公开') : t('不公开') }}</span>
                <span
                  v-if="formData.is_public"
                  class="value-cls"
                >
                  {{ formData.allow_apply_permission ? t('（允许申请权限）') : t('（不允许申请权限）') }}
                </span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="publicEdit = true"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkSwitcher
                  v-model="formData.is_public"
                  theme="primary"
                  size="small"
                  class="mt-8px!"
                  @change="handleEditSave"
                />
              </div>
            </div>
          </div>
          <div class="label-content-group stages">
            <div class="label">
              {{ t('已使用的环境') }}
            </div>
            <div class="content">
              <span v-if="!servicesData?.config?.length">--</span>
              <span v-else>{{ servicesData?.config?.map((item: any) => item?.stage?.name)?.join(', ') }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-30px">
        <div class="title">
          {{ t('前端配置') }}
        </div>
        <div class="label-content-grid">
          <div class="label-content-group">
            <div class="label">
              {{ t('请求方法') }}
            </div>
            <div class="content">
              <div
                v-if="!frontMethodEdit"
                class="value-container"
              >
                <BkTag :theme="METHOD_THEMES[formData?.method]">
                  {{ formData?.method }}
                </BkTag>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="frontMethodEdit = true"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkSelect
                  v-model="formData.method"
                  :input-search="false"
                  :clearable="false"
                  class="method"
                  @change="handleEditSave"
                >
                  <BkOption
                    v-for="item in HTTP_METHODS"
                    :key="item.id"
                    :value="item.id"
                    :label="item.name"
                  />
                </BkSelect>
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              {{ t('启用 WebSocket') }}
            </div>
            <div class="content">
              <div
                v-if="!frontWsEdit"
                class="value-container"
              >
                <span>{{ formData?.enable_websocket ? t('是') : t('否') }}</span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="frontWsEdit = true"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name mt-8px"
              >
                <BkSwitcher
                  v-model="formData.enable_websocket"
                  theme="primary"
                  size="small"
                  class="method"
                  @change="handleEditSave"
                />
              </div>
            </div>
          </div>
          <div class="label-content-group path">
            <div class="label">
              {{ t('请求路径') }}
            </div>
            <div class="content">
              <div
                v-if="!frontPathEdit"
                class="value-container"
              >
                <span class="value-cls">{{ formData.path }}</span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="frontPathEdit = true"
                  />
                  <AgIcon
                    name="copy-info"
                    @click="() => copy(formData.path)"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkPopover
                  disable-outside-click
                  trigger="click"
                  :is-show="frontPathEdit"
                  :component-event-delay="300"
                  :offset="16"
                  placement="bottom"
                  theme="light"
                  width="490"
                >
                  <span class="value-cls">{{ formData.path }}</span>
                  <template #content>
                    <div class="p-4px">
                      <BkForm
                        :model="formData"
                        form-type="vertical"
                      >
                        <BkFormItem
                          :label="t('请求路径')"
                          class="mt-8px!"
                        >
                          <BkInput
                            v-model="formData.path_copy"
                            :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
                            class="mb-12px"
                          />
                          <BkCheckbox
                            v-model="formData.match_subpath_copy"
                            class="lh-20px"
                          >
                            {{ t('匹配所有子路径') }}
                          </BkCheckbox>
                        </BkFormItem>
                        <BkFormItem class="text-right mb-0">
                          <BkButton
                            theme="primary"
                            native-type="button"
                            @click="frontPathSubmit"
                          >
                            {{ t('确定') }}
                          </BkButton>
                          <BkButton
                            class="ml-8px"
                            @click="frontPathEdit = false"
                          >
                            {{ t('取消') }}
                          </BkButton>
                        </BkFormItem>
                      </BkForm>
                    </div>
                  </template>
                </BkPopover>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-30px">
        <div class="title">
          {{ t('请求参数') }}
        </div>
        <div>
          <span
            v-if="formData.schema?.none_schema"
            class="text-12px"
          >{{ t('该资源无请求参数') }}</span>
          <RequestParams
            v-else
            :detail="formData"
            readonly
          />
        </div>
      </div>

      <div class="mb-30px">
        <div class="title">
          {{ t('后端配置') }}
        </div>
        <div class="label-content-grid">
          <div class="label-content-group service">
            <div class="label">
              {{ t('服务') }}
            </div>
            <div class="content">
              <div class="h-42px w-full pl-16px flex items-center border-b-1px border-b-solid border-b-#DCDEE5">
                <div
                  v-if="!backServicesEdit"
                  class="value-container"
                >
                  <BkButton
                    text
                    class="color-#1768ef!"
                    @click="() => handleServiceNameClick(servicesData)"
                  >
                    {{ servicesData.name }}
                  </BkButton>
                  <span class="operate-btn">
                    <AgIcon
                      name="edit-line"
                      @click="backServicesEdit = true"
                    />
                  </span>
                </div>
                <div
                  v-else
                  class="edit-name"
                >
                  <BkSelect
                    v-model="formData.backend.id"
                    :input-search="false"
                    :clearable="false"
                    class="service"
                    @change="() => getServiceData(true)"
                  >
                    <BkOption
                      v-for="item in backendsList"
                      :key="item.id"
                      :value="item.id"
                      :label="item.name"
                    />
                  </BkSelect>
                </div>
              </div>

              <div class="p-16px">
                <BkTable
                  v-if="formData.id"
                  :data="servicesData.config"
                  :border="['outer']"
                  @row-mouse-enter="backServicesEdit ? handleMouseEnter : ''"
                  @row-mouse-leave="backServicesEdit ? handleMouseLeave : ''"
                >
                  <BkTableColumn
                    :label="t('环境名称')"
                    :resizable="false"
                  >
                    <template #default="{ data }">
                      {{ data?.stage?.name }}
                    </template>
                  </BkTableColumn>
                  <BkTableColumn
                    :label="t('后端服务地址')"
                    :resizable="false"
                  >
                    <template #default="{ data }">
                      <div v-if="data.hosts.length">
                        <div
                          v-for="host in data.hosts"
                          :key="host.host"
                          class="lh-22px"
                        >
                          {{ host.scheme }}://{{ host.host }}
                        </div>
                      </div>
                      <span v-else>--</span>
                    </template>
                  </BkTableColumn>
                  <BkTableColumn
                    v-if="!backServicesEdit"
                    :label="t('超时时间')"
                    prop="timeout"
                    :resizable="false"
                  >
                    <template #default="{ data }">
                      <span>{{ data?.timeout || '0' }}s</span>
                    </template>
                  </BkTableColumn>
                  <BkTableColumn
                    v-else
                    :label="renderTimeOutLabel"
                    prop="timeout"
                    :resizable="false"
                  >
                    <template #default="{ data }">
                      <span>{{ data?.timeout || '0' }}s</span>
                      <BkTag
                        v-if="data?.isCustom"
                        theme="warning"
                      >
                        {{ t('自定义') }}
                      </BkTag>
                    </template>
                  </BkTableColumn>
                </BkTable>
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              {{ t('请求方法') }}
            </div>
            <div class="content">
              <div
                v-if="!backMethodEdit"
                class="value-container"
              >
                <BkTag :theme="METHOD_THEMES[formData.backend?.config?.method]">
                  {{ formData.backend?.config?.method }}
                </BkTag>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="backMethodEdit = true"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkSelect
                  v-model="formData.backend.config.method"
                  :input-search="false"
                  :clearable="false"
                  class="method"
                  @change="handleEditSave"
                >
                  <BkOption
                    v-for="item in HTTP_METHODS"
                    :key="item.id"
                    :value="item.id"
                    :label="item.name"
                  />
                </BkSelect>
              </div>
            </div>
          </div>
          <div class="label-content-group">
            <div class="label">
              {{ t('请求路径') }}
            </div>
            <div class="content">
              <div
                v-if="!backPathEdit"
                class="value-container"
              >
                <span class="value-cls">{{ formData.backend?.config?.path }}</span>
                <span class="operate-btn">
                  <AgIcon
                    name="edit-line"
                    @click="backPathEdit = true"
                  />
                  <AgIcon
                    name="copy-info"
                    @click="() => copy(formData.backend?.config?.path)"
                  />
                </span>
              </div>

              <div
                v-else
                class="edit-name"
              >
                <BkPopover
                  disable-outside-click
                  trigger="click"
                  :is-show="backPathEdit"
                  :component-event-delay="300"
                  :offset="16"
                  placement="bottom"
                  theme="light"
                  width="740"
                >
                  <span class="value-cls">{{ formData.backend?.config?.path_copy }}</span>
                  <template #content>
                    <div class="p-4px">
                      <BkForm
                        :model="formData"
                        form-type="vertical"
                      >
                        <BkFormItem
                          :label="t('请求路径')"
                          class="mb-8px"
                        >
                          <div class="flex items-center">
                            <BkInput
                              v-model="formData.backend.config.path_copy"
                              :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
                              clearable
                            />
                            <BkButton
                              theme="primary"
                              outline
                              class="ml-10px"
                              :disabled="!formData.backend.id || !formData.backend?.config?.path"
                              @click="handleCheckPath"
                            >
                              {{ t('校验并查看地址') }}
                            </BkButton>
                          </div>
                          <BkCheckbox
                            v-model="formData.backend.config.match_subpath"
                            disabled
                          >
                            {{ t('追加匹配的子路径') }}
                          </BkCheckbox>
                          <div class="text-12px! color-#979ba5!">
                            {{ t("后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在\{\}中") }}
                          </div>
                          <div v-if="servicesCheckData?.length">
                            <BkAlert
                              theme="success"
                              class="w-70%! max-w-700px! mt-10px!"
                              :title="t('路径校验通过，路径合法，请求将被转发到以下地址')"
                            />
                            <BkTable
                              class="w-70%! max-w-700px! mt-10px"
                              :data="servicesCheckData"
                              :border="['outer']"
                            >
                              <BkTableColumn
                                :label="t('环境名称')"
                              >
                                <template #default="{ data }">
                                  {{ data?.stage?.name }}
                                </template>
                              </BkTableColumn>
                              <BkTableColumn
                                :label="t('请求类型')"
                              >
                                <template #default="{ data }">
                                  {{ formData.backend.config.method || data?.stage?.name }}
                                </template>
                              </BkTableColumn>
                              <BkTableColumn
                                :label="t('请求地址')"
                              >
                                <template #default="{ data }">
                                  {{ data?.backend_urls[0] }}
                                </template>
                              </BkTableColumn>
                            </BkTable>
                          </div>
                        </BkFormItem>
                        <BkFormItem class="mb-0 text-right">
                          <BkButton
                            theme="primary"
                            native-type="button"
                            @click="backPathSubmit"
                          >
                            {{ t('确定') }}
                          </BkButton>
                          <BkButton
                            class="ml-8px"
                            @click="backPathCancel"
                          >
                            {{ t('取消') }}
                          </BkButton>
                        </BkFormItem>
                      </BkForm>
                    </div>
                  </template>
                </BkPopover>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-30px">
        <div class="title">
          {{ t('响应参数') }}
        </div>
        <div>
          <ResponseParams
            v-if="Object.keys(formData.openapi_schema?.responses || {}).length"
            :detail="formData"
            readonly
          />
          <div
            v-else
            class="text-12px"
          >
            {{ t('该资源无响应参数') }}
          </div>
        </div>
      </div>
    </div>

    <div
      class="footer-btn-wrapper"
      :class="{ 'fixed-footer-btn-wrapper': isStickyFixed }"
    >
      <BkButton
        theme="primary"
        class="min-w-88px"
        @click="handleEditClick"
      >
        {{ t('编辑') }}
      </BkButton>
      <BkPopConfirm
        :title="t('确认删除资源{resourceName}？', { resourceName: formData?.name || '' })"
        :content="t('删除操作无法撤回，请谨慎操作')"
        width="288"
        trigger="click"
        @confirm="handleDeleteResource(formData.id)"
      >
        <BkButton
          class="min-w-88px ml-8px"
        >
          {{ t('删除') }}
        </BkButton>
      </BkPopConfirm>
    </div>
  </div>
</template>

<script setup lang="tsx">
import {
  backendsPathCheck,
  deleteResources,
  getResourceDetail,
  updateResources,
} from '@/services/source/resource';
import { getBackendServiceDetail, getBackendServiceList } from '@/services/source/backend-services.ts';
import { getGatewayLabels } from '@/services/source/gateway';
import { Message } from 'bkui-vue';
import { copy } from '@/utils';
import { METHOD_THEMES } from '@/enums';
import { HTTP_METHODS } from '@/constants';
import { cloneDeep } from 'lodash-es';
import RequestParams from '../../components/request-params/Index.vue';
import ResponseParams from '../../components/response-params/Index.vue';
import { useGateway, useStage } from '@/stores';
import { useStickyBottom } from '@/hooks';
import SelectCheckBox from './SelectCheckBox.vue';

interface IProps {
  resourceId?: number
  gatewayId?: number
}

const {
  resourceId = 0,
  gatewayId = 0,
} = defineProps<IProps>();

const emit = defineEmits<{
  'done': [value: boolean]
  'deleted-success': [void]
  'updated': [void]
}>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();
const stageStore = useStage();
const { controlStickyToggle, observerNodeScroll, destroyEvent } = useStickyBottom({
  offsetBottom: 52,
  footerNodeClass: '.footer-btn-wrapper',
  scrollNodeClass: '.detail-container-content',
  parentNodeClass: '.resource-container',
});

const labelsData = ref([]);
const isStickyFixed = ref(false);
const nameEdit = ref(false);
const descEdit = ref(false);
const labelsEdit = ref(false);
const verifiedEdit = ref(false);
const permEdit = ref(false);
const publicEdit = ref(false);
const frontMethodEdit = ref(false);
const frontPathEdit = ref(false);
const frontWsEdit = ref(false); // 是否启用websocket的编辑态
const backMethodEdit = ref(false);
const backServicesEdit = ref(false);
const backPathEdit = ref(false);
const nameInputRef = ref();
// 服务列表下拉框数据
const backendsList = ref([]);
const popoverConfirmRef = ref();
const isShowPopConfirm = ref(false);
const isTimeEmpty = ref(false);
const timeOutValue = ref('');

// 校验列表
const servicesCheckData = ref([]);

const formData = ref<any>({});

// 服务table
const servicesData = ref<any>({});

const truncatedDesc = computed(() => {
  if (!formData.value.description) {
    return '--';
  }
  if (formData.value.description.length > 50) {
    return `${formData.value.description.substring(0, 50)}...`;
  }
  return formData.value.description;
});

// 资源详情
const getResourceDetails = async () => {
  const res = await getResourceDetail(gatewayId, resourceId);
  formData.value = res;

  nextTick(() => {
    formData.value.label_ids = res?.labels?.map((item: any) => item.id);

    formData.value.auth_config.app_verified_required_copy = res?.auth_config?.app_verified_required;
    formData.value.auth_config.auth_verified_required_copy = res?.auth_config?.auth_verified_required;
    formData.value.auth_config.resource_perm_required_copy = res?.auth_config?.resource_perm_required;

    formData.value.path_copy = res?.path;
    formData.value.match_subpath_copy = res?.match_subpath;

    formData.value.backend.config.path_copy = formData.value.backend.config.path;

    formData.value.openapi_schema = cloneDeep(res.schema);
    delete formData.value.schema;
  });

  getServiceData();
};

watch(
  () => resourceId,
  () => {
    if (resourceId) {
      getResourceDetails();
    }
  },
  { immediate: true },
);

const handleEditClick = () => {
  router.push({
    name: 'ResourceEdit',
    params: { resourceId: `${formData.value.id}` },
    query: { ...route.query },
  });
};

const initLabels = async () => {
  labelsData.value = await getGatewayLabels(gatewayId);
};
initLabels();

// 初始化判断按钮组是否吸附
const getStickyBottom = () => {
  const { isStickyBottom } = controlStickyToggle();
  isStickyFixed.value = isStickyBottom;
  nextTick(() => {
    observerNodeScroll();
  });
};
getStickyBottom();

// 更新成功
const handleUpdateLabelSuccess = () => {
  getResourceDetails();
  initLabels();
  labelsEdit.value = false;
};

// 选择服务获取服务详情数据
const getServiceData = async (update?: boolean) => {
  const res = await getBackendServiceDetail(gatewayId, formData.value.backend.id);

  const resourceDetailTimeout = formData.value?.backend?.config?.timeout;
  if (resourceDetailTimeout !== 0) {
    res.configs.forEach((item: any) => {
      item.timeout = resourceDetailTimeout;
    });
  }
  servicesData.value.config = res.configs;
  servicesData.value.name = res.name;

  servicesConfigsStorage.value = cloneDeep(res.configs || []);
  emit('done', false);

  if (update) {
    handleEditSave();
  }
};

// 获取服务列表数据
const getBackendsList = async () => {
  const res = await getBackendServiceList(gatewayId);
  backendsList.value = res.results;
};
getBackendsList();

const handleMouseEnter = (e: Event, row: Record<string, number | string | boolean>) => {
  setTimeout(() => {
    row.isTime = true;
  }, 100);
};

const handleMouseLeave = (e: Event, row: Record<string, number | string | boolean>) => {
  setTimeout(() => {
    row.isTime = false;
  }, 100);
};

// 服务详情缓存数据
const servicesConfigsStorage = ref([]);

const handleClickOutSide = (e: Event) => {
  if (
    isShowPopConfirm.value
    && !unref(popoverConfirmRef)?.content?.el?.contains(e?.target)
  ) {
    handleCancelTime();
  }
};
const handleShowPopover = () => {
  isShowPopConfirm.value = true;
  isTimeEmpty.value = false;
  servicesData.value.config.forEach((item: any) => {
    item.isEditTime = false;
  });
};
const handleCancelTime = () => {
  isTimeEmpty.value = false;
  isShowPopConfirm.value = false;
  timeOutValue.value = '';
};
const handleTimeOutTotal = (value: any[]) => {
  formData.value.backend.config.timeout = Number(value[0].timeout);
};
const handleRefreshTime = () => {
  servicesData.value.config = cloneDeep(servicesConfigsStorage.value);
  handleTimeOutTotal(servicesData.value.config);
};
const handleTimeOutInput = (value: string) => {
  value = value.replace(/\D/g, '');
  if (Number(value) > 300) {
    value = '300';
  }
  timeOutValue.value = value.replace(/\D/g, '');
  isTimeEmpty.value = !value;
};
const handleConfirmTime = () => {
  if (!timeOutValue.value) {
    isTimeEmpty.value = true;
    return;
  }
  servicesData.value.config.forEach((item: Record<string, string | boolean>) => {
    item.isCustom = true;
    item.timeout = timeOutValue.value;
  });
  handleTimeOutTotal(servicesData.value.config);
  isShowPopConfirm.value = false;
  timeOutValue.value = '';
  handleEditSave();
};

const renderTimeOutLabel = () => {
  return (
    <div>
      <div class="back-config-timeout">
        <span>{t('超时时间')}</span>
        <BkPopConfirm
          width="280"
          trigger="manual"
          ref={popoverConfirmRef}
          title={t('批量修改超时时间')}
          extCls="back-config-timeout-popover"
          is-show={isShowPopConfirm.value}
          content={(
            <div class="back-config-timeout-wrapper">
              <div class="back-config-timeout-content">
                <div class="back-config-timeout-input">
                  <BkInput
                    v-model={timeOutValue.value}
                    maxlength={3}
                    overMaxLengthLimit={true}
                    class={isTimeEmpty.value ? 'time-empty-error' : ''}
                    placeholder={t('请输入超时时间')}
                    onInput={(value: string) => {
                      handleTimeOutInput(value);
                    }}
                    // nativeOnKeypress={(value: string) => {
                    //   value = value.replace(/\d/g, '');
                    // }}
                    autofocus={true}
                    suffix="s"
                    onEnter={() => handleConfirmTime()}
                  />
                </div>
                <div class="back-config-timeout-tip">{t('最大 300s')}</div>
              </div>
              {
                isTimeEmpty.value
                  ? (
                    <div class="time-empty-error">
                      {t('超时时间不能为空')}
                      {isTimeEmpty.value}
                    </div>
                  )
                  : ''
              }
            </div>
          )}
          onConfirm={() => handleConfirmTime()}
          onCancel={() => handleCancelTime()}
        >
          <i
            class="apigateway-icon icon-ag-bulk-edit edit-action"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('自定义超时时间')}
                </div>
              ),
            }}
            onClick={() => handleShowPopover()}
            v-clickOutSide={(e: any) => handleClickOutSide(e)}
          />
        </BkPopConfirm>
        <i
          class="apigateway-icon icon-ag-undo-2 refresh-icon"
          v-bk-tooltips={{
            content: (
              <div>{t('恢复初始值')}</div>
            ),
          }}
          onClick={() => handleRefreshTime()}
        />
      </div>
    </div>
  );
};

// 校验路径
const handleCheckPath = async () => {
  const params = {
    path: formData.value.path,
    backend_id: formData.value.backend.id,
    backend_path: formData.value.backend.config.path_copy,
  };
  servicesCheckData.value = await backendsPathCheck(gatewayId, params);
};

const verifiedRequired = (auth_config: any = {}) => {
  const { app_verified_required, auth_verified_required } = auth_config;
  if (app_verified_required && auth_verified_required) {
    return '蓝鲸应用认证，用户认证';
  }
  if (app_verified_required) {
    return '蓝鲸应用认证';
  }
  if (auth_verified_required) {
    return '用户认证';
  }
  return '--';
};

// 修改资源
const handleEditSave = async () => {
  const params = { ...formData.value };
  await updateResources(gatewayId, resourceId, params);
  Message({
    message: t('更新成功'),
    theme: 'success',
  });
  nameEdit.value = false;
  descEdit.value = false;
  labelsEdit.value = false;
  verifiedEdit.value = false;
  permEdit.value = false;
  publicEdit.value = false;
  frontMethodEdit.value = false;
  frontPathEdit.value = false;
  frontWsEdit.value = false;
  backMethodEdit.value = false;
  backServicesEdit.value = false;
  backPathEdit.value = false;
  emit('updated');
  getResourceDetails();
};

const handleNameBlur = (name: string) => {
  if (!name) {
    Message({
      message: t('请填写名称'),
      theme: 'warning',
    });
  }
  else if (!/^[a-zA-Z][a-zA-Z0-9_]{0,255}$|^$/.test(name)) {
    Message({
      message: t('名称由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符'),
      theme: 'warning',
    });
  }
  else {
    handleEditSave();
  }
};

const handleEditEnter = () => {
  nextTick(() => {
    nameInputRef.value.blur();
  });
};

const toggleEdit = () => {
  nameEdit.value = true;
  nextTick(() => {
    nameInputRef.value.focus();
  });
};

// 认证方式修改
const verifiedSubmit = () => {
  formData.value.auth_config.app_verified_required = formData.value.auth_config.app_verified_required_copy;
  formData.value.auth_config.auth_verified_required = formData.value.auth_config.auth_verified_required_copy;
  formData.value.auth_config.resource_perm_required = formData.value.auth_config.resource_perm_required_copy;

  handleEditSave();
};

// 前端请求路径修改
const frontPathSubmit = () => {
  formData.value.path = formData.value.path_copy;
  formData.value.match_subpath = formData.value.match_subpath_copy;

  handleEditSave();
};

// 后端请求路径修改
const backPathSubmit = () => {
  formData.value.backend.config.path = formData.value.backend.config.path_copy;
  handleEditSave();
};

const backPathCancel = () => {
  formData.value.backend.config.path_copy = formData.value.backend.config.path;
  servicesCheckData.value = [];
  backPathEdit.value = false;
};

// 删除资源
const handleDeleteResource = async (id: number) => {
  await deleteResources(gatewayId, id);
  Message({
    message: t('删除成功'),
    theme: 'success',
  });
  emit('deleted-success');
};

const handleServiceNameClick = (service: { name: string }) => {
  if (!service?.name) {
    return;
  }
  router.push({
    name: 'BackendService',
    query: { name: service.name },
  });
};

onUnmounted(() => {
  destroyEvent();
});
</script>

<style lang="scss" scoped>
.detail-container {

  .detail-container-content {
    max-height: calc(100vh - 175px);
    padding-inline: 14px;
    overflow-y: auto;

    &.has-notice {
      max-height: calc(100vh - 217px);
    }

    .title {
      margin-bottom: 12px;
      font-size: 14px;
      font-weight: 700;
      color: #313238;
    }

    .label-content-grid {
      display: grid;
      font-size: 12px;
      border: 1px solid #DCDEE5;
      border-bottom: none;
      border-left: none;
      grid-template-columns: repeat(2, 1fr);

      .label-content-group {
        display: flex;
        width: 100%;
        height: 42px;
        align-items: center;
        border-bottom: 1px solid #DCDEE5;

        &.stages,
        &.path {
          grid-column: 1 / 3;
        }

        &.service {
          grid-column: 1 / 3;
          height: auto;

          .content {
            padding-left: 0;
            flex-direction: column;
            align-items: flex-start;
          }
        }

        .label {
          display: flex;
          width: 140px;
          height: 100%;
          padding-left: 16px;
          color:#4D4F56;
          background-color: #fafbfd;
          border-right: 1px solid #DCDEE5;
          border-left: 1px solid #DCDEE5;
          align-items: center;
          flex-shrink: 0;
        }

        .content {
          display: flex;
          height: 100%;
          padding-left: 16px;
          align-items: center;

          .value-container {

            .value-cls {
              color: #313238;
              cursor: pointer;
            }

            .operate-btn {
              display: none;
            }

            &:hover {

              .value-cls {
                color: #1768ef;
              }

              .operate-btn {
                display: inline-block;
              }
            }
          }

        }
      }
    }

    .apigateway-icon {
      padding: 2px;
      font-size: 14px;
      color: #3a84ff;
      cursor: pointer;
    }

    .edit-name {
      display: flex;
      align-items: center;

      .edit-name-icon {
        padding: 2px;
        margin-left: 4px;
        font-size: 16px;
        color: #3a84ff;
        cursor: pointer;
      }
    }

    :deep(.back-config-timeout) {
      display: inline-block;

      .edit-action,
      .refresh-icon {
        margin-left: 8px;
        font-size: 16px;
        color: #3A84FF;
        vertical-align: middle;
        cursor: pointer;
      }
    }
  }

  .footer-btn-wrapper {
    bottom: 0;
    height: 52px;
    padding-left: 170px;
    line-height: 52px
  }

  .fixed-footer-btn-wrapper {
    position: absolute;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 9;
    width: 100%;
    padding-left: 24px;
    background-color: #fff;
    box-shadow: 0 -2px 4px 0 #0000000f;
    transition: .3s;
  }
}
</style>
