from cmath import e
import sqlite3

def get_connection():
    """Returns a connection object for the application database, 
        with the row factory set to Row so that row data can be referenced using
        either index or column names"""
    connection = sqlite3.connect("data.sqlite")

    # Allow for indexing of rows using either integers or column names
    # See https://docs.python.org/3/library/sqlite3.html#row-objects
    connection.row_factory = sqlite3.Row  

    # Enforce referential entegrity
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    return connection

def get_user(username):
    """Gets the user with the given username as a dict containing 
        the keys 'username' and 'password_hash'"""
    with get_connection() as cnx:
        cursor = cnx.cursor()
        sql = "SELECT username, password_hash FROM user WHERE username = ?"
        user = cursor.execute(sql, (username,)) . fetchone()
        return dict(user) if user else None

def update_password(username, password_hash):
    """Securely update the password hash for the given username."""
    with get_connection() as cnx:
        cursor = cnx.cursor()
        sql = "UPDATE user SET password_hash = ? WHERE username = ?"
        cursor.execute(sql, (password_hash, username))
        cnx.commit()


def add_person(data):
    """Inserts a new person row based on the given data (must be a dict with keys corresponding to the
        column names of the person table).
        The person data may also include a 'phone_numbers' array that contains any number of 
        phone number dicts of the form {'number','label'}
        """
    with get_connection() as cnx:
        cursor = cnx.cursor()
        try:
            # Insert person data
            sql = """INSERT INTO person (first_name, last_name, birthday, email, 
                     address_line1, address_line2, city, prov, country, postcode) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            cursor.execute(sql, [
                data['first_name'], data['last_name'], data['birthday'],
                data['email'], data['address_line1'], data['address_line2'],
                data['city'], data['prov'], data['country'], data['postcode']
            ])
            person_id = cursor.lastrowid  # Get newly inserted person's ID

            # Insert phone numbers
            if 'phone_numbers' in data:
                phone_sql = "INSERT INTO phone(person_id, number, label) VALUES (?, ?, ?)"
                phone_data = [(person_id, pn['number'], pn['label']) for pn in data['phone_numbers']]
                cursor.executemany(phone_sql, phone_data)

            cnx.commit()  # Commit only if everything is successful

        except Exception as e:
            cnx.rollback()  # Rollback changes on failure
            print(f"Error adding person: {e}")
            raise  # Rethrow the error for debugging


            

def delete_person(id):
    """Deletes the person with the given id from the person table
        id must be an id that exists in the person table"""
    with get_connection() as cnx:
        cursor = cnx.cursor()
        sql = """DELETE FROM person WHERE person_id = ?"""
        return cursor.execute(sql, [id])

PERSON_SORTABLE_FIELDS = ('person_id','first_name','last_name','birthday','email')
PERSON_SORTABLE_FIELD_HEADINGS = ('ID','First Name','Last Name','Birthday','Email')
def get_people_list(order_by):
    """Gets a list of people, including their phone numbers."""
    assert order_by in PERSON_SORTABLE_FIELDS, "Invalid sorting field."

    with get_connection() as cnx:
        cursor = cnx.cursor()
        sql = """SELECT p.person_id AS person_id, p.first_name, p.last_name, p.birthday, p.email,
                        p.address_line1, p.address_line2, p.city, p.prov, p.country, p.postcode,
                        ph.number AS phone_number, ph.label AS phone_label
                    FROM person p
                    LEFT JOIN phone ph ON p.person_id = ph.person_id"""
 
        if order_by:
            sql += " ORDER BY " + order_by
 
        results = cursor.execute(sql).fetchall()
        
        people = {}
        people_dict = {}
        # TODO: Update this loop so that it correctly adds a phone number list to each person
        for r in results:
            person_id = r['person_id']
            if person_id not in people_dict:
                people_dict[person_id] = {
                    'person_id': person_id,
                    'first_name': r['first_name'],
                    'last_name': r['last_name'],
                    'birthday': r['birthday'],
                    'email': r['email'],
                    'address_line1': r['address_line1'],
                    'address_line2': r['address_line2'],
                    'city': r['city'],
                    'prov': r['prov'],
                    'country': r['country'],
                    'postcode': r['postcode'],
                    'phone_numbers': []
                }
 
            if r['phone_number']:
                people_dict[person_id]['phone_numbers'].append({
                    'number': r['phone_number'],
                    'label': r['phone_label']
                })
 
        return list(people_dict.values())

def get_person_ids():
    """Returns a list of the person ids that exist in the database"""
    with get_connection() as cnx:
        cursor = cnx.cursor()
        sql = """SELECT person_id FROM person"""
        return [ row[0] for row in cursor.execute(sql).fetchall() ]
