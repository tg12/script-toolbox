#!/usr/bin/env bash
#
# Author: James Sawyer
# Disclaimer: Provided as-is. No warranty whatsoever. No liability for any damages. Use at your own risk.
#
set -euo pipefail

# Discover where Proxmox wants QEMU configs
PVE_QEMU_DIR=$(readlink -f /etc/pve/qemu-server)
PVE_NODE=$(basename "$(dirname "$PVE_QEMU_DIR")")
mkdir -p "$PVE_QEMU_DIR"

echo "Scanning running QEMU processes for VMIDs & names…"
declare -A vm_names

for pf in /var/run/qemu-server/*.pid; do
  base=$(basename "$pf")
  if [[ $base =~ ^([0-9]+)\.pid$ ]]; then
    vmid=${BASH_REMATCH[1]}
    pid=$(<"$pf")
    [[ -d /proc/$pid ]] || continue
    cmd=$(tr '\0' ' ' </proc/$pid/cmdline)

    if [[ $cmd =~ guest=([^,[:space:]]+) ]]; then
      name=${BASH_REMATCH[1]}
    elif [[ $cmd =~ -name[[:space:]]+guest=([^,[:space:]]+) ]]; then
      name=${BASH_REMATCH[1]}
    elif [[ $cmd =~ -name[[:space:]]+([^,[:space:],]+) ]]; then
      name=${BASH_REMATCH[1]}
    else
      name="vm${vmid}"
    fi

    vm_names[$vmid]=$name
    echo "   • Found VM $vmid → name='$name'"
  fi
done

echo
echo "Recreating .conf files in $PVE_QEMU_DIR…"
for vmid in "${!vm_names[@]}"; do
  name=${vm_names[$vmid]}
  out="$PVE_QEMU_DIR/${vmid}.conf"
  printf " - VM %-4s: writing name='%s'\n" "$vmid" "$name"
  {
    echo "vmid: $vmid"
    echo "name: $name"
  } > "$out"
done

echo
echo "Restarting pve-cluster…"
systemctl restart pve-cluster

echo
echo "Done! Verify with:"
echo "  pvesh get /nodes/$PVE_NODE/qemu"
echo "Then refresh the Proxmox GUI—your VMs should now appear by name."
