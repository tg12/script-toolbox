#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# build-linux-tkg-docker.sh
#   1. Generates Dockerfile (no install step baked in)
#   2. Builds image
#   3. Launches container interactively and runs install.sh with prompts
# -----------------------------------------------------------------------------

# Configuration
IMAGE_NAME="tkg-builder"
OUT_DIR="$(pwd)/tkg-out"
EXT_CFG_HOST="$(pwd)/linux-tkg.cfg"
DOCKERFILE_HOST="$(pwd)/Dockerfile"

# 1) Write external linux-tkg config
cat > "$EXT_CFG_HOST" <<EOF
# linux-tkg external overrides:
_configfile="config.x86_64"
_cpusched="muqss"
_processor_opt="-march=native"
_noccache="false"
_force_all_threads="true"
EOF

echo "✔ Wrote external config to $EXT_CFG_HOST"

# 2) Generate Dockerfile (without RUN install.sh)
cat > "$DOCKERFILE_HOST" <<'EOF'
FROM gcc:latest

# Install build dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
      bc bison build-essential ccache cpio flex git kmod \
      libelf-dev libncurses5-dev libssl-dev lz4 qtbase5-dev \
      rsync schedtool wget zstd && \
    rm -rf /var/lib/apt/lists/*

# Clone linux-tkg (shallow)
RUN git clone --depth 1 https://github.com/Frogging-Family/linux-tkg.git /linux-tkg

# Copy in your overrides and set env var
COPY linux-tkg.cfg /root/.config/frogminer/linux-tkg.cfg
ENV _EXT_CONFIG_PATH=/root/.config/frogminer/linux-tkg.cfg

WORKDIR /linux-tkg

# Leave install.sh for runtime
EOF

echo "✔ Wrote Dockerfile to $DOCKERFILE_HOST"

# 3) Build the Docker image
docker build -t "$IMAGE_NAME" .
echo "✔ Docker image built: $IMAGE_NAME"

# 4) Ensure output directory exists
mkdir -p "$OUT_DIR"
echo "✔ Host output dir ready: $OUT_DIR"

# 5) Run the container interactively and invoke the installer
echo
echo "▶ Launching container; you’ll see linux-tkg’s prompts now…"
echo
docker run --rm -it \
  -v "$OUT_DIR":/out \
  $IMAGE_NAME \
  bash -c 'cd /linux-tkg && ./install.sh install && cp /usr/src/linux-tkg-*/build/*.deb /out/'

echo
echo "Done! Your .deb packages are in: $OUT_DIR"
