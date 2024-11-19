import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from apigateway.apps.support.api_sdk.models import Packager

logger = logging.getLogger(__name__)


@dataclass
class SourcePackager(Packager):
    def pack(self, output_dir: str) -> List[str]:
        # 保存当前工作目录
        original_dir = os.getcwd()
        try:
            # 切换到 Maven 项目目录
            os.chdir(output_dir)
            result = subprocess.run(
                [
                    "mvn",
                    "-s",
                    str(Path(original_dir) / "apigateway/apps/support/api_sdk/maven/settings.xml"),
                    "clean",
                    "package",
                ],
                env={"HOME": output_dir},
                cwd=output_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )

            logger.info(result.stdout)
            logger.info(result.stderr)
            # 查找生成的 JAR 文件
            target_dir = os.path.join(output_dir, "target")
            jar_files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(".jar")]

            if not jar_files:
                raise FileNotFoundError("No JAR files found in the target directory.")

            return [os.path.join(output_dir + "/target", os.path.basename(jar_file)) for jar_file in jar_files]

        except subprocess.CalledProcessError as e:
            logger.exception("Command failed with return code %s", e.returncode)
            raise
        finally:
            # 切换回原来的工作目录
            os.chdir(original_dir)
