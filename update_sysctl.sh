#!/bin/bash

# Path to the tweaks file
tweaks_file="tweaks.sysctl"

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
    echo "Dry run: $parameter = $value (Old: $old_value)"

    # Apply the tweak only if not in dry run mode
    if [ "$1" != "--dry-run" ]; then
      # Apply the tweak
      sysctl -w "$parameter=$value"

      # Check if the tweak was applied successfully
      if [ $? -eq 0 ]; then
        echo "Applied tweak: $parameter = $value (Old: $old_value)"
      else
        echo "Failed to apply tweak: $parameter = $value"
      fi

      # Create or update the custom configuration file
      echo "$parameter = $value" | sudo tee -a /etc/sysctl.d/99-custom-tweaks.conf > /dev/null
    fi
  fi
done < "$tweaks_file"

# Notify the user if changes will be made persistent
if [ -f "/etc/sysctl.d/99-custom-tweaks.conf" ]; then
  echo "Tweaks have been applied and will be persistent across reboots."
else
  echo "Tweaks could not be applied. Please check the tweaks file and try again."
fi

