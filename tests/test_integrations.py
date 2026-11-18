import io
import json
import unittest
from unittest.mock import patch
import urllib.error
import subprocess

from automation.integrations import GitHubProject, IntegrationError, Telegram, eligible_items


class ProjectTests(unittest.TestCase):
    def test_github_timeout_is_sanitized(self):
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('sensitive-args', 60)):
            with self.assertRaises(IntegrationError) as caught:
                GitHubProject().query('query{}')
            self.assertNotIn('sensitive', str(caught.exception))

    def test_only_open_ready_issues_for_target_repo(self):
        good = {'id': 'item', 'fieldValueByName': {'name': 'Ready'}, 'content': {
            'state': 'OPEN', 'repository': {'nameWithOwner': 'IdeaCodeAcademy/fde_odoo_automation'}}}
        other_repo = {**good, 'content': {**good['content'], 'repository': {'nameWithOwner': 'other/repo'}}}
        closed = {**good, 'content': {**good['content'], 'state': 'CLOSED'}}
        self.assertEqual(eligible_items([good, other_repo, closed, {'content': None}]), [good])

    def test_pagination_keeps_all_items(self):
        project = GitHubProject()
        def page(items, more, cursor):
            return {'node': {'items': {'nodes': items, 'pageInfo': {'hasNextPage': more, 'endCursor': cursor}}}}
        with patch.object(project, 'query', side_effect=[page([{'id': 'a'}], True, 'next'), page([{'id': 'b'}], False, None)]) as query:
            self.assertEqual(project.items('project'), [{'id': 'a'}, {'id': 'b'}])
            self.assertEqual(query.call_args.kwargs['after'], 'next')

    def test_status_change_refuses_foreign_item(self):
        project = GitHubProject()
        with patch.object(project, 'items', return_value=[]), patch.object(project, 'query') as query:
            with self.assertRaises(IntegrationError):
                project.set_status({'project_id': 'p'}, 'foreign', 'In progress')
            query.assert_not_called()

    def test_missing_status_rejected(self):
        data = {'organization': {'projectV2': {'id': 'p', 'fields': {
            'nodes': [{'id': 'f', 'name': 'Status', 'options': [{'name': 'Ready', 'id': 'r'}]}],
            'pageInfo': {'hasNextPage': False}}}}}
        with patch.object(GitHubProject, 'query', return_value=data):
            with self.assertRaises(IntegrationError):
                GitHubProject().configuration()


class TelegramTests(unittest.TestCase):
    def test_success_returns_message_id(self):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps({'ok': True, 'result': {'message_id': 3}}).encode())):
            self.assertEqual(Telegram('test-placeholder').send('test'), 3)

    def test_permanent_error_not_retried_or_leaked(self):
        error = urllib.error.HTTPError('secret-url', 403, 'secret-token', {}, None)
        with patch('urllib.request.urlopen', side_effect=error) as request:
            with self.assertRaisesRegex(IntegrationError, 'HTTP 403') as caught:
                Telegram('test-placeholder').send('test')
            self.assertNotIn('secret', str(caught.exception))
            self.assertEqual(request.call_count, 1)

    def test_transient_failure_retried(self):
        success = io.BytesIO(b'{"ok":true,"result":{"message_id":4}}')
        with patch('urllib.request.urlopen', side_effect=[urllib.error.URLError('private'), success]):
            self.assertEqual(Telegram('test-placeholder', sleep=lambda _: None).send('test'), 4)

    def test_delivery_failure_is_bounded(self):
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('private')) as request:
            with self.assertRaisesRegex(IntegrationError, 'after retries'):
                Telegram('test-placeholder', sleep=lambda _: None).send('test')
            self.assertEqual(request.call_count, 3)


if __name__ == '__main__':
    unittest.main()
