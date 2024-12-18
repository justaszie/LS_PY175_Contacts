import unittest
from app import app
import os
import yaml
from utils import get_full_name
from contacts.db_storage import ContactsDatabaseStorage

class ContactsAppTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True
        self.set_up_test_storage()

    def set_up_test_storage(self):
        # Setting up the directory and empty file for the contacts data
        # root_dir = os.path.abspath(os.path.dirname(__name__))
        # data_dir = os.path.join(root_dir, 'tests', 'data')
        # os.makedirs(data_dir, exist_ok=True)

        # self.contacts_file_path = os.path.join(data_dir, 'contacts.yaml')
        self.storage = ContactsDatabaseStorage(is_testing_environment=True)

    def contact_not_found_response(self, response):
        self.assertEqual(response.status_code, 302)
        follow_response = self.client.get(response.headers.get('Location'))
        self.assertIn('not found', follow_response.get_data(as_text=True))

    # def create_test_data(self, test_data):
    #     for contact in test_data:
    #         self.storage.create_new_contact(**contact)
        # with open(self.contacts_file_path, 'w') as file:
        #     yaml.dump(test_data, file)

    # ---- CONTACT LIST TESTS ------
    def test_contact_list_success(self):
        test_data = [
            {
                # 'id': '733809ee-a80c-4b30-aa0d-07d34320a44c',
                'first_name': 'Lilly',
                'middle_names': 'Elizabeth',
                'last_name': 'Martinez',
                'phone_number': '5696934238',
                'email_address': 'l.martinez@example.com'
            },
            {
                # 'id': '556d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name': 'John',
                'middle_names': 'Stefanie',
                'last_name': 'Miller',
                'phone_number': '8544089059',
                'email_address': 'j.miller@example.com'
            },
        ]
        for test_contact in test_data:
            self.storage.create_new_contact(**test_contact)
        # self.create_test_data(test_data)

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

    # TODO - rethink about how to tests 500 errors
    @unittest.skip
    def test_contact_list_problem_loading_contacts(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 500)

    # ---- CONTACT DETAILS TESTS ------
    def test_contact_details_success(self):
        test_contact = {
                'first_name': 'Lilly',
                'middle_names': 'Elizabeth',
                'last_name': 'Martinez',
                'phone_number': '5696934238',
                'email_address': 'l.martinez@example.com'
            }

        new_id = self.storage.create_new_contact(**test_contact)

        response = self.client.get(f'/contacts/{new_id}')

        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)

        attributes = [value for value in list(test_contact.values())]
        for attribute in attributes:
            self.assertIn(attribute.lower(), data.lower())

        for actions in ('Edit', 'Delete'):
            self.assertIn(actions, data)

    # TODO - think about handling the IDs of wrong format
    @unittest.skip
    def test_contact_details_not_found(self):
        # self.create_test_data([])
        response = self.client.get('/contacts/bad_id')
        self.contact_not_found_response(response)

    # TODO - rethink about how to tests 500 errors
    @unittest.skip
    def test_contact_details_problem_loading_contacts(self):
        # Contacts file doesn't exist in this case
        response = self.client.get('/contacts/any_id')
        self.assertEqual(response.status_code, 500)

    # ---- CREATE CONTACT TESTS ------
    def test_create_contact_success(self):
        # self.create_test_data([])
        test_contacts = [{
                'first_name': 'John',
                'middle_names': 'C',
                'last_name': 'Miller',
                'phone_number': '8544189059',
                'email_address': 'cmiller@example.com'
            },
            {
                'first_name': 'John',
                'email_address': 'j.cmiller@example.gov.nz'
            },
            {
                'first_name': 'John Doe',
                'email_address': 'j.cmiller@example.gov.nz'
            },
        ]
        for test_contact in test_contacts:
            response = self.client.post('/contacts',
                                        data=test_contact,
                                        follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('has been added to your contacts', response.get_data(as_text=True))
            self.assertIn(get_full_name(test_contact), response.get_data(as_text=True))

    def test_create_contact_bad_phone(self):
        # self.create_test_data([])
        test_contact =  {
                'first_name': 'John',
                'phone_number': '111',
            }
        response = self.client.post('/contacts', data=test_contact)
        self.assertEqual(response.status_code, 422)
        self.assertIn('6 digits', response.get_data(as_text=True))

        test_contact =  {
                'first_name': 'John',
                'phone_number': '1234abcd1',
            }
        response = self.client.post('/contacts', data=test_contact)
        self.assertEqual(response.status_code, 422)
        self.assertIn('digits only', response.get_data(as_text=True))

    def test_create_contact_bad_email(self):
        # self.create_test_data([])
        invalid_values = ('aasd2.com', 'aaaaa@ccccc', 'john', 'katy@katy@katy', '@something.co.uk', 'example@example..gv')
        test_contacts = [
            {
                'first_name' : 'John Doe',
                'email_address': invalid_value
            }
            for invalid_value in invalid_values
        ]
        for test_contact in test_contacts:
            response = self.client.post('/contacts',
                                        data=test_contact,
                                        follow_redirects=True)
            self.assertEqual(response.status_code, 422)
            self.assertIn('Email address is not valid', response.get_data(as_text=True))

    def test_create_contact_first_name_error(self):
        # 1. First name is required
        # self.create_test_data([])
        test_contacts = [{
            'first_name' : ' ',
            'email_address': 'whatever'
            },
            {}
        ]
        for test_contact in test_contacts:
            response = self.client.post('/contacts',
                                        data=test_contact,
                                        follow_redirects=True)
            self.assertEqual(response.status_code, 422)
            self.assertIn('First name is required', response.get_data(as_text=True))

        # 1. First name must be >= 2 letters
        test_contact = {
            'first_name' : 'a',
            }
        response = self.client.post('/contacts',
                                        data=test_contact,
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 422)
        self.assertIn('must be at least 2 letters', response.get_data(as_text=True))

    # ---- DELETE CONTACT TESTS ------
    def test_delete_option_available(self):
        test_contact = {
                # 'id': '556d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name': 'John',
                'middle_names': 'C',
                'last_name': 'Miller',
                'phone_number': '8544189059',
                'email_address': 'cmiller@example.com',
            }
        new_id = self.storage.create_new_contact(**test_contact)
        response = self.client.get('/')
        self.assertIn(f'action="/contacts/{new_id}/delete"', response.get_data(as_text=True))

        response = self.client.get(f'/contacts/{new_id}')
        self.assertIn(f'action="/contacts/{new_id}/delete"', response.get_data(as_text=True))

    def test_delete_success(self):
        test_data = [
             {
                # 'id': '556d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name': 'John',
                'middle_names': 'C',
                'last_name': 'Miller',
                'phone_number': '8544189059',
                'email_address': 'cmiller@example.com',
            }
            ,{
                # 'id' : 'abc123',
                'first_name': 'john',
            }
        ]

        test_id_to_delete, test_id_to_remain = [
            self.storage.create_new_contact(**test_contact)
            for test_contact in test_data
        ]

        response = self.client.post(f'/contacts/{test_id_to_delete}/delete',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(f'/contacts/{test_id_to_delete}', response.get_data(as_text=True))
        self.assertIn(f'{test_id_to_remain}', response.get_data(as_text=True))

    # TODO - think about handling the IDs of wrong format
    @unittest.skip
    def test_delete_contact_not_found(self):
        self.create_test_data([{'id' : 'abc123', 'first_name': 'john',}])

        response = self.client.post('/contacts/123someid/delete')
        self.contact_not_found_response(response)

    # TODO - rethink about how to tests 500 errors
    @unittest.skip
    def test_delete_contact_problem_loading_contacts(self):
        # Contacts file doesn't exist in this case
        response = self.client.post('/contacts/any_id/delete')
        self.assertEqual(response.status_code, 500)

    # ---- EDIT CONTACT TESTS ------
    def test_edit_contact_available(self):
        test_contact =  {
            # 'id':'abc123',
            'first_name': 'john',
        }
        new_id = self.storage.create_new_contact(**test_contact)

        response = self.client.get('/')
        self.assertIn(f'href="/contacts/{new_id}/edit"', response.get_data(as_text=True))

        response = self.client.get(f'/contacts/{new_id}')
        self.assertIn(f'href="/contacts/{new_id}/edit"', response.get_data(as_text=True))

    def test_edit_contact_form_displayed(self):
        test_contact = {
                # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name': 'John',
                'last_name': 'Miller',
                'phone_number': '8544189059',
                'email_address': 'cmiller@example.com',
            }
        # self.create_test_data([test_contact])
        new_id = self.storage.create_new_contact(**test_contact)

        response = self.client.get(f'/contacts/{new_id}/edit')
        data = response.get_data(as_text=True)
        self.assertIn('<form', data)
        self.assertIn(f'action="/contacts/{new_id}/edit"', data)
        for attribute in test_contact.values():
            self.assertIn(attribute, data)

    def test_edit_contact_success(self):
        test_contact = {
            # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
            'first_name': 'John',
            'middle_names' : 'Jr.',
            'last_name': 'Miller',
            'phone_number': '8544189059',
            'email_address': 'cmiller@example.com',
        }
        # self.create_test_data([test_contact])
        new_id = self.storage.create_new_contact(**test_contact)

        updated_contact = {
            # 'id': new_id,
            'first_name': 'Johnny',
            'last_name': 'Smith',
            'phone_number': '12345667',
            'email_address': 'jsmith@example.com',
        }

        response = self.client.post(
            f'/contacts/{new_id}/edit',
            data=updated_contact,
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn(f'Details for {get_full_name(updated_contact)}', data)
        for attribute in updated_contact.values():
            self.assertIn(attribute, data)

    def test_edit_contact_bad_phone(self):
        test_contact = {
             # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
            'first_name': 'John',
            'phone_number': '11111111',
        }
        # self.create_test_data([test_contact])
        new_id = self.storage.create_new_contact(**test_contact)

        updated_contact = {
                # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
                'phone_number': '111',
        }
        response = self.client.post(
            f'/contacts/{new_id}/edit',
            data=updated_contact)

        self.assertEqual(response.status_code, 422)
        self.assertIn('6 digits', response.get_data(as_text=True))

        updated_contact = {
                # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
                'phone_number': '1123aaaaa555',
        }

        response = self.client.post(
            f'/contacts/{new_id}/edit',
            data=updated_contact)

        self.assertEqual(response.status_code, 422)
        self.assertIn('digits only', response.get_data(as_text=True))

    def test_edit_contact_bad_email(self):
        test_contact = {
                # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name': 'John',
                'email_address': 'john@john.com',
            }

        new_id = self.storage.create_new_contact(**test_contact)

        invalid_values = ('aasd2.com', 'aaaaa@ccccc', 'john', 'katy@katy@katy', '@something.co.uk', 'example@example..gv')
        test_updated_contacts = [
            {
                # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
                'email_address': invalid_value,
            }
            for invalid_value in invalid_values
        ]

        for updated_contact in test_updated_contacts:
            response = self.client.post(
                f'/contacts/{new_id}/edit',
                data=updated_contact)

            self.assertEqual(response.status_code, 422)
            self.assertIn('Email address is not valid', response.get_data(as_text=True))

    def test_edit_contact_first_name_error(self):
        test_contact = {
                # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name': 'John',
                'email_address': 'john@john.com',
            }

        new_id = self.storage.create_new_contact(**test_contact)

        test_updated_contacts = [
            {
                # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
                'first_name' : ' ',},
            {

            }
        ]

        for updated_contact in test_updated_contacts:
            response = self.client.post(
                f'/contacts/{new_id}/edit',
                data=updated_contact)

            self.assertEqual(response.status_code, 422)
            self.assertIn('First name is required', response.get_data(as_text=True))

        updated_contact = {
            # 'id': '56d2de4-49c3-43d4-b46a-6872627fde88',
            'first_name' : 'a',
            }
        response = self.client.post(
            f'/contacts/{new_id}/edit',
                                        data=updated_contact,
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 422)
        self.assertIn('must be at least 2 letters', response.get_data(as_text=True))

    # TODO think about handling the IDs of wrong format
    @unittest.skip
    def test_edit_contact_not_found(self):
        self.create_test_data([{'id' : 'abc123', 'first_name': 'john',}])

        response = self.client.get('/contacts/123someid/edit')
        self.contact_not_found_response(response)

        response = self.client.post(
            '/contacts/123someid/edit',
            data={'id':'1213', 'first_name': 'aaa'}
        )
        self.contact_not_found_response(response)


    # TODO - rethink about how to tests 500 errors
    @unittest.skip
    def test_edit_contact_problem_loading_contacts(self):
        # Contacts file doesn't exist in this case
        response = self.client.get('/contacts/123someid/edit')
        self.assertEqual(response.status_code, 500)

        response = self.client.post(
            '/contacts/123someid/edit',
            data={'id':'1213', 'first_name': 'aaa'}
        )
        self.assertEqual(response.status_code, 500)


    def tearDown(self):
        # Call storage.destroy_data()
        self.storage.destroy_data()
        self.storage.close_connection()

if __name__ == '__main__':
    unittest.main()