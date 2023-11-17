import dayjs from 'dayjs';
import { Message } from 'bkui-vue';
// import JSZip from 'jszip';
// import FileSaver from 'file-saver';
// import axios from 'axios';

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
  Message({ theme: 'primary', message: '复制成功', delay: 2000, dismissable: false });
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
