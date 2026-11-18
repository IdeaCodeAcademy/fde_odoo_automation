# FDE Odoo Automation

Odoo 20.0 Community development environment. Development branch: `20.0-DEV`.
Uses the official `odoo:20.0` image and PostgreSQL 17.

## Start

Docker Desktop with Compose is required.

```sh
cp .env.example .env
cp config/odoo.conf.example config/odoo.conf
```

Set a local PostgreSQL password in `.env` and a database manager master password
(`admin_passwd`) in `config/odoo.conf` before starting. Both files are ignored by Git.
For the initial local setup these files have already been generated with random passwords.

```sh
docker compose up -d
```

Open http://localhost:8069 and create a development database. Use `admin_passwd`
from `config/odoo.conf` as the master password; choose your own admin email and password.
Set `ODOO_PORT` in `.env` if port 8069 is occupied.

## Development

Put custom modules in `addons/`. The directory is mounted into Odoo and development
reload is enabled. Restart after adding modules, then update the Apps list with developer mode enabled.

```sh
docker compose logs -f web
docker compose restart web
docker compose exec web odoo --version
docker compose stop
```

Upgrade a custom module while the web server is stopped (replace placeholders):

```sh
docker compose stop web
docker compose run --rm web odoo -d DATABASE -u MODULE --stop-after-init --no-http
docker compose up -d web
```

Database and filestore persist in Docker volumes. `docker compose down` preserves
them; `docker compose down -v` permanently deletes this project's data.
PostgreSQL is accessible only within the Compose network; HTTP is bound to localhost.

References: [official Docker image](https://hub.docker.com/_/odoo),
[Odoo 20 source requirements](https://www.odoo.com/documentation/20.0/administration/on_premise/source.html).
