"""Preflight and truthful queue heartbeat; does not dispatch Cloud work."""
import argparse
from datetime import datetime
import json
import os
from zoneinfo import ZoneInfo

from .integrations import GitHubProject, IntegrationError, Telegram, eligible_items


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preflight', 'heartbeat'])
    parser.add_argument('--send', action='store_true', help='Deliver heartbeat to Telegram')
    args = parser.parse_args()
    project = GitHubProject()
    try:
        config = project.configuration()
        items = project.items(config['project_id'])
        ready = eligible_items(items)
        active = sum((i.get('fieldValueByName') or {}).get('name') == 'In progress'
                     and (i.get('content') or {}).get('repository', {}).get('nameWithOwner')
                     == 'IdeaCodeAcademy/fde_odoo_automation' for i in items)
        message = (f'FDE queue check: {len(ready)} Ready; {active} In Progress. '
                   'Cloud runner health is not verified by this check.')
    except (IntegrationError, OSError, TimeoutError, ValueError):
        # Do not forward exception details which may contain credentials or URLs.
        message = 'FDE queue check unavailable. Check GitHub authorization/connectivity. Runner health unknown.'
        if args.command == 'preflight':
            raise SystemExit(message) from None
        config = None
    message += '\nChecked: ' + datetime.now(ZoneInfo('Asia/Yangon')).isoformat(timespec='seconds')
    if args.send:
        if args.command != 'heartbeat':
            parser.error('--send is only valid with heartbeat')
        Telegram(os.environ.get('TELEGRAM_BOT_TOKEN'), os.environ.get('TELEGRAM_CHAT_ID', '-5188855137')).send(message)
    print(json.dumps({'project': config, 'message': message, 'sent': args.send}))


if __name__ == '__main__':
    main()
