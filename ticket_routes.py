from flask import render_template, request, redirect, url_for, session
from database import get_db_connection
from datetime import datetime


def register_ticket_routes(app):

    # --------------------------------------------------
    # TICKET DETAILS
    # --------------------------------------------------

    @app.route("/tickets/<int:ticket_id>")
    def ticket_details(ticket_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] not in ["employee", "support"]:
            return "Unauthorized", 403

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT
                tickets.*,
                creator.username AS creator_name,
                assigned.username AS assigned_name
            FROM tickets

            JOIN users AS creator
                ON tickets.creator_id = creator.id

            LEFT JOIN users AS assigned
                ON tickets.assigned_to = assigned.id

            WHERE tickets.id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return "Ticket not found", 404

        if (
            session["role"] == "employee"
            and ticket["creator_id"] != session["user_id"]
        ):
            connection.close()
            return "Unauthorized", 403

        support_users = connection.execute("""
            SELECT id, username
            FROM users
            WHERE role = 'support'
            ORDER BY username
        """).fetchall()

        comments = connection.execute("""
            SELECT
                comments.*,
                users.username AS username

            FROM comments

            JOIN users
                ON comments.user_id = users.id

            WHERE comments.ticket_id = ?

            ORDER BY comments.created_at ASC
        """, (ticket_id,)).fetchall()

        history = connection.execute("""
            SELECT
                ticket_history.*,
                users.username AS actor_name

            FROM ticket_history

            JOIN users
                ON ticket_history.actor_id = users.id

            WHERE ticket_history.ticket_id = ?

            ORDER BY ticket_history.created_at ASC
        """, (ticket_id,)).fetchall()

        connection.close()

        return render_template(
            "ticket_details.html",
            ticket=ticket,
            support_users=support_users,
            comments=comments,
            history=history
        )

    # --------------------------------------------------
    # ASSIGN / REASSIGN
    # --------------------------------------------------

    @app.route("/tickets/<int:ticket_id>/assign", methods=["POST"])
    def assign_ticket(ticket_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "support":
            return "Unauthorized", 403

        support_id = request.form["support_id"]

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return "Ticket not found", 404

        if ticket["status"] == "Closed":
            connection.close()
            return "Closed tickets cannot be reassigned", 400

        support_user = connection.execute("""
            SELECT *
            FROM users
            WHERE id = ?
            AND role = 'support'
        """, (support_id,)).fetchone()

        if support_user is None:
            connection.close()
            return "Invalid support user", 400

        old_assigned_name = "Unassigned"

        if ticket["assigned_to"] is not None:

            old_user = connection.execute("""
                SELECT username
                FROM users
                WHERE id = ?
            """, (ticket["assigned_to"],)).fetchone()

            if old_user:
                old_assigned_name = old_user["username"]

        new_assigned_name = support_user["username"]

        now = datetime.now().isoformat()

        connection.execute("""
            UPDATE tickets
            SET assigned_to = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            support_id,
            now,
            ticket_id
        ))

        connection.execute("""
            INSERT INTO ticket_history
            (
                ticket_id,
                actor_id,
                change_type,
                old_value,
                new_value,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            session["user_id"],
            "assignee",
            old_assigned_name,
            new_assigned_name,
            None,
            now
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "ticket_details",
                ticket_id=ticket_id
            )
        )

    # --------------------------------------------------
    # START WORK
    # --------------------------------------------------

    @app.route("/tickets/<int:ticket_id>/start", methods=["POST"])
    def start_ticket(ticket_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "support":
            return "Unauthorized", 403

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return "Ticket not found", 404

        if ticket["status"] != "Open":
            connection.close()
            return "Only Open tickets can be started", 400

        if ticket["assigned_to"] is None:
            connection.close()
            return "Ticket must be assigned first", 400

        now = datetime.now().isoformat()

        connection.execute("""
            UPDATE tickets
            SET status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            "In Progress",
            now,
            ticket_id
        ))

        connection.execute("""
            INSERT INTO ticket_history
            (
                ticket_id,
                actor_id,
                change_type,
                old_value,
                new_value,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            session["user_id"],
            "status",
            "Open",
            "In Progress",
            None,
            now
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "ticket_details",
                ticket_id=ticket_id
            )
        )

    # --------------------------------------------------
    # RESOLVE
    # --------------------------------------------------

    @app.route("/tickets/<int:ticket_id>/resolve", methods=["POST"])
    def resolve_ticket(ticket_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "support":
            return "Unauthorized", 403

        resolution_note = request.form["resolution_note"].strip()

        if not resolution_note:
            return "Resolution note is required", 400

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return "Ticket not found", 404

        if ticket["status"] != "In Progress":
            connection.close()
            return "Only In Progress tickets can be resolved", 400

        now = datetime.now().isoformat()

        connection.execute("""
            UPDATE tickets
            SET status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            "Resolved",
            now,
            ticket_id
        ))

        connection.execute("""
            INSERT INTO ticket_history
            (
                ticket_id,
                actor_id,
                change_type,
                old_value,
                new_value,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            session["user_id"],
            "status",
            "In Progress",
            "Resolved",
            resolution_note,
            now
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "ticket_details",
                ticket_id=ticket_id
            )
        )

    # --------------------------------------------------
    # CLOSE
    # --------------------------------------------------

    @app.route("/tickets/<int:ticket_id>/close", methods=["POST"])
    def close_ticket(ticket_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "employee":
            return "Unauthorized", 403

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return "Ticket not found", 404

        if ticket["creator_id"] != session["user_id"]:
            connection.close()
            return "Unauthorized", 403

        if ticket["status"] != "Resolved":
            connection.close()
            return "Only Resolved tickets can be closed", 400

        now = datetime.now().isoformat()

        connection.execute("""
            UPDATE tickets
            SET status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            "Closed",
            now,
            ticket_id
        ))

        connection.execute("""
            INSERT INTO ticket_history
            (
                ticket_id,
                actor_id,
                change_type,
                old_value,
                new_value,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            session["user_id"],
            "status",
            "Resolved",
            "Closed",
            None,
            now
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "ticket_details",
                ticket_id=ticket_id
            )
        )

    # --------------------------------------------------
    # REOPEN
    # --------------------------------------------------

    @app.route("/tickets/<int:ticket_id>/reopen", methods=["POST"])
    def reopen_ticket(ticket_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "employee":
            return "Unauthorized", 403

        reopen_reason = request.form["reopen_reason"].strip()

        if not reopen_reason:
            return "Reopen reason is required", 400

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return "Ticket not found", 404

        if ticket["creator_id"] != session["user_id"]:
            connection.close()
            return "Unauthorized", 403

        if ticket["status"] != "Resolved":
            connection.close()
            return "Only Resolved tickets can be reopened", 400

        now = datetime.now().isoformat()

        connection.execute("""
            UPDATE tickets
            SET status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            "In Progress",
            now,
            ticket_id
        ))

        connection.execute("""
            INSERT INTO ticket_history
            (
                ticket_id,
                actor_id,
                change_type,
                old_value,
                new_value,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            session["user_id"],
            "status",
            "Resolved",
            "In Progress",
            reopen_reason,
            now
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "ticket_details",
                ticket_id=ticket_id
            )
        )

    # --------------------------------------------------
    # ADD COMMENT
    # --------------------------------------------------

    @app.route("/tickets/<int:ticket_id>/comment", methods=["POST"])
    def add_comment(ticket_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] not in ["employee", "support"]:
            return "Unauthorized", 403

        comment = request.form["comment"].strip()

        if not comment:
            return "Comment cannot be empty", 400

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return "Ticket not found", 404

        if session["role"] == "employee":

            if ticket["creator_id"] != session["user_id"]:
                connection.close()
                return "Unauthorized", 403

        if ticket["status"] == "Closed":
            connection.close()
            return "Cannot comment on a Closed ticket", 400

        now = datetime.now().isoformat()

        connection.execute("""
            INSERT INTO comments
            (
                ticket_id,
                user_id,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            ticket_id,
            session["user_id"],
            comment,
            now
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "ticket_details",
                ticket_id=ticket_id
            )
        )
