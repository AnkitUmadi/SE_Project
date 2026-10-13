# Student Record System

Software Engineering Mini Project — Team 12, PES University.

A web application to manage student records: departments and sections, courses, enrollment,
attendance, fee status, ESA (exam) registration with eligibility rules, marks, grades, SGPA and result analysis.

## Team
| Name | Role |
|---|---|
| Suhas D | QA Lead, Developer |
| Gowri T N | Test Engineer, Developer |
| Ankit Umadi | Developer (defect triage lead) |
| Sidhant Holla | Product Owner, Developer |

## Tech stack (use ONLY these)
- **Frontend:** React 18 + Vite, React-Bootstrap, React Router, axios — in `frontend/`
- **Backend:** Python 3.10+ with Flask (JSON REST API under `/api`), Flask-Login, Flask-WTF (CSRF) — in `src/`
- **Database:** MySQL 8 via SQLAlchemy (tests use in-memory SQLite)
- **Testing & quality:** pytest, pytest-cov, pylint, black, bandit · Vitest, React Testing Library, ESLint, Prettier, npm audit
- **CI/CD:** GitHub Actions

## Folder structure
```
SE_Project/
├── src/                  # Flask backend (Python)
│   ├── app.py            #   creates the app
│   ├── config.py         #   settings (reads .env)
│   ├── extensions.py     #   database, login, CSRF objects
│   ├── routes/           #   API endpoints (one file per module)
│   ├── services/         #   business rules (eligibility, grading, ...)
│   └── models/           #   database tables
├── tests/
│   ├── unit/             # tests for single functions
│   └── integration/      # tests for API + database together
├── frontend/             # React app
│   └── src/              #   pages, components, api client, tests (*.test.jsx)
├── .github/workflows/    # CI/CD pipeline (added in issue #2)
├── requirements.txt      # Python libraries
├── .env.example          # copy to .env and fill in your MySQL password
└── run.py                # starts the backend
```

## First-time setup (Windows, PowerShell)
You need: Git, Python 3.10+, Node.js 20 or newer, MySQL 8.

```powershell
# 1. Get the code
git clone https://github.com/suhasdstudy123-crypto/SE_Project.git
cd SE_Project

# 2. Backend: create and activate a virtual environment, then install libraries
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Your settings: copy the example and put YOUR MySQL password in .env
copy .env.example .env

# 4. Frontend: install libraries
cd frontend
npm install
cd ..
```
If `Activate.ps1` is blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Create the database once (reads your `.env`, safe to re-run):
```powershell
python scripts/create_db.py
```

Load the shared demo data (1 Admin, 3 Faculty, 30 Students, 2 Departments, 3 Sections, 5 Courses, sample attendance; safe to re-run):
```powershell
python scripts/seed.py
```

Or create an individual login account interactively:
```powershell
python scripts/create_user.py admin@pes.edu "Admin User" admin
```
Roles: `admin`, `faculty`, `student`.

## Running the app (two terminals)
```powershell
# Terminal 1 — backend (http://localhost:5000)
.venv\Scripts\Activate.ps1
python run.py

# Terminal 2 — frontend (http://localhost:5173)
cd frontend
npm run dev
```
Open http://localhost:5173 and log in with the account you created.

## Checks to run before every pull request
```powershell
# Backend
pytest --cov=src                 # tests + coverage (must be >= 80%)
pylint src/                      # code quality (must be >= 7.0)
black src tests                  # auto-format
bandit -r src                    # security scan

# Frontend (inside frontend/)
npm test                         # tests
npm run lint                     # code quality
npm run format                   # auto-format
```

## How we work (Git workflow)
1. Pick your card on the GitHub Project board and move it to **In Progress**.
2. `git checkout main` → `git pull` → `git checkout -b feature/<issue-number>-<short-name>`
3. Write code + tests, run the checks above, commit with a clear message.
4. `git push -u origin <branch>` and open a Pull Request with `Closes #<issue-number>` in the description.
5. A teammate reviews; once CI is green and approved, it is merged. Never push directly to `main`.

## Documents
SRS, SAD and Test Plan will be added to the `docs/` folder.
