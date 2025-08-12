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

/**
 * datepicker 时间选择器 hooks 适用于列表筛选
 */

/**
 * useDatePicker - 时间选择器的自定义钩子函数
 * @param {any} filterData - 可选参数，用于筛选数据
 * @returns {object} - 返回包含快捷日期范围、日期值、处理日期变化、清除日期和确认日期的函数
 */
export const useDatePicker = (filterData?: any) => {
  const { t } = useI18n(); // 获取国际化函数
  const shortcutsRange = reactive([
    {
      text: t('今天'), // 今天的快捷选项
      value() {
        const end = new Date();
        const start = new Date(end.getFullYear(), end.getMonth(), end.getDate());
        return [start, end];
      },
    },
    {
      text: t('近7天'), // 近7天的快捷选项
      value() {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
        return [start, end];
      },
    },
    {
      text: t('近15天'), // 近15天的快捷选项
      value() {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 15);
        return [start, end];
      },
    },
    {
      text: t('近30天'), // 近30天的快捷选项
      value() {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
        return [start, end];
      },
    },
  ]);

  const dateValue = ref<string[]>([]); // 日期值

  /**
   * handleChange - 处理日期变化
   * @param {any} date - 选中的日期
   */
  const handleChange = (date: any) => {
    dateValue.value = date;
  };

  /**
   * handleClear - 清除日期
   */
  const handleClear = () => {
    dateValue.value = ['', ''];
    setFilterDate(dateValue.value);
  };

  /**
   * handleConfirm - 确认日期
   */
  const handleConfirm = () => {
    setFilterDate(dateValue.value);
  };

  /**
   * setFilterDate - 格式化时间并设置筛选数据
   * @param {any[]} date - 日期数组
   */
  const setFilterDate = (date: any[]) => {
    if (date[0] && date[1]) {
      // @ts-expect-error ignore
      filterData.value.time_start = parseInt((+new Date(date[0])) / 1000, 10);
      // @ts-expect-error ignore
      filterData.value.time_end = parseInt((+new Date(date[1])) / 1000, 10);
    }
    else {
      filterData.value.time_start = '';
      filterData.value.time_end = '';
    }
  };

  return {
    shortcutsRange,
    dateValue,
    handleChange,
    handleClear,
    handleConfirm,
  };
};
