# API reference

The development server listens at `http://127.0.0.1:8000`. API paths end with a slash. Examples assume `python manage.py seed_demo` has run on a fresh database.

## Authentication

Public reads require no login. Authenticated users who are not staff have the same page visibility as anonymous visitors and cannot write.

Staff can authenticate with a Django session or HTTP Basic authentication. Sign in at `/admin/` to use a session with the browsable API. Session writes require a CSRF token.

For local command line requests, pass a username to curl and enter the password when prompted:

```bash
curl -u editor http://127.0.0.1:8000/api/sites/main/pages/
```

`editor` must be an existing staff account. The demo command does not create one. You can use the account created by `createsuperuser` instead. Basic authentication is suitable here for localhost examples; use HTTPS when credentials travel over a network.

Django REST Framework's default authenticator order puts sessions first. With this configuration, denied anonymous writes and denied authenticated reader writes return 403.

## Page fields

| Field | Type | Write behavior |
| :--- | :--- | :--- |
| `slug` | String, up to 50 characters | Required on creation; unique within the selected site |
| `title` | String, up to 200 characters | Required on creation |
| `body` | String | Optional; defaults to an empty string |
| `published` | Boolean | Optional; defaults to false |
| `updated_at` | Timestamp | Read only; updated by Django on save |

The serialized response contains these five fields. It does not expose the database ID or site ID. Unrecognized input fields, including `site`, are ignored by the serializer. The current configuration uses Django's default slug validation.

## List pages

```http
GET /api/sites/main/pages/
```

Returns 200 with a JSON array ordered by slug. Anonymous users and authenticated readers see only published pages. Staff see drafts as well. A site with no visible pages returns `[]`; an unknown site returns 404.

There is no pagination, search, or client selected ordering.

## Read one page

```http
GET /api/sites/main/pages/hello/
```

Returns 200 with a page object. An unknown site, unknown page, or draft hidden from the current user returns 404.

## Create a page

Staff only:

```http
POST /api/sites/main/pages/
Content-Type: application/json

{
  "slug": "about",
  "title": "About",
  "body": "A short introduction.",
  "published": false
}
```

Returns 201 with the created page. For a portable curl example, save the JSON body above in a local `page.json` file:

```bash
curl -u editor -H "Content-Type: application/json" --data-binary @page.json http://127.0.0.1:8000/api/sites/main/pages/
```

Use `curl.exe` in Windows PowerShell. Do not put passwords in example files or commit them to the repository.

The page is assigned to `main` by the view. A duplicate slug in that site returns 400:

```json
{
  "slug": [
    "A page with this slug already exists on this site."
  ]
}
```

The same slug in a different site is valid.

## Update a page

Staff only. PATCH changes supplied fields:

```http
PATCH /api/sites/main/pages/about/
Content-Type: application/json

{
  "published": true
}
```

PUT requires the required page fields, including slug and title. Both methods return 200 with the saved page. The site assignment cannot change through either method. Renaming the slug changes the detail URL and is subject to the same uniqueness rule as creation.

## Delete a page

Staff only:

```bash
curl -u editor -X DELETE http://127.0.0.1:8000/api/sites/main/pages/about/
```

Returns 204 with no response body. Pages in other sites are unaffected.

## Other methods and errors

HEAD and OPTIONS are available without authentication. Unsupported methods return 405. Field validation failures return 400. Session writes without a valid CSRF token return 403.

The database also enforces slug uniqueness. Serializer validation does not eliminate races between simultaneous writes; a concurrent collision can still raise a database error. This project does not include a concurrent write conflict handler.
