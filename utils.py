import random
from uuid import uuid4

def get_full_name(contact):
    return ' '.join(
        (contact['first_name'],
         contact['middle_names'],
         contact['last_name']))


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

