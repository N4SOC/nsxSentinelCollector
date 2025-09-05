FROM docker.elastic.co/logstash/logstash:8.15.3

ARG environment_name
ARG workspaceID
ARG workspaceKey
ARG table

USER root

# RUN dnf -y update

RUN logstash-plugin install microsoft-logstash-output-azure-loganalytics

RUN rm -f /usr/share/logstash/pipeline/*
RUN rm -f /usr/share/logstash/config/*

COPY pipeline/ /usr/share/logstash/pipeline/
COPY config/ /usr/share/logstash/config/