**Disclaimer:**  
These scripts are provided *as-is* and carry **no warranty**. Use at your own risk—always test in a non-production environment first. They directly manipulate your Proxmox cluster database (`pmxcfs`) and overwrite configuration files. **Make backups** of `/etc/pve` and your VMs/CTs before running them. I’m not responsible for any data loss or downtime they may cause.

---

**Background**  
I recently resurrected an old Proxmox node in my lab that had failed months ago—one of those maintenance tasks I’d been avoiding forever. Unfortunately, when I re-joined it to my two-node cluster, none of my running VMs or containers showed up in the GUI anymore, even though I could still SSH into them and verify they were running. The underlying disk images and LXC rootfses were all intact; it was just the cluster metadata that had vanished.

---

**What Happened**  
- **Cluster database lost**  
  My `/etc/pve/nodes/.../{lxc,qemu-server}` directories were empty because pmxcfs snapshots had never been enabled.  
- **Containers still running**  
  LXC stores live configs under `/var/lib/lxc/<vmid>/config`, so the containers continued to run—but Proxmox had no metadata to show them.  
- **VMs still running**  
  QEMU kept its processes alive with pidfiles in `/var/run/qemu-server`, but without the old `/etc/pve/nodes/.../qemu-server/*.conf`, the GUI had nothing to list.

---

**Solution Overview**  
1. **For LXC**: Scan `/var/lib/lxc/<vmid>/config` (and fall back to each container’s `/etc/hostname`), extract hostname, memory, arch, rootfs, net0, and write a new `<vmid>.conf` into `/etc/pve/nodes/<node>/lxc/`.  
2. **For QEMU/KVM**: Scan running `qemu-system-*` processes via their pidfiles, parse out each VM’s ID and name from the command-line, then write new `<vmid>.conf` files into `/etc/pve/nodes/<node>/qemu-server/`.  
3. **Reload**: Restart `pve-cluster` so pmxcfs picks up the rebuilt configs, and voilà—everything reappears in the web UI.

---

## Recovery Script: LXC Containers

```bash
#!/usr/bin/env bash
#
# recover-lxc-configs.sh
# Rebuild Proxmox LXC container definitions from live /var/lib/lxc data.
#
# DISCLAIMER: Overwrites /etc/pve cluster metadata. Backup first!
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
    # Pull settings from live config (gracefully handle missing fields)
    hostname=$(grep -E '^lxc\.uts\.name'   "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true
    arch=$(grep -E '^lxc\.arch'            "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true

    mem_bytes=$(grep -E '^lxc\.cgroup\.memory\.limit_in_bytes' "$LIVE_CFG" 2>/dev/null \
                 | cut -d= -f2) || true
    (( memory_mb = mem_bytes / 1024 / 1024 )) 2>/dev/null || true

    rootfs=$(grep -m1 -E '^lxc\.rootfs\.path' "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true

    link=$(grep -m1 '^lxc.net.0.link'   "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true
    hw=$(grep -m1 '^lxc.net.0.hwaddr'   "$LIVE_CFG" 2>/dev/null | cut -d= -f2) || true
    [[ -n $link ]] && net0="bridge=${link},hwaddr=${hw}"

    status="full"
  else
    # Fallback: recover only the hostname from the container’s /etc/hostname
    if [[ -f "$CTPATH/rootfs/etc/hostname" ]]; then
      hostname=$(<"$CTPATH/rootfs/etc/hostname")
      status="name-only"
    else
      status="skipped"
    fi
  fi

  # Write the new .conf if we recovered a hostname
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

echo; echo "Restarting pve-cluster…"
systemctl restart pve-cluster

echo; echo "Done. Verify with:"
echo "  pvesh get /nodes/$PVE_NODE/lxc"
echo "Then refresh the Proxmox GUI—your CTs should now appear by name."
```

---

## Recovery Script: QEMU/KVM VMs

```bash
#!/usr/bin/env bash
#
# recover-qemu-configs.sh
# Rebuild Proxmox QEMU VM definitions from running qemu-system processes.
#
# DISCLAIMER: Overwrites /etc/pve cluster metadata. Backup first!
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

    # Extract the guest name via multiple patterns
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

echo; echo "Recreating .conf files in $PVE_QEMU_DIR…"
for vmid in "${!vm_names[@]}"; do
  name=${vm_names[$vmid]}
  out="$PVE_QEMU_DIR/${vmid}.conf"
  printf " - VM %-4s: writing name='%s'
" "$vmid" "$name"
  {
    echo "vmid: $vmid"
    echo "name: $name"
  } > "$out"
done

echo; echo "Restarting pve-cluster…"
systemctl restart pve-cluster

echo; echo "Done! Verify with:"
echo "  pvesh get /nodes/$PVE_NODE/qemu"
echo "Then refresh the Proxmox GUI—your VMs should now appear by name."
```

---

**How to Use**  
1. Copy each script to your Proxmox node (e.g. under `/root/`), then:  
   ```bash
   chmod +x /root/recover-lxc-configs.sh /root/recover-qemu-configs.sh
   ```  
2. **Backup** `/etc/pve` (and optionally `/var/lib/pve-cluster/config.db`) before proceeding.  
3. Run them:  
   ```bash
   /root/recover-lxc-configs.sh  
   /root/recover-qemu-configs.sh  
   ```  
4. Confirm recovery via:  
   ```bash
   pvesh get /nodes/$(hostname)/lxc  
   pvesh get /nodes/$(hostname)/qemu  
   ```  
5. Refresh your Proxmox web UI—your containers and VMs should now reappear, correctly named.

---

**Final Thoughts**  
These scripts saved me hours of manual work when my lab cluster’s metadata vanished. If you ever face a similar “everything’s running but nothing shows up in the GUI” scenario, give them a try—just remember the **backup first** disclaimer!
