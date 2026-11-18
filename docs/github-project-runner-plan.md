# GitHub Project task runner plan

## Requested behavior

Execute tasks from a GitHub Project in `IdeaCodeAcademy/fde_odoo_automation`.
Only tasks in `Ready` are eligible. After a task is claimed and its runner
starts, change it to `In progress` and send a start notification to the
configured Telegram channel using a bot. Move review-ready results to
`In review`. Return work that cannot be completed to `Backlog`, recording a
specific reason and any partial work.

This document is a plan. No live task execution, status changes, or Telegram
messages have been performed.

## Confirmed configuration

- GitHub organization: `IdeaCodeAcademy`; Project number: `2`.
- Board: https://github.com/orgs/IdeaCodeAcademy/projects/2/views/1
- Start mode: automatically claim eligible `Ready` tasks when a worker is free.
- Telegram destination: the private channel/group supplied by the user. Its
  invite link is intentionally excluded from this public repository. Resolve
  the numeric chat ID after the bot is added with posting permission; an invite
  link cannot be used as the Bot API `chat_id`.
- Execution repository: `IdeaCodeAcademy/fde_odoo_automation`, base `20.0-DEV`.
- Selected Cloud environment: `fde_odoo_automation`, runnable configuration
  `672217d4-e5da-433e-b461-f4233e553d52~asenvcfg_a6515f1bce5c81918fb06e63cc0378da`.
  Recheck availability before dispatch. The saved repository ref is currently
  `main`; each execution must explicitly use `20.0-DEV` as its task base.
- Initial proposal: one worker, one active task, poll every 60 seconds. These
  concurrency and timing defaults remain adjustable.

## Proposed execution

1. A Python dispatcher reads all pages of project items and resolves the
   configured Status field and exact option IDs. Fail configuration validation
   if any required status is missing; never create or guess statuses silently.
2. Initially accept issue-backed tasks linked to the configured repository.
   Draft items or tasks for other repositories need explicit mapping before
   execution. Read the issue description and acceptance criteria.
3. Claim one eligible task using a durable run record and a unique active-task
   constraint. Recheck `Ready` immediately before starting. Store project item,
   issue, run ID, branch, base commit, timestamps, heartbeat and progress.
4. Start a Codex CLI worker in an isolated checkout based on the latest
   `20.0-DEV`. One active task per worker. Confirm startup, then synchronize
   `In progress` to GitHub and enqueue the Telegram start message. If status
   synchronization fails, pause code execution and retry synchronization.
5. Implement the task, following AGENTS.md, Odoo Git conventions and unit-test
   requirements. Run appropriate local tests, commit and push a feature branch,
   and open a PR targeting `20.0-DEV`. Record the PR and exact commit revision.
6. Wait for required CI on that revision. On a fixable failure, revise within
   a configured attempt/time budget. After tests pass and the requested scope
   is complete, publish a review summary and set `In review`. This does not
   merge the PR or deploy anything. Existing protected-branch checks remain.
7. If blocked, canceled, timed out, or unable to finish within the budget,
   preserve logs/partial commits, record the reason and return to `Backlog`.
   Do not automatically reselect Backlog tasks. A human must move them to Ready.

## Reliability and recovery

- Persist run state in PostgreSQL, separate from GitHub's displayed status.
  Use a dedicated runner database, not a user's Odoo business database.
- Poll automatically for Ready tasks; a persistent host runs the dispatcher
  and worker. Host selection remains pending.
- Use a lease and heartbeat to detect crashed workers. Check existing branches,
  PRs and run records before resuming; do not start duplicate runs.
- Persist GitHub updates and Telegram notifications in an outbox with bounded
  exponential retries. Telegram outages must not discard task history or
  rerun code work. Delivery retries can produce a duplicate after an ambiguous
  timeout; include run IDs for identification.
- Human status changes take precedence: stop and reconcile rather than blindly
  overwriting a task moved out of In Progress during execution.
- Log task state transitions and external delivery results. Exclude credentials
  and redact bot-token URLs. Store ECC summaries after meaningful work; retain
  repository documentation as the canonical configuration and behavior source.

## Telegram start notification

Include task title/number, issue URL, repository, run ID, worker, branch and
start time (Asia/Yangon). The bot must have posting permission in the chosen
channel. Notify the Telegram group about task starts, plans/progress, code milestones,
commits/pushes, tests/CI results, PR/review readiness, errors and Backlog reasons.
Include task/run links; never send secrets. Delivery uses the retry outbox.

When no task is active, send an idle heartbeat once every hour, 24 hours a day
(user confirmed). Include verified runner/queue health, the last successful
check and next check time in Asia/Yangon. Never report "online" or "no Ready
tasks" when runtime/project checks failed; send the actual unavailable state.
The verified destination is the Telegram group "Odoo Development with vibe
coding", chat ID `-5188855137`, using `@ica_vibe_coding_bot`.

The user selected Codex Cloud execution. Cloud dispatch and an hourly cloud
scheduler still need verified integration; a local desktop automation does not
fulfill this requirement. No live recurring schedule has been enabled.

## Configuration needed before live enablement

- Resolve Project #2's GraphQL node ID, Status field ID and option IDs.
- Runner host, Codex CLI authentication and repository credentials.
- Project read/write permission plus repository branch/PR permissions, ideally
  through a scoped GitHub App or dedicated credential. Local gh project read/write authorization completed on 2026-11-18;
  live preflight succeeded. Cloud-runtime credentials still need provisioning.
  For the local CLI credential, `gh auth refresh -s project` requests project
  read/write authorization; an account owner must complete GitHub authorization.
- Telegram channel username/chat ID and bot token supplied through local secret
  configuration or a secret manager, never committed or pasted into task text.
- Run timeout, revision budget and polling interval.

## Delivery and validation

1. Implement state storage, task claiming and configurable GitHub status adapter.
2. Add supervised Codex execution and isolated branch/checkout lifecycle.
3. Add PR/CI tracking and Telegram outbox delivery.
4. Test successful review, test failure/revision, blocked task, duplicate claim,
   worker crash, API outage, Telegram retry and human status override scenarios.
5. Validate against a designated test issue and channel before enabling ongoing
   automatic intake. Use the existing PR and CI process for implementation.

References:

- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects
- https://core.telegram.org/bots/api#sendmessage
