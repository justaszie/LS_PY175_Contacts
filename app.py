from flask import Flask, render_template, redirect, flash
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
            return yaml.safe_load(file)
    except FileNotFoundError:
            return None


@app.route('/')
def home():
    contacts_data = load_contacts()
    contacts = [{'id': contact['id'],
                 'full_name' : get_full_name(contact),}
                 for contact in contacts_data]

    return render_template('contact_list.html', contacts=contacts)

if __name__ == '__main__':
    app.run(debug=True, port=5008)
