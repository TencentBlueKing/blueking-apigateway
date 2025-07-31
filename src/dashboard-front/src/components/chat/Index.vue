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
  <div class="chat-box">
    <a
      href="javascript: void(0);"
      class="support-btn"
      @click="handleShowDialog"
    >
      <AgIcon
        name="qiye-weixin"
        size="16"
        class="doc-qw icon-ag-qw mr-3px"
      /> {{ t('一键拉群') }}
    </a>

    <BkDialog
      v-model:is-show="chatDialog.visible"
      width="600"
      header-align="left"
      theme="primary"
      :quick-close="false"
      :title="t('一键拉群')"
      @confirm="handleConfirm"
      @closed="handleCancel"
    >
      <div class="chat-dialog">
        <div class="flex items-center header">
          <div class="icon">
            <AgIcon
              name="qiye-weixin"
              size="50"
              class="ag-doc-icon doc-qw apigateway-icon icon-ag-qw"
            />
          </div>
          <div class="desc">
            <p> {{ t('一键拉群功能') }} </p>
            <p> {{ t('可以通过企业微信将需求的相关人员邀请到一个群里进行讨论') }} </p>
          </div>
        </div>
        <div v-bk-tooltips="{ content: userlist.join(', ') }">
          <BkInput
            :key="renderKey"
            v-model="userlist"
            :show-overflow-tooltips="false"
            :placeholder="t('请输入群成员')"
            class="chat-selector"
            disabled
          />
        </div>
      </div>
    </BkDialog>
  </div>
</template>

<script lang="ts" setup>
import {
  createChat,
  sendChat,
} from '@/services/source/chat';
import { useStage } from '@/stores';
import { Message } from 'bkui-vue';

interface IProps {
  name: string
  owner: string
  defaultUserList: string[]
  content: string
  isQuery: boolean
}

const {
  name = '',
  owner = '',
  defaultUserList = [] as string[],
  content = '',
  isQuery = false,
} = defineProps<IProps>();

const { t } = useI18n();
const stageStore = useStage();

const renderKey = ref<number>(0);
const chatDialog = reactive<any>({ visible: false });
const userlist = ref([...defaultUserList]);

const curStage = computed(() => stageStore.curStageData?.id);

const handleShowDialog = () => {
  chatDialog.visible = true;
};

const handleCancel = () => {
  chatDialog.visible = false;
};

const handleConfirm = async () => {
  let contentStr = content;
  if (isQuery) {
    const qeury = contentStr.split('?')[1];
    if (!qeury) {
      contentStr = `${contentStr}?stage=${curStage.value}`;
    }
  }
  if (!userlist.value?.length) {
    Message({
      theme: 'error',
      message: t('请选择群成员'),
    });
    return false;
  }

  // 创建群
  const body = {
    bk_app_code: 'create-chat',
    name: name,
    owner: owner,
    userlist: [...userlist.value, owner],
  };
  const res = await createChat(body);
  // 发送消息
  const chartId = res.data.chatid;

  const data = {
    bk_app_code: 'create-chat',
    chatid: chartId,
    msgtype: 'text',
    text: { content: contentStr },
  };
  await sendChat(data);
  Message({
    theme: 'success',
    message: t('创建成功'),
  });
};

watch(
  () => defaultUserList,
  () => {
    defaultUserList?.forEach((user: any) => {
      if (!userlist.value?.includes(user)) {
        userlist.value.push(user);
      }
    });
    renderKey.value += 1;
  },
);

</script>

<style lang="scss" scoped>
.chat-dialog {
  padding-bottom: 32px;
}

.chat-box {
  display: inline-block;
}

:deep(.chat-selector) {

  .bk-tag-input {
    min-height: 100px;
  }

  .bk-tag-selector .bk-tag-input {
    align-items: flex-start;
  }

  .clear-icon {
    display: none;
  }
}

.support-btn {
  display: inline-block;
  font-size: 12px;
  color: #3A84FF;
}

.header {
  margin-bottom: 10px;

  .icon {
    width: 60px;
    text-align: left;
    font-size: 50px;
    line-height: 1;
  }

  .desc {
    flex: 1;
    padding-top: 10px;

    p {
      margin-bottom: 10px;
      font-size: 14px;
      line-height: 1;
    }
  }
}
</style>
