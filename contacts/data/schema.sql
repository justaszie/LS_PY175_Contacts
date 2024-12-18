CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    middle_names TEXT,
    last_name TEXT,
    email_address TEXT,
    CHECK(position('@' in email_address) > 0)
);

CREATE TYPE phone_number_type as ENUM ('personal', 'home', 'work', 'other');

CREATE TABLE phone_numbers(
    id SERIAL PRIMARY KEY,
    number_value TEXT NOT NULL,
    number_type phone_number_type NOT NULL,
    contact_id INT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    CHECK(LENGTH(number_value) >= 6),
    CHECK(number_value SIMILAR TO '\d{6,}')
);