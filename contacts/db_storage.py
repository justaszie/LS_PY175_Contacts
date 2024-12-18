import psycopg2
from psycopg2.extras import DictCursor
from textwrap import dedent
from functools import wraps

class DataHandlingError(Exception):
    def __init__(self, message):
        super().__init__(message)


### Decorators do not work on instance methods:
def db_query(cursor_type=None):
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

    @db_query()
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
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    middle_names TEXT,
                    last_name TEXT,
                    phone_number TEXT,
                    email_address TEXT,
                    CHECK(LENGTH(phone_number) >= 6),
                    CHECK(phone_number SIMILAR TO '\d{6,}'),
                    CHECK(position('@' in email_address) > 0)
                )
                """
            )


    @db_query()
    def destroy_data(self, cursor):
        cursor.execute('DELETE FROM contacts')

    @db_query(DictCursor)
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

    @db_query(DictCursor)
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

    @db_query()
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

    @db_query()
    def update_one_contact(
        self,
        cursor,
        contact_id,
        first_name,
        middle_names,
        last_name,
        phone_number,
        email_address
    ):
        # with self.connection:
        #     with self.connection.cursor(cursor_factory=DictCursor) as cursor:
        query = dedent(
            """
            UPDATE contacts
            SET
                first_name = %s,
                middle_names = %s,
                last_name = %s,
                phone_number = %s,
                email_address = %s
            WHERE id = %s
            """
        )
        params = (
            first_name, middle_names,
            last_name, phone_number,
            email_address, contact_id
        )

        cursor.execute(query, params)

    @db_query()
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

        query = dedent(
            """
            INSERT INTO phone_numbers(number_value, number_type, contact_id)
            VALUES (%s, %s, %s)
            """
        )
        for phone_num in phone_numbers:
            params = (
                phone_num['number_value'],
                phone_num['number_type'],
                created_contact_id,
            )
            cursor.execute(query, params)

        # Returning the ID of the new contact so that the app
        # can redirect to the details of the contact
        return created_contact_id

