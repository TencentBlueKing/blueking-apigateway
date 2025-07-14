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

/** 基于infoBox二次封装  */
import { type VNode } from 'vue';
import { InfoBox } from 'bkui-vue';
import { isFunction } from 'lodash-es';

type Align = 'center' | 'left' | 'right';
type Theme = 'danger' | 'success' | 'warning' | 'primary';
type InfoType = 'danger' | 'success' | 'warning' | 'loading';

export interface IProps {
  isShow?: boolean
  width?: number | string
  class?: string | string[]
  type?: InfoType
  title?: (() => VNode | string) | VNode | string
  subTitle?: (() => VNode) | VNode | string
  content?: (() => VNode) | VNode | string
  footer?: (() => VNode) | VNode | string
  headerAlign?: Align
  footerAlign?: Align
  contentAlign?: Align
  showContentBgColor?: boolean
  showMask?: boolean
  quickClose?: boolean
  escClose?: boolean
  closeIcon?: boolean
  confirmText?: (() => VNode) | VNode | string
  cancelText?: (() => VNode) | VNode | string
  confirmButtonTheme?: Theme
  beforeClose?: (v: string) => Promise<boolean> | boolean
  onConfirm?: () => void
  onCancel?: () => void
}

export class InfoModel implements IProps {
  isShow?: boolean = false;
  width?: number | string = 480;
  contentAlign?: Align = 'left';
  showContentBgColor?: boolean = true;
}

export function usePopInfoBox(props: Partial<IProps>) {
  const infoBoxInstance = InfoBox(new InfoModel());

  const renderTitle = () => {
    if (isFunction(props.title)) {
      return <div class="info-box-title">{props.title?.()}</div>;
    }
    return props.title;
  };

  const renderContent = () => {
    const displayContent = props.subTitle ?? props.content;
    if (isFunction(displayContent)) {
      return <div class="info-box-content">{displayContent?.()}</div>;
    }
    return displayContent;
  };

  const renderInfoBox = () => {
    infoBoxInstance.update({
      ...props,
      title: renderTitle(),
      content: renderContent(),
    });
    infoBoxInstance.show();
  };

  // 是否初始化的时候展示infoBox
  if (props?.isShow) {
    renderInfoBox();
  }
}
