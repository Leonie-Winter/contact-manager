# why is there so much stringify?
# due to a fuckload of problems when trying to import values, such as lists when only strings are accepted, the program makes a string out of every imported value so as not to cause any problems

import sqlite3
import vobject
import base64

DB_PATH = 'dbms/contacts.db'

def stringify(val, seen=None):
    if seen is None:
        seen = set()

    if id(val) in seen:
        return '[RECURSION]'

    seen.add(id(val))

    if isinstance(val, list):
        return ', '.join(stringify(v, seen) for v in val)
    if hasattr(val, 'value'):
        return stringify(val.value, seen)
    try:
        return str(val)
    except Exception:
        return '[UNSTRINGIFIABLE]'

def extract_property(vcard, prop_name):
    try:
        if hasattr(vcard, prop_name):
            val = getattr(vcard, prop_name)
            if isinstance(val, list):
                return [v.value if hasattr(v, 'value') else v for v in val]
            return val.value if hasattr(val, 'value') else val
    except Exception as e:
        print(f"Error extracting {prop_name}: {e}")
    return None


def photo_to_blob(photo_obj):
    if hasattr(photo_obj, 'value') and isinstance(photo_obj.value, bytes):
        return photo_obj.value
    elif hasattr(photo_obj, 'value'):
        try:
            return base64.b64decode(photo_obj.value)
        except Exception:
            return None
    return None

def insert_person(cursor, person):
    cursor.execute("""
        INSERT INTO persons (fn, n, nickname, photo, bday, anniversary, gender, adr, tel, email, impp, lang, tz, geo, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        person.get('fn'),
        person.get('n'),
        person.get('nickname'),
        person.get('photo'),
        person.get('bday'),
        person.get('anniversary'),
        person.get('gender'),
        person.get('adr'),
        person.get('tel'),
        person.get('email'),
        person.get('impp'),
        person.get('lang'),
        person.get('tz'),
        person.get('geo'),
        person.get('note')
    ))
    return cursor.lastrowid

def insert_group(cursor, group):
    cursor.execute("""
        INSERT INTO groups (title, logo, org, related, url)
        VALUES (?, ?, ?, ?, ?)
    """, (
        group.get('title'),
        group.get('logo'),
        group.get('org'),
        group.get('related'),
        group.get('url')
    ))
    return cursor.lastrowid

def insert_role(cursor, role):
    cursor.execute("""
        INSERT INTO role (role, member)
        VALUES (?, ?)
    """, (
        role.get('role'),
        role.get('member')
    ))
    return cursor.lastrowid

def insert_is_in(cursor, person_id, group_id, role_id):
    cursor.execute("""
        INSERT INTO is_in (person_id, group_id, role_id)
        VALUES (?, ?, ?)
    """, (person_id, group_id, role_id))

def insert_other(cursor, person_id, other):
    cursor.execute("""
        INSERT INTO other (
            person_id, categories, prodid, rev, sound, uid,
            clientpidmap, version, key, fburl, caladruri, caluri
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        person_id,
        stringify(other.get('categories')),
        stringify(other.get('prodid')),
        stringify(other.get('rev')),
        stringify(other.get('sound')),
        stringify(other.get('uid')),
        stringify(other.get('clientpidmap')),
        stringify(other.get('version')),
        stringify(other.get('key')),
        stringify(other.get('fburl')),
        stringify(other.get('caladruri')),
        stringify(other.get('caluri'))
    ))


def import_vcard(vcf_path):
    with open(vcf_path, 'r') as f:
        vcard_data = f.read()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    for vcard in vobject.readComponents(vcard_data):
        person = {
        'fn': stringify(extract_property(vcard, 'fn')),
        'n': None,  # handled later
        'nickname': stringify(extract_property(vcard, 'nickname')),
        'photo': None,
        'bday': None,
        'anniversary': None,
        'gender': stringify(extract_property(vcard, 'gender')),
        'adr': None,
        'tel': None,
        'email': None,
        'impp': None,
        'lang': None,
        'tz': stringify(extract_property(vcard, 'tz')),
        'geo': stringify(extract_property(vcard, 'geo')),
        'note': stringify(extract_property(vcard, 'note'))
}


        if hasattr(vcard, 'n'):
            n = vcard.n.value
            person['n'] = ' '.join(n) if isinstance(n, (list, tuple)) else str(n)

        if hasattr(vcard, 'photo'):
            person['photo'] = photo_to_blob(vcard.photo)

        if hasattr(vcard, 'bday'):
            val = vcard.bday.value
            person['bday'] = val.strftime('%Y-%m-%d') if hasattr(val, 'strftime') else str(val)

        if hasattr(vcard, 'anniversary'):
            val = vcard.anniversary.value
            person['anniversary'] = val.strftime('%Y-%m-%d') if hasattr(val, 'strftime') else str(val)

        for field in ['adr', 'tel', 'email', 'impp', 'lang']:
            val = extract_property(vcard, field)
            if isinstance(val, list):
                val = val[0] if val else None
            person[field] = stringify(val)


        person_id = insert_person(cursor, person)

        # Insert into 'other' table
        other_data = {
        'categories': stringify(extract_property(vcard, 'categories')),
        'prodid': stringify(extract_property(vcard, 'prodid')),
        'rev': stringify(extract_property(vcard, 'rev')),
        'sound': stringify(extract_property(vcard, 'sound')),
        'uid': stringify(extract_property(vcard, 'uid')),
        'clientpidmap': stringify(extract_property(vcard, 'clientpidmap')),
        'version': stringify(extract_property(vcard, 'version')),
        'key': stringify(extract_property(vcard, 'key')),
        'fburl': stringify(extract_property(vcard, 'fburl')),
        'caladruri': stringify(extract_property(vcard, 'caladruri')),
        'caluri': stringify(extract_property(vcard, 'caluri'))
        }


        if any(other_data.values()):
            insert_other(cursor, person_id, other_data)

        group = {
        'title': stringify(extract_property(vcard, 'title')),
        'logo': None,
        'org': stringify(extract_property(vcard, 'org')),
        'related': stringify(extract_property(vcard, 'related')),
        'url': stringify(extract_property(vcard, 'url'))
        }


        if group['logo']:
            group['logo'] = photo_to_blob(group['logo'])

        group_id = insert_group(cursor, group) if any(group.values()) else None

        role = {
        'role': stringify(extract_property(vcard, 'role')),
        'member': stringify(extract_property(vcard, 'member'))
        }


        role_id = insert_role(cursor, role) if any(role.values()) else None

        if person_id and group_id and role_id:
            insert_is_in(cursor, person_id, group_id, role_id)

    connection.commit()
    connection.close()
    print("Import complete.")
