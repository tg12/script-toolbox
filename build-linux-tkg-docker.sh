#!/usr/bin/env bash
set -euo pipefail

# Configuration
IMAGE_NAME="tkg-builder"
CONTAINER_OUT_DIR="$(pwd)/tkg-out"
EXT_CFG_HOST="$(pwd)/linux-tkg.cfg"
DOCKERFILE_PATH="$(pwd)/Dockerfile"

# 1. Generate external linux-tkg config
cat > "$EXT_CFG_HOST" <<EOF
# External linux-tkg configuration overrides:
_configfile="config.x86_64"
_cpusched="muqss"
_processor_opt="-march=native"
_noccache="false"
_force_all_threads="true"
EOF

# 2. Write Dockerfile
cat > "$DOCKERFILE_PATH" <<EOF
FROM gcc:latest
# Install linux-tkg build dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \\
    apt-get install -y --no-install-recommends \\
      bc bison build-essential ccache cpio flex git kmod \\
      libelf-dev libncurses5-dev libssl-dev lz4 qtbase5-dev \\
      rsync schedtool wget zstd && rm -rf /var/lib/apt/lists/*
# Clone linux-tkg
RUN git clone --depth 1 https://github.com/Frogging-Family/linux-tkg.git /linux-tkg
# Add external config
COPY linux-tkg.cfg /root/.config/frogminer/linux-tkg.cfg
ENV _EXT_CONFIG_PATH=/root/.config/frogminer/linux-tkg.cfg
WORKDIR /linux-tkg
# Build & install
RUN yes | ./install.sh install
# Copy resulting .deb packages out
RUN mkdir /out && cp /usr/src/linux-tkg-*/build/*.deb /out/
EOF

# 3. Build the Docker image
docker build -t "$IMAGE_NAME" .

# 4. Ensure host output directory exists
mkdir -p "$CONTAINER_OUT_DIR"

# 5. Run container and extract artifacts
docker run --rm \
  -v "$CONTAINER_OUT_DIR":/out \
  "$IMAGE_NAME"

echo "Built linux-tkg Debian packages are in: $CONTAINER_OUT_DIR"
