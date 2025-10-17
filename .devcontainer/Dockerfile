FROM python:3.14.0-slim-bookworm

USER root

ENV http_proxy=http://proxy.police.tas.gov.au:8080 \
    https_proxy=http://proxy.police.tas.gov.au:8080 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1

COPY kbr5.conf /etc/krb5.conf
COPY config/fancygit/app_config /tmp
COPY requirements.txt /tmp

# Install dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git wget build-essential fontconfig make htop \
    krb5-user libkrb5-dev unixodbc unixodbc-dev \
    gnupg2 ca-certificates openssl corkscrew odbcinst \
    openssh-client libmemcached-dev jq sqlite3 redis-tools sudo && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install latest stable Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x -o /tmp/nodesource_setup.sh && \
    bash /tmp/nodesource_setup.sh && \
    apt-get update && \
    apt-get install -y nodejs && \
    npm install -g @anthropic-ai/claude-code && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/nodesource_setup.sh

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create vscode user
RUN useradd -m -s /bin/bash vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER vscode
WORKDIR /workspace