---
name: job-plan-run-and-log
description: 执行作业平台（JOB、jobv3）的作业执行方案并跟踪到结束；失败时拉取失败主机的执行日志，汇总失败步骤、主机和关键报错。会在方案配置的主机上真实执行。用户给出业务和方案、要求现在执行时使用，例如“执行作业方案 1024”“跑一下 JOB 方案”“用作业平台的发布方案把 version 改成 1.2.3 跑一遍，失败的机器把日志给我”。只想查看已经跑过的作业结果时不要使用。
display_name: 执行作业方案并收集日志
display_name_en: Run JOB Plan and Collect Logs
metadata:
  type: "platform"
  version: "1.0.0"
  author: "apigateway"
  datetime: "2026-10-29T10:00:00Z"
  source: "apigateway"
---
