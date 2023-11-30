# -*- coding: utf-8 -*-
from collections.abc import Mapping
from typing import Dict, Optional

from django.db import models
from django.utils.translation import get_language
from rest_framework.fields import CharField


class I18nProperty:
    """
    I18nProperty proxied the access to the real field which according to the language
    """

    def __init__(self, field_template: models.Field, default_language: Optional[str] = None, allow_none: bool = False):
        self._field_template = field_template
        self._default_language = default_language
        self._translated_fields: Dict[Optional[str], models.Field] = {}
        self._allow_none = allow_none

    def _get_attrname_by_language(self):
        language = get_language()
        if language not in self._translated_fields:
            return None

        field = self._translated_fields[language]

        return field.get_attname()

    def _get_default_attrname(self):
        field = self._translated_fields[self._default_language]
        return field.get_attname()

    def __get__(self, obj, obj_type=None):
        if obj is None:
            return self

        attrname = self._get_attrname_by_language()
        # 找不到对应语言的属性，直接返回默认属性
        if not attrname:
            return getattr(obj, self._get_default_attrname())

        value = getattr(obj, attrname, None)
        if value is not None or self._allow_none:
            return value

        # 如果不允许空，则在默认语言的值为 None 时，返回默认字段值
        return getattr(obj, self._get_default_attrname())

    def __set__(self, obj, value):
        # 直接赋值给默认语言字段
        setattr(obj, self._get_default_attrname(), value)

    def field(self, language, **override_kwargs):
        """
        Return a model field which is use to store the translated value for specific language
        """

        if language and self._field_template.verbose_name:
            override_kwargs.setdefault("verbose_name", f"{self._field_template.verbose_name}({language})")
        _, _, args, kwargs = self._field_template.deconstruct()
        field = self._field_template.__class__(*args, **{**kwargs, **override_kwargs})
        self._translated_fields[language] = field
        return field

    def default_field(self, **override_kwargs):
        """
        Return a model field which is use to store the default value
        """
        return self.field(self._default_language, **override_kwargs)


class SerializerTranslatedField(CharField):
    def __init__(
        self,
        translated_fields: Optional[Dict[str, str]] = None,
        default_field: Optional[str] = None,
        allow_none: bool = False,
        **kwargs,
    ):
        self.translated_fields = translated_fields
        self.default_field = default_field
        self.allow_none = allow_none
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        if not self.default_field:
            self.default_field = field_name

        super().bind(field_name, parent)

    def _item_getter(self, x, key, default=None):
        return x.get(key, default)

    def get_attribute(self, instance):
        getter = self._item_getter if isinstance(instance, Mapping) else getattr

        if self.translated_fields:
            # 尝试根据语言获取属性值
            language = get_language()
            field = self.translated_fields.get(language, self.default_field)
            value = getter(instance, field, None)
            # 当具体的语言属性值为 None 时，倾向于认为当前对象没有提供多语言方案，除非明确允许值为空
            if value is not None or self.allow_none:
                return value

        # 返回默认属性值
        return getter(instance, self.default_field)
