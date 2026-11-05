import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.config import DB_PATH


VALID_STATUSES = {
    "NEW",
    "ACKNOWLEDGED",
    "UNDER MAINTENANCE",
    "RESOLVED",
    "VERIFIED",
}

SEVERITY_RANK = {
    "WARNING": 1,
    "CRITICAL": 2,
}


class AlertError(Exception):
    """Raised when an alert operation is invalid or not permitted."""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        timeout=15,
        isolation_level="DEFERRED",
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 15000")

    return connection


def initialize_database():
    """Create database tables from schema.sql."""
    schema_path = Path(__file__).with_name("schema.sql")

    if not schema_path.exists():
        raise AlertError(f"Database schema not found: {schema_path}")

    with _connect() as connection:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )


def _record_activity(
    connection,
    alert_id,
    action,
    performed_by,
    role,
    details=None,
):
    connection.execute(
        """
        INSERT INTO alert_activity
        (alert_id, action, performed_by, role, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            alert_id,
            action,
            performed_by,
            role,
            details,
            _now(),
        ),
    )


def _require_role(role, allowed_roles):
    if role not in allowed_roles:
        raise AlertError(
            "You do not have permission to perform this action."
        )


def _get_alert_for_update(connection, alert_id):
    """
    Retrieve an alert inside a write transaction.

    BEGIN IMMEDIATE ensures competing submissions are serialized.
    """
    connection.execute("BEGIN IMMEDIATE")

    alert = connection.execute(
        "SELECT * FROM alerts WHERE id = ?",
        (alert_id,),
    ).fetchone()

    if not alert:
        raise AlertError("Alert not found.")

    return alert


# ---------------------------------------------------------
# ALERT CREATION
# ---------------------------------------------------------

def create_alert(
    bearing,
    severity,
    recording_timestamp,
    anomaly_score,
    condition_label,
    performed_by="MANTIQ System",
):
    """Create or update an alert without duplicating historical events."""

    if bearing not in (1, 2, 3, 4):
        raise AlertError("Invalid bearing number.")

    severity = str(severity).upper()

    if severity not in SEVERITY_RANK:
        raise AlertError("Severity must be WARNING or CRITICAL.")

    initialize_database()

    with _connect() as connection:

        connection.execute("BEGIN IMMEDIATE")

        historical = connection.execute(
            """
            SELECT * FROM alerts
            WHERE bearing = ? AND recording_timestamp = ?
            ORDER BY id DESC LIMIT 1
            """,
            (bearing, str(recording_timestamp)),
        ).fetchone()

        if historical:
            alert_id = historical["id"]

            if (
                historical["status"] != "VERIFIED"
                and SEVERITY_RANK[severity]
                > SEVERITY_RANK[historical["severity"]]
            ):
                connection.execute(
                    "UPDATE alerts SET severity = ? WHERE id = ?",
                    (severity, alert_id),
                )

                _record_activity(
                    connection,
                    alert_id,
                    "SEVERITY_UPGRADED",
                    performed_by,
                    "system",
                    f"Severity upgraded to {severity}.",
                )

            return alert_id

        existing = connection.execute(
            """
            SELECT * FROM alerts
            WHERE bearing = ? AND status != 'VERIFIED'
            ORDER BY id DESC LIMIT 1
            """,
            (bearing,),
        ).fetchone()

        if existing:
            alert_id = existing["id"]

            if SEVERITY_RANK[severity] > SEVERITY_RANK[existing["severity"]]:
                connection.execute(
                    "UPDATE alerts SET severity = ? WHERE id = ?",
                    (severity, alert_id),
                )

                _record_activity(
                    connection,
                    alert_id,
                    "SEVERITY_UPGRADED",
                    performed_by,
                    "system",
                    f"Severity upgraded to {severity}.",
                )

            return alert_id

        created_at = _now()

        alert_code = (
            f"MNT-B{bearing}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        )

        cursor = connection.execute(
            """
            INSERT INTO alerts (
                alert_code,
                bearing,
                severity,
                status,
                created_at,
                recording_timestamp,
                anomaly_score,
                condition_label
            )
            VALUES (?, ?, ?, 'NEW', ?, ?, ?, ?)
            """,
            (
                alert_code,
                bearing,
                severity,
                created_at,
                str(recording_timestamp),
                float(anomaly_score),
                condition_label,
            ),
        )

        alert_id = cursor.lastrowid

        _record_activity(
            connection,
            alert_id,
            "ALERT_CREATED",
            performed_by,
            "system",
            f"{severity} alert generated for Bearing {bearing}.",
        )

        return alert_id


# ---------------------------------------------------------
# ALERT RETRIEVAL
# ---------------------------------------------------------

def get_alert(alert_id):
    initialize_database()

    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()

    return dict(row) if row else None


def get_all_alerts():
    initialize_database()

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM alerts
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_alert_activity(alert_id):
    initialize_database()

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM alert_activity
            WHERE alert_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (alert_id,),
        ).fetchall()

    return [dict(row) for row in rows]


# ---------------------------------------------------------
# ACKNOWLEDGEMENT
# ---------------------------------------------------------

def acknowledge_alert(alert_id, username, role):
    _require_role(role, {"operator", "maintenance_head"})

    with _connect() as connection:
        alert = _get_alert_for_update(connection, alert_id)

        if alert["status"] != "NEW":
            raise AlertError(
                "This alert has already been acknowledged."
            )

        connection.execute(
            """
            UPDATE alerts
            SET status = 'ACKNOWLEDGED'
            WHERE id = ? AND status = 'NEW'
            """,
            (alert_id,),
        )

        _record_activity(
            connection,
            alert_id,
            "ACKNOWLEDGED",
            username,
            role,
        )


# ---------------------------------------------------------
# OPERATOR FINDINGS
# ---------------------------------------------------------

def add_operator_findings(alert_id, username, role, findings):
    _require_role(role, {"operator"})

    findings = str(findings or "").strip()

    if not findings:
        raise AlertError("Please enter your findings.")

    with _connect() as connection:
        alert = _get_alert_for_update(connection, alert_id)

        if alert["status"] in {"RESOLVED", "VERIFIED"}:
            raise AlertError("This alert is already closed.")

        connection.execute(
            """
            UPDATE alerts
            SET operator_findings = ?
            WHERE id = ?
            """,
            (findings, alert_id),
        )

        _record_activity(
            connection,
            alert_id,
            "OPERATOR_FINDINGS_ADDED",
            username,
            role,
            findings,
        )


# ---------------------------------------------------------
# ESCALATION
# ---------------------------------------------------------

def escalate_alert(
    alert_id,
    username,
    role,
    reason="",
):
    _require_role(role, {"operator", "maintenance_head"})

    reason = str(reason or "").strip()

    with _connect() as connection:
        alert = _get_alert_for_update(connection, alert_id)

        if alert["status"] in {"RESOLVED", "VERIFIED"}:
            raise AlertError("Closed alerts cannot be escalated.")

        if bool(alert["escalated"]):
            raise AlertError(
                "This alert has already been escalated."
            )

        connection.execute(
            """
            UPDATE alerts
            SET escalated = 1
            WHERE id = ? AND escalated = 0
            """,
            (alert_id,),
        )

        _record_activity(
            connection,
            alert_id,
            "ESCALATED",
            username,
            role,
            reason or "Escalated to maintenance head.",
        )


# ---------------------------------------------------------
# MAINTENANCE ASSIGNMENT
# ---------------------------------------------------------

def assign_maintenance(
    alert_id,
    username,
    role,
    assigned_to,
    instructions="",
):
    _require_role(role, {"maintenance_head"})

    assigned_to = str(assigned_to or "").strip()
    instructions = str(instructions or "").strip()

    if not assigned_to:
        raise AlertError("Please specify the person assigned.")

    with _connect() as connection:
        alert = _get_alert_for_update(connection, alert_id)

        if alert["status"] in {"RESOLVED", "VERIFIED"}:
            raise AlertError("Closed alerts cannot be assigned.")

        if alert["status"] == "UNDER MAINTENANCE":
            raise AlertError(
                "Maintenance has already been assigned to this alert."
            )

        now = _now()

        connection.execute(
            """
            UPDATE alerts
            SET assigned_to = ?,
                status = 'UNDER MAINTENANCE'
            WHERE id = ?
            """,
            (assigned_to, alert_id),
        )

        connection.execute(
            """
            INSERT INTO maintenance_assignments
            (
                alert_id,
                assigned_to,
                assigned_by,
                instructions,
                assigned_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                assigned_to,
                username,
                instructions,
                now,
            ),
        )

        details = f"Assigned to {assigned_to}."

        if instructions:
            details += f" {instructions}"

        _record_activity(
            connection,
            alert_id,
            "MAINTENANCE_ASSIGNED",
            username,
            role,
            details,
        )


# ---------------------------------------------------------
# RESOLUTION
# ---------------------------------------------------------

def resolve_alert(
    alert_id,
    username,
    role,
    corrective_action,
):
    _require_role(role, {"maintenance_head"})

    corrective_action = str(corrective_action or "").strip()

    if not corrective_action:
        raise AlertError("Please record the corrective action.")

    with _connect() as connection:
        alert = _get_alert_for_update(connection, alert_id)

        if alert["status"] != "UNDER MAINTENANCE":
            raise AlertError(
                "This alert must be under maintenance before resolution."
            )

        now = _now()

        connection.execute(
            """
            UPDATE alerts
            SET status = 'RESOLVED',
                corrective_action = ?,
                resolved_at = ?
            WHERE id = ?
            """,
            (corrective_action, now, alert_id),
        )

        connection.execute(
            """
            UPDATE maintenance_assignments
            SET completed_at = ?
            WHERE alert_id = ? AND completed_at IS NULL
            """,
            (now, alert_id),
        )

        _record_activity(
            connection,
            alert_id,
            "RESOLVED",
            username,
            role,
            corrective_action,
        )


# ---------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------

def verify_alert(
    alert_id,
    username,
    role,
    verification_notes="",
):
    _require_role(role, {"maintenance_head"})

    verification_notes = str(verification_notes or "").strip()

    with _connect() as connection:
        alert = _get_alert_for_update(connection, alert_id)

        if alert["status"] != "RESOLVED":
            raise AlertError(
                "Only resolved alerts can be verified."
            )

        now = _now()

        connection.execute(
            """
            UPDATE alerts
            SET status = 'VERIFIED',
                verified_at = ?
            WHERE id = ?
            """,
            (now, alert_id),
        )

        _record_activity(
            connection,
            alert_id,
            "VERIFIED",
            username,
            role,
            verification_notes
            or "Maintenance verification completed.",
        )