from odoo.addons.base.tests.common import BaseCommon


class TestPartner(BaseCommon):
    _test_user_groups = ('base.group_user', 'base.group_partner_manager')

    def test_coordinates_update_only_complete_entries(self):
        partners = self.env['res.partner'].create([
            {'name': 'First location', 'partner_latitude': 1.0},
            {'name': 'Second location', 'partner_latitude': 2.0},
            {'name': 'Unchanged location', 'partner_latitude': 3.0},
        ])
        self.env['res.partner'].update_latitude_longitude([
            {'id': partners[0].id, 'partner_latitude': 16.8, 'partner_longitude': 96.1},
            {'id': partners[1].id, 'partner_latitude': 16.8, 'partner_longitude': 96.1},
            {'id': partners[2].id, 'partner_longitude': 97.0},
        ])
        for partner in partners[:2]:
            self.assertAlmostEqual(partner.partner_latitude, 16.8)
            self.assertAlmostEqual(partner.partner_longitude, 96.1)
        self.assertEqual(partners[2].partner_latitude, 3.0)

    def test_complete_address_recomputes(self):
        partner = self.env['res.partner'].create({'name': 'Location', 'street': 'First Street'})
        self.assertIn('First Street', partner.contact_address_complete)
        partner.street = 'Second Street'
        self.assertIn('Second Street', partner.contact_address_complete)
        self.assertNotIn('First Street', partner.contact_address_complete)
