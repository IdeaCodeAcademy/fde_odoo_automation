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

## Contributions and CI

Follow [Odoo 20.0 Git guidelines](https://www.odoo.com/documentation/20.0/contributing/development/git_guidelines.html)
and the repository rules in `AGENTS.md`. Example new-module commit:
`[ADD] module_name: explain the purpose` with a body explaining why it is needed.

Open feature pull requests against `20.0-DEV`. GitHub Actions runs
`Odoo 20.0 unit tests` on every such PR, on pushes to the development branch,
and on manual dispatch. No path filter skips documentation-only PRs.
All installable modules under `addons/` are installed into a fresh PostgreSQL
database and their standard Odoo Python tests run. Modules must include
`tests/test_*.py` imported by `tests/__init__.py`; test failures fail CI.
Until custom modules exist, an Odoo base unit-test smoke suite runs instead.
Logs are uploaded as a workflow artifact, including on failure.

To enforce passing CI before merging, configure the branch protection/ruleset
for `20.0-DEV` to require the `Odoo 20.0 unit tests` status check.

Project context and verified work summaries are saved using ECC unified-memory.
Local project memory lives in `.ecc/memory/project/` and is ignored by Git;
`AGENTS.md` and this README retain shared project rules and instructions.

## GitHub Project automation

See [the task runner plan](docs/github-project-runner-plan.md) and
[integration setup/current limits](docs/automation-setup.md). Project preflight
and Telegram adapter helpers are available; automatic Cloud dispatch and the
hourly scheduler are not enabled. Run `python3 -m automation preflight` to
check Project #2 access without starting or modifying tasks.
