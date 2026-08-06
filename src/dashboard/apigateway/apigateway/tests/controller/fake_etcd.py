#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
from typing import Dict, List, Optional, Sequence, Tuple

from etcd3.client import Transactions
from etcd3.etcdrpc import Compare
from etcd3.transactions import Delete, Mod, Put
from etcd3.utils import prefix_range_end, to_bytes

DUPLICATE_KEY_MESSAGE = "etcdserver: duplicate key given in txn request"


class FakeEtcdTransactionError(Exception):
    """模拟真实 etcd 对单个 txn 请求返回的 INVALID_ARGUMENT 错误"""


class FakeResponseHeader:
    def __init__(self, revision: int):
        self.revision = revision


class FakeKVMetadata:
    def __init__(self, key: bytes, mod_revision: int, response_header: FakeResponseHeader):
        self.key = key
        self.mod_revision = mod_revision
        self.response_header = response_header


class FakeEtcdClient:
    """维护真实 keyspace 的内存 etcd 客户端，复用 etcd3 的事务操作对象

    与真实 etcd 一致地校验单个事务：PUT key 不能落在同一事务的 DELETE range 内，同一个 key
    也不能被 PUT 两次，否则返回 duplicate key 错误。也按 etcd 规则评估 compare 条件。
    """

    def __init__(self, keyspace: Optional[Dict[str, str]] = None):
        self.transactions = Transactions()
        self.transaction_ops: List[List[object]] = []
        self.transaction_compares: List[List[object]] = []
        self._revision = 0
        self._keyspace: Dict[bytes, Tuple[bytes, int]] = {}
        for key, value in (keyspace or {}).items():
            self.put(key, value)

    @property
    def keys(self) -> List[str]:
        return [key.decode() for key in sorted(self._keyspace)]

    def get(self, key) -> Tuple[Optional[bytes], Optional[FakeKVMetadata]]:
        key_bytes = to_bytes(key)
        item = self._keyspace.get(key_bytes)
        if item is None:
            return None, None

        value, mod_revision = item
        return value, FakeKVMetadata(key_bytes, mod_revision, FakeResponseHeader(self._revision))

    def get_prefix(self, key_prefix, keys_only: bool = False):
        prefix = to_bytes(key_prefix)
        prefix_end = prefix_range_end(prefix)
        header = FakeResponseHeader(self._revision)
        return [
            (b"" if keys_only else value, FakeKVMetadata(key, mod_revision, header))
            for key, (value, mod_revision) in sorted(self._keyspace.items())
            if in_range(key, prefix, prefix_end)
        ]

    def put(self, key, value) -> None:
        self._revision += 1
        self._keyspace[to_bytes(key)] = (to_bytes(value), self._revision)

    def delete(self, key) -> bool:
        key_bytes = to_bytes(key)
        if key_bytes not in self._keyspace:
            return False
        self._revision += 1
        del self._keyspace[key_bytes]
        return True

    def delete_prefix(self, key_prefix) -> None:
        prefix = to_bytes(key_prefix)
        self._delete_range(prefix, prefix_range_end(prefix))

    def transaction(self, compare, success=None, failure=None) -> Tuple[bool, List[object]]:
        compares = list(compare or [])
        self.transaction_compares.append(compares)
        if not self._evaluate_compares(compares):
            return False, []

        ops = list(success or [])
        self.transaction_ops.append(ops)
        self.check_intervals(ops)

        for op in ops:
            if isinstance(op, Delete):
                self._apply_delete(op)
            elif isinstance(op, Put):
                self.put(op.key, op.value)
            else:
                raise FakeEtcdTransactionError(f"unsupported transaction operation: {type(op).__name__}")

        return True, []

    @staticmethod
    def check_intervals(ops: Sequence[object]) -> None:
        delete_ranges = get_delete_ranges(ops)
        put_keys = set()
        for op in ops:
            if not isinstance(op, Put):
                continue

            key = to_bytes(op.key)
            if key in put_keys or any(in_range(key, start, end) for start, end in delete_ranges):
                raise FakeEtcdTransactionError(DUPLICATE_KEY_MESSAGE)

            put_keys.add(key)

    def _evaluate_compares(self, compares: Sequence[object]) -> bool:
        for compare in compares:
            if not isinstance(compare, Mod):
                raise FakeEtcdTransactionError(f"unsupported compare: {type(compare).__name__}")
            if not self._evaluate_mod_compare(compare):
                return False
        return True

    def _evaluate_mod_compare(self, compare: Mod) -> bool:
        start = to_bytes(compare.key)
        end = to_bytes(compare.range_end) if compare.range_end is not None else None
        expected = int(compare.value)
        for key, (_, mod_revision) in self._keyspace.items():
            if not in_range(key, start, end):
                continue
            if compare.op == Compare.EQUAL and mod_revision != expected:
                return False
            if compare.op == Compare.NOT_EQUAL and mod_revision == expected:
                return False
            if compare.op == Compare.LESS and not mod_revision < expected:
                return False
            if compare.op == Compare.GREATER and not mod_revision > expected:
                return False
        return True

    def _apply_delete(self, op: Delete) -> None:
        key = to_bytes(op.key)
        if op.range_end is None:
            self.delete(key)
            return

        self._delete_range(key, to_bytes(op.range_end))

    def _delete_range(self, start: bytes, end: bytes) -> None:
        keys = [key for key in self._keyspace if in_range(key, start, end)]
        if not keys:
            return
        self._revision += 1
        for key in keys:
            del self._keyspace[key]


def get_delete_ranges(ops: Sequence[object]) -> List[Tuple[bytes, Optional[bytes]]]:
    return [
        (to_bytes(op.key), to_bytes(op.range_end) if op.range_end is not None else None)
        for op in ops
        if isinstance(op, Delete)
    ]


def get_put_keys(ops: Sequence[object]) -> List[bytes]:
    return [to_bytes(op.key) for op in ops if isinstance(op, Put)]


def in_range(key: bytes, start: bytes, end: Optional[bytes]) -> bool:
    if end is None:
        return key == start

    # etcd 约定：range_end 为单个 \x00 时表示 key 之后的所有 key
    if end == b"\x00":
        return key >= start

    return start <= key < end


def ranges_overlap(first: Tuple[bytes, Optional[bytes]], second: Tuple[bytes, Optional[bytes]]) -> bool:
    first_start, first_end = first
    second_start, second_end = second
    if first_end is None or second_end is None:
        return in_range(first_start, second_start, second_end) or in_range(second_start, first_start, first_end)

    return first_start < second_end and second_start < first_end
