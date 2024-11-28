from flask import Flask, render_template, redirect, flash, url_for, abort, request
import os
import yaml
from utils import *
from uuid import uuid4
from functools import wraps

app = Flask(__name__)
app.secret_key = '*T2<3>g;=E1Kc+N;^GP='

CONTACTS_DIR_STRUCTURE = ('contacts', 'data')
CONTACTS_DIR_STRUCTURE_TEST =  ('tests', 'data')
CONTACTS_FILE_NAME = 'contacts.yaml'

def get_contacts_file_path():
    root_dir = os.path.abspath(os.path.dirname(__name__))
    if app.config['TESTING']:
        file_path = os.path.join(root_dir,
                                 *CONTACTS_DIR_STRUCTURE_TEST,
                                 CONTACTS_FILE_NAME)
    else:
        file_path = os.path.join(root_dir,
                                 *CONTACTS_DIR_STRUCTURE,
                                 CONTACTS_FILE_NAME)
    return file_path

def load_contacts():
    file_path = get_contacts_file_path()
    try:
        with open(file_path, 'r') as file:
            contacts = yaml.safe_load(file)
            return contacts if contacts else []
    except FileNotFoundError:
            return None

def erorrs_in_contact_data(form_data):
    validation_callbacks = {
        'first_name': errors_for_first_name,
        'phone_number': errors_for_phone_num,
        'email_address': errors_for_email_addr,
    }
    errors = []
    for attribute_name, validation_callback in validation_callbacks.items():
        attribute_value = form_data.get(attribute_name)
        errors.extend(validation_callback(attribute_value))

    return errors if errors else None

def get_clean_contact_data(form_data):
    attributes = (
        'first_name',
        'middle_names',
        'last_name',
        'phone_number',
        'email_address',
    )

    contact_data = {attribute: form_data.get(attribute) for attribute in attributes}
    contact_data = {
        key: value.strip() if value and not value.isspace() else None
        for key, value in contact_data.items()
    }

    return contact_data

def update_contacts(contacts):
    with open(get_contacts_file_path(), 'w') as file:
        yaml.dump(contacts, file)

def requires_contacts(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        contacts = load_contacts()
        if contacts is None:
            abort(500, description = 'Problem with loading contacts. Please try again later')
        else:
            result = func(contacts=contacts, *args, **kwargs)
            return result
    return wrapper

def requires_contact(func):
    @wraps(func)
    @requires_contacts
    def wrapper(contacts, *args, **kwargs):
        contact_id = kwargs.get('contact_id')
        contact = get_contact_by_id(contact_id, contacts)

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

@app.route('/contacts/<contact_id>')
@requires_contact
def view_contact(contacts, contact, contact_id):
    contact['full_name'] = get_full_name(contact)
    return render_template('contact_details.html', contact=contact)

@app.route('/contacts/new')
def new_contact():
    return render_template('create_contact.html')

@app.route('/contacts', methods=["POST"])
@requires_contacts
def create_contact(contacts):
    errors = erorrs_in_contact_data(request.form)
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('create_contact.html'), 422

    contact = get_clean_contact_data(request.form) | {'id':str(uuid4())}

    contacts = load_contacts()
    contacts.append(contact)
    update_contacts(contacts)

    flash(f'{get_full_name(contact)} has been added to your contacts', 'success')
    return redirect(url_for('view_contact', contact_id=contact['id']))

@app.route('/contacts/<contact_id>/edit', methods=['GET', 'POST'])
@requires_contact
def edit_contact(contacts, contact, contact_id):
    if request.method == 'GET':
        if contact:
            return render_template('edit_contact.html', contact=contact, form_data=None)

    elif request.method == 'POST':
        errors = erorrs_in_contact_data(request.form)
        if errors:
            for error in errors:
                flash(error, 'error')
            contact = {'id': contact['id']} | request.form
            return render_template('edit_contact.html', contact=contact), 422

        updated_data = {'id':contact['id']} | get_clean_contact_data(request.form)

        for existing_contact in contacts:
            if existing_contact['id'] == contact_id:
                existing_contact.update(updated_data)

        update_contacts(contacts)

        flash(f'{get_full_name(updated_data)} has been updated.', 'success')
        return redirect(url_for('view_contact', contact_id=contact['id']))


@app.route('/contacts/<contact_id>/delete', methods=['POST'])
@requires_contact
def delete_contact(contacts, contact, contact_id):
    contacts.remove(contact)
    update_contacts(contacts)

    flash('The contact has been deleted', 'success')
    return redirect(url_for('home'))

# Creating a filter that will display empty strings when non-mandatory
# fields are null in the data storage
def display_optional_value(value):
    return value if value is not None else ''

app.jinja_env.filters['optional_value'] = display_optional_value

if __name__ == '__main__':
    app.run(debug=True, port=5008)
