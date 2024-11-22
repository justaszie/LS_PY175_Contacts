from flask import Flask, render_template, redirect, flash, url_for, abort
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

if __name__ == '__main__':
    app.run(debug=True, port=5008)
