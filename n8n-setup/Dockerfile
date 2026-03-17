# Custom n8n image: Latest n8n (hardened) + Python3 + openpyxl
# Multi-stage: copy entire Python install from standard Alpine

# Stage 1: Build Python + packages in standard Alpine
FROM python:3.12-alpine AS python-build
RUN pip install --no-cache-dir openpyxl

# Stage 2: Latest n8n + inject Python
FROM docker.n8n.io/n8nio/n8n:latest

USER root

# Copy the entire Python installation from stage 1
COPY --from=python-build /usr/local /usr/local
COPY --from=python-build /usr/lib /usr/lib
COPY --from=python-build /lib /lib

# Create symlink
RUN ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3 && \
    ln -sf /usr/local/bin/python3.12 /usr/local/bin/python
