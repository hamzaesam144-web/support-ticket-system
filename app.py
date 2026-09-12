from flask import Flask
import os
from api_routes import register_api_routes
from auth_routes import register_auth_routes
from employee_routes import register_employee_routes
from support_routes import register_support_routes
from ticket_routes import register_ticket_routes


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-key"
)

register_auth_routes(app)
register_employee_routes(app)
register_support_routes(app)
register_ticket_routes(app)
register_api_routes(app)


@app.route("/")
def home():
    from flask import redirect, url_for
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
