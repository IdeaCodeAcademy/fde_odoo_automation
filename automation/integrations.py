"""External adapters. Credentials are supplied by environment, never logged."""
import json
import subprocess
import time
import urllib.error
import urllib.request


STATUSES = ('Backlog', 'Ready', 'In progress', 'In review')


class IntegrationError(RuntimeError):
    pass


class GitHubProject:
    def __init__(self, owner='IdeaCodeAcademy', number=2):
        self.owner = owner
        self.number = number

    def query(self, query, **variables):
        args = ['gh', 'api', 'graphql', '-f', f'query={query}']
        for key, value in variables.items():
            args += ['-F' if isinstance(value, int) else '-f', f'{key}={value}']
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            raise IntegrationError('GitHub client unavailable or request timed out') from None
        if result.returncode:
            raise IntegrationError('GitHub request failed; check project permission and connectivity')
        payload = json.loads(result.stdout)
        if payload.get('errors'):
            raise IntegrationError('GitHub GraphQL request returned errors')
        return payload['data']

    def configuration(self):
        data = self.query('''query($owner:String!,$number:Int!){
          organization(login:$owner){projectV2(number:$number){id
            fields(first:100){nodes{... on ProjectV2SingleSelectField{
              id name options{id name}
            }} pageInfo{hasNextPage}}}}}''', owner=self.owner, number=self.number)
        project = (data.get('organization') or {}).get('projectV2')
        if not project:
            raise IntegrationError('Project is unavailable')
        if project['fields']['pageInfo']['hasNextPage']:
            raise IntegrationError('Project field list truncated; refuse incomplete configuration')
        fields = [f for f in project['fields']['nodes'] if f.get('name') == 'Status']
        if len(fields) != 1:
            raise IntegrationError('Expected exactly one Status field')
        field = fields[0]
        options = {option['name']: option['id'] for option in field['options']}
        if any(status not in options for status in STATUSES):
            raise IntegrationError('Missing required Status options')
        return {'project_id': project['id'], 'field_id': field['id'], 'options': options}

    def items(self, project_id):
        cursor = None
        items = []
        while True:
            variables = {'id': project_id}
            if cursor:
                variables['after'] = cursor
            data = self.query('''query($id:ID!,$after:String){node(id:$id){
              ... on ProjectV2{items(first:100,after:$after){nodes{id
                fieldValueByName(name:"Status"){
                  ... on ProjectV2ItemFieldSingleSelectValue{name}}
                content{... on Issue{id title url number body state
                  repository{nameWithOwner}}}}
                pageInfo{hasNextPage endCursor}}}}}''', **variables)
            node = data.get('node')
            if not node or 'items' not in node:
                raise IntegrationError('Project items unavailable')
            page = node['items']
            items.extend(page['nodes'])
            info = page['pageInfo']
            if not info['hasNextPage']:
                return items
            if not info['endCursor'] or info['endCursor'] == cursor:
                raise IntegrationError('Invalid Project pagination cursor')
            cursor = info['endCursor']

    def set_status(self, config, item_id, status):
        if status not in STATUSES:
            raise ValueError('Unsupported task status')
        # Verify membership before mutation; IDs from another board are refused.
        if item_id not in {item['id'] for item in self.items(config['project_id'])}:
            raise IntegrationError('Item does not belong to the configured project')
        self.query('''mutation($project:ID!,$item:ID!,$field:ID!,$option:String!){
          updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,
            fieldId:$field,value:{singleSelectOptionId:$option}}){projectV2Item{id}}}''',
            project=config['project_id'], item=item_id, field=config['field_id'],
            option=config['options'][status])


def eligible_items(items, repository='IdeaCodeAcademy/fde_odoo_automation'):
    return [item for item in items
            if (item.get('fieldValueByName') or {}).get('name') == 'Ready'
            and (item.get('content') or {}).get('state') == 'OPEN'
            and (item.get('content') or {}).get('repository', {}).get('nameWithOwner') == repository]


class Telegram:
    def __init__(self, token, chat_id='-5188855137', attempts=3, sleep=time.sleep):
        if not token:
            raise IntegrationError('TELEGRAM_BOT_TOKEN is not configured')
        self.token, self.chat_id = token, chat_id
        self.attempts, self.sleep = attempts, sleep

    def send(self, text):
        if not text or len(text) > 4096:
            raise ValueError('Telegram text must contain 1 to 4096 characters')
        payload = json.dumps({'chat_id': self.chat_id, 'text': text}).encode()
        for attempt in range(self.attempts):
            delay = 2 ** attempt
            request = urllib.request.Request(
                'https://api.telegram.org/bot' + self.token + '/sendMessage',
                data=payload, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    result = json.load(response)
                if not result.get('ok'):
                    raise IntegrationError('Telegram rejected the message')
                return result['result']['message_id']
            except urllib.error.HTTPError as error:
                if error.code != 429 and error.code < 500:
                    raise IntegrationError(f'Telegram request rejected (HTTP {error.code})') from None
                if error.code == 429:
                    try:
                        delay = min(60, int(json.load(error).get('parameters', {}).get('retry_after', delay)))
                    except (ValueError, TypeError):
                        pass
            except (urllib.error.URLError, TimeoutError):
                pass
            if attempt + 1 < self.attempts:
                self.sleep(delay)
        raise IntegrationError('Telegram delivery failed after retries; delivery may be ambiguous')
