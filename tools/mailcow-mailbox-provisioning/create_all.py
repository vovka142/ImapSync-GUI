#!/usr/bin/env python3
"""Create Mailcow mailboxes from a CSV using the Mailcow API.

The script only reads mailbox names from MySQL. Mailboxes are created through
the Mailcow API; it does not write to the database directly.
"""

import csv
import getpass
import http.client
import json
import os
import ssl
import subprocess
import sys
import time
from pathlib import Path

MAILCOW_DIR = Path(os.environ.get("MAILCOW_DIR", "/opt/mailcow-dockerized"))
CSV_FILE = Path(os.environ.get("MAILBOX_CSV", "/root/mail-migration/mailboxes.csv"))
MAILCOW_HOST = os.environ.get("MAILCOW_HOST", "webmail.example.com")
HTTPS_PORT = int(os.environ.get("MAILCOW_HTTPS_PORT", "448"))
QUOTA_MIB = int(os.environ.get("MAILBOX_QUOTA_MIB", "5120"))
DELAY_SECONDS = 0.5


def read_mailcow_config():
    config_path = MAILCOW_DIR / "mailcow.conf"
    if not config_path.is_file():
        sys.exit(f"Mailcow config not found: {config_path}")

    config = {}
    with config_path.open(encoding="utf-8") as config_file:
        for line in config_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key] = value

    api_key = config.get("API_KEY")
    db_password = config.get("DBPASS")
    if not api_key or not db_password:
        sys.exit("API_KEY or DBPASS is missing from mailcow.conf")
    return api_key, db_password


def read_csv_addresses():
    if not CSV_FILE.is_file():
        sys.exit(f"CSV file not found: {CSV_FILE}")

    with CSV_FILE.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        if not reader.fieldnames or "target_user" not in reader.fieldnames:
            sys.exit("CSV must contain a 'target_user' column (separator: ';').")
        addresses = [
            (row.get("target_user") or "").strip().lower()
            for row in reader
        ]

    addresses = [address for address in addresses if address]
    if not addresses:
        sys.exit("CSV contains no mailbox addresses.")
    if len(addresses) != len(set(addresses)):
        sys.exit("CSV contains duplicate mailbox addresses.")

    for address in addresses:
        if address.count("@") != 1:
            sys.exit(f"Invalid email address: {address}")
        local_part, domain = address.rsplit("@", 1)
        if not local_part or not domain or "." not in domain:
            sys.exit(f"Invalid email address: {address}")

    return addresses


def get_existing_mailboxes(db_password):
    command = [
        "docker", "compose", "exec", "-T", "mysql-mailcow",
        "mysql", "-umailcow", f"-p{db_password}", "mailcow",
        "-N", "-e", "SELECT username FROM mailbox",
    ]
    result = subprocess.run(
        command,
        cwd=MAILCOW_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        sys.exit("Could not read existing mailboxes from MySQL:\n" +
                 result.stderr[-1500:])

    return {
        line.strip().lower()
        for line in result.stdout.splitlines()
        if "@" in line
    }


def add_mailbox(email, password, api_key):
    local_part, domain = email.rsplit("@", 1)
    payload = {
        "local_part": local_part,
        "domain": domain,
        "name": "",
        "password": password,
        "password2": password,
        "quota": str(QUOTA_MIB),
        "active": "1",
        "force_pw_update": "1",
    }

    connection = http.client.HTTPSConnection(
        "127.0.0.1",
        HTTPS_PORT,
        context=ssl._create_unverified_context(),
        timeout=30,
    )
    try:
        connection.request(
            "POST",
            "/api/v1/add/mailbox",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Host": MAILCOW_HOST,
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response = connection.getresponse()
        status = response.status
        raw_body = response.read().decode("utf-8", errors="replace")
    finally:
        connection.close()

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        body = raw_body
    return status, body


def is_success(status, response):
    return (
        status == 200
        and isinstance(response, list)
        and any(
            isinstance(item, dict)
            and item.get("type") == "success"
            and (
                item.get("msg") == "mailbox_added"
                or (
                    isinstance(item.get("msg"), list)
                    and bool(item["msg"])
                    and item["msg"][0] == "mailbox_added"
                )
            )
            for item in response
        )
    )


def main():
    api_key, db_password = read_mailcow_config()
    addresses = read_csv_addresses()

    password = getpass.getpass("Temporary mailbox password: ")
    if len(password) < 12:
        sys.exit("Password must contain at least 12 characters.")
    if password != getpass.getpass("Repeat temporary password: "):
        sys.exit("Passwords do not match.")

    existing = get_existing_mailboxes(db_password)
    to_create = [address for address in addresses if address not in existing]

    print(f"Addresses in CSV: {len(addresses)}")
    print(f"Already present: {len(addresses) - len(to_create)}")
    print(f"To create: {len(to_create)}")
    print(f"Quota per mailbox: {QUOTA_MIB} MiB")

    created = []
    errors = []

    for index, email in enumerate(to_create, start=1):
        status, response = add_mailbox(email, password, api_key)
        if not is_success(status, response):
            errors.append(email)
            print(f"\nERROR: {email}")
            print(f"HTTP: {status}")
            print("Response:", json.dumps(response, ensure_ascii=False))
            print("Stopping; fix the error before rerunning.")
            break

        created.append(email)
        print(f"[{index}/{len(to_create)}] CREATED: {email}")
        time.sleep(DELAY_SECONDS)

    print("\n===== SUMMARY =====")
    print(f"Created: {len(created)}")
    print(f"Skipped (already present): {len(addresses) - len(to_create)}")
    print(f"Errors: {len(errors)}")


if __name__ == "__main__":
    main()
