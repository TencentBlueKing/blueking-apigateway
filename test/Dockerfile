FROM node:21.7.3

RUN npm install -g @usebruno/cli

RUN which bru

WORKDIR /app

ADD bin /app/bin
ADD cases /app/cases

RUN ls -alrt /app/

CMD ["bash", "/app/bin/start.sh"]
