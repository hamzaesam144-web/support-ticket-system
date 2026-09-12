from flask import render_template, request, redirect, url_for, session
from database import get_db_connection


def register_support_routes(app):

    @app.route("/support")
    def support_dashboard():

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "support":
            return "Unauthorized", 403

        search = request.args.get("search", "").strip()
        status = request.args.get("status", "")
        priority = request.args.get("priority", "")
        assignee = request.args.get("assignee", "")

        connection = get_db_connection()

        # Summary counts before filters
        summary_rows = connection.execute("""
            SELECT status, COUNT(*) AS count
            FROM tickets
            GROUP BY status
        """).fetchall()

        summary = {
            "Open": 0,
            "In Progress": 0,
            "Resolved": 0,
            "Closed": 0
        }

        for row in summary_rows:
            summary[row["status"]] = row["count"]

        # Tickets query
        query = """
            SELECT
                tickets.*,
                creator.username AS creator_name,
                assigned.username AS assigned_name

            FROM tickets

            JOIN users AS creator
                ON tickets.creator_id = creator.id

            LEFT JOIN users AS assigned
                ON tickets.assigned_to = assigned.id

            WHERE 1 = 1
        """

        params = []

        if search:
            query += " AND tickets.title LIKE ?"
            params.append("%" + search + "%")

        if status:
            query += " AND tickets.status = ?"
            params.append(status)

        if priority:
            query += " AND tickets.priority = ?"
            params.append(priority)

        if assignee == "unassigned":
            query += " AND tickets.assigned_to IS NULL"

        elif assignee:
            query += " AND tickets.assigned_to = ?"
            params.append(assignee)

        query += " ORDER BY tickets.created_at DESC"

        tickets = connection.execute(
            query,
            params
        ).fetchall()

        support_users = connection.execute("""
            SELECT id, username
            FROM users
            WHERE role = 'support'
            ORDER BY username
        """).fetchall()

        connection.close()

        return render_template(
            "support_dashboard.html",
            tickets=tickets,
            support_users=support_users,
            search=search,
            status=status,
            priority=priority,
            assignee=assignee,
            summary=summary
        )
