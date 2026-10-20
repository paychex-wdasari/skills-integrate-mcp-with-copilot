# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- View activity participants
- Teachers can sign students up or unregister them after logging in

## Teacher Access

Teacher credentials are stored in `src/teachers.json`. Passwords are salted and
hashed; plaintext passwords are never written to the file. From the repository
root, create a teacher account with:

```sh
python src/manage_teachers.py add teacher-username
```

The command prompts for the password twice. Remove an account with:

```sh
python src/manage_teachers.py remove teacher-username
```

Set `TEACHER_SESSION_SECRET` to a stable, high-entropy value when deploying so
sessions remain valid across server restarts and workers. Generate one with
`python -c "import secrets; print(secrets.token_urlsafe(32))"`. Set
`COOKIE_SECURE=true` when serving the site over HTTPS. For local development,
the secure-cookie setting can remain unset.

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| GET    | `/auth/me`                                                        | Check whether the current browser has a teacher session              |
| POST   | `/auth/login`                                                     | Log a teacher in using a JSON username and password                  |
| POST   | `/auth/logout`                                                    | End the current teacher session                                      |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only student signup                                         |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only unregister                                              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
