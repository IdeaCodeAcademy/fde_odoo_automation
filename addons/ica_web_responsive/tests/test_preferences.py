from odoo.addons.base.tests.common import BaseCommon


class TestPreferences(BaseCommon):
    def test_user_can_save_theme_preference(self):
        user = self.env.user
        for scheme in ('dark', 'light', 'system'):
            user.write({'color_scheme': scheme})
            self.assertEqual(user.color_scheme, scheme)
            self.assertEqual(user.res_users_settings_id.color_scheme, scheme)

    def test_empty_theme_preserves_saved_preference(self):
        settings = self.env.user.res_users_settings_id
        settings.write({'color_scheme': 'dark'})
        settings.write({'color_scheme': False})
        self.assertEqual(settings.color_scheme, 'dark')
