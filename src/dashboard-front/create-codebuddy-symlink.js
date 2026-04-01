import { symlinkDir } from 'symlink-dir';
import fs from 'node:fs';

// 📌 定义源目录和目标软链接路径
const source = './.agents';
const target = './.codebuddy';
const backup = './.codebuddy.backup';

// 🚀 告知用户脚本的目的
console.log('🔗 开始为 .agents 文件夹创建一个名为 .codebuddy 的软链接...\n');

async function main() {
  try {
    // 🔍 检测 .codebuddy 是否已存在
    if (fs.existsSync(target)) {
      console.log(`📂 检测到 ${target} 已存在，正在将其备份为 ${backup} ...`);

      // 🗑️ 如果旧的备份已存在，先删除旧备份
      if (fs.existsSync(backup)) {
        fs.rmSync(backup, {
          recursive: true,
          force: true,
        });
        console.log(`🧹 已清理旧的备份文件 ${backup}`);
      }

      // 📦 将已存在的 .codebuddy 重命名为 .codebuddy.backup
      fs.renameSync(target, backup);
      console.log(`✅ 备份完成：${target} → ${backup}\n`);
    }

    // 🔗 创建软链接
    console.log(`🔨 正在创建软链接：${source} → ${target} ...`);
    await symlinkDir(source, target);
    console.log('🎉 软链接创建成功！');
  }
  catch (err) {
    // ❌ 捕获并告知用户错误信息
    console.error('\n❌ 出错了！创建软链接时发生错误：');
    console.error(`💥 错误详情：${err.message}`);
    process.exit(1);
  }
}

// 🏁 执行主函数
main();
