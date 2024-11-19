ARG IMAGE=python
ARG TAG=3.10.15-slim-bullseye
FROM ${IMAGE}:${TAG}

RUN apt-get update && apt-get install -y libssl-dev libffi-dev \
    build-essential libc6-dev libjpeg-dev zlib1g-dev vim procps default-mysql-client curl zip unzip

# install kona-jdk maven
RUN curl -s "https://get.sdkman.io" | bash 
RUN bash -c "source /root/.sdkman/bin/sdkman-init.sh && sdk install java 11.0.19-kona && apt-get -y install maven"

ARG PYPI="https://pypi.org/simple/"
RUN pip config set global.index-url "${PYPI}"

WORKDIR /app
ADD build/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# install mvn dep
RUN mvn dependency:get -Dartifact=com.squareup.okhttp3:okhttp:4.12.0 && \
    mvn dependency:get -Dartifact=com.fasterxml.jackson.core:jackson-databind:2.13.4.1 && \
    mvn dependency:get -Dartifact=org.apache.maven.plugins:maven-compiler-plugin:3.8.1 && \
    mvn dependency:get -Dartifact=org.apache.maven.plugins:maven-jar-plugin:3.1.0

ADD build /app


CMD ["bash", "/app/bin/start.sh"]
