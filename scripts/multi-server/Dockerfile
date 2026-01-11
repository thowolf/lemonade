# Build Lemonade Server from source

FROM mcr.microsoft.com/devcontainers/cpp:1-debian-12 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake git ninja-build pkg-config libssl-dev libcurl4-openssl-dev \
    ca-certificates python3 python3-pip wget curl git && rm -rf /var/lib/apt/lists/*

WORKDIR /work
# Copy entire repository into build context
COPY . /work

# Build the C++ server
WORKDIR /work/src/cpp
# Install newer CMake (required: >= 3.28)
RUN CMAKE_VERSION=3.28.4 \
    && wget -q https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz \
    && tar -xzf cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz --strip-components=1 -C /usr/local \
    && rm cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz

RUN mkdir -p build && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=Release -G Ninja \
    && cmake --build . --config Release -j$(nproc)

# Optional: build ryzenai-server dependency if present
RUN if [ -d "/work/src/ryzenai-server" ]; then \
      cd /work/src/ryzenai-server && mkdir -p build && cd build && cmake .. -G Ninja && cmake --build . --config Release -j$(nproc) || true; \
    fi

# Final runtime image
FROM debian:12-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 libcurl4 ca-certificates curl procps && rm -rf /var/lib/apt/lists/*

# Copy binaries
# Built server binaries on Linux are placed in src/cpp/build/
COPY --from=builder /work/src/cpp/build/lemonade-router /usr/local/bin/lemonade-router
COPY --from=builder /work/src/cpp/build/lemonade-server /usr/local/bin/lemonade-server
# Copy resource files generated at build-time (server_models.json, etc.)
COPY --from=builder /work/src/cpp/build/resources /usr/local/bin/resources
RUN chmod +x /usr/local/bin/lemonade-router /usr/local/bin/lemonade-server || true

# Create folders for model cache and logs
RUN mkdir -p /root/.cache/huggingface /var/log/lemonade
VOLUME ["/root/.cache/huggingface", "/var/log/lemonade"]

EXPOSE 8000-8010

# Default command (overridden by docker-compose service command)
CMD ["/usr/local/bin/lemonade-router", "serve", "--host", "0.0.0.0"]
