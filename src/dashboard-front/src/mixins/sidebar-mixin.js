/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
export default {
  data () {
    return {
      // 初始化状态
      initDataStr: ''
    }
  },
  methods: {
    /**
         * 侧边栏离开，二次确认
         * @return true / error
         */
    $isSidebarClosed (targetDataStr) {
      let isEqual = this.initDataStr === targetDataStr
      if (typeof targetDataStr !== 'string') {
        // 数组长度对比
        const initData = JSON.parse(this.initDataStr)
        isEqual = initData.length === targetDataStr.length
      }
      return new Promise((resolve, reject) => {
        // 未编辑
        if (isEqual) {
          resolve(true)
        } else {
          // 已编辑
          this.$bkInfo({
            extCls: 'sideslider-close-cls',
            title: this.$t('确认离开当前页？'),
            subTitle: this.$t('离开将会导致未保存信息丢失'),
            okText: this.$t('离开'),
            confirmFn () {
              resolve(true)
            },
            cancelFn () {
              resolve(false)
            }
          })
        }
      })
    },
    initSidebarFormData (data) {
      this.initDataStr = JSON.stringify(data)
    }
  }
}
