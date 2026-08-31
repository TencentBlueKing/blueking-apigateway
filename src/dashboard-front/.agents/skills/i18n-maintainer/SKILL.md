---
name: i18n-maintainer
description: 当提交的文件中的国际化内容发生变化时，检查词条包是否有对应的词条
---

# I18n Maintainer

## Overview

当提交的文件中的国际化内容发生变化时，检查词条包是否有对应的词条

## 流程

1. 检查提交的 .vue, .ts, .tsx, .js, .jsx 文件，其他文件忽略
2. 检查这些文件中是否有改动包含 t('') 或 $t('') 的内容
3. 检查引号中的内容是否在 `src/dashboard-front/src/locales/cn.json` 和 `src/dashboard-front/src/locales/en.json` 有对应修改，如果没有则修改这两个文件，保持所有国际化内容都能在这两个 json 中找到

## 注意

1. 要保证 `src/dashboard-front/src/locales/cn.json` 和 `src/dashboard-front/src/locales/en.json` 是合法的 JSON 文件，不要用 JSON 不支持的语法
2. 要把 cn.json 和 en.json 的同一个词条放在同一行里，即保持行号相同
