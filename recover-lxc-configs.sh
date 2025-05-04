#!/usr/bin/env bash
#
# Author: James Sawyer
# Disclaimer: Provided as-is. No warranty whatsoever. No liability for any damages. Use at your own risk.
#
set -euo pipefail

# Discover the real Proxmox node and config path
PVE_LXC_DIR=$(readlink -f /etc/pve/lxc)
PVE_NODE=$(basename "$(dirname "$PVE_LXC_DIR")")
mkdir -p "$PVE_LXC_DIR"

echo "Recovering LXC CT definitions into $PVE_LXC_DIR (node: $PVE_NODE)"
for CTPATH in /var/lib/lxc/[0-9]*; do
  CTID=$(basename "$CTPATH")
  LIVE_CFG="$CTPATH/config"
  OUT_CFG="$PVE_LXC_DIR/${CTID}.conf"

  printf " - CT %-4s: " "$CTID"

  # Initialize
  hostname=""; arch=""; memory_mb=""; rootfs=""; net0=""

  if [[ -f "$LIVE_CFG" ]]; then
    hostname=$(grep -E '^lxc\.uts\.name' "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true
    arch=$(grep -E '^lxc\.arch' "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true

    mem_bytes=$(grep -E '^lxc\.cgroup\.memory\.limit_in_bytes' "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true
    (( memory_mb = mem_bytes / 1024 / 1024 )) 2>/dev/null || true

    rootfs=$(grep -m1 -E '^lxc\.rootfs\.path' "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true

    link=$(grep -m1 '^lxc.net.0.link' "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true
    hw=$(grep -m1 '^lxc.net.0.hwaddr' "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true
    [[ -n $link ]] && net0="bridge=${link},hwaddr=${hw}"

    status="full"
  else
    if [[ -f "$CTPATH/rootfs/etc/hostname" ]]; then
      hostname=$(<"$CTPATH/rootfs/etc/hostname")
      status="name-only"
    else
      status="skipped"
    fi
  fi

  if [[ -n "$hostname" ]]; then
    {
      echo "vmid: $CTID"
      echo "hostname: $hostname"
      [[ -n "$arch"      ]] && echo "arch: $arch"
      [[ -n "$memory_mb" ]] && echo "memory: $memory_mb"
      [[ -n "$rootfs"    ]] && echo "rootfs: $rootfs"
      [[ -n "$net0"      ]] && echo "net0: $net0"
    } > "$OUT_CFG"
  fi

  echo "$status"
done

echo
echo "Restarting pve-cluster…"
systemctl restart pve-cluster

echo
echo "Done. Verify with:"
echo "  pvesh get /nodes/$PVE_NODE/lxc"
echo "Then refresh the Proxmox GUI—your CTs should now appear by name."
