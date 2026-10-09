"""Open the configured SQL source without logging or storing credentials."""

import getpass
import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


def connect_source():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    def quote(value):
        return "{" + str(value).replace("}", "}}") + "}"

    password = os.getenv("DB_PASSWORD") or getpass.getpass("SQL password (not saved): ")
    host = os.getenv("DB_HOST", "192.168.1.200")
    port = os.getenv("DB_PORT", "1433")
    settings = {
        "DRIVER": os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server"),
        "SERVER": f"tcp:{host},{port}",
        "DATABASE": os.getenv("DB_NAME", "PeCalHackathon2026"),
        "UID": os.getenv("DB_USER", "PeCalHackathonParticipant"),
        "PWD": password,
        "Encrypt": "yes",
        # Retain the existing exporter policy for the lab SQL Server.
        "TrustServerCertificate": os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes"),
        "ApplicationIntent": "ReadOnly",
    }
    connection = pyodbc.connect(
        ";".join(f"{key}={quote(value)}" for key, value in settings.items()) + ";",
        timeout=20,
        autocommit=True,
    )
    connection.timeout = 120
    return connection
