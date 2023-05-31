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
import dayjs from 'dayjs'

export default {
  methods: {
    $getChartIntervalOption (max, type, axis) {
      const option = {
        yAxis: {
          axisLabel: {}
        },
        xAxis: {
          axisLabel: {}
        }
      }

      // 动态计算出max合适值和interval配置
      if (type === 'number') {
        if (max >= 0 && max <= 10) {
          option[axis].interval = 1
        } else if (max > 10 && max <= 20) {
          option[axis].interval = 2
        } else if (max > 20 && max <= 50) {
          option[axis].interval = 5
        } else if (max > 50 && max <= 100) {
          option[axis].interval = 10
        } else if (max > 100 && max <= 1000) {
          option[axis].interval = 100
        } else if (max > 1000 && max <= 5000) {
          option[axis].interval = 500
        } else if (max > 5000 && max <= 10000) {
          option[axis].interval = 1000
        } else if (max > 10000 && max <= 20000) {
          option[axis].interval = 2000
        } else if (max > 20000 && max <= 50000) {
          option[axis].interval = 5000
        } else if (max > 50000 && max <= 100000) {
          option[axis].interval = 10000
        } else if (max > 100000 && max <= 500000) {
          option[axis].interval = 20000
        } else if (max > 500000 && max <= 1000000) {
          option[axis].interval = 50000
        } else if (max > 1000000 && max <= 5000000) {
          option[axis].interval = 500000
        } else if (max > 5000000 && max <= 10000000) {
          option[axis].interval = 1000000
        } else {
          option[axis].interval = 10000000
        }
        option[axis].max = function (value) {
          return value.max + (option[axis].interval - (value.max % option[axis].interval))
        }

        option[axis].min = function (value) {
          // 使0值显示在grid中间
          if (value.max === 0) {
            return -1 * (value.max + (option[axis].interval - (value.max % option[axis].interval)))
          }

          return 0
        }

        // option[axis].axisLabel.formatter = (value) => {
        //     let displayValue = value
        //     if (value >= 1e3) {
        //         displayValue = `${value / 1e3} K`
        //     }
        //     return displayValue
        // }
      }

      // 根据时间值计算显示年/月/日/时间部分
      if (type === 'time') {
        if (max >= 0 && max <= 3600) {
          // 1小时内
          option[axis].interval = 60 * 1000 * 5
          option[axis].axisLabel.formatter = (value) => {
            return dayjs(value).format('HH:mm:ss')
          }
        } else if (max > 3600 && max <= 86400) {
          // 1天内
          option[axis].interval = 60 * 60 * 1000 * 2
          option[axis].axisLabel.formatter = (value) => {
            return dayjs(value).format('HH:mm')
          }
        } else if (max > 86400 && max <= 86400 * 31) {
          // 1月内
          option[axis].interval = 86400 * 1000
          option[axis].axisLabel.formatter = (value) => {
            return dayjs(value).format('MM-DD HH:mm')
          }
        } else if (max > 86400 * 31 && max <= 86400 * 31 * 12) {
          // 1年内
          option[axis].interval = 86400 * 1000 * 31
          option[axis].axisLabel.formatter = (value) => {
            return dayjs(value).format('MM-DD')
          }
        } else {
          // 大于1年
          option[axis].interval = 86400 * 1000 * 31 * 3
          option[axis].axisLabel.formatter = (value) => {
            return dayjs(value).format('YYYY-MM-DD')
          }
        }
      }

      return option
    }
  }
}
