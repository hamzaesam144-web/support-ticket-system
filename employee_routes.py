from flask import render_template, request, redirect, url_for, session
from database import get_db_connection
from datetime import datetime


def register_employee_routes(app):

    # --------------------------------------------------
    # EMPLOYEE DASHBOARD
    # --------------------------------------------------

    @app.route("/employee")
    def employee_dashboard():

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "employee":
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
            WHERE creator_id = ?
            GROUP BY status
        """, (session["user_id"],)).fetchall()

        summary = {
            "Open": 0,
            "In Progress": 0,
            "Resolved": 0,
            "Closed": 0
        }

        for row in summary_rows:
            summary[row["status"]] = row["count"]

        # Employee tickets
        query = """
            SELECT
                tickets.*,
                assigned.username AS assigned_name
            FROM tickets
            LEFT JOIN users AS assigned
                ON tickets.assigned_to = assigned.id
            WHERE tickets.creator_id = ?
        """

        params = [session["user_id"]]

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
            "employee_dashboard.html",
            tickets=tickets,
            support_users=support_users,
            search=search,
            status=status,
            priority=priority,
            assignee=assignee,
            summary=summary
        )

    # --------------------------------------------------
    # CREATE TICKET
    # --------------------------------------------------

    @app.route("/tickets/create", methods=["GET", "POST"])
    def create_ticket():

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "employee":
            return "Unauthorized", 403

        error = None

        if request.method == "POST":

            title = request.form["title"].strip()
            description = request.form["description"].strip()
            category = request.form["category"]
            priority = request.form["priority"]

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
                error = "Title and description are required."

            elif category not in valid_categories:
                error = "Invalid category."

            elif priority not in valid_priorities:
                error = "Invalid priority."

            else:

                connection = get_db_connection()

                now = datetime.now().isoformat()

                connection.execute("""
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

                connection.commit()
                connection.close()

                return redirect(
                    url_for("employee_dashboard")
                )

        return render_template(
            "create_ticket.html",
            error=error
        )
