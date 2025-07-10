const { toString } = Object.prototype;

/**
 * Determine if a value is an Array
 * @param {Object} val The value to test
 * @returns {boolean} True if value is an Array, otherwise false
 */
function isArray(val: object): boolean {
  return toString.call(val) === '[object Array]';
}

/**
 * Determine if a value is an Object
 * @param {Object} val The value to test
 * @returns {boolean} True if value is an Object, otherwise false
 */
function isObject(val: any): boolean {
  return val !== null && typeof val === 'object';
}

/**
 * Determine if a value is a Date
 * @param {Object} val The value to test
 * @returns {boolean} True if value is a Date, otherwise false
 */
function isDate(val: any): boolean {
  return toString.call(val) === '[object Date]';
}

/**
 * Iterate over an Array or an Object invoking a function for each item.
 *
 * If `obj` is an Array callback will be called passing
 * the value, index, and complete array for each item.
 *
 * If 'obj' is an Object callback will be called passing
 * the value, key, and complete object for each property.
 * @param {Object|Array} obj The object to iterate
 * @param {Function} fn The callback to invoke for each item
 */
function forEach(obj: any, fn: any) {
  // Don't bother if no value provided
  if (obj === null || typeof obj === 'undefined') {
    return;
  }

  // Force an array if not already something iterable
  if (typeof obj !== 'object') {
    /* eslint no-param-reassign:0 */
    obj = [obj];
  }

  if (isArray(obj)) {
    // Iterate over array values
    for (let i = 0, l = obj.length; i < l; i++) {
      /* eslint-disable */
      fn.call(null, obj[i], i, obj);
    }
  } else {
    // Iterate over object keys
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        fn.call(null, obj[key], key, obj);
      }
    }
  }
}

function encode(val: string) {
  return encodeURIComponent(val)
    .replace(/%40/gi, '@')
    .replace(/%3A/gi, ':')
    .replace(/%24/g, '$')
    .replace(/%2C/gi, ',')
    .replace(/%20/g, '+');
}
export const paramsSerializer = (params: any) => {
  const parts: string[] = [];

  forEach(params, function serialize(val: any, key: any) {
    if (val === null || typeof val === 'undefined') {
      return;
    }

    if (isArray(val)) {
      key = key + '[]';
    } else {
      val = [val];
    }

    forEach(val, function parseValue(v: any) {
      if (isDate(v)) {
        v = v.toISOString();
      } else if (isObject(v)) {
        v = JSON.stringify(v);
      }
      parts.push(encode(key) + '=' + encode(v));
    });
  });

  return parts.join('&');
};
