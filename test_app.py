import unittest
from app import app
import os
import yaml

class ContactsAppTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

        root_dir = os.path.abspath(os.path.dirname(__name__))
        data_dir = os.path.join(root_dir, 'tests', 'data')
        os.makedirs(data_dir, exist_ok=True)

        self.file_path = os.path.join(data_dir, 'contacts.yaml')

    def test_contact_list(self):
        test_data = [
            {
                'id': '733809ee-a80c-4b30-aa0d-07d34320a44c',
                'first_name': 'Lilly',
                'middle_names': 'Elizabeth',
                'last_name': 'Martinez',
                'phone_number': '5696934238',
                'email_address': 'l.martinez@example.com'
            },
            {
                'id': '556d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name': 'John',
                'middle_names': 'Stefanie',
                'last_name': 'Miller',
                'phone_number': '8544089059',
                'email_address': 'j.miller@example.com'
            },
        ]
        with open(self.file_path, 'w') as file:
            yaml.dump(test_data, file)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)

        # All contacts are displayed
        for test_contact in test_data:
            self.assertIn(test_contact['first_name'], data)
            self.assertIn(test_contact['last_name'], data)

        # The CTAs are available
        for content in ('Delete', '+ New Contact', 'Edit', '<button'):
            self.assertIn(content, data)


    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()