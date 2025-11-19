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

import { onMounted, onUnmounted, ref } from 'vue';

interface OperationLockOptions {
  lockTime?: number // 锁定时间（秒），默认 10 秒
  storageKey?: string // localStorage 存储的 key
}

export function useOperationLock(options: OperationLockOptions = {}) {
  const {
    lockTime = 10,
    storageKey = 'operation_lock_timestamp',
  } = options;

  const isLocked = ref(false);
  const remainingTime = ref(0);
  let countdownTimer: number | null = null;

  // 检查锁定状态
  const checkLockStatus = () => {
    const lockUntil = localStorage.getItem(storageKey);
    if (lockUntil) {
      const lockTime = parseInt(lockUntil);
      const now = Math.floor(Date.now() / 1000);

      if (lockTime > now) {
        // 仍在锁定期内
        isLocked.value = true;
        startCountdown(lockTime - now);
      }
      else {
        // 锁定已过期
        clearLock();
      }
    }
    else {
      isLocked.value = false;
      remainingTime.value = 0;
    }
  };

  // 开始倒计时
  const startCountdown = (initialRemainingTime: number) => {
    remainingTime.value = initialRemainingTime;

    if (countdownTimer) {
      clearInterval(countdownTimer);
    }

    countdownTimer = setInterval(() => {
      remainingTime.value -= 1;

      if (remainingTime.value <= 0) {
        clearLock();
      }
    }, 1000);
  };

  // 设置锁定
  const setLock = () => {
    const lockUntil = Math.floor(Date.now() / 1000) + lockTime;
    localStorage.setItem(storageKey, lockUntil.toString());
    isLocked.value = true;
    startCountdown(lockTime);
  };

  // 清除锁定
  const clearLock = () => {
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
    localStorage.removeItem(storageKey);
    isLocked.value = false;
    remainingTime.value = 0;
  };

  onMounted(() => {
    checkLockStatus();
  });

  onUnmounted(() => {
    if (countdownTimer) {
      clearInterval(countdownTimer);
    }
  });

  return {
    isLocked,
    remainingTime,
    setLock,
    clearLock,
  };
}
