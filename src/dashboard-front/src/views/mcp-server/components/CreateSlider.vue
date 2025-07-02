<template>
  <BkSideslider
    v-model:is-show="isShow"
    :title="sliderTitle"
    :width="1280"
    class="create-slider"
    quick-close
    :before-close="handleBeforeClose"
  >
    <template #default>
      <div class="slider-content">
        <div class="main">
          <BkAlert v-if="noValidStage" style="margin-bottom: 24px;" theme="warning">{{ t('没有可用的环境') }}</BkAlert>
          <bk-form ref="formRef" :model="formData" :rules="rules" form-type="vertical">
            <bk-form-item :label="t('环境')" property="stage_id" required>
              <bk-select
                v-model="formData.stage_id"
                :clearable="false"
                :disabled="isEditMode || noValidStage"
                @change="handleStageSelectChange"
              >
                <bk-option
                  v-for="_stage in stageList"
                  :id="_stage.id"
                  :key="_stage.id"
                  :disabled="!_stage.resource_version?.version"
                  :name="_stage.name"
                />
              </bk-select>
            </bk-form-item>
            <bk-form-item :label="t('服务名称')" property="name" required>
              <bk-input
                v-model="formData.name"
                :disabled="isEditMode || noValidStage"
                :prefix="(isEditMode || noValidStage )? undefined : serverNamePrefix"
              />
              <div class="name-help-text">
                <div class="text-body">{{ t('唯一标识，以网关名称和环境名称为前缀，创建后不可更改') }}</div>
                <div class="url">
                  <div class="label">{{ t('访问地址') }}：</div>
                  <div class="content">{{ serverUrl }}</div>
                  <div class="suffix">
                    <AgIcon name="copy-info" @click.stop="handleCopyClick" />
                  </div>
                </div>
              </div>
            </bk-form-item>
            <bk-form-item :label="t('描述')" property="description">
              <bk-input v-model="formData.description" :disabled="noValidStage" clearable />
            </bk-form-item>
            <bk-form-item :label="t('标签')" property="labels">
              <bk-tag-input
                v-model="formData.labels"
                :disabled="noValidStage"
                allow-create
                collapse-tags
                has-delete-icon
              />
            </bk-form-item>
            <bk-form-item :label="t('是否公开')" property="is_public" required>
              <bk-switcher v-model="formData.is_public" :disabled="noValidStage" theme="primary" />
              <span style="color:#979ba5;font-size: 12px;">{{
                  t('不公开则不会展示到 MCP 市场，且蓝鲸应用无法申请主动申请权限，只能由网关管理员给应用主动授权')
                }}</span>
            </bk-form-item>
            <!-- 资源选择表格 -->
            <bk-form-item>
              <template #label>
                <div class="resource-form-item-label">
                  <div class="label-text"><span>{{ t('工具') }}</span><span class="required-mark">*</span></div>
                  <BkButton
                    :disabled="noValidStage || !isCurrentStageValid" text theme="primary" @click="handleRefreshClick"
                  >
                    <AgIcon class="mr4" name="refresh-line" />
                    {{ t('刷新') }}
                  </BkButton>
                </div>
              </template>
              <!--              <div class="resource-tips">-->
              <!--                {{ resourceTips }}-->
              <!--              </div>-->
              <div class="resource-tips">
                {{ t('请从已经发布到该环境的资源列表选取资源作为 MCP Server 的工具') }}
              </div>
              <div class="resource-selector-wrapper">
                <div class="selector-main">
                  <div class="selector-title">{{ t('资源列表') }}</div>
                  <div class="resource-filter">
                    <BkInput v-model="filterKeyword" :disabled="noValidStage" type="search" />
                  </div>
                  <bk-table
                    ref="tableRef"
                    :columns="columns"
                    :data="filteredResourceList"
                    :pagination="pagination"
                    border="outer"
                    show-overflow-tooltip
                  >
                    <template #empty>
                      <TableEmpty :keyword="filterKeyword" @clear-filter="filterKeyword = ''" />
                    </template>
                  </bk-table>
                </div>
                <div class="result-preview">
                  <div class="result-preview-list">
                    <div class="header-title-wrapper">
                      <div class="name">{{ t('结果预览') }}</div>
                      <BkButton
                        text
                        theme="primary"
                        @click="handleClearSelections"
                      >
                        {{ t('清空') }}
                      </BkButton>
                    </div>
                    <template v-if="selections.length">
                      <div v-for="(name, index) in selections" :key="index" class="list-main">
                        <div class="list-item">
                          <span class="name">
                            {{ name }}
                          </span>
                          <AgIcon
                            class="delete-icon"
                            name="icon-close"
                            size="24"
                            @click="() => handleRemoveResource(name)"
                          />
                        </div>
                      </div>
                    </template>
                    <TableEmpty v-else />
                  </div>
                </div>
              </div>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </template>
    <template #footer>
      <div style="margin-left: 16px;">
        <bk-button :disabled="noValidStage" style="width: 100px" theme="primary" @click="handleSubmit">
          {{ t('确定') }}
        </bk-button>
        <bk-button style="margin-left: 4px; width: 100px" @click="handleCancel">
          {{ t('取消') }}
        </bk-button>
      </div>
    </template>
  </BkSideslider>
</template>

<script lang="tsx" setup>
import { useI18n } from 'vue-i18n';
import {
  computed,
  ref,
  watch,
} from 'vue';
import { useRouter } from 'vue-router';
import {
  getResourceVersionsInfo,
  getStageList,
} from '@/http';
import { useCommon } from '@/store';
import AgIcon from '@/components/ag-icon.vue';
import { IPagination } from '@/types';
import { refDebounced } from '@vueuse/core';
import {
  Form,
  Message,
  Table,
} from 'bkui-vue';
import TableEmpty from '@/components/table-empty.vue';
import {
  createServer,
  getServer,
  patchServer,
} from '@/http/mcp-server';
import { useSidebar } from '@/hooks';
import { copy } from '@/common/util';

const { BK_API_URL_TMP } = window;

interface IProps {
  serverId?: number,
}

interface FormData {
  name: string,
  description: string,
  stage_id: number | undefined,
  is_public: boolean,
  labels: string[],
}

const { serverId } = defineProps<IProps>();

const emit = defineEmits<{
  updated: [],
}>();

const { t } = useI18n();
const router = useRouter();
const common = useCommon();
const { initSidebarFormData, isSidebarClosed } = useSidebar();

const isShow = ref(false);
const formRef = ref<InstanceType<typeof Form>>();
const formData = ref<FormData>({
  name: '',
  description: '',
  stage_id: 0,
  is_public: true,
  labels: [],
});

const stageList = ref<any[]>([]);
const resourceList = ref<any[]>([]);
const isLoading = ref(false);
const filterKeyword = ref('');
const filterKeywordDebounced = refDebounced(filterKeyword, 300);
const pagination = ref<IPagination>({
  offset: 0,
  limit: 10,
  count: 0,
  current: 1,
});
const selections = ref<string[]>([]);
const tableRef = ref<InstanceType<typeof Table>>();

const rules = {
  stage_id: [
    {
      required: true,
      message: t('请选择'),
      trigger: 'blur',
    },
  ],
};

const methodTagThemeMap = {
  'POST': 'info',
  'GET': 'success',
  'DELETE': 'danger',
  'PUT': 'warning',
  'PATCH': 'info',
  'ANY': 'success',
};

const columns = [
  {
    label: () => <bk-checkbox
      indeterminate={!!selections.value.length && selections.value.length !== resourceList.value.length}
      modelValue={selections.value.length && selections.value.length === resourceList.value.length}
      onChange={(checked: boolean) => handleSelectAllResource(checked)}
    />,
    width: 60,
    align: 'center',
    render: ({ row }: any) => <bk-checkbox
      modelValue={isRowSelected(row)}
      disabled={!row.has_openapi_schema}
      onChange={(checked: boolean) => handleSelectResource(row, checked)}
    />,
  },
  {
    label: t('资源名称'),
    render: ({ row }: any) =>
      <bk-button
        text
        theme="primary"
        v-bk-tooltips={{
          content: (<div>{t('资源需要确认请求参数后才能添加到MCP Server')}</div>),
          disabled: row.has_openapi_schema,
        }}
        onClick={() => handleToolNameClick(row)}
      >{row.name}</bk-button>,
  },
  {
    label: t('是否配置请求参数声明'),
    width: 170,
    showOverflowTooltips: false,
    render: ({ row }: any) => row.has_openapi_schema ? t('是') : t('否'),
  },
  {
    label: t('请求方法'),
    width: 100,
    showOverflowTooltips: false,
    render: ({ row }: any) => <bk-tag
      theme={methodTagThemeMap[row.method as keyof typeof methodTagThemeMap]}
    >{row.method}</bk-tag>,
  },
  {
    label: t('请求路径'),
    field: 'path',
  },
  {
    label: t('描述'),
    field: 'description',
  },
];

const isEditMode = computed(() => !!serverId);
const stage = computed(() => stageList.value.find(stage => stage.id === formData.value.stage_id));
const stageName = computed(() => stage.value?.name || '');
const serverNamePrefix = computed(() => `${common.curApigwData.name}-${stageName.value}-`);
const sliderTitle = computed(() => {
  return isEditMode.value ? t('编辑 {n}', { n: `${serverNamePrefix.value}${formData.value.name}` })
                          : t('创建 MCP Server');
});

const filteredResourceList = computed(() => {
  return resourceList.value.filter((resource: any) => {
    const keyword = filterKeywordDebounced.value.trim().toLowerCase();
    const matchName = resource.name.toLowerCase().includes(keyword);
    const matchPath = resource.path.toLowerCase().includes(keyword);
    return matchName || matchPath;
  });
});

const serverUrl = computed(() => {
  return `${BK_API_URL_TMP || ''}/prod/api/v2/mcp-servers/${formData.value.name}/sse/`
});

// const resourceTips = computed(() => t('请从已经发布到 {s} 环境的资源列表选取资源作为 MCP Server 的工具', { s: stage.value.name || '--' }))

watch(isShow, async () => {
  if (isShow.value) {
    await fetchStageList();
    if (isEditMode.value) {
      await fetchServer();
    }
    initSidebarFormData(formData.value);
  } else {
    resetSliderData();
  }
});

const handleSubmit = async () => {
  await formRef.value.validate();
  if (selections.value.length === 0) {
    Message({
      theme: 'error',
      message: t('请选择工具'),
    });
    return;
  }
  if (isEditMode.value) {
    const {
      description,
      is_public,
      labels,
    } = formData.value;
    const params = {
      description,
      is_public,
      labels,
      resource_names: [...selections.value],
    };
    await patchServer(
      common.apigwId,
      serverId,
      params,
    );
    Message({
      theme: 'success',
      message: t('编辑成功'),
    });
  } else {
    const params = Object.assign({}, formData.value, {
      name: `${serverNamePrefix.value}${formData.value.name}`,
      resource_names: [...selections.value],
    });
    await createServer(
      common.apigwId,
      params,
    );
    Message({
      theme: 'success',
      message: t('创建成功'),
    });
  }
  emit('updated');
  isShow.value = false;
};

const noValidStage = computed(() => stageList.value.every(stage => stage.status === 0));

const isCurrentStageValid = computed(() => stageList.value.find(stage => stage.id === formData.value.stage_id)?.status === 1);

const fetchStageList = async () => {
  try {
    isLoading.value = true;
    const response = await getStageList(common.apigwId);
    stageList.value = response || [];
    const validStage = stageList.value.find(stage => stage.status === 1);
    formData.value.stage_id = validStage?.id ?? undefined;
    if (formData.value.stage_id) {
      await fetchStageResources();
    }
  } finally {
    isLoading.value = false;
  }
};

const fetchServer = async () => {
  const response = await getServer(common.apigwId, serverId!);
  formData.value.name = response.name || '';
  formData.value.description = response.description || '';
  formData.value.labels = response.labels || [];
  formData.value.is_public = response.is_public ?? true;
  formData.value.stage_id = response.stage.id || 0;
  selections.value = response.resource_names;
}

const fetchStageResources = async () => {
  if (stage.value && stage.value.resource_version?.id) {
    const response = await getResourceVersionsInfo(
      common.curApigwData.id,
      stage.value.resource_version.id,
      {
        stage_id: stage.value.id,
        source: 'mcp_server',
      },
    );
    resourceList.value = response?.resources || [];
    pagination.value.offset = 0;
    pagination.value.count = resourceList.value.length;
  } else {
    resourceList.value = [];
  }
}

const handleSelectResource = (row: any, checked: boolean) => {
  if (checked) {
    if (!selections.value.includes(row.name)) {
      selections.value.push(row.name);
    }
  } else {
    selections.value = selections.value.filter(item => item !== row.name);
  }
};

const handleSelectAllResource = (checked: boolean) => {
  if (checked) {
    selections.value = resourceList.value.filter((resource) => resource.has_openapi_schema)
                                   .map((resource) => resource.name);
  } else {
    selections.value = [];
  }
};

const handleRemoveResource = (name: string) => {
  selections.value = selections.value.filter(item => item !== name);
}

const handleClearSelections = () => {
  selections.value = [];
};

const isRowSelected = (row: any) => selections.value.includes(row.name);

const handleRefreshClick = async () => {
  if (!isCurrentStageValid.value) {
    return;
  }
  filterKeyword.value = '';
  const response = await getResourceVersionsInfo(
    common.curApigwData.id,
    stage.value.resource_version.id,
    {
      stage_id: stage.value.id,
      source: 'mcp_server',
    },
  );
  resourceList.value = response?.resources || [];
  selections.value = selections.value.filter(selectedResourceName =>
    resourceList.value.some(resource => resource.name === selectedResourceName),
  );
  pagination.value = {
    offset: 0,
    limit: 10,
    count: resourceList.value.length,
    current: 1,
  };
};

const handleStageSelectChange = () => {
  fetchStageResources();
};

const handleToolNameClick = (row: { id: number }) => {
  const routeData = router.resolve({
    name: 'apigwResourceEdit',
    params: { id: common.curApigwData.id, resourceId: row.id },
  });
  window.open(routeData.href, '_blank');
};

const handleCancel = () => {
  isShow.value = false;
};

const handleCopyClick = () => {
  copy(serverUrl.value);
}

const resetSliderData = () => {
  formData.value = {
    name: '',
    description: '',
    stage_id: 0,
    is_public: true,
    labels: [],
  };
  stageList.value = [];
  resourceList.value = [];
  selections.value = [];
};

const handleBeforeClose = () => {
  return isSidebarClosed(JSON.stringify(formData.value));
};

defineExpose({
  show: () => {
    isShow.value = true;
  },
});

</script>

<style lang="scss" scoped>
.create-slider {
  :deep(.bk-modal-content) {
    overflow-y: auto;
  }

  .slider-content {
    width: 100%;

    .main {
      color: #4d4f56;
      padding: 28px 40px 0;

      .name-help-text {
        .text-body {
          font-size: 12px;
          color: #979ba5;
        }

        .url {
          padding-left: 8px;
          width: 100%;
          height: 32px;
          background: #f5f7fa;
          font-size: 12px;
          display: flex;
          align-items: center;

          .label {
            color: #4d4f56;
            line-height: 20px;
          }

          .content {
            color: #313238;
            line-height: 20px;
          }

          .suffix {
            margin-left: 8px;
            cursor: pointer;

            &:hover {
              color: #3a84ff;
            }
          }
        }
      }
    }
  }
}

.resource-form-item-label {
  display: flex;
  align-items: center;
  gap: 16px;

  .label-text {
    position: relative;

    .required-mark {
      position: absolute;
      top: 0;
      width: 14px;
      color: #ea3636;
      text-align: center;
      font-size: 14px;
    }
  }
}

.resource-tips {
  font-size: 12px;
  color: #979ba5;
  margin-bottom: 8px;
}

.resource-selector-wrapper {
  border: 1px solid #dcdee5;
  display: flex;

  .selector-main {
    width: 908px;
    padding: 16px;
    flex-shrink: 0;

    .selector-title {
      font-weight: 700;
      font-size: 14px;
      color: #4d4f56;
      margin-bottom: 16px;
    }

    .resource-filter {
      margin-bottom: 16px;
    }
  }

  .result-preview {
    width: 275px;
    max-height: 653px;
    background: #f5f7fa;
    padding: 16px;
    display: flex;
    flex-direction: column;
    border-left: 1px solid #dcdee5;
    overflow-y: auto;

    .result-preview-list {
      flex: 1;
    }

    .header-title-wrapper {
      display: flex;
      font-size: 14px;
      justify-content: space-between;
      margin-bottom: 16px;

      .name {
        font-weight: 700;
        color: #4d4f56;
      }
    }

    .list-main {
      overflow-y: auto;
      flex: 1;

      .list-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 32px;
        padding: 6px 10px;
        background: #fff;
        border-radius: 2px;
        box-shadow: 0 1px 2px 0 #0000001f;
        margin-bottom: 4px;

        .name {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .delete-icon {
          color: #c4c6cc;
          cursor: pointer;

          &:hover {
            color: #3a84ff;
          }
        }
      }
    }
  }
}
</style>
