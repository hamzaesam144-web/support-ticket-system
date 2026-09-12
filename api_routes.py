from flask import request, jsonify, session
from werkzeug.security import check_password_hash
from database import get_db_connection
from datetime import datetime


def register_api_routes(app):

    # --------------------------------------------------
    # API LOGIN
    # --------------------------------------------------

    @app.route("/api/login", methods=["POST"])
    def api_login():

        data = request.get_json(silent=True) or {}

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({
                "error": "Username and password are required"
            }), 400

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        if not user or not check_password_hash(
            user["password"],
            password
        ):
            return jsonify({
                "error": "Invalid username or password"
            }), 401

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"]
            }
        }), 200

    # --------------------------------------------------
    # API LIST TICKETS
    # --------------------------------------------------

    @app.route("/api/tickets", methods=["GET"])
    def api_list_tickets():

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] not in ["employee", "support"]:
            return jsonify({"error": "Unauthorized"}), 403

        connection = get_db_connection()

        if session["role"] == "employee":

            tickets = connection.execute("""
                SELECT
                    tickets.*,
                    assigned.username AS assigned_name

                FROM tickets

                LEFT JOIN users AS assigned
                    ON tickets.assigned_to = assigned.id

                WHERE tickets.creator_id = ?

                ORDER BY tickets.created_at DESC
            """, (
                session["user_id"],
            )).fetchall()

        elif session["role"] == "support":

            tickets = connection.execute("""
                SELECT
                    tickets.*,
                    creator.username AS creator_name,
                    assigned.username AS assigned_name

                FROM tickets

                JOIN users AS creator
                    ON tickets.creator_id = creator.id

                LEFT JOIN users AS assigned
                    ON tickets.assigned_to = assigned.id

                ORDER BY tickets.created_at DESC
            """).fetchall()

        else:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 403

        connection.close()

        return jsonify([
            dict(ticket)
            for ticket in tickets
        ]), 200

    # --------------------------------------------------
    # API TICKET DETAILS
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>", methods=["GET"])
    def api_ticket_details(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

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
        """, (
            ticket_id,
        )).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if (
            session["role"] == "employee"
            and ticket["creator_id"] != session["user_id"]
        ):
            connection.close()
            return jsonify({"error": "Unauthorized"}), 403

        comments = connection.execute("""
            SELECT
                comments.*,
                users.username AS username

            FROM comments

            JOIN users
                ON comments.user_id = users.id

            WHERE comments.ticket_id = ?

            ORDER BY comments.created_at ASC
        """, (
            ticket_id,
        )).fetchall()

        history = connection.execute("""
            SELECT
                ticket_history.*,
                users.username AS actor_name

            FROM ticket_history

            JOIN users
                ON ticket_history.actor_id = users.id

            WHERE ticket_history.ticket_id = ?

            ORDER BY ticket_history.created_at ASC
        """, (
            ticket_id,
        )).fetchall()

        connection.close()

        return jsonify({
            "ticket": dict(ticket),

            "comments": [
                dict(comment)
                for comment in comments
            ],

            "history": [
                dict(item)
                for item in history
            ]
        }), 200

    # --------------------------------------------------
    # API SUMMARY
    # --------------------------------------------------

    @app.route("/api/summary", methods=["GET"])
    def api_summary():

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        connection = get_db_connection()

        if session["role"] == "employee":

            rows = connection.execute("""
                SELECT status, COUNT(*) AS count
                FROM tickets

                WHERE creator_id = ?

                GROUP BY status
            """, (
                session["user_id"],
            )).fetchall()

        elif session["role"] == "support":

            rows = connection.execute("""
                SELECT status, COUNT(*) AS count
                FROM tickets
                GROUP BY status
            """).fetchall()

        else:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 403

        connection.close()

        summary = {
            "Open": 0,
            "In Progress": 0,
            "Resolved": 0,
            "Closed": 0
        }

        for row in rows:
            summary[row["status"]] = row["count"]

        return jsonify(summary), 200
    # --------------------------------------------------
    # API CREATE TICKET
    # --------------------------------------------------

    @app.route("/api/tickets", methods=["POST"])
    def api_create_ticket():

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] != "employee":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}

        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        category = data.get("category", "")
        priority = data.get("priority", "Medium")

        valid_categories = [
            "Technical Issue",
            "Access Request",
            "Other"
        ]

        valid_priorities = [
            "Low",
            "Medium",
            "High"
        ]

        if not title or not description:
            return jsonify({
                "error": "Title and description are required"
            }), 400

        if category not in valid_categories:
            return jsonify({
                "error": "Invalid category"
            }), 400

        if priority not in valid_priorities:
            return jsonify({
                "error": "Invalid priority"
            }), 400

        connection = get_db_connection()

        now = datetime.now().isoformat()

        cursor = connection.execute("""
            INSERT INTO tickets
            (
                title,
                description,
                category,
                priority,
                status,
                creator_id,
                assigned_to,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            category,
            priority,
            "Open",
            session["user_id"],
            None,
            now,
            now
        ))

        ticket_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return jsonify({
            "message": "Ticket created successfully",
            "ticket_id": ticket_id
        }), 201

    # --------------------------------------------------
    # API ASSIGN TICKET
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>/assign", methods=["POST"])
    def api_assign_ticket(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] != "support":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}

        support_id = data.get("support_id")

        if not support_id:
            return jsonify({
                "error": "support_id is required"
            }), 400

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if ticket["status"] == "Closed":
            connection.close()
            return jsonify({
                "error": "Closed tickets cannot be reassigned"
            }), 400

        support_user = connection.execute("""
            SELECT *
            FROM users
            WHERE id = ?
            AND role = 'support'
        """, (support_id,)).fetchone()

        if support_user is None:
            connection.close()
            return jsonify({
                "error": "Invalid support user"
            }), 400

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

        return jsonify({
            "message": "Ticket assigned successfully"
        }), 200

    # --------------------------------------------------
    # API START TICKET
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>/start", methods=["POST"])
    def api_start_ticket(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] != "support":
            return jsonify({"error": "Unauthorized"}), 403

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if ticket["status"] != "Open":
            connection.close()
            return jsonify({
                "error": "Only Open tickets can be started"
            }), 400

        if ticket["assigned_to"] is None:
            connection.close()
            return jsonify({
                "error": "Ticket must be assigned first"
            }), 400

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

        return jsonify({
            "message": "Ticket started successfully"
        }), 200

    # --------------------------------------------------
    # API RESOLVE TICKET
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>/resolve", methods=["POST"])
    def api_resolve_ticket(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] != "support":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}

        resolution_note = data.get(
            "resolution_note",
            ""
        ).strip()

        if not resolution_note:
            return jsonify({
                "error": "Resolution note is required"
            }), 400

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if ticket["status"] != "In Progress":
            connection.close()
            return jsonify({
                "error": "Only In Progress tickets can be resolved"
            }), 400

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

        return jsonify({
            "message": "Ticket resolved successfully"
        }), 200

    # --------------------------------------------------
    # API REOPEN TICKET
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>/reopen", methods=["POST"])
    def api_reopen_ticket(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] != "employee":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}

        reopen_reason = data.get(
            "reopen_reason",
            ""
        ).strip()

        if not reopen_reason:
            return jsonify({
                "error": "Reopen reason is required"
            }), 400

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if ticket["creator_id"] != session["user_id"]:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 403

        if ticket["status"] != "Resolved":
            connection.close()
            return jsonify({
                "error": "Only Resolved tickets can be reopened"
            }), 400

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

        return jsonify({
            "message": "Ticket reopened successfully"
        }), 200

    # --------------------------------------------------
    # API CLOSE TICKET
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>/close", methods=["POST"])
    def api_close_ticket(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] != "employee":
            return jsonify({"error": "Unauthorized"}), 403

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if ticket["creator_id"] != session["user_id"]:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 403

        if ticket["status"] != "Resolved":
            connection.close()
            return jsonify({
                "error": "Only Resolved tickets can be closed"
            }), 400

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

        return jsonify({
            "message": "Ticket closed successfully"
        }), 200

    # --------------------------------------------------
    # API ADD COMMENT
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>/comments", methods=["POST"])
    def api_add_comment(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session["role"] not in ["employee", "support"]:
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}

        comment = data.get("comment", "").strip()

        if not comment:
            return jsonify({
                "error": "Comment cannot be empty"
            }), 400

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if (
            session["role"] == "employee"
            and ticket["creator_id"] != session["user_id"]
        ):
            connection.close()
            return jsonify({"error": "Unauthorized"}), 403

        if ticket["status"] == "Closed":
            connection.close()
            return jsonify({
                "error": "Cannot comment on a Closed ticket"
            }), 400

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

        return jsonify({
            "message": "Comment added successfully"
        }), 201

    # --------------------------------------------------
    # API HISTORY
    # --------------------------------------------------

    @app.route("/api/tickets/<int:ticket_id>/history", methods=["GET"])
    def api_ticket_history(ticket_id):

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        connection = get_db_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if ticket is None:
            connection.close()
            return jsonify({"error": "Ticket not found"}), 404

        if (
            session["role"] == "employee"
            and ticket["creator_id"] != session["user_id"]
        ):
            connection.close()
            return jsonify({"error": "Unauthorized"}), 403

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

        return jsonify([
            dict(item)
            for item in history
        ]), 200
