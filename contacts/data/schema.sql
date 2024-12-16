CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    middle_names TEXT,
    last_name TEXT,
    phone_number TEXT,
    email_address TEXT
    CHECK(LENGTH(phone_number) >= 6),
    CHECK(phone_number SIMILAR TO '\d{6,}'),
    CHECK(position('@' in email_address) > 0)
);