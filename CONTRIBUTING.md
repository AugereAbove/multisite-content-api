# Contributing

Keep the request path and permission rules easy to follow. A useful change explains an observable problem and includes a focused check for the resulting behavior.

## Setup

Use Python 3.10 or newer in a virtual environment. From the repository root:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
```

## Before opening a pull request

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

For a model change, create and commit the migration with `python manage.py makemigrations`. Do not edit the initial migration to hide a schema change after it has been published.

For container changes, also run:

```bash
docker build -t multisite-content-api .
docker run --rm multisite-content-api python manage.py check
docker run --rm multisite-content-api python manage.py test
```

## Expectations

Preserve site filtering on every read and write. Permission changes need checks for anonymous readers, authenticated readers, and staff. Keep example credentials out of commits. Do not commit local SQLite databases, virtual environments, or archives.

Use clear names and ordinary Python control flow. Source files use no comments or docstrings; longer explanations belong in `docs/design.md`. Keep required syntax, including hyphens in commands and configuration.

Describe the problem, resulting behavior, and verification in the pull request. Update the API reference when request fields, response fields, or status codes change.

## Bug reports

Include your Python version, operating system, exact request or command, expected result, and actual response or traceback. Remove passwords, cookies, authorization headers, and private content before posting.
