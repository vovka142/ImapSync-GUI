# Mailcow mailbox provisioning from CSV

A small Python utility to create Mailcow mailboxes in bulk through the Mailcow API.

It was tested with Mailcow Dockerized using the `/api/v1/add/mailbox` endpoint. The script reads existing mailbox names from MySQL (read-only query), skips mailboxes that already exist, and creates the remaining mailboxes through the API. It does **not** insert or update database records directly.

## Safety notes

- Run this only on the Mailcow server, as an administrator with access to Docker Compose and `mailcow.conf`.
- The script reads `API_KEY` and `DBPASS` from the local `mailcow.conf`; it does not print them.
- The temporary mailbox password is requested interactively and is not stored in the script or CSV.
- Do not commit `mailcow.conf`, CSV files, mailbox passwords, API keys, database passwords, or other credentials.
- The script sets `force_pw_update=1`, so users are required to change the temporary password at first login.
- The HTTPS connection is made to localhost and certificate verification is disabled for that local connection. The `Host` header is set to the configured Mailcow hostname.
- Existing mailbox discovery is a read-only SQL query. Mailbox creation is performed only through the Mailcow API.

## Requirements

- Mailcow Dockerized is installed and running.
- Python 3.8 or newer.
- Docker Compose v2, with permission to execute `docker compose`.
- A Mailcow API key with permission to create mailboxes.
- The API key is enabled in Mailcow and local API access is permitted.
- A CSV file with a semicolon separator and a `target_user` column.

Example CSV:

```csv
target_user;target_password
alice@example.org;not-used
bob@example.org;not-used
```

The `target_password` column is ignored. Do not put real passwords in this file.

## Configuration

The script uses these environment variables. Defaults are suitable only as examples; set the hostname and paths for your installation.

| Variable | Default | Description |
|---|---|---|
| `MAILCOW_DIR` | `/opt/mailcow-dockerized` | Directory containing `mailcow.conf` and the Compose project |
| `MAILBOX_CSV` | `/root/mail-migration/mailboxes.csv` | Input CSV path |
| `MAILCOW_HOST` | `webmail.example.com` | Mailcow hostname used in the HTTP Host header |
| `MAILCOW_HTTPS_PORT` | `448` | Local HTTPS port |
| `MAILBOX_QUOTA_MIB` | `5120` | Mailbox quota in MiB (5120 MiB = 5 GiB) |

The API key and database password are read from `mailcow.conf`; do not set or paste them into shell commands.

## Install and run

Copy `create_all.py` to the Mailcow server, then set the values for your installation:

```bash
export MAILCOW_DIR="/opt/mailcow-dockerized"
export MAILBOX_CSV="/root/mail-migration/mailboxes.csv"
export MAILCOW_HOST="webmail.your-domain.example"
export MAILCOW_HTTPS_PORT="448"
export MAILBOX_QUOTA_MIB="5120"

chmod 700 /root/mail-migration
chmod 600 "$MAILBOX_CSV"
python3 -m py_compile create_all.py
python3 create_all.py
```

The script prompts for one temporary password twice using hidden input. Use a strong password of at least 12 characters and distribute it to users through a secure channel.

## Behavior

1. Validates the CSV header, addresses, and duplicate entries.
2. Reads the existing mailbox list from the Mailcow MySQL container.
3. Skips addresses that already exist.
4. Requests the temporary password interactively.
5. Creates each missing mailbox through `POST /api/v1/add/mailbox` with:
   - `local_part` and `domain` (the fields expected by the Mailcow API);
   - `quota` in MiB;
   - `active=1`;
   - `force_pw_update=1`.
6. Stops on the first API error and prints a summary.

The script can be rerun safely after correcting an error: mailboxes already present in the database are skipped.

## Verify the result

Run a read-only query on the Mailcow server:

```bash
cd /opt/mailcow-dockerized

docker compose exec mysql-mailcow mysql \
  -umailcow -p"$(grep '^DBPASS=' mailcow.conf | cut -d= -f2-)" \
  mailcow -e "SELECT username, active, quota FROM mailbox ORDER BY username;"
```

For a 5 GiB mailbox, the stored quota is normally `5368709120` bytes. Confirm that the expected addresses are present, `active=1`, and the quota matches your configured value.

## Limitations

- This utility creates mailboxes; it does not migrate message contents, contacts, calendars, aliases, or filters.
- It does not retrieve or migrate users' old passwords.
- The CSV schema and Mailcow API behavior may vary between installations and versions. Review the API schema for your installed Mailcow release before using it in production.
