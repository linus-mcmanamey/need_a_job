FROM python:3.14.0-slim-bookworm

USER root

# Removed proxy configuration - only set if needed on your network
# ENV http_proxy=http://proxy.police.tas.gov.au:8080 \
#     https_proxy=http://proxy.police.tas.gov.au:8080

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1

#COPY kbr5.conf /etc/krb5.conf
COPY config/fancygit/app_config /tmp
COPY requirements.txt /tmp

# Install dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git wget build-essential fontconfig make htop \
    krb5-user libkrb5-dev unixodbc unixodbc-dev \
    gnupg2 ca-certificates openssl \
    openssh-client libmemcached-dev jq sudo \
    ffmpeg gcc libasound2-dev libasound2-plugins libportaudio2 portaudio19-dev pulseaudio pulseaudio-utils python3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install latest stable Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x -o /tmp/nodesource_setup.sh && \
    bash /tmp/nodesource_setup.sh && \
    apt-get update && \
    apt-get install -y nodejs && \
    npm install -g @anthropic-ai/claude-code && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/nodesource_setup.sh


# Install uv Python package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/ && \
    mv /root/.local/bin/uvx /usr/local/bin/

RUN uvx voice-mode-install
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

# Create vscode user
RUN useradd -m -s /bin/bash vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER vscode
WORKDIR /workspace