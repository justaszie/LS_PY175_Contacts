from flask import Flask, render_template, redirect, flash, url_for, abort, request, g
# from contacts.file_storage import ContactsFileStorage, DataHandlingError
from contacts.db_storage import ContactsDatabaseStorage, DataHandlingError
import os
import secrets
import yaml
from utils import *
from uuid import uuid4
from functools import wraps
from werkzeug.exceptions import InternalServerError, HTTPException

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
# '*T2<3>g;=E1Kc+N;^GP='

# CONTACTS_DIR_STRUCTURE = ('contacts', 'data')
# CONTACTS_DIR_STRUCTURE_TEST =  ('tests', 'data')
# CONTACTS_FILE_NAME = 'contacts.yaml'

# def get_contacts_file_path():
#     root_dir = os.path.abspath(os.path.dirname(__name__))
#     if app.config['TESTING']:
#         file_path = os.path.join(root_dir,
#                                  *CONTACTS_DIR_STRUCTURE_TEST,
#                                  CONTACTS_FILE_NAME)
#     else:
#         file_path = os.path.join(root_dir,
#                                  *CONTACTS_DIR_STRUCTURE,
#                                  CONTACTS_FILE_NAME)
#     return file_path

# def load_contacts():
#     file_path = get_contacts_file_path()
#     try:
#         with open(file_path, 'r') as file:
#             contacts = yaml.safe_load(file)
#             return contacts if contacts else []
#     except FileNotFoundError:
#             raise InternalServerError('Problem while loading contacts. Try again later')

def errors_in_contact_data(form_data):
    # error_checkers = {
    #     'first_name': errors_for_first_name,
    #     'phone_number_1': errors_for_phone_num,
    #     'phone_number_1_type': errors_for_phone_num,
    #     'email_address': errors_for_email_addr,
    # }
    error_checkers = {
        errors_for_first_name: ('first_name', ),
        errors_for_email_addr: ('email_address', ),
        errors_for_phone_num: (
            'phone_number_1',
            'phone_number_2',
            'phone_number_3'
        ),
        # To make it simpler, we rely on DB check for the phone type value.
        # It's very unlikely that the type will be wrong if the form
        # is submitted ia UI

        # errors_for_phone_num_type: (
        #     'phone_number_1_type',
        #     'phone_number_2_type',
        #     'phone_number_3_type'
        # )
    }
    errors = []
    # TODO - if multiple attrs, run checker for each
    for error_checker, attributes,  in error_checkers.items():
        for attribute_name in attributes:
            attribute_value = form_data.get(attribute_name)
            attribute_errors = error_checker(attribute_value)
            errors.extend(attribute_errors)

    return errors if errors else None

def get_phone_nums_from_form(form_data):
    phone_nums = []
    phone_num_attributes = (
        ('phone_number_1', 'phone_number_1_type', 'phone_number_1_id'),
        ('phone_number_2', 'phone_number_2_type', 'phone_number_2_id'),
        ('phone_number_3', 'phone_number_3_type', 'phone_number_3_id'),
    )
    for value_attr, type_attr, id_attr in phone_num_attributes:
        value = form_data.get(value_attr)
        type = form_data.get(type_attr)
        id = form_data.get(id_attr)
        # if value and not value.isspace():
        phone_nums.append({
            'number_value': value,
            'number_type': type.lower(),
            'id': id
        })

    return phone_nums

def get_contact_data_from_form(form_data):
    attributes = (
        'first_name',
        'middle_names',
        'last_name',
        'email_address',
    )

    contact_data = {attribute: form_data.get(attribute) for attribute in attributes}
    contact_data = {
        key: value.strip() if value and not value.isspace() else None
        for key, value in contact_data.items()
    }

    contact_data['phone_numbers'] = get_phone_nums_from_form(form_data)

    return contact_data

# def update_contacts(contacts):
#     with open(get_contacts_file_path(), 'w') as file:
#         yaml.dump(contacts, file)

@app.before_request
def load_storage():
    is_testing_env = app.config.get('TESTING', False)
    g.storage = ContactsDatabaseStorage(is_testing_env)

@app.teardown_appcontext
def close_storage(exception=None):
    if hasattr(g, 'storage'):
        g.storage.close_connection()

def requires_contacts(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # TODO - replace to use g.storage
            contacts = g.storage.get_all_contacts()
        except DataHandlingError as e:
            abort(500, description="Problem while loading contacts. Try again later")
        result = func(contacts=contacts, *args, **kwargs)
        return result
    return wrapper

def requires_contact(func):
    @wraps(func)
    @requires_contacts
    def wrapper(contacts, *args, **kwargs):
        contact_id = kwargs.get('contact_id')
        # contact = get_contact_by_id(contact_id, contacts)
        contact = g.storage.find_contact_by_id(contact_id)

        if contact is None:
            flash('Contact not found.', 'error')
            return redirect(url_for('home'))

        result = func(contacts=contacts, contact=contact, *args, **kwargs)
        return result
    return wrapper


@app.route('/')
@requires_contacts
def home(contacts):
    add_full_name(contacts)
    contacts = [ {'id': contact['id'], 'full_name': contact['full_name']} for contact in contacts ]
    return render_template('contact_list.html', contacts=contacts)

@app.route('/contacts/<int:contact_id>')
@requires_contact
def view_contact(contacts, contact, contact_id):
    contact['full_name'] = get_full_name(contact)
    # For now, the number of phone numbers is fixed to 3 in the app.
    # So we only take 3 first results from the storage
    phone_numbers = g.storage.get_phone_numbers(contact_id)[:3]
    return render_template('contact_details.html', contact=contact, phone_numbers=phone_numbers)

@app.route('/contacts/new')
def new_contact():
    return render_template('create_contact.html')

@app.route('/contacts', methods=["POST"])
# @requires_contacts
def create_contact():
    errors = errors_in_contact_data(request.form)
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('create_contact.html'), 422

    # contact = get_clean_contact_data(request.form) | {'id':str(uuid4())}
    contact = get_contact_data_from_form(request.form)
    new_id = g.storage.create_new_contact(**contact)

    # contacts = load_contacts()
    # contacts.append(contact)
    # update_contacts(contacts)

    flash(f'{get_full_name(contact)} has been added to your contacts', 'success')
    return redirect(url_for('view_contact', contact_id=new_id))

@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@requires_contact
def edit_contact(contacts, contact, contact_id):
    if request.method == 'GET':
        phone_numbers_data = g.storage.get_phone_numbers(contact_id)

        # We only support 3 phone numbers in the frontend.
        # If there are less than 3 phone numbers in the database,
        # We populate the remaining fields with default data

        phone_numbers = [
            phone_numbers_data[i] if len(phone_numbers_data) > i
            else default_phone_number_data()
            for i in range(3)
        ]

        return render_template('edit_contact.html', contact=contact, phone_numbers=phone_numbers)

    elif request.method == 'POST':
        errors = errors_in_contact_data(request.form)
        if errors:
            for error in errors:
                flash(error, 'error')

            contact = {'id': contact['id']} | request.form
            phone_numbers = get_phone_nums_from_form(request.form)

            return render_template('edit_contact.html', contact=contact, phone_numbers=phone_numbers), 422

        # updated_data = {'id':contact['id']} | get_clean_contact_data(request.form)
        updated_data = get_contact_data_from_form(request.form)

        g.storage.update_one_contact(contact_id, **updated_data)

        # update_contacts(contacts)

        flash(f'{get_full_name(updated_data)} has been updated.', 'success')
        return redirect(url_for('view_contact', contact_id=contact_id))


@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
@requires_contact
def delete_contact(contacts, contact, contact_id):
    g.storage.delete_one_contact(contact_id)
    # contacts.remove(contact)
    # update_contacts(contacts)

    flash('The contact has been deleted', 'success')
    return redirect(url_for('home'))

@app.route('/test')
def test_view():
    pass

# Creating a filter that will display empty strings when non-mandatory
# fields are null in the data storage
def display_optional_value(value):
    return value if value is not None else ''

app.jinja_env.filters['optional_value'] = display_optional_value

if __name__ == '__main__':
    app.run(debug=True, port=5008)
