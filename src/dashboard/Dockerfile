ARG IMAGE=python
ARG TAG=3.11.13-slim-bullseye
FROM ${IMAGE}:${TAG}

# RUN sed -i "s/http/https/g" /etc/apt/sources.list

# replace the source
RUN echo 'deb https://mirrors.cloud.tencent.com/debian/ bullseye main contrib non-free\n\
deb-src https://mirrors.cloud.tencent.com/debian/ bullseye main contrib non-free\n\
deb https://mirrors.cloud.tencent.com/debian/ bullseye-updates main contrib non-free\n\
deb-src https://mirrors.cloud.tencent.com/debian/ bullseye-updates main contrib non-free\n\
deb https://mirrors.cloud.tencent.com/debian/ bullseye-backports main contrib non-free\n\
deb-src https://mirrors.cloud.tencent.com/debian/ bullseye-backports main contrib non-free\n\
deb https://mirrors.cloud.tencent.com/debian-security/ bullseye-security main contrib non-free\n\
deb-src https://mirrors.cloud.tencent.com/debian-security/ bullseye-security main contrib non-free\n\
' > /etc/apt/sources.list


RUN apt-get update && apt-get install -y --no-install-recommends libssl-dev libffi-dev \
    build-essential libc6-dev libjpeg-dev zlib1g-dev vim procps default-mysql-client curl zip unzip

# install kona-jdk maven
RUN curl -s "https://get.sdkman.io" | bash
RUN bash -c "source /root/.sdkman/bin/sdkman-init.sh && sdk install java 11.0.19-kona && rm -rf /root/.sdkman/archives/* && rm -rf /root/.sdkman/tmp/* && apt-get -y install maven"

# install mvn dep
# replace the source
RUN echo '<settings>\
      <mirrors>\
        <mirror>\
          <id>nexus-tencentyun</id>\
          <mirrorOf>*</mirrorOf>\
          <name>Nexus tencentyun</name>\
          <url>http://mirrors.cloud.tencent.com/nexus/repository/maven-public/</url>\
        </mirror>\
      </mirrors>\
    </settings>' > /usr/share/maven/conf/settings.xml
RUN mvn dependency:get -Dartifact=com.squareup.okhttp3:okhttp:4.12.0 && \
    mvn dependency:get -Dartifact=com.fasterxml.jackson.core:jackson-databind:2.13.4.1 && \
    mvn dependency:get -Dartifact=org.apache.maven.plugins:maven-compiler-plugin:3.8.1 && \
    mvn dependency:get -Dartifact=org.apache.maven.plugins:maven-jar-plugin:3.1.0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ADD build/uv.lock  /app/uv.lock
ADD build/pyproject.toml /app/pyproject.toml
# for etcd3 lib installed from git
RUN apt-get install -y git
RUN export UV_PROJECT_ENVIRONMENT=/usr/local/ && uv sync --locked


ADD build /app

RUN apt-get clean autoclean && apt-get autoremove --yes && rm -rf /var/lib/{apt,dpkg,cache,log}/

CMD ["bash", "/app/bin/start.sh"]
