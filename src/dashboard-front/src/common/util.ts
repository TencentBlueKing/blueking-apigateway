import dayjs from 'dayjs';
import { Message } from 'bkui-vue';
// import JSZip from 'jszip';
// import FileSaver from 'file-saver';
// import axios from 'axios';
import i18n from '@/language/i18n';
import jsYaml from 'js-yaml';

const { t } = i18n.global;


// 获取 cookie object
export function getCookies(strCookie = document.cookie): any {
  if (!strCookie) {
    return {};
  }
  const arrCookie = strCookie.split('; ');// 分割
  const cookiesObj = {};
  arrCookie.forEach((cookieStr) => {
    const arr = cookieStr.split('=');
    const [key, value] = arr;
    if (key) {
      cookiesObj[key] = value;
    }
  });
  return cookiesObj;
}

/**
 * 检查是不是 object 类型
 * @param item
 * @returns {boolean}
 */
export function isObject(item: any) {
  return Object.prototype.toString.apply(item) === '[object Object]';
}


/**
 * 深度合并多个对象
 * @param objectArray 待合并列表
 * @returns {object} 合并后的对象
 */
export function deepMerge(...objectArray: object[]) {
  return objectArray.reduce((acc, obj) => {
    Object.keys(obj || {}).forEach((key) => {
      const pVal = acc[key];
      const oVal = obj[key];

      if (isObject(pVal) && isObject(oVal)) {
        acc[key] = deepMerge(pVal, oVal);
      } else {
        acc[key] = oVal;
      }
    });

    return acc;
  }, {});
}

/**
 * 时间格式化
 * @param val 待格式化时间
 * @param format 格式
 * @returns 格式化后的时间
 */
export function timeFormatter(val: string, format = 'YYYY-MM-DD HH:mm:ss') {
  return val ? dayjs(val).format(format) : '--';
}

/**
 * 对象转为 url query 字符串
 *
 * @param {*} param 要转的参数
 * @param {string} key key
 *
 * @return {string} url query 字符串
 */
export function json2Query(param: any, key?: any) {
  const mappingOperator = '=';
  const separator = '&';
  let paramStr = '';
  if (
    param instanceof String
      || typeof param === 'string'
      || param instanceof Number
      || typeof param === 'number'
      || param instanceof Boolean
      || typeof param === 'boolean'
  ) {
    // @ts-ignore
    paramStr += separator + key + mappingOperator + encodeURIComponent(param);
  } else {
    if (param) {
      Object.keys(param).forEach((p) => {
        const value = param[p];
        const k = key === null || key === '' || key === undefined
          ? p
          : key + (param instanceof Array ? `[${p}]` : `.${p}`);
        paramStr += separator + json2Query(value, k);
      });
    }
  }
  return paramStr.substr(1);
}

/**
 * 复制
 * @param {Object} value 复制内容
 */
export function copy(value: string) {
  if (!value) {
    Message({ theme: 'warning', message: t('暂无可复制数据'), delay: 2000, dismissable: false });
    return;
  }
  const el = document.createElement('textarea');
  el.value = value;
  el.setAttribute('readonly', '');
  el.style.position = 'absolute';
  el.style.left = '-9999px';
  document.body.appendChild(el);
  const selected = document.getSelection().rangeCount > 0 ? document.getSelection().getRangeAt(0) : false;
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
  if (selected) {
    document.getSelection().removeAllRanges();
    document.getSelection().addRange(selected);
  }
  Message({ theme: 'success', width: 'auto', message: t('复制成功'), delay: 2000, dismissable: false });
}

/**
 * 导出下载公共方法
 * @param {Object} res 接口返回值
 */
export const blobDownLoad = async (res: any) => {
  if (res.ok) {
    const blob: any = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    const url = URL.createObjectURL(blob);
    const elment = document.createElement('a');
    // eslint-disable-next-line prefer-destructuring
    elment.download = (disposition.match(/filename="(\S+?)"/) || [])[1];
    elment.href = url;
    elment.click();
    URL.revokeObjectURL(blob);
    return Promise.resolve({ success: true });
  }

  const errorInfo = await res.json();
  return Promise.reject(errorInfo);
};


/**
 * 实现类似CSS filter:hue-rotate色调旋转生成颜色
 */
export function getColorHue(rgb, degree) {
  // exepcts a string and returns an object
  function rgbToHSL(rgb) {
    // strip the leading # if it's there
    rgb = rgb.replace(/^\s*#|\s*$/g, '');

    // convert 3 char codes --> 6, e.g. `E0F` --> `EE00FF`
    if (rgb.length === 3) {
      rgb = rgb.replace(/(.)/g, '$1$1');
    }

    const r = parseInt(rgb.substr(0, 2), 16) / 255;
    const g = parseInt(rgb.substr(2, 2), 16) / 255;
    const b = parseInt(rgb.substr(4, 2), 16) / 255;
    const cMax = Math.max(r, g, b);
    const cMin = Math.min(r, g, b);
    const delta = cMax - cMin;
    const l = (cMax + cMin) / 2;
    let h = 0;
    let s = 0;

    if (delta === 0) {
      h = 0;
    } else if (cMax === r) {
      h = 60 * (((g - b) / delta) % 6);
    } else if (cMax === g) {
      h = 60 * (((b - r) / delta) + 2);
    } else {
      h = 60 * (((r - g) / delta) + 4);
    }

    if (delta === 0) {
      s = 0;
    } else {
      s = (delta / (1 - Math.abs(2 * l - 1)));
    }

    return {
      h,
      s,
      l,
    };
  }

  // expects an object and returns a string
  function hslToRGB(hsl: any) {
    const { h } = hsl;
    const { s } = hsl;
    const { l } = hsl;
    const c = (1 - Math.abs(2 * l - 1)) * s;
    const x = c * (1 - (Math.abs((h / 60) % 2) - 1));
    const m = l - c / 2;
    let r; let g; let b;

    if (h < 60) {
      r = c;
      g = x;
      b = 0;
    } else if (h < 120) {
      r = x;
      g = c;
      b = 0;
    } else if (h < 180) {
      r = 0;
      g = c;
      b = x;
    } else if (h < 240) {
      r = 0;
      g = x;
      b = c;
    } else if (h < 300) {
      r = x;
      g = 0;
      b = c;
    } else {
      r = c;
      g = 0;
      b = x;
    }

    r = normalizeRgbValue(r, m);
    g = normalizeRgbValue(g, m);
    b = normalizeRgbValue(b, m);

    return rgbToHex(r, g, b);
  }

  function normalizeRgbValue(color, m) {
    color = Math.floor((color + m) * 255);
    if (color < 0) {
      color = 0;
    }
    return color;
  }

  function rgbToHex(r, g, b) {
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  }

  const hsl = rgbToHSL(rgb);
  hsl.h += degree;
  if (hsl.h > 360) {
    hsl.h -= 360;
  } else if (hsl.h < 0) {
    hsl.h += 360;
  }
  return hslToRGB(hsl);
}

/**
 * 将文件 url 格式转换为 Bolb 类型格式 或者 arraybuffer 格式
 * @param fileUrl 文件完整地址
 */
// const getFileData  = (fileUrl: string) => {
//   return new Promise((resolve, reject) => {
//     fetch(fileUrl, {
//       method: 'GET',
//     }).then((res: any) => {
//       if (res.ok) {
//         resolve(res.blob());
//       } else {
//         reject(res);
//       }
//     }).
//       catch((e: Error) => {
//         reject(e);
//       });
//   });
// };

/**
 * 根据文件url批量压缩下载成zip包
 * @param fileList 文件列表[{fileUrl: 'xxxxx', fileName: '文件1'}, {fileUrl: 'xxxxx', fileName: '文件2'}]
 * @param zipName 压缩包名如 测试.zip
 */
// export const zipDownload = async (fileList: any[], zipName: string) => {
//   const zip = new JSZip();
//   const promises: any = [];
//   fileList.forEach((item: any) => {
//     const promise = getFileData(item.fileUrl).then((res: any) => {
//       zip.file(String(item.fileName), res, { binary: true });
//     });
//     promises.push(promise);
//   });

//   Promise.all(promises).then(() => {
//     // 生成zip文件
//     zip.generateAsync({
//       type: 'blob',
//       compression: 'DEFLATE',  // STORE: 默认不压缩， DEFLATE：需要压缩
//       compressionOptions: {
//         level: 9,         // 压缩等级 1~9   1 压缩速度最快， 9 最优压缩方式
//       },
//     }).then((res: any) => {
//       FileSaver.saveAs(res, zipName);
//     });
//   });
// };

/**
 * 对元素为对象的数组进行简单排序
 */
export function sortByKey(list: any = [], key: string | number) {
  let sortKeys = list.map((item: any) => {
    return item[key].toLowerCase();
  });
  sortKeys = [...new Set(sortKeys)]; // 去除重复key
  sortKeys.sort(); // 排序

  const results: any[] = [];
  sortKeys.forEach((sortItem: any) => {
    list.forEach((item: any) => {
      if (item[key].toLowerCase() === sortItem) {
        results.push(item);
      }
    });
  });
  return results;
}
/**
 * 读取文件内容
 * @param {Object} file file文件对象
 */
export const getStrFromFile = (file: any) => {
  let resolveFn: Function = () => {};
  const PromiseFunc = new Promise(resolve => resolveFn = resolve);
  // ▼ new 一个 FileReader
  // ▼ 然后监听 onload 事件，从中取得文本内容
  const oReader = Object.assign(new FileReader(), {
    onload(event: any) {
      resolveFn(event.target.result);
    },
  });
  oReader.readAsText(file);
  return PromiseFunc;
};


export const is24HoursAgo = (dateString: string) => {
  // 将日期字符串转换为 Date 对象
  const date: any = new Date(dateString);

  // 获取当前时间
  const now: any = new Date();

  // 计算时间差，单位为毫秒
  const diff = now - date;

  // 将时间差转换为小时
  const hours = diff / (1000 * 60 * 60);

  // 判断时间差是否大于等于24小时
  return hours >= 24;
};
/**
 * 手动清空table过滤条件
 *
 * @param refInstance {Object} 指定的 table
 *
 */
export function clearFilter(refInstance: any) {
  if (refInstance?.filterPanels) {
    const { filterPanels } = refInstance;
    for (const key in filterPanels) {
      filterPanels[key].handleReset();
    }
  }
}

/**
 * 判断表格是否存在筛选条件
 *
 * @param filters {Object} 对应筛选条件
 *
 */
export function isTableFilter(filters: any) {
  let isFilter = false;
  if (Object.keys(filters)?.length) {
    for (const key in filters) {
      if (filters[key].length) {
        isFilter = true;
        break;
      }
    }
  }
  return isFilter;
}

/**
 * 根据请求方法返回tab的对应主题
 * @param methods 请求方法
 * @returns tag的主题
 */
export const getMethodsTheme = (methods: string) => {
  if (!methods) return 'success';

  let theme = '';
  switch (methods.toLocaleLowerCase()) {
    case 'get':
      theme = 'success';
      break;
    case 'patch':
    case 'post':
      theme = 'info';
      break;
    case 'put':
      theme = 'warning';
      break;
    case 'delete':
      theme = 'danger';
      break;
  };
  return theme;
};

// 环境状态
export const getStatus = (stageData: any) => {
  if (stageData?.status === 1) {
    return stageData?.release?.status;
  }
  // stageData.status = 0
  if (stageData?.release?.status === 'unreleased') { // 未发布
    return 'unreleased';
  }
  return 'delist';
};

export const json2yaml = (jsonStr: string) => {
  try {
    return {
      data: jsYaml.dump(JSON.parse(jsonStr)),
      error: false,
    };
  } catch (err) {
    return {
      data: '',
      error: true,
    };
  }
};

export const yaml2json = (yamlStr: string) => {
  yamlStr = yamlStr.replace(/\|-(?!\s*\n)/g, '|-\n');
  try {
    return {
      data: jsYaml.load(yamlStr),
      error: false,
    };
  } catch (err) {
    return {
      data: '',
      error: true,
    };
  }
};
