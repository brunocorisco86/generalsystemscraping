#!/bin/bash

# Script to backup PostgreSQL database and sync to Cloudflare R2
# Based on the strategy outlined in backups_guide.md

# --- Configuration ---
# Load environment variables from .env file
if [ -f .env ]; then
    # shellcheck disable=SC1091 # Source .env file
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found. Please create it with your database credentials and Cloudflare R2 API details."
    exit 1
fi

# Database connection details (should be set in .env)
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}" # PGPASSWORD will be set from this
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Backup settings
BACKUP_DIR="./data/backups"
LOCAL_RETENTION_DAYS=30
R2_REMOTE="r2" # IMPORTANT: Assumes you have configured an rclone remote named 'r2'
                # pointing to your Cloudflare R2 bucket 'piscicultura-backups'.
                # Follow the guide to set up rclone and its remote.
R2_BUCKET="piscicultura-backups" # The target bucket name in Cloudflare R2

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE_SQL="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"
BACKUP_FILE_ZIP="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.zip"

# --- Pre-checks ---
echo "Starting database backup script..."

# Check for required commands
command -v pg_dump >/dev/null 2>&1 || { echo >&2 "Error: pg_dump is not installed. Please install PostgreSQL client tools."; exit 1; }
command -v zip >/dev/null 2>&1 || { echo >&2 "Error: zip is not installed. Please install zip."; exit 1; }
rclone --version >/dev/null 2>&1 || { echo >&2 "Error: rclone is not installed. Please install rclone. You will need to configure it for Cloudflare R2."; exit 1; }

# Check if essential database credentials are set
if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo >&2 "Error: Essential database credentials (DB_NAME, DB_USER, DB_PASSWORD) are not set in .env file. Aborting."
    exit 1
fi

# --- Create Backup Directory ---
echo "Ensuring backup directory exists: '$BACKUP_DIR'"...
mkdir -p "$BACKUP_DIR"
if [ $? -ne 0 ]; then
    echo >&2 "Error: Could not create backup directory '$BACKUP_DIR'. Aborting."
    exit 1
fi
echo "Backup directory ready."

# --- Perform Database Dump ---
echo "Dumping database '$DB_NAME' to '$BACKUP_FILE_SQL'..."
export PGPASSWORD="$DB_PASSWORD" # Set password for pg_dump
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE_SQL"

# Check if pg_dump was successful
if [ $? -ne 0 ]; then
    echo >&2 "Error: pg_dump failed. Please check database connection details and credentials."
    unset PGPASSWORD # Clear password from environment
    exit 1
fi
unset PGPASSWORD # Clear password from environment (security best practice)
echo "Database dump successful."

# --- Compress Backup ---
echo "Compressing backup file '$BACKUP_FILE_SQL' to '$BACKUP_FILE_ZIP'..."
zip "$BACKUP_FILE_ZIP" "$BACKUP_FILE_SQL"
if [ $? -ne 0 ]; then
    echo >&2 "Error: zip compression failed. Aborting."
    rm -f "$BACKUP_FILE_SQL" # Clean up uncompressed file if zip failed
    exit 1
fi
echo "Compression successful."

# Remove the original SQL file to save space
rm "$BACKUP_FILE_SQL"
echo "Removed uncompressed SQL file: '$BACKUP_FILE_SQL'."

# --- Local Retention Policy ---
echo "Applying local retention policy: removing backups older than $LOCAL_RETENTION_DAYS days from '$BACKUP_DIR'..."
find "$BACKUP_DIR" -type f -name "*.zip" -mtime +"$LOCAL_RETENTION_DAYS" -delete
if [ $? -ne 0 ]; then
    echo >&2 "Warning: Failed to delete old local backups. Please check permissions or disk space."
    # Continue execution even if old local backups cannot be deleted
else
    echo "Old local backups removed successfully."
fi

# --- Cloud Synchronization ---
echo "Synchronizing local backups to Cloudflare R2 bucket '$R2_BUCKET' using rclone remote '$R2_REMOTE'..."
echo "IMPORTANT: Ensure 'rclone' is installed and configured with a remote named '$R2_REMOTE' pointing to your Cloudflare R2 bucket '$R2_BUCKET'."
echo "You can configure rclone using 'rclone config'."

# Execute rclone sync command
rclone sync "$BACKUP_DIR" "$R2_REMOTE:$R2_BUCKET" --progress

if [ $? -ne 0 ]; then
    echo >&2 "Error: rclone sync to Cloudflare R2 bucket '$R2_BUCKET' failed."
    echo >&2 "Please check your rclone configuration ('rclone config'), credentials in .env, and network connectivity."
    exit 1 # Exit with error if sync fails
else
    echo "Synchronization to Cloudflare R2 successful."
fi

echo "Database backup and sync process completed successfully."
exit 0
