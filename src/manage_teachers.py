import argparse
import getpass
import json
import os

from teacher_auth import TEACHERS_FILE, hash_password, load_teachers


def save_teachers(teachers):
    temporary_file = TEACHERS_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps({"teachers": teachers}, indent=2) + "\n", encoding="utf-8"
    )
    os.chmod(temporary_file, 0o600)
    temporary_file.replace(TEACHERS_FILE)


def main():
    parser = argparse.ArgumentParser(description="Manage local teacher login credentials.")
    commands = parser.add_subparsers(dest="command", required=True)
    add_command = commands.add_parser("add", help="Add a teacher login")
    add_command.add_argument("username")
    remove_command = commands.add_parser("remove", help="Remove a teacher login")
    remove_command.add_argument("username")
    args = parser.parse_args()

    teachers = load_teachers()
    if args.command == "add":
        if args.username in teachers:
            parser.error(f"Teacher '{args.username}' already exists.")
        password = getpass.getpass("Teacher password (at least 12 characters): ")
        confirmation = getpass.getpass("Confirm password: ")
        if len(password) < 12:
            parser.error("Password must be at least 12 characters.")
        if password != confirmation:
            parser.error("Passwords do not match.")
        teachers[args.username] = hash_password(password)
        save_teachers(teachers)
        print(f"Added teacher '{args.username}'.")
    elif args.command == "remove":
        if args.username not in teachers:
            parser.error(f"Teacher '{args.username}' was not found.")
        del teachers[args.username]
        save_teachers(teachers)
        print(f"Removed teacher '{args.username}'.")


if __name__ == "__main__":
    main()