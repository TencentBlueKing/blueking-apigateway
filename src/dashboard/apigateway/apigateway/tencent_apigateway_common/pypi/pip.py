from urllib.parse import urlparse

from packaging.version import parse as parse_version


class PipHelper:
    def __init__(self, extra_index_url: str = ""):
        self.extra_index_url = extra_index_url

    def install_command(self, package: str, version: str = ""):
        commands = ["pip", "install"]

        if self.extra_index_url:
            commands.append(f"--extra-index-url={self.extra_index_url}")

            urlinfo = urlparse(self.extra_index_url)
            if urlinfo.scheme == "http":
                commands.append(f"--trusted-host={urlinfo.hostname}")

        if version:
            commands.append(f"{package}=={parse_version(version)}")
        else:
            commands.append(f"{package}")

        return " ".join(commands)
