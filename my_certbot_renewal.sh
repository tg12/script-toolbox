#!/bin/bash

# Define variables
INTERFACE="eth0"
PORT="80"
WWW_ROOT="/var/www/html"
HTACCESS_FILE="${WWW_ROOT}/.htaccess"
TEMP_HTACCESS_FILE="${HTACCESS_FILE}.backup"

# Insert iptables rule to allow traffic on port 80
echo "Adding iptables rule to allow traffic on port ${PORT} through ${INTERFACE}..."
sudo iptables -I INPUT 1 -i ${INTERFACE} -p tcp --dport ${PORT} -j ACCEPT

# Check if .htaccess file exists and rename it
if [ -f "${HTACCESS_FILE}" ]; then
    echo "Renaming .htaccess to ${TEMP_HTACCESS_FILE}..."
    sudo mv "${HTACCESS_FILE}" "${TEMP_HTACCESS_FILE}"
else
    echo ".htaccess file not found in ${WWW_ROOT}."
fi

# Run certbot renew
echo "Running certbot renew..."
sudo certbot renew

# Cleanup: Restore the .htaccess file and remove the iptables rule

# Remove the iptables rule
echo "Removing iptables rule..."
sudo iptables -D INPUT -i ${INTERFACE} -p tcp --dport ${PORT} -j ACCEPT

# Restore the .htaccess file
if [ -f "${TEMP_HTACCESS_FILE}" ]; then
    echo "Restoring original .htaccess file..."
    sudo mv "${TEMP_HTACCESS_FILE}" "${HTACCESS_FILE}"
else
    echo "Temporary .htaccess file not found. Nothing to restore."
fi

echo "Cleanup complete."
