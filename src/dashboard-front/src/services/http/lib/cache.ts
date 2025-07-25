import { isNumber } from 'lodash-es';

export type CacheValue = Promise<any>;
export type CacheExpire = number | boolean;

export interface ICache {
  set: (name: string, value: CacheValue, expire: CacheExpire) => boolean
  get: (name: string) => any
  has: (name: string) => boolean
  delete: (name: string) => boolean
  clear: () => boolean
}

export default class Cache implements ICache {
  cacheMap: Map<string, CacheValue>;
  cacheExpireMap: Map<string, number>;
  constructor() {
    this.cacheMap = new Map();
    this.cacheExpireMap = new Map();
  }

  set(name: string, value: CacheValue, expire: CacheExpire) {
    if (isNumber(expire)) {
      this.cacheExpireMap.set(name, Date.now() + expire);
    }
    if (!this.cacheMap.has(name)) {
      this.cacheMap.set(name, value);
    }
    return true;
  }

  get(name: string) {
    if (this.cacheMap.has(name)) {
      return this.cacheMap.get(name);
    }
    return false;
  }

  has(name: string) {
    if (!this.cacheMap.has(name)) {
      return false;
    }
    const expire = this.cacheExpireMap.get(name);
    if (!expire) {
      return true;
    }
    if (Date.now() > expire) {
      this.cacheMap.delete(name);
      this.cacheExpireMap.delete(name);
      return false;
    }
    return true;
  }

  delete(name: string) {
    if (this.cacheMap.has(name)) {
      return this.cacheMap.delete(name);
    }
    return true;
  }

  clear() {
    this.cacheMap.clear();
    return this.cacheMap.size < 1;
  }
}
