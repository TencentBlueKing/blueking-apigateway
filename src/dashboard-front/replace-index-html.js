#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

function showHelp() {
  console.log(`
用法: node copy-html.js <source-html-file>

参数:
  source-html-file    要复制的 HTML 文件路径

选项:
  -h, --help         显示帮助信息
    `);
}

// 获取命令行参数
const args = process.argv.slice(2);

// 检查帮助参数
if (args.includes('-h') || args.includes('--help') || args.length === 0) {
  showHelp();
  process.exit(0);
}

const sourceFilePath = args[0];
const targetFilePath = path.join(process.cwd(), 'index.html');

// 检查源文件是否存在
if (!fs.existsSync(sourceFilePath)) {
  console.error(`❌ 错误: 文件 '${sourceFilePath}' 不存在`);
  process.exit(1);
}

// 检查源文件是否为 HTML 文件
const ext = path.extname(sourceFilePath).toLowerCase();
if (ext !== '.html' && ext !== '.htm') {
  console.warn('⚠️  警告: 源文件扩展名不是 .html 或 .htm');
}

try {
  // 读取源文件内容
  const content = fs.readFileSync(sourceFilePath, 'utf8');

  // 备份原 index.html（如果存在）
  if (fs.existsSync(targetFilePath)) {
    const backupPath = targetFilePath + '.backup';
    fs.copyFileSync(targetFilePath, backupPath);
    console.log(`💾 已备份原 index.html 到 ${backupPath}`);
  }

  // 写入到目标文件（覆盖原有内容）
  fs.writeFileSync(targetFilePath, content, 'utf8');

  console.log(`✅ 成功: 已将 '${sourceFilePath}' 的内容复制到 '${targetFilePath}'`);
  console.log(`📄 源文件大小: ${content.length} 字符`);
}
catch (error) {
  console.error('❌ 错误:', error.message);
  process.exit(1);
}
