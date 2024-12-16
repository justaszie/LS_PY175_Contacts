import os
import yaml
from uuid import uuid4

CONTACTS_DIR_STRUCTURE = ('contacts', 'data')
CONTACTS_DIR_STRUCTURE_TEST =  ('tests', 'data')

CONTACTS_FILE_NAME = 'contacts.yaml'

class DataHandlingError(Exception):
    def __init__(self, message):
        super().__init__(message)

class ContactsFileStorage:
    def __init__(self, is_testing_environment=False):
        root_dir = os.path.abspath(os.path.dirname(__name__))
        if is_testing_environment:
            self._file_path = os.path.join(root_dir,
                                 *CONTACTS_DIR_STRUCTURE_TEST,
                                 CONTACTS_FILE_NAME)
        else:
            self._file_path = os.path.join(root_dir,
                                 *CONTACTS_DIR_STRUCTURE,
                                 CONTACTS_FILE_NAME)

    def _load_all_contacts(self):
        try:
            with open(self._file_path, 'r') as file:
                contacts = yaml.safe_load(file)
            return contacts if contacts else []
        except FileNotFoundError:
            raise DataHandlingError('File not found')

    def get_all_contacts(self):
        contacts = self._load_all_contacts()
        return contacts

    def _overwrite_contacts(self, contacts):
        try:
            with open(self._file_path, 'w') as file:
                yaml.dump(contacts, file)
        except FileNotFoundError:
            raise DataHandlingError('File not found')

    def find_contact_by_id(self, contact_id):
        contacts = self._load_all_contacts()
        if not contacts:
            return None
        return next((contact for contact in contacts if contact['id'] == contact_id), None)

    @staticmethod
    def _contact_as_dict(first_name, middle_names, last_name,
                       phone_number, email_address):
        contact = {}
        contact['first_name'] = first_name
        contact['middle_names'] = middle_names
        contact['last_name'] = last_name
        contact['phone_number'] = phone_number
        contact['email_address'] = email_address

        return contact

    def update_one_contact(self, contact_id, first_name, middle_names,
                       last_name, phone_number, email_address):

        updated_contact_data = ContactsFileStorage._contact_as_dict(
            first_name, middle_names, last_name, phone_number, email_address
        )

        all_contacts = self._load_all_contacts()
        for existing_contact in all_contacts:
            if existing_contact['id'] == contact_id:
                existing_contact.update(updated_contact_data)

        self._overwrite_contacts(all_contacts)


    def delete_one_contact(self, contact_id):
        all_contacts = self._load_all_contacts()
        all_contacts = [
            contact for contact in all_contacts
            if contact['id'] != contact_id
        ]
        self._overwrite_contacts(all_contacts)

    def create_new_contact(self, first_name, middle_names, last_name,
                       phone_number, email_address):

        new_contact = ContactsFileStorage._contact_as_dict(
            first_name, middle_names, last_name, phone_number, email_address
        )
        new_contact['id'] = str(uuid4())

        all_contacts = self._load_all_contacts()
        all_contacts.append(new_contact)
        self._overwrite_contacts(all_contacts)

        return new_contact['id']




