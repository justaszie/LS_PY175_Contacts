import random
from uuid import uuid4
import re

def get_full_name(contact):
    first_name = contact['first_name']
    middle_names = contact.get('middle_names', '')
    last_name = contact.get('last_name', '')
    return ' '.join(
        (first_name,
         middle_names if middle_names else '',
         last_name if last_name else '')).rstrip()

def default_phone_number_data():
    return {
        'number_value': '',
        'number_type': 'personal',
        'id': None
    }

def add_full_name(contacts):
    if contacts is not None:
        for contact in contacts:
            contact['full_name'] = get_full_name(contact)

def get_contact_by_id(contact_id, contacts):
    if not contacts:
        return None
    return next((contact for contact in contacts if contact['id'] == contact_id), None)

def create_random_contact():
    names = ('John', 'Matthew', 'Kelly', 'Ronald', 'Alice', 'Michael', 'Lilly', 'Robert', 'Stefanie', 'Ryan', 'Elizabeth')
    last_names = ("Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Taylor")

    first_name = random.choice(names)
    middle_names = random.choice(names)
    last_name = random.choice(last_names)
    phone_num = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    email_address = f'{first_name[:1]}.{last_name}@example.com'.lower()
    contact_uuid = str(uuid4())
    return {
        'id': contact_uuid,
        'first_name': first_name,
        'middle_names': middle_names,
        'last_name': last_name,
        'phone_number': phone_num,
        'email_address': email_address,
    }

def errors_for_first_name(first_name):
    first_name = first_name.strip() if first_name else None

    if not first_name:
        return ['First name is required']

    if len(first_name) < 2:
        return ['First name must be at least 2 letters']

    return []

def errors_for_phone_num(phone_number):
    phone_number = phone_number.strip() if phone_number else None

    if not phone_number:
        return []

    errors = []

    if not phone_number.isdigit():
        errors.append('Phone numbers must be digits only')
    if len(phone_number) < 6:
        errors.append('Phone numbers must be at least 6 digits')

    return errors

# def errors_for_phone_num_type(phone_number_type):
#     errors = []
#     phone_number_type = phone_number_type.strip() if phone_number_type else None

#     if not phone_number_type:
#         return []

#     errors = []

def errors_for_email_addr(email_address):
    email_address = email_address.strip() if email_address else None

    if not email_address:
        return []

    email_pattern = r'^[a-z0-9\.]+@[a-z0-9]+(\.[a-z0-9]+)+$'
    if not re.search(email_pattern, email_address, flags=re.IGNORECASE):
        return ['Email address is not valid. Expected format: someaddr@example.com']

    return []