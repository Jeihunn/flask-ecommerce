import getpass


def create_superuser():
    from models import User
    from start import app, db
    from werkzeug.security import generate_password_hash

    with app.app_context():
        first_name = input("SuperUser First Name (Super): ").strip() or "Super"
        if first_name.lower().strip() == "exit()":
            print("\n----- create_superuser function exited! -----")
            return

        last_name = input("\nSuperUser Last Name (User): ").strip() or "User"
        if last_name.lower().strip() == "exit()":
            print("\n----- create_superuser function exited! -----")
            return

        while True:
            email = input("\nSuperUser Email: ").strip()
            if email == "":
                print("Please enter a valid email.")
            elif email.lower().strip() == "exit()":
                print("\n----- create_superuser function exited! -----")
                return
            elif User.query.filter_by(email=email).first():
                print("Please enter a different email.")
            else:
                break

        while True:
            print(
                "\n*The password can contain a minimum of 8 and a maximum of 30 characters")
            password = getpass.getpass("SuperUser Password: ")
            if password.lower().strip() == "exit()":
                print("\n----- create_superuser function exited! -----")
                return
            elif len(password) < 8 or len(password) > 30:
                continue

            confirm_password = getpass.getpass("\nConfirm Password: ")
            if confirm_password.lower().strip() == "exit()":
                print("\n----- create_superuser function exited! -----")
                return

            if password == "" or password != confirm_password:
                print("Passwords do not match. Please try again.")
            else:
                break

        superuser = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=generate_password_hash(password),
            is_superuser=True
        )

        print("\n----- Superser created!!! -----")

        with app.app_context():
            db.create_all()
            db.session.add(superuser)
            db.session.commit()

    exit()


COMMANDS = {
    "create_superuser": create_superuser,
}
