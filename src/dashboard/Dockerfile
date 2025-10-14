ARG IMAGE=hub.bktencent.com/blueking/python
ARG TAG=3.11.13-ts4
FROM ${IMAGE}:${TAG}


RUN dnf install -y vim mysql curl zip unzip git

# install kona-jdk maven
RUN curl -s "https://get.sdkman.io?ci=true" | bash
RUN bash -c "source /root/.sdkman/bin/sdkman-init.sh && sdk install java 11.0.27-kona && rm -rf /root/.sdkman/archives/* && rm -rf /root/.sdkman/tmp/* && dnf -y install maven"

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

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

WORKDIR /app
ADD build/uv.lock  /app/uv.lock
ADD build/pyproject.toml /app/pyproject.toml
# for etcd3 lib installed from git
RUN export UV_PROJECT_ENVIRONMENT=/usr/local/ && uv sync --locked && uv clean


ADD build /app

RUN dnf clean all

CMD ["bash", "/app/bin/start.sh"]
