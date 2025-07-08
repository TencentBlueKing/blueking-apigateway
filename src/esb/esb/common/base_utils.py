# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

import datetime
import decimal
import hashlib
import json
import random
import re
from builtins import range, str

import yaml
from django.utils.encoding import force_bytes, force_text, smart_bytes, smart_text
from past.builtins import basestring

from common.errors import error_codes
from common.log import logger

EMPTY_VALUES = (None, "", [], (), {})  # type: ignore


class CustomJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    And process the smart place name object
    """

    date_format = "%Y-%m-%d"
    time_format = "%H:%M:%S"

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%s %s" % (self.date_format, self.time_format))
        elif isinstance(o, datetime.date):
            return o.strftime(self.date_format)
        elif isinstance(o, datetime.time):
            return o.strftime(self.time_format)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        else:
            return super(CustomJSONEncoder, self).default(o)


def jsonize(d):
    return json.dumps(d, cls=CustomJSONEncoder, ensure_ascii=False)


def str_bool(value):
    """
    Convert string to boolean.

        >>> str_bool("0")
        False
        >>> str_bool("1")
        True
        >>> str_bool("true")
        True
        >>> str_bool("false")
        False
    """
    if isinstance(value, basestring):
        value = value.strip()
        if force_text(value.lower()) in ("0", "false"):
            return False
    return bool(value)


class FancyDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)


def smart_lower(value):
    """
    >>> smart_lower('RequestFriendHandler')
    'request_friend_handler'
    """
    result = [value[0].lower()]
    for c in value[1:]:
        if c >= "A" and c <= "Z":
            result.append("_")
        result.append(c.lower())
    return "".join(result)


def smart_upper(value):
    """
    >>> smart_upper('request_friend_handler')
    'requestFriendHandler'
    """
    value_list = value.split("_")
    return "".join(word.capitalize() if i != 0 else word for i, word in enumerate(value_list))


def smart_upper_v2(value):
    """
    >>> smart_upper('request_friend_handler')
    'RequestFriendHandler'
    """
    value_list = value.split("_")
    return "".join(word.capitalize() for _, word in enumerate(value_list))


def smart_str(s, encoding="utf-8"):
    """
    转换一个字符串或者unicode为指定的编码
    """
    return smart_bytes(s, encoding="utf-8", errors="ignore")


def smart_unicode(s, encoding="utf-8"):
    """
    转换一个字符串或者unicode为unicode
    """
    return smart_text(s, encoding="utf-8", errors="ignore")


def smart_unicode_v2(s, encoding=None):
    def get_chardet_module():
        """获取系统中可用的chardet模块"""
        try:
            from requests.compat import chardet
        except ImportError:
            try:
                import chardet
            except ImportError:
                return
        return chardet

    def guess_encoding(s):
        chardet = get_chardet_module()
        if chardet:
            encoding = chardet.detect(s)["encoding"]
        return encoding or "utf-8"

    if isinstance(s, str):
        return s
    if encoding is None:
        encoding = guess_encoding(s)
    try:
        s = str(s, encoding, errors="replace")
    except (LookupError, TypeError):
        s = str(s, errors="replace")
    return s


def unique(obj):
    """
    Unique with order
    """
    temp = set()
    return [x for x in obj if x not in temp and not temp.add(x)]


def get_not_empty_value(kwargs):
    """
    获取非空数据，去除数据为空字段
    """
    data = {}
    for k, v in list(kwargs.items()):
        if v not in (None, "", [], {}):
            data[k] = v
    return data


UNICODE_ASCII_CHARACTER_SET = "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789"


def generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET):
    """
    Generates a non-guessable OAuth token
    """
    rand = random.SystemRandom()
    return "".join(rand.choice(chars) for x in range(length))


def get_client_ip(request):
    """
    获取远程访问主机的IP地址
    """
    client_ip = request.META.get("HTTP_X_FORWARDED_FOR")
    if not client_ip:
        client_ip = request.META.get("REMOTE_ADDR", "")
    try:
        client_ip = re.findall(r"[\d.]{7,15}", client_ip)
    except Exception:
        logger.exception("request: %s" % request)
        client_ip = ""
    else:
        client_ip = ";".join(client_ip)
    return client_ip


def get_client_real_ip(request):
    real_ip = request.META.get("HTTP_X_REAL_IP")
    if real_ip:
        return real_ip
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.rsplit(",", 1)[-1].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_request_params(request):
    # "GET"方法
    if request.method == "GET":
        return dict(list(request.GET.items()))

    # "POST"方法
    if request.body and request.body.strip().startswith(force_bytes("{")):
        try:
            return json.loads(request.body)
        except Exception:
            logger.exception("request.body should be a json: %s", request.body)
            raise error_codes.COMMON_ERROR.format_prompt(
                "Request JSON string is wrong in format, which cannot be analyzed.", replace=True
            )

    return dict(list(request.POST.items()))


def datetime_format(dt):
    date_format = "%Y-%m-%d"
    time_format = "%H:%M:%S"

    if isinstance(dt, (int, float)):
        dt = datetime.datetime.utcfromtimestamp(dt)

    if isinstance(dt, datetime.datetime):
        return dt.strftime("%s %s" % (date_format, time_format))
    elif isinstance(dt, datetime.date):
        return dt.strftime(date_format)


def get_md5(src):
    m = hashlib.md5()
    m.update(force_bytes(src))
    return m.hexdigest()


def load_yaml(path):
    with open(path, "r") as fp:
        return yaml.safe_load(fp)


def yaml_dumps(data):
    return yaml.safe_dump(data, allow_unicode=True)


def read_file(path):
    with open(path, "r") as fp:
        return fp.read()


def html_escape(html, is_json=False):
    """
    Replace special characters "&", "<" and ">" to HTML-safe sequences.
    If the optional flag quote is true, the quotation mark character (")
    is also translated.
    rewrite the cgi method
    @param html: html代码
    @param is_json: 是否为json串（True/False） ，默认为False
    """
    # &转换
    if not is_json:
        html = html.replace("&", "&amp;")  # Must be done first!
    # <>转换
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")
    # 单双引号转换
    if not is_json:
        html = html.replace('"', "&quot;")
        html = html.replace("'", "&#39;")
    return html


def get_first_not_empty_value(data, keys, default=None):
    """
    获取 keys 中第一个数据非空的字段数据
    """
    for key in keys:
        if data.get(key) not in EMPTY_VALUES:
            return data[key]

    return default


def urljoin(base_url, path):
    if not base_url:
        return path

    if not path:
        return base_url

    return "%s/%s" % (base_url.rstrip("/"), path.lstrip("/"))
