/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

const COLORS_HEX = [
  '#D2E6B8',
  '#8FDBB5',
  '#7FC7EB',
  '#B7C1F5',
  '#EEB4FA',
  '#FAA796',
  '#FFE294',
  '#B8D1A7',
  '#82C7B0',
  '#76A9DB',
  '#ABABE6',
  '#DB9EDB',
  '#E09D87',
  '#E0D782',
  '#B5E0AB',
  '#66CCCC',
  '#A3C6FF',
  '#CFBEFF',
  '#F5B7E0',
  '#FFCC99',
  '#EBF0A3',
  '#9CCC9C',
  '#61B2C2',
  '#93A6E6',
  '#C0A7E0',
  '#E0A7BA',
  '#EBCB8D',
  '#CBDB95',
];

export class ColorGenerator {
  colorsHex: string[];
  colorsRgb: [number, number, number][];
  cache: Map<string, number>;
  currentIdx: number;

  constructor(colorsHex: string[] = COLORS_HEX) {
    this.colorsHex = colorsHex;
    this.colorsRgb = colorsHex.map(strToRgb);
    this.cache = new Map();
    this.currentIdx = 0;
  }

  _getColorIndex(key: string): number {
    let i = this.cache.get(key);
    // if (i === null) {
    if (i === undefined) {
      i = this.currentIdx;
      this.cache.set(key, this.currentIdx);

      this.currentIdx = ++this.currentIdx % this.colorsHex.length;
    }

    return i;
  }

  /**
   * Will assign a color to an arbitrary key.
   * If the key has been used already, it will
   * use the same color.
   */
  getColorByKey(key: string) {
    const i = this._getColorIndex(key);
    return this.colorsHex[i];
  }

  /**
   * Retrieve the RGB values associated with a key. Adds the key and associates
   * it with a color if the key is not recognized.
   * @return {number[]} An array of three ints [0, 255] representing a color.
   */
  getRgbColorByKey(key: string): [number, number, number] {
    const i = this._getColorIndex(key);
    return this.colorsRgb[i];
  }

  clear() {
    this.cache.clear();
    this.currentIdx = 0;
  }
}

// TS needs the precise return type
function strToRgb(s: string): [number, number, number] {
  if (s.length !== 7) {
    return [0, 0, 0];
  }
  const r = s.slice(1, 3);
  const g = s.slice(3, 5);
  const b = s.slice(5);
  return [Number.parseInt(r, 16), Number.parseInt(g, 16), Number.parseInt(b, 16)];
}

export default new ColorGenerator();
