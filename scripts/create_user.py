"""Create a login account on your own laptop (until the seed script from issue #4 exists).

Usage (from the SE_Project folder, with the venv active):
    python scripts/create_user.py admin@pes.edu "Admin User" admin
It then asks for the password (typing is hidden).
Roles: admin, faculty, student
"""

import getpass
import os
import sys

# Let Python find the src package when this file is run as "python scripts/create_user.py"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from src.app import create_app
from src.models.user import Role, User
from src.services.auth_service import create_user


def main():
    """Read email, name and role from the command line, ask for a password, save the user."""
    if len(sys.argv) != 4 or sys.argv[3] not in Role.ALL:
        sys.exit(__doc__)
    email, name, role = sys.argv[1], sys.argv[2], sys.argv[3]

    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email.strip().lower()).first():
            sys.exit(f"A user with email {email} already exists.")
        password = getpass.getpass("Password (min 8 characters): ")
        if len(password) < 8:
            sys.exit("Password too short.")
        user = create_user(email, name, password, role)
        print(f"Created {user.role} account: {user.email}")


if __name__ == "__main__":
    main()
