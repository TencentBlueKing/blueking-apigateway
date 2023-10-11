<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { createGateway, getGatewaysList } from '@/http';
import { Message } from 'bkui-vue';
import { IPagination, IDialog } from '@/types';
import {
  ref,
} from 'vue';
const { t } = useI18n();

const filterKey = ref<string>('updated_time');
// 弹窗
const dialogData = ref<IDialog>({
  isShow: false,
  title: t('新建网关'),
  loading: false,
});
// 分页状态
const pagination = ref<IPagination>({
  offset: 0,
  limit: 10,
  count: 0,
});
const formData = ref({
  name: '',
  maintainers: ['admin'],
  description: '',
  is_public: false,
});

const tableData = ref([]);

// 当前年份
const curYear = (new Date()).getFullYear();

const filterData = ref([
  { value: 'created_time', label: t('创建时间') },
  { value: 'updated_time', label: t('更新时间') },
  { value: 'name', label: t('字母 A-Z') },
]);

// 新建网关弹窗
const showAddDialog = () => {
  formData.value = {
    name: '',
    maintainers: ['admin'],
    description: '',
    is_public: false,
  };
  dialogData.value.isShow = true;
};

// 创建网关确认
const handleConfirmCreate = async () => {
  dialogData.value.loading = true;
  try {
    await createGateway(formData.value);
    Message({
      message: t('创建成功'),
      theme: 'success',
    });
  } catch (error) {} finally {
    dialogData.value.loading = false;
  }
};

// 获取列表数据
const getGatewaysListData = async () => {
  try {
    const res = await getGatewaysList({
      limit: pagination.value.limit,
      offset: pagination.value.limit * pagination.value.offset,
    });
    tableData.value = res.results;
  } catch (error) {}
};

getGatewaysListData();

</script>

<template>
  <div class="home-container">
    <div class="title-container flex-row justify-content-between">
      <div class="flex-1 left">{{ t('我的网关') }} (3)</div>
      <div class="flex-1 flex-row">
        <bk-button
          theme="primary"
          @click="showAddDialog"
        >
          {{ t('新建网关') }}
        </bk-button>
        <bk-input class="ml10 mr10 search-input" placeholder="请输入网关名"></bk-input>
        <bk-select
          v-model="filterKey"
        >
          <bk-option v-for="(item, index) in filterData" :key="index" :value="item.value" :label="item.label" />
        </bk-select>
      </div>
    </div>
    <div class="table-container">
      <div class="table-header flex-row">
        <div class="flex-1 of4">{{t('网关名')}}</div>
        <div class="flex-1 of1">创建者</div>
        <div class="flex-1 of2">环境列表</div>
        <div class="flex-1 of1 text-c">资源数量</div>
        <div class="flex-1 of2">操作</div>
      </div>
      <div class="table-item flex-row align-items-center" v-for="item in tableData" :key="item.id">
        <div class="flex-1 flex-row align-items-center of4">
          <div class="name-logo mr10" :class="item.status ? '' : 'deact'">
            {{ item.name[0].toUpperCase() }}
          </div>
          <span class="name mr10" :class="item.status ? '' : 'deact-name'">{{ item.name }}</span>
          <bk-tag theme="info" v-if="item.is_official">{{ t('官方') }}</bk-tag>
          <bk-tag theme="warning" v-if="item.is_public">{{ t('公开') }}</bk-tag>
          <bk-tag v-if="item.status === 0">{{ t('已停用') }}</bk-tag>
        </div>
        <div class="flex-1 of1">{{ item.created_by }}</div>
        <div class="flex-1 of2 env">
          <div class="flex-row">
            <bk-tag v-for="envItem in item.stages" :key="envItem.id">
              <i :class="['ag-dot',{ 'success': envItem.released }]"></i>
              {{ envItem.name }}
            </bk-tag>
          </div>
        </div>
        <div class="flex-1 of1 text-c" :class="item.resource_count ? 'default-c' : ''">{{ item.resource_count }}</div>
        <div class="flex-1 of2">
          <bk-button
            text
            theme="primary"
          >
            环境概览
          </bk-button>
          <bk-button
            text
            theme="primary"
            class="pl20"
          >
            资源配额
          </bk-button>
          <bk-button
            text
            theme="primary"
            class="pl20"
          >
            流水日志
          </bk-button>
        </div>
      </div>
    </div>
    <div class="footer-container">
      <div>
        <bk-link theme="primary">技术支持</bk-link> | <bk-link theme="primary">产品官网</bk-link>
      </div>
      Copyright © 2012-{{curYear}} Tencent BlueKing. All Rights Reserved.
    </div>

    <bk-dialog
      v-model:is-show="dialogData.isShow"
      width="600"
      :title="dialogData.title"
      theme="primary"
      quick-close
      :is-loading="dialogData.loading"
      @confirm="handleConfirmCreate">
      <bk-form ref="formRef" form-type="vertical" :model="formData">
        <bk-form-item
          label="名称"
          property="name"
          required
        >
          <bk-input
            v-model="formData.name"
            placeholder="请输入"
            clearable
          />
        </bk-form-item>
        <bk-form-item
          label="维护人员"
          property="name"
          required
        >
          <bk-input
            v-model="formData.maintainers"
            placeholder="请输入"
            clearable
          />
        </bk-form-item>
        <bk-form-item
          label="描述"
          property="name"
          required
        >
          <bk-input
            type="textarea"
            v-model="formData.description"
            placeholder="请输入"
            clearable
          />
        </bk-form-item>
        <bk-form-item
          label="是否公开"
          property="isopen"
          required
        >
          <bk-switcher v-model="formData.is_public" />
          <span class="common-form-tips">公开，则用户可查看资源文档、申请资源权限；不公开，则网关对用户隐藏</span>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<style lang="scss" scoped>
.home-container{
  width: 80%;
  margin: 0 auto;
  font-size: 14px;
  .title-container{
    width: 100%;
    padding: 28px 16px;
    .left{
      font-size: 20px;
      color: #313238;
      flex: 0 0 60%;
    }
  }
  .table-container{
    width: 100%;
    height: calc(100vh - 192px);
    .table-header{
      width: 100%;
      color: #979BA5;
      padding: 0 16px;
    }
    .table-item{
      width: 100%;
      height: 80px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      padding: 0 16px;
      margin: 12px 0px;
      cursor: pointer;
      .name-logo{
        width: 48px;
        height: 48px;
        line-height: 48px;
        text-align: center;
        background: #F0F5FF;
        border-radius: 4px;
        color: #3A84FF;
        font-size: 26px;
        font-weight: 700;
      }
      .name{
        font-weight: 700;
        color: #313238;
        &:hover{
          color: #3a84ff;
        }
      }
      .env{
        overflow: hidden;
        .ag-dot{
          width: 8px;
          height: 8px;
          display: inline-block;
          vertical-align: middle;
          border-radius: 50%;
          border: 1px solid #C4C6CC;
        }
        .success{
          background: #e5f6ea;
          border: 1px solid #3fc06d;
        }
      }
    }
    .of1{
        flex: 0 0 10%;
      }
      .of2{
        flex: 0 0 20%;
      }
      .of4{
        flex: 0 0 40%;
      }
  }

  .footer-container{
    text-align: center;
    height: 52px;
  }

  .deact{
    background: #EAEBF0 !important;
    color: #fff !important;
    &-name{
      color: #979BA5 !important;
    }
  }
}
</style>
