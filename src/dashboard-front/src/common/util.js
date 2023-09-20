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
/**
 * @file 通用方法
 * @author
 */

import jsYaml from 'js-yaml'
/**
 * 函数柯里化
 *
 * @example
 *     function add (a, b) {return a + b}
 *     curry(add)(1)(2)
 *
 * @param {Function} fn 要柯里化的函数
 *
 * @return {Function} 柯里化后的函数
 */
export function curry (fn) {
  const judge = (...args) => {
    return args.length === fn.length
      ? fn(...args)
      : arg => judge(...args, arg)
  }
  return judge
}

/**
 * 判断是否是对象
 *
 * @param {Object} obj 待判断的
 *
 * @return {boolean} 判断结果
 */
export function isObject (obj) {
  return obj !== null && typeof obj === 'object'
}

/**
 * 规范化参数
 *
 * @param {Object|string} type vuex type
 * @param {Object} payload vuex payload
 * @param {Object} options vuex options
 *
 * @return {Object} 规范化后的参数
 */
export function unifyObjectStyle (type, payload, options) {
  if (isObject(type) && type.type) {
    options = payload
    payload = type
    type = type.type
  }

  if (NODE_ENV !== 'production') {
    if (typeof type !== 'string') {
      console.warn(`expects string as the type, but found ${typeof type}.`)
    }
  }

  return { type, payload, options }
}

/**
 * 以 baseColor 为基础生成随机颜色
 *
 * @param {string} baseColor 基础颜色
 * @param {number} count 随机颜色个数
 *
 * @return {Array} 颜色数组
 */
export function randomColor (baseColor, count) {
  const segments = baseColor.match(/[\da-z]{2}/g)
  // 转换成 rgb 数字
  for (let i = 0; i < segments.length; i++) {
    segments[i] = parseInt(segments[i], 16)
  }
  const ret = []
  // 生成 count 组颜色，色差 20 * Math.random
  for (let i = 0; i < count; i++) {
    ret[i] = '#'
            + Math.floor(segments[0] + (Math.random() < 0.5 ? -1 : 1) * Math.random() * 20).toString(16)
            + Math.floor(segments[1] + (Math.random() < 0.5 ? -1 : 1) * Math.random() * 20).toString(16)
            + Math.floor(segments[2] + (Math.random() < 0.5 ? -1 : 1) * Math.random() * 20).toString(16)
  }
  return ret
}

/**
 * min max 之间的随机整数
 *
 * @param {number} min 最小值
 * @param {number} max 最大值
 *
 * @return {number} 随机数
 */
export function randomInt (min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min)
}

/**
 * 异常处理
 *
 * @param {Object} err 错误对象
 * @param {Object} ctx 上下文对象，这里主要指当前的 Vue 组件
 */
export function catchErrorHandler (err, ctx) {
  if (!err.data && !err.response) {
    return false
  }
  const data = err.data || err.response.data
  if (data) {
    if (!data.code || data.code === 404) {
      ctx.exceptionCode = {
        code: '404',
        msg: '当前访问的页面不存在'
      }
    } else if (data.code === 403) {
      ctx.exceptionCode = {
        code: '403',
        msg: 'Sorry，您的权限不足!'
      }
    } else if (data.code !== 40101) {
      console.error(err)
      ctx.bkMessageInstance = ctx.$bkMessage({
        theme: 'error',
        message: data.message || err.message || err.data.msg || err.statusText
      })
    }
  } else {
    console.error(err)
    ctx.bkMessageInstance = ctx.$bkMessage({
      theme: 'error',
      message: err.message || err.data.msg || err.statusText
    })
  }
}

/**
 * 获取字符串长度，中文算两个，英文算一个
 *
 * @param {string} str 字符串
 *
 * @return {number} 结果
 */
export function getStringLen (str) {
  let len = 0
  for (let i = 0; i < str.length; i++) {
    if (str.charCodeAt(i) > 127 || str.charCodeAt(i) === 94) {
      len += 2
    } else {
      len++
    }
  }
  return len
}

/**
 * 转义特殊字符
 *
 * @param {string} str 待转义字符串
 *
 * @return {string} 结果
 */
export const escape = str => String(str).replace(/([.*+?^=!:${}()|[\]\/\\])/g, '\\$1')

/**
 * 对象转为 url query 字符串
 *
 * @param {*} param 要转的参数
 * @param {string} key key
 *
 * @return {string} url query 字符串
 */
export function json2Query (param, key) {
  const mappingOperator = '='
  const separator = '&'
  let paramStr = ''

  if (param instanceof String || typeof param === 'string'
        || param instanceof Number || typeof param === 'number'
        || param instanceof Boolean || typeof param === 'boolean'
  ) {
    paramStr += separator + key + mappingOperator + encodeURIComponent(param)
  } else {
    Object.keys(param).forEach(p => {
      const value = param[p]
      const k = (key === null || key === '' || key === undefined)
        ? p
        : key + (param instanceof Array ? '[' + p + ']' : '.' + p)
      paramStr += separator + json2Query(value, k)
    })
  }
  return paramStr.substr(1)
}

/**
 * 字符串转换为驼峰写法
 *
 * @param {string} str 待转换字符串
 *
 * @return {string} 转换后字符串
 */
export function camelize (str) {
  return str.replace(/-(\w)/g, (strMatch, p1) => p1.toUpperCase())
}

/**
 * 获取元素的样式
 *
 * @param {Object} elem dom 元素
 * @param {string} prop 样式属性
 *
 * @return {string} 样式值
 */
export function getStyle (elem, prop) {
  if (!elem || !prop) {
    return false
  }

  // 先获取是否有内联样式
  let value = elem.style[camelize(prop)]

  if (!value) {
    // 获取的所有计算样式
    let css = ''
    if (document.defaultView && document.defaultView.getComputedStyle) {
      css = document.defaultView.getComputedStyle(elem, null)
      value = css ? css.getPropertyValue(prop) : null
    }
  }

  return String(value)
}

/**
 *  获取元素相对于页面的高度
 *
 *  @param {Object} node 指定的 DOM 元素
 */
export function getActualTop (node) {
  let actualTop = node.offsetTop
  let current = node.offsetParent

  while (current !== null) {
    actualTop += current.offsetTop
    current = current.offsetParent
  }

  return actualTop
}

/**
 *  获取元素相对于页面左侧的宽度
 *
 *  @param {Object} node 指定的 DOM 元素
 */
export function getActualLeft (node) {
  let actualLeft = node.offsetLeft
  let current = node.offsetParent

  while (current !== null) {
    actualLeft += current.offsetLeft
    current = current.offsetParent
  }

  return actualLeft
}

/**
 * document 总高度
 *
 * @return {number} 总高度
 */
export function getScrollHeight () {
  let scrollHeight = 0
  let bodyScrollHeight = 0
  let documentScrollHeight = 0

  if (document.body) {
    bodyScrollHeight = document.body.scrollHeight
  }

  if (document.documentElement) {
    documentScrollHeight = document.documentElement.scrollHeight
  }

  scrollHeight = (bodyScrollHeight - documentScrollHeight > 0) ? bodyScrollHeight : documentScrollHeight

  return scrollHeight
}

/**
 * 滚动条在 y 轴上的滚动距离
 *
 * @return {number} y 轴上的滚动距离
 */
export function getScrollTop () {
  let scrollTop = 0
  let bodyScrollTop = 0
  let documentScrollTop = 0

  if (document.body) {
    bodyScrollTop = document.body.scrollTop
  }

  if (document.documentElement) {
    documentScrollTop = document.documentElement.scrollTop
  }

  scrollTop = (bodyScrollTop - documentScrollTop > 0) ? bodyScrollTop : documentScrollTop

  return scrollTop
}

/**
 * 浏览器视口的高度
 *
 * @return {number} 浏览器视口的高度
 */
export function getWindowHeight () {
  const windowHeight = document.compatMode === 'CSS1Compat'
    ? document.documentElement.clientHeight
    : document.body.clientHeight

  return windowHeight
}

/**
 * 简单的 loadScript
 *
 * @param {string} url js 地址
 * @param {Function} callback 回调函数
 */
export function loadScript (url, callback) {
  const script = document.createElement('script')
  script.async = true
  script.src = url

  script.onerror = () => {
    callback(new Error('Failed to load: ' + url))
  }

  script.onload = () => {
    callback()
  }

  document.getElementsByTagName('head')[0].appendChild(script)
}

/**
 * 对元素为对象的数组进行简单排序
 */
export function sortByKey (list = [], key) {
  let sortKeys = list.map(item => {
    return item[key].toLowerCase()
  })
  sortKeys = [...new Set(sortKeys)] // 去除重复key
  sortKeys.sort() // 排序

  const results = []
  sortKeys.forEach(sortItem => {
    list.forEach(item => {
      if (item[key].toLowerCase() === sortItem) {
        results.push(item)
      }
    })
  })
  return results
}

/**
 * 实现类似CSS filter:hue-rotate色调旋转生成颜色
 */
export function getColorHue (rgb, degree) {
  // exepcts a string and returns an object
  function rgbToHSL (rgb) {
    // strip the leading # if it's there
    rgb = rgb.replace(/^\s*#|\s*$/g, '')

    // convert 3 char codes --> 6, e.g. `E0F` --> `EE00FF`
    if (rgb.length === 3) {
      rgb = rgb.replace(/(.)/g, '$1$1')
    }

    const r = parseInt(rgb.substr(0, 2), 16) / 255
    const g = parseInt(rgb.substr(2, 2), 16) / 255
    const b = parseInt(rgb.substr(4, 2), 16) / 255
    const cMax = Math.max(r, g, b)
    const cMin = Math.min(r, g, b)
    const delta = cMax - cMin
    const l = (cMax + cMin) / 2
    let h = 0
    let s = 0

    if (delta === 0) {
      h = 0
    } else if (cMax === r) {
      h = 60 * (((g - b) / delta) % 6)
    } else if (cMax === g) {
      h = 60 * (((b - r) / delta) + 2)
    } else {
      h = 60 * (((r - g) / delta) + 4)
    }

    if (delta === 0) {
      s = 0
    } else {
      s = (delta / (1 - Math.abs(2 * l - 1)))
    }

    return {
      h: h,
      s: s,
      l: l
    }
  }

  // expects an object and returns a string
  function hslToRGB (hsl) {
    const h = hsl.h
    const s = hsl.s
    const l = hsl.l
    const c = (1 - Math.abs(2 * l - 1)) * s
    const x = c * (1 - Math.abs((h / 60) % 2 - 1))
    const m = l - c / 2
    let r; let g; let b

    if (h < 60) {
      r = c
      g = x
      b = 0
    } else if (h < 120) {
      r = x
      g = c
      b = 0
    } else if (h < 180) {
      r = 0
      g = c
      b = x
    } else if (h < 240) {
      r = 0
      g = x
      b = c
    } else if (h < 300) {
      r = x
      g = 0
      b = c
    } else {
      r = c
      g = 0
      b = x
    }

    r = normalizeRgbValue(r, m)
    g = normalizeRgbValue(g, m)
    b = normalizeRgbValue(b, m)

    return rgbToHex(r, g, b)
  }

  function normalizeRgbValue (color, m) {
    color = Math.floor((color + m) * 255)
    if (color < 0) {
      color = 0
    }
    return color
  }

  function rgbToHex (r, g, b) {
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
  }

  const hsl = rgbToHSL(rgb)
  hsl.h += degree
  if (hsl.h > 360) {
    hsl.h -= 360
  } else if (hsl.h < 0) {
    hsl.h += 360
  }
  return hslToRGB(hsl)
}

export function json2yaml (jsonStr) {
  try {
    return {
      data: jsYaml.dump(JSON.parse(jsonStr)),
      error: false
    }
  } catch (err) {
    return {
      data: '',
      error: true
    }
  }
}

/**
 * 手动清空table过滤条件
 *
 * @param refInstance {Object} 指定的 table
 *
 */
export function clearFilter (refInstance) {
  if (refInstance.filterPanels) {
    const filterPanels = refInstance.filterPanels
    for (const key in filterPanels) {
      filterPanels[key].handleReset()
    }
  }
}

/**
 * 判断表格是否存在筛选条件
 *
 * @param filters {Object} 对应筛选条件
 *
 */
export function isTableFilter (filters) {
  let isFilter = false
  if (Object.keys(filters).length) {
    for (const key in filters) {
      if (filters[key].length) {
        isFilter = true
        break
      }
    }
  }
  return isFilter
}

/**
 *  设置表头tips
 *
 * @param refInstance {h, { column }} 渲染函数
 *
 */
export function renderHeader (h, { column }) {
  return h('p', { class: 'table-header-tips-cls', directives: [{ name: 'bk-overflow-tips' }] }, [column.label])
}

/**
 *  jsonp请求
 *
 * @param {url} str 请求地址
 * @param {params} str 请求参数
 * @param {callback} str 回调名
 *
 */
export function jsonpRequest (url, params, callbackName) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    if (callbackName) {
      callbackName = callbackName + Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1)
    }
    Object.assign(params, callbackName ? { callback: callbackName } : {})
    const arr = Object.keys(params).map(key => `${key}=${params[key]}`)
    script.src = `${url}?${arr.join('&')}`
    document.body.appendChild(script)
    window[callbackName] = (data) => {
      resolve(data)
    }
  })
}
