from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import check_password_hash

from database import get_db_connection


def register_auth_routes(app):

    @app.route("/login", methods=["GET", "POST"])
    def login():

        error = None

        if request.method == "POST":

            username = request.form["username"]
            password = request.form["password"]

            connection = get_db_connection()

            user = connection.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            connection.close()

            if user and check_password_hash(
                user["password"],
                password
            ):

                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]

                if user["role"] == "employee":
                    return redirect(
                        url_for("employee_dashboard")
                    )

                elif user["role"] == "support":
                    return redirect(
                        url_for("support_dashboard")
                    )

            else:
                error = "Invalid username or password."

        return render_template(
            "login.html",
            error=error
        )

    @app.route("/logout")
    def logout():

        session.clear()

        return redirect(
            url_for("login")
        )
