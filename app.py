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

# TODO : full name shouldn't be added here but ony in the views that require it
def load_contacts():
    file_path = get_contacts_file_path()
    try:
        with open(file_path, 'r') as file:
            contacts = yaml.safe_load(file)
            add_full_name(contacts)
            return contacts if contacts else []
    except FileNotFoundError:
            return None

@app.route('/')
def home():
    contacts = load_contacts()
    if contacts is None:
        abort(500, description = 'Problem with loading contacts. Please try again later')
    contacts = [ {'id': contact['id'], 'full_name': contact['full_name']} for contact in contacts ]
    return render_template('contact_list.html', contacts=contacts)

@app.route('/contacts/<contact_id>')
def view_contact(contact_id):
    contacts = load_contacts()
    if contacts is None:
        abort(500, description = 'Problem with loading contacts. Please try again later')

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
    first_name = request.form.get('first_name')
    middle_names = request.form.get('middle_names')
    last_name = request.form.get('last_name')
    phone_number = request.form.get('phone_number')
    email_address = request.form.get('email_address')

    # error_checkers = {
    #     'first_name':
    # }'error_for_first_name', 'error_for_phone_num', 'error_for_email_addr')
    # errors = [error_checker() for error_checker in error_checkers]

    # TODO - implement validations
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

    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('create_contact.html'), 422

    first_name = first_name.strip()
    middle_names = middle_names.strip() if middle_names else None
    last_name = last_name.strip() if last_name else None
    phone_number = phone_number.strip() if phone_number else None
    email_address = email_address.strip() if email_address else None

    contact = {
        'id': str(uuid4()),
        'first_name': first_name,
        'middle_names': middle_names,
        'last_name': last_name,
        'phone_number': phone_number,
        'email_address': email_address
    }

    contacts = load_contacts()
    contacts.append(contact)
    with open(get_contacts_file_path(), 'w') as file:
        yaml.dump(contacts, file)

    flash(f'{get_full_name(contact)} has been added to your contacts', 'success')
    return redirect(url_for('view_contact', contact_id=contact['id']))


if __name__ == '__main__':
    app.run(debug=True, port=5008)
