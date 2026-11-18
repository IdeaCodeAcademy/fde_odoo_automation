# Automation integration setup and current limits

The selected execution environment is the runnable `fde_odoo_automation`
Codex Cloud configuration, not a local Codex worker. See
`github-project-runner-plan.md` for the requested full flow.

## Implemented helpers

```sh
python3 -m automation preflight
python3 -m automation heartbeat
python3 -m unittest discover -s tests -v
```

Preflight reads Project #2's Status options and paginates all items. Eligible
items are open issues for `IdeaCodeAcademy/fde_odoo_automation` in Ready.
Draft items and other repositories are excluded. Actual board labels are
`Backlog`, `Ready`, `In progress`, `In review`, and `Done`.

The `GitHubProject.set_status` adapter validates project membership before
changing status. It is not automatically invoked by preflight or heartbeat.
No task execution or claiming is implemented yet.

Heartbeat defaults to a preview. To send it, provide `TELEGRAM_BOT_TOKEN`
through secret configuration, optionally override `TELEGRAM_CHAT_ID`, and run:

```sh
python3 -m automation heartbeat --send
```

The default destination is group `-5188855137` (Odoo Development with vibe
coding), bot `@ica_vibe_coding_bot`. Do not put credentials in command arguments,
Git, ECC memory or logs. The Telegram adapter retries transient failures up to
three times, handles rate limits, and sanitizes failures. There is no durable
outbox yet. Retry after a network timeout may duplicate a delivered message.
Messages report queue checks, not unverified Cloud runner health.

## Cloud skills setup

`scripts/install-cloud-tools.sh` is a prepared replacement for the environment's
earlier inline setup script. It discovers every `*/SKILL.md` under the configured
Odoo checkout; it does not assume there are exactly five skills. Newly added
skills are copied on the next setup execution. Existing differing skills are
preserved and require review instead of being overwritten. ECC is refreshed
through the native marketplace/plugin lifecycle, with Codex-owned hook trust.

Once this change is merged and the environment's main project checkout includes
it, configure the Environment install script to run:

```sh
bash /workspace/fde_odoo_automation/scripts/install-cloud-tools.sh
```

Keep the Odoo and ECC checkouts configured at `/workspace/odoo` and
`/workspace/ecc`. Save/publish the environment and verify a new task sees the
skills. The script has local behavior tests and shell syntax validation; it has
not been executed in Cloud or applied to the published environment from this
chat. The environment's old onboarding history was inspected to identify the
fixed-five check; its current saved install script is not exposed by available
tools, so it may have changed since onboarding.

This does not poll remote repositories or change configured commit revisions.
A skill added upstream becomes available only after the configured checkout is
updated and setup runs again, before a new Codex session discovers skills.

## Verified access

Local GitHub project read/write authorization was completed on 2026-11-18.
Preflight successfully read project `PVT_kwDOCSs9Us4BsL8h`, Status field
`PVTSSF_lADOCSs9Us4BsL8hzhqbONA`. Credentials on a future Cloud/scheduled
runtime must be configured separately; local authorization does not provision
Cloud secrets. Telegram testing delivery was verified with a transient token.
The token has not been saved in this repository.

## Pending before live enablement

- A supported Cloud dispatcher and scheduler. Although desktop lists the saved
  configuration as runnable, local `codex cloud list --env ...` returned
  `no cloud environments are available for this workspace` on 2026-11-18.
  Do not assume desktop configuration IDs are accepted by that CLI.
- A scheduled runtime with GitHub and Telegram credentials and network access.
  No hourly schedule was created and no local schedule was substituted.
- Durable task claims, supervised execution, PR/CI tracking, recoverable state
  transitions and notification outbox. The adapter helpers alone do not provide
  these features.

The requested hourly ping and task progress messages remain planned. Never
label the system online or the queue empty when its checks are unavailable.
