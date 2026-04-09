#!/bin/bash
set -e

# This script runs once when the PostGIS container is first initialized.
# It ensures the PostGIS extension is available in the application database.

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL

echo "✓ PostGIS extension created successfully."
