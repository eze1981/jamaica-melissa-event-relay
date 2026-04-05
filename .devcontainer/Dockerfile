FROM mcr.microsoft.com/devcontainers/python:3.12

# Install base dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    && rm -rf /var/lib/apt/lists/*
