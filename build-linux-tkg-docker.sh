#!/usr/bin/env bash
set -euo pipefail

# Configuration
IMAGE_NAME="tkg-builder"
SCRIPT_DIR="$(pwd)"
OUT_DIR_HOST="$SCRIPT_DIR/tkg-out"
EXT_CFG_HOST="$SCRIPT_DIR/linux-tkg.cfg"
DOCKERFILE_HOST="$SCRIPT_DIR/Dockerfile"

# 1) Write external linux-tkg config
cat > "$EXT_CFG_HOST" <<EOF
# external overrides for linux-tkg:
_configfile="config.x86_64"
_cpusched="muqss"
_processor_opt="-march=native"
_noccache="false"
_force_all_threads="true"
EOF

echo "Wrote external config to $EXT_CFG_HOST"

# 2) Generate Dockerfile
cat > "$DOCKERFILE_HOST" <<'EOF'
FROM gcc:latest

# Install build dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
      bc bison build-essential ccache cpio flex git kmod \
      libelf-dev libncurses5-dev libssl-dev lz4 qtbase5-dev \
      rsync schedtool wget zstd && \
    rm -rf /var/lib/apt/lists/*

# Shallow-clone linux-tkg
RUN git clone --depth 1 https://github.com/Frogging-Family/linux-tkg.git /linux-tkg

# Copy in external config and set env var
COPY linux-tkg.cfg /root/.config/frogminer/linux-tkg.cfg
ENV _EXT_CONFIG_PATH=/root/.config/frogminer/linux-tkg.cfg

WORKDIR /linux-tkg
EOF

echo "Wrote Dockerfile to $DOCKERFILE_HOST"

# 3) Build the Docker image
docker build -t "$IMAGE_NAME" .
echo "Built Docker image: $IMAGE_NAME"

# 4) Prepare host output directory
mkdir -p "$OUT_DIR_HOST"
echo "Host output directory ready: $OUT_DIR_HOST"

# 5) Run the container interactively to build and export linux-src-git
echo "Launching container for interactive build..."
echo "  • In the prompts, choose 'Generic' and answer 'n' when asked to install inside the container."
docker run --rm -it \
  -v "$OUT_DIR_HOST":/out \
  "$IMAGE_NAME" \
  bash -euo pipefail -c '
    cd /linux-tkg
    ./install.sh install
    cp -R linux-src-git /out/linux-src-git
  '

# 6) On host: install the kernel
SRC_DIR="$OUT_DIR_HOST/linux-src-git"
if [ ! -d "$SRC_DIR" ]; then
  echo "Error: build tree not found at $SRC_DIR" >&2
  exit 1
fi

# Detect kernel version
KVER=$(make -s -C "$SRC_DIR" kernelrelease)
echo "Detected kernel version: $KVER"

# Prepare /usr/src and remove old tree
sudo mkdir -p /usr/src
sudo rm -rf "/usr/src/linux-tkg-$KVER"

# Copy build tree into place
echo "Copying build tree to /usr/src/linux-tkg-$KVER"
sudo cp -R "$SRC_DIR" "/usr/src/linux-tkg-$KVER"

# Install modules and kernel
echo "Installing modules and kernel..."
cd "/usr/src/linux-tkg-$KVER"
sudo make modules_install
sudo make install

echo "linux-tkg $KVER has been installed on your host."
