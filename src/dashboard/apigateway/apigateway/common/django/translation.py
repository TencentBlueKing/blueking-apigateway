# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import translation as django_translation


def get_current_language_code():
    language_code = django_translation.get_language()
    if not language_code:
        return settings.LANGUAGE_CODE

    try:
        language_info = django_translation.get_language_info(language_code)
    except KeyError:
        return settings.LANGUAGE_CODE

    return language_info["code"]
