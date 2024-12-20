import psycopg2
from psycopg2.extras import DictCursor
from textwrap import dedent
from functools import wraps

class DataHandlingError(Exception):
    def __init__(self, message):
        super().__init__(message)


### Decorators do not work on instance methods:
def db_transaction(cursor_type=None):
    def query_decorator(meth):
        @wraps(meth)
        def wrapper(self, *args, **kwargs):
            with self.connection:
                # cursor_type = DictCursor
                cursor = (
                    self.connection.cursor(cursor_factory=cursor_type)
                    if cursor_type
                    else self.connection.cursor()
                )

                with cursor:
                    result = meth(self, cursor, *args, **kwargs)
                    return result
        return wrapper
    return query_decorator

class ContactsDatabaseStorage:
    def __init__(self, is_testing_environment):
        db_name = ('contact_list' if not is_testing_environment
                   else 'test_contact_list')

        self.connection = psycopg2.connect(f'dbname={db_name}')
        self.setup_schema()

    @db_transaction()
    def setup_schema(self, cursor):

        cursor.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'contacts'
            """
        )
        if cursor.rowcount < 1:
            cursor.execute(
                r"""
                CREATE TABLE contacts (
                    id SERIAL PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    middle_names TEXT,
                    last_name TEXT,
                    email_address TEXT,
                    CHECK(position('@' in email_address) > 0)
                )
                """
            )

        cursor.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'phone_numbers'
            """
        )
        if cursor.rowcount < 1:
            cursor.execute(
                """
                CREATE TYPE phone_number_type
                AS ENUM ('personal', 'home', 'work', 'other')
                """
            )
            cursor.execute(
                """
                CREATE TABLE phone_numbers(
                    id SERIAL PRIMARY KEY,
                    number_value TEXT NOT NULL,
                    number_type phone_number_type NOT NULL,
                    contact_id INT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
                    CHECK(LENGTH(number_value) >= 6),
                    CHECK(number_value SIMILAR TO '\d{6,}')
                )
                """
            )

    @db_transaction()
    def destroy_data(self, cursor):
        cursor.execute('DELETE FROM contacts')

    @db_transaction(DictCursor)
    def _load_all_contacts(self, cursor):
        # with self.connection:
        #     with self.connection.cursor(cursor_factory=DictCursor) as cursor:
        query = 'SELECT * FROM contacts'
        cursor.execute(query)
        results = cursor.fetchall()

        return results

    def get_all_contacts(self):
        # Converting contact rows from DictRow to simple dict
        # so that we can update those objects later in the app
        contacts = [dict(contact) for contact in self._load_all_contacts()]
        return contacts

    @db_transaction(DictCursor)
    def find_contact_by_id(self, cursor, contact_id):
        # with self.connection:
        #     with self.connection.cursor(cursor_factory=DictCursor) as cursor:
        query = dedent(
            """
            SELECT *
            FROM contacts
            WHERE id = %s
            """
        )
        cursor.execute(query, (contact_id, ))
        contact = dict(cursor.fetchone())
        return contact

    @db_transaction()
    def delete_one_contact(self, cursor, contact_id):
        # with self.connection:
        #     with self.connection.cursor() as cursor:
        query = dedent(
            """
            DELETE
            FROM contacts
            WHERE id = %s
            """
        )
        cursor.execute(query, (contact_id, ))

    def close_connection(self):
        self.connection.close()

    def _update_contact_details(
        self, cursor, contact_id,first_name,
        middle_names, last_name, email_address):

        query = dedent(
            """
            UPDATE contacts
            SET
                first_name = %s,
                middle_names = %s,
                last_name = %s,
                email_address = %s
            WHERE id = %s
            """
        )
        params = (
            first_name, middle_names,
            last_name,
            email_address, contact_id
        )

        cursor.execute(query, params)


    # Updating a contact is a transaction.
    # All the sub_queries composing the update are
    # pat the same transaction. 1 sub-query fails = txn fails
    @db_transaction()
    def update_one_contact(
        self,
        cursor,
        contact_id,
        first_name,
        middle_names,
        last_name,
        email_address,
        phone_numbers
    ):
        # Update basic contact details
        self._update_contact_details(cursor, contact_id, first_name,
                                     middle_names,last_name, email_address)

        # Update phone numbers based on input data
        for phone_number in phone_numbers:
            # Existing phone number
            if phone_number['id']:
                # Existing phone number should be updated
                if phone_number['number_value']:
                    self._update_phone_number(
                        cursor,
                        contact_id,
                        int(phone_number['id']),
                        phone_number['number_value'],
                        phone_number['number_type']
                    )
                # Existing phone number was deleted
                else:
                    self._delete_phone_number(cursor, contact_id, int(phone_number['id']))
            # There is no existing number but value was entered:
            # add new number
            elif phone_number['number_value']:
                self._add_phone_number(
                    cursor,
                    contact_id,
                    phone_number['number_value'],
                    phone_number['number_type']
                )


    def _delete_phone_number(self, cursor, contact_id, number_id):
        query = dedent(
            """
            DELETE FROM phone_numbers
            WHERE id = %s and contact_id = %s
            """
        )
        params = (
           number_id,
           contact_id
        )
        cursor.execute(query, params)

    def _update_phone_number(self, cursor, contact_id, number_id, number_value, number_type):
        query = dedent(
            """
            UPDATE phone_numbers
            SET number_value = %s,
                number_type = %s
            WHERE id = %s and contact_id = %s
            """
        )
        params = (
           number_value,
           number_type,
           number_id,
           contact_id
        )
        cursor.execute(query, params)

    def _add_phone_number(self, cursor, contact_id, number_value, number_type):
        query = dedent(
            """
            INSERT INTO phone_numbers(
                number_value,
                number_type,
                contact_id
            )
            VALUES (%s, %s, %s)
            """
        )
        params = (
           number_value,
           number_type,
           contact_id
        )
        cursor.execute(query, params)


    @db_transaction()
    def create_new_contact(
        self,
        cursor,
        first_name,
        middle_names=None,
        last_name=None,
        email_address=None,
        phone_numbers=None
    ):
        # with self.connection:
        #     with self.connection.cursor(cursor_factory=DictCursor) as cursor:
        query = dedent(
            """
            INSERT INTO contacts(
                first_name,
                middle_names,
                last_name,
                email_address
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
        )

        params = (first_name, middle_names, last_name, email_address)
        cursor.execute(query, params)

        created_contact_id = cursor.fetchone()[0]

        for phone_num in phone_numbers:
            if phone_num['number_value'].strip():
                self._add_phone_number(
                    cursor,
                    created_contact_id,
                    phone_num['number_value'],
                    phone_num['number_type']
                )

        # Returning the ID of the new contact so that the app
        # can redirect to the details of the contact
        return created_contact_id

    @db_transaction(DictCursor)
    def get_phone_numbers(self, cursor, contact_id):
        query = dedent(
            """
            SELECT *
            FROM phone_numbers
            WHERE contact_id = %s
            """
        )
        cursor.execute(query, (contact_id, ))
        return [dict(row) for row in cursor.fetchall()]
