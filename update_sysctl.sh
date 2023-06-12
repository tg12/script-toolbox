#!/bin/bash

# Path to the tweaks file
tweaks_file="tweaks.sysctl"

# Check if dry-run flag is invoked
dry_run=false
if [ "$1" == "--dry-run" ]; then
    dry_run=true
fi

# Read the tweaks from the file
while IFS= read -r line; do
  # Skip empty lines and comments starting with #
  if [[ -n "$line" && "${line:0:1}" != "#" ]]; then
    # Split the line into parameter and value
    parameter=$(echo "$line" | cut -d '=' -f 1)
    value=$(echo "$line" | cut -d '=' -f 2)

    # Trim leading/trailing whitespaces
    parameter=$(echo "$parameter" | awk '{$1=$1};1')
    value=$(echo "$value" | awk '{$1=$1};1')

    # Get the current value for the parameter
    old_value=$(sysctl -n "$parameter")

    # Display the dry run information
    if [ "$dry_run" = true ]; then
        echo "Dry run: $parameter = $value (Old: $old_value)"
    else
        # Apply the tweak
        if sysctl -w "$parameter=$value" > /dev/null 2>&1; then
            echo "Applied tweak: $parameter = $value (Old: $old_value)"
            # Create or update the sysctl configuration file
            echo "$parameter = $value" | sudo tee -a /etc/sysctl.conf > /dev/null
        else
            echo "Failed to apply tweak: $parameter = $value"
        fi
    fi
  fi
done < "$tweaks_file"

if [ "$dry_run" = false ]; then
    # Load new settings
    if sudo sysctl -p; then
        echo "Tweaks have been applied and will be persistent across reboots."
    else
        echo "Failed to load new settings. Please check the tweaks file and try again."
    fi
fi
