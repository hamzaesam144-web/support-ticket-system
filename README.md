# Internal Support Ticket System

## Description

The Internal Support Ticket System is a web application built using Flask and SQLite.

The system provides two user roles:

- **Employee** – can create and manage their own support tickets.
- **Support** – can view all tickets, assign or reassign tickets, update ticket status, add comments, and resolve issues.

The application includes authentication, role-based authorization, ticket workflow management, comments, ticket history, search, filters, summary counts, a JSON API, and persistent database storage.

---

## Repository

GitHub Repository:

https://github.com/hamzaesam144-web/support-ticket-system

---

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- Git

---

## Features

### Employee

Employees can:

- Login
- Create support tickets
- View only their own tickets
- Search tickets by title
- Filter tickets by status, priority, and assignee
- View ticket details
- Add comments to their own non-Closed tickets
- View ticket history
- View ticket summary counts
- Reopen their own Resolved tickets with a required reason
- Close their own Resolved tickets

### Support

Support users can:

- Login
- View all tickets
- Search tickets by title
- Filter tickets by status, priority, and assignee
- Assign and reassign tickets
- Start work on assigned Open tickets
- Resolve In Progress tickets with a required resolution note
- Add comments to any non-Closed ticket
- View ticket history
- View ticket summary counts

---

## Ticket Workflow

The normal ticket workflow is:

```text
Open → In Progress → Resolved → Closed
```

A Resolved ticket can also be reopened by the Employee who created it:

```text
Resolved → In Progress
```

### Workflow Rules

- New tickets start as **Open**.
- New tickets start **Unassigned**.
- An Open ticket must be assigned to a Support user before work can start.
- Starting work changes the ticket from **Open → In Progress**.
- Only Support users can start work.
- Only Support users can resolve In Progress tickets.
- A non-empty resolution note is required when resolving.
- Only the Employee who created a Resolved ticket can close it.
- Only the Employee who created a Resolved ticket can reopen it.
- A non-empty reopen reason is required.
- Reopening changes the ticket from **Resolved → In Progress**.
- The assigned Support user is retained when a ticket is reopened.
- Reassignment is allowed on non-Closed tickets.
- Closed tickets are read-only.
- Closed tickets cannot receive new comments.
- Closed tickets cannot be reassigned.
- Closed tickets cannot have their status changed.

---

## Setup

### 1. Prerequisites

The following software is required:

- Python 3
- pip
- Git

### 2. Clone the Repository

```bash
git clone https://github.com/hamzaesam144-web/support-ticket-system.git
cd support-ticket-system
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

On Windows:

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configuration

The Flask secret key can be provided using the `SECRET_KEY` environment variable.

PowerShell example:

```powershell
$env:SECRET_KEY="your-secret-key"
```

A development fallback key is included for local development.

No external database configuration is required because SQLite is used.

### 7. Initialize the Database

```bash
python init_db.py
```

The database initialization script:

- Creates the required database tables.
- Creates the test Employee accounts.
- Creates the test Support accounts.
- Adds sample tickets when the tickets table is empty.

The sample data includes tickets across different statuses and users to make permissions, search, filters, and summary counts easy to review.

### 8. Run the Application

```bash
python app.py
```

Open the application in a browser at:

```text
http://127.0.0.1:5000
```

---

## Test Accounts

| Role | Username | Password |
|---|---|---|
| Employee | employee1 | emp123 |
| Employee | employee2 | emp123 |
| Support | support1 | sup123 |
| Support | support2 | sup123 |

---

## Ticket Fields

Each ticket contains:

- Automatically generated unique ID
- Title
- Description
- Category
- Priority
- Status
- Creator
- Assigned Support user
- Created timestamp
- Last updated timestamp

### Categories

Supported categories are:

- Technical Issue
- Access Request
- Other

### Priorities

Supported priorities are:

- Low
- Medium
- High

The default priority is **Medium**.

---

## Database

SQLite is used for persistent storage.

The main database tables are:

- `users`
- `tickets`
- `comments`
- `ticket_history`

The database stores users, ticket information, comments, and ticket history.

Ticket data remains available after refreshing the page or restarting the Flask application.

---

## Web Routes

The application provides web routes used by the HTML interface.

Main routes include:

```text
/login
/logout
/employee
/support
/tickets/create
/tickets/<ticket_id>
/tickets/<ticket_id>/assign
/tickets/<ticket_id>/start
/tickets/<ticket_id>/resolve
/tickets/<ticket_id>/reopen
/tickets/<ticket_id>/close
/tickets/<ticket_id>/comment
```

The HTML interface uses Flask GET and POST routes.

---

## Backend API

The application also provides a JSON API.

Authentication uses Flask sessions.

### API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/login` | Login |
| GET | `/api/tickets` | List visible tickets |
| POST | `/api/tickets` | Create a new ticket |
| GET | `/api/tickets/<id>` | Get ticket details |
| POST | `/api/tickets/<id>/assign` | Assign or reassign a ticket |
| POST | `/api/tickets/<id>/start` | Start work on a ticket |
| POST | `/api/tickets/<id>/resolve` | Resolve a ticket |
| POST | `/api/tickets/<id>/reopen` | Reopen a ticket |
| POST | `/api/tickets/<id>/close` | Close a ticket |
| POST | `/api/tickets/<id>/comments` | Add a comment |
| GET | `/api/tickets/<id>/history` | Get ticket history |
| GET | `/api/summary` | Get ticket summary counts |

### Login Example

Request:

```json
{
    "username": "employee1",
    "password": "emp123"
}
```

### Create Ticket Example

```json
{
    "title": "Printer not working",
    "description": "The office printer is not responding.",
    "category": "Technical Issue",
    "priority": "High"
}
```

A new ticket is automatically created as:

```text
Status: Open
Assigned To: Unassigned
```

### Assign Ticket Example

```json
{
    "support_id": 3
}
```

Only a Support user can assign or reassign tickets.

### Resolve Ticket Example

```json
{
    "resolution_note": "Printer connection was restored."
}
```

A non-empty resolution note is required.

### Reopen Ticket Example

```json
{
    "reopen_reason": "The problem happened again."
}
```

A non-empty reopen reason is required.

### Add Comment Example

```json
{
    "comment": "Additional information about the issue."
}
```

Comments cannot be added to Closed tickets.

### API Responses

The API returns appropriate HTTP responses for:

- Successful operations
- Invalid input
- Unauthorized access
- Forbidden actions
- Invalid ticket workflow transitions
- Nonexistent ticket IDs

---

## Search and Filters

Ticket lists support:

- Search by ticket title
- Status filter
- Priority filter
- Assignee filter
- Unassigned filter
- Combined search and filters

Employees only search and filter tickets they are allowed to see.

Support users can search and filter all tickets.

---

## Ticket Summary

The dashboards display separate counts for:

- Open
- In Progress
- Resolved
- Closed

Employee summary counts include only tickets visible to that Employee.

Support summary counts include all tickets.

Summary counts are calculated before search and filters are applied.

---

## Comments

Employees can comment only on their own tickets.

Support users can comment on any ticket.

Comments cannot be added to Closed tickets.

Comments are displayed from oldest to newest.

---

## Ticket History

The system records important ticket changes including:

- Assignment
- Reassignment
- Status changes
- Resolution
- Reopening
- Closing

Each history entry contains:

- Actor
- Change type
- Old value
- New value
- Optional note
- Timestamp

History is displayed in chronological order.

Resolution notes and reopen reasons are stored in the history.

---

## Security and Validation

The system includes:

- Password hashing
- Session-based authentication
- Role-based authorization
- Employee ticket ownership checks
- Support-only workflow actions
- Parameterized SQLite queries
- Required title validation
- Required description validation
- Whitespace-only input rejection
- Category validation
- Priority validation
- Required resolution notes
- Required reopen reasons
- Empty comment validation
- Closed ticket restrictions
- Ticket visibility protection

An Employee cannot access another Employee's ticket by manually changing the ticket ID.

---

## Verification and Testing

The application was manually tested during development.

### Authentication and Permissions

- Employee login was tested.
- Support login was tested.
- Employees can view only their own tickets.
- Cross-employee ticket access through the API was rejected.
- Unauthorized Employee attempts to perform Support actions were rejected.

### Ticket Creation

- Employee ticket creation was tested.
- New tickets start with status Open.
- New tickets start Unassigned.
- Default and selected priorities were tested.

### Open → In Progress

- Starting an unassigned ticket was rejected.
- Support assignment was tested.
- Assigned Open tickets can be moved to In Progress.

### In Progress → Resolved

- Resolving without a resolution note was rejected.
- Resolving with a valid resolution note was successful.
- Resolution notes were recorded in ticket history.

### Resolved → In Progress

- Reopening without a reason was rejected.
- Reopening with a valid reason was successful.
- Reopen reasons were recorded in ticket history.
- The assigned Support user remained assigned after reopening.

### Resolved → Closed

- The ticket creator can close their own Resolved ticket.
- Unauthorized status changes were rejected.

### Closed Tickets

- Adding comments to Closed tickets was rejected.
- Closed tickets are treated as read-only.

### Search and Filters

- Search by title was tested.
- Status filtering was tested.
- Priority filtering was tested.
- Assignee filtering was tested.
- Unassigned filtering was tested.
- Combined filters were tested.

### Summary

- Open counts were checked.
- In Progress counts were checked.
- Resolved counts were checked.
- Closed counts were checked.
- Summary counts reflect tickets visible to the current user.

### History

Ticket history was checked for:

- Assignment changes
- Status changes
- Actor
- Timestamp
- Old value
- New value
- Resolution note
- Reopen reason

### Persistence

Persistence was manually tested by restarting the Flask application and confirming that ticket information and history remained stored in SQLite.

### Complete Lifecycle Test

The complete ticket lifecycle was tested:

```text
Open
→ Assigned
→ In Progress
→ Resolved
→ Reopened
→ In Progress
→ Resolved
→ Closed
```

---

## Repeatable Database Setup

The project includes `init_db.py`.

It uses:

```text
CREATE TABLE IF NOT EXISTS
```

to safely create the required tables.

Test users are inserted without creating duplicate usernames.

When the tickets table is empty, sample tickets are automatically inserted across different users and statuses.

This allows a fresh installation to demonstrate:

- Employee permissions
- Support permissions
- Open tickets
- In Progress tickets
- Resolved tickets
- Closed tickets
- Assigned tickets
- Unassigned tickets
- Search
- Filters
- Summary counts

---

## Project Organization

The application is separated into modules:

```text
app.py
auth_routes.py
employee_routes.py
support_routes.py
ticket_routes.py
api_routes.py
database.py
init_db.py
```

Route responsibilities are separated to keep the application easier to read and maintain.

The frontend templates are stored in:

```text
templates/
```

CSS is stored in:

```text
static/css/
```

---

## Technical Choices

### Flask

Flask was chosen because it is lightweight and suitable for a small internal web application.

It provides routing, sessions, templates, request handling, and API development without requiring a large framework.

### SQLite

SQLite was chosen because it provides persistent relational database storage without requiring a separate database server.

It is also simple to initialize and suitable for local execution of this assignment.

### HTML and CSS

HTML and CSS were used to build a simple and usable interface for Employee and Support users.

### Git

Git was used for version control and to maintain project history through commits.

---

## Challenges

The main challenges during development were:

- Implementing role-based permissions
- Protecting Employee ticket ownership
- Enforcing the required ticket workflow
- Implementing assignment and reassignment
- Recording ticket history consistently with ticket changes
- Implementing combined search and filters
- Keeping summary counts independent from search and filters
- Applying the same validation rules to web and API operations

---

## Completion Summary

The project implements the required core functionality:

- Frontend interface
- Backend JSON API
- Persistent SQLite database
- Authentication
- Employee and Support roles
- Test accounts
- Sample ticket data
- Ticket creation
- Ticket details
- Assignment and reassignment
- Required ticket workflow
- Resolution notes
- Reopen reasons
- Comments
- Ticket history
- Search
- Combined filters
- Summary counts
- Backend validation
- Role-based authorization
- Employee ownership protection
- Closed ticket restrictions
- Repeatable database initialization
- Responsive UI

---

## Incomplete Items

None.

---

## Known Issues

No known issues after manual testing.

---

## Assumptions

- Registration and password reset are not implemented because they are not required.
- Ticket editing and deletion after creation are not implemented because they are outside the required scope.
- User management is not implemented because it is outside the required scope.
- Email delivery is not implemented because it is optional.
- Attachments are not implemented because they are optional.
- Real-time updates are not implemented because they are optional.
- SLA functionality is not implemented because it is optional.
- Deployment is not included because local execution is sufficient.

---

## AI Usage

AI tools were used during development for:

- Explaining Flask and SQLite concepts
- Debugging assistance
- Reviewing code and validation
- Reviewing ticket workflow rules
- API testing guidance
- UI and CSS assistance
- Documentation support

AI-generated suggestions were reviewed, understood, tested, and modified before being included in the project.

---

## References

- Flask Documentation
- Python Documentation
- SQLite Documentation
- Werkzeug Documentation