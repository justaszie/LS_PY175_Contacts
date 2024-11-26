from flask import Flask, render_template, redirect, flash, url_for, abort, request
import os
import yaml
from utils import *
from uuid import uuid4

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
    first_name = form_data.get('first_name')
    phone_number = form_data.get('phone_number')
    email_address = form_data.get('email_address')

    # error_checkers = {
    #     'first_name':
    # }'error_for_first_name', 'error_for_phone_num', 'error_for_email_addr')
    # errors = [error_checker() for error_checker in error_checkers]

    errors = []
    error = error_for_first_name(first_name)
    if error:
        errors.append(error)

    phone_errors = errors_for_phone_num(phone_number)
    if phone_errors:
        errors.extend(phone_errors)

    error = error_for_email_addr(email_address)
    if error:
        errors.append(error)

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
        key: value.strip() if value else None
        for key, value in contact_data.items()
    }

    # first_name =
    # middle_names = form_data.get('middle_names')
    # last_name = form_data.get('last_name')
    # phone_number = form_data.get('phone_number')
    # email_address = form_data.get('email_address')

    # first_name = first_name.strip()
    # middle_names = middle_names.strip() if middle_names else None
    # last_name = last_name.strip() if last_name else None
    # phone_number = phone_number.strip() if phone_number else None
    # email_address = email_address.strip() if email_address else None

    # contact = {
    #         'first_name': first_name,
    #         'middle_names': middle_names,
    #         'last_name': last_name,
    #         'phone_number': phone_number,
    #         'email_address': email_address
    #     }

    return contact_data

    # 1. Store dict keys: first_name, middle_names, etc., in a tuple
    # 2. Iterate through the keys And assign data from the form as value for each key
    # 3. Iterare through dict items, strip value if it's not None, else None
    # 4. Return the dict


@app.route('/')
def home():
    contacts = load_contacts()

    if contacts is None:
        abort(500, description = 'Problem with loading contacts. Please try again later')\

    add_full_name(contacts)
    contacts = [ {'id': contact['id'], 'full_name': contact['full_name']} for contact in contacts ]
    return render_template('contact_list.html', contacts=contacts)

@app.route('/contacts/<contact_id>')
def view_contact(contact_id):
    contacts = load_contacts()

    if contacts is None:
        abort(500, description = 'Problem with loading contacts. Please try again later')

    add_full_name(contacts)
    contact = get_contact_by_id(contact_id, contacts)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('home'))

    return render_template('contact_details.html', contact=contact)

@app.route('/contacts/new')
def new_contact():
    return render_template('create_contact.html')

@app.route('/contacts', methods=["POST"])
def create_contact():
    errors = erorrs_in_contact_data(request.form)
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('create_contact.html'), 422

    contact = get_clean_contact_data(request.form) | {'id':str(uuid4())}

    contacts = load_contacts()
    contacts.append(contact)
    with open(get_contacts_file_path(), 'w') as file:
        yaml.dump(contacts, file)

    flash(f'{get_full_name(contact)} has been added to your contacts', 'success')
    return redirect(url_for('view_contact', contact_id=contact['id']))

@app.route('/contacts/<contact_id>/edit', methods=['GET', 'POST'])
def edit_contact(contact_id):
    if request.method == 'GET':
        contacts = load_contacts()
        if contacts is None:
            abort(500, description = 'Problem with loading contacts. Please try again later')
        contact = get_contact_by_id(contact_id, contacts)
        if not contact:
            flash('Contact not found.', 'error')
            return redirect(url_for('home'))
        if contact:
            return render_template('edit_contact.html', contact=contact, form_data=None)

    elif request.method == 'POST':
        contacts = load_contacts()
        if contacts is None:
            abort(500, description = 'Problem with loading contacts. Please try again later')
        contact = get_contact_by_id(contact_id, contacts)
        if not contact:
            flash('Contact not found.', 'error')
            return redirect(url_for('home'))

        errors = erorrs_in_contact_data(request.form)
        if errors:
            for error in errors:
                flash(error, 'error')
            contact = {'id': contact['id']} | request.form
            return render_template('edit_contact.html', contact=contact), 422

        updated_data = {'id':contact['id']} | get_clean_contact_data(request.form)
        contact.update(updated_data)
        with open(get_contacts_file_path(), 'w') as file:
            yaml.dump(contacts, file)

        flash(f'{get_full_name(updated_data)} has been updated.', 'success')
        return redirect(url_for('view_contact', contact_id=contact['id']))


@app.route('/contacts/<contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    contacts = load_contacts()

    contact = get_contact_by_id(contact_id, contacts)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('home'))

    contacts.remove(contact)
    with open(get_contacts_file_path(), 'w') as file:
        yaml.dump(contacts, file)

    flash('The contact has been deleted', 'success')
    return redirect(url_for('home'))

# Creating a filter that will display empty strings when non-mandatory
# fields are null in the data storage

def display_optional_value(value):
    return value if value is not None else ''

app.jinja_env.filters['optional_value'] = display_optional_value

if __name__ == '__main__':
    app.run(debug=True, port=5008)
