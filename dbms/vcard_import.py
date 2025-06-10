import sqlite3
import vobject
import base64

DB_PATH = 'dbms/contacts.db'

def extract_property(vcard, prop_name):
    if hasattr(vcard, prop_name):
        val = getattr(vcard, prop_name)
        if isinstance(val, list):
            return [v.value if hasattr(v, 'value') else v for v in val]
        else:
            return val.value if hasattr(val, 'value') else val
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

def insert_contact(cursor, contact):
    cursor.execute("""
        INSERT INTO contact (fn, n, nickname, photo, bday, anniversary, gender, adr, tel, email, impp, lang, tz, geo, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        contact.get('fn'),
        contact.get('n'),
        contact.get('nickname'),
        contact.get('photo'),
        contact.get('bday'),
        contact.get('anniversary'),
        contact.get('gender'),
        contact.get('adr'),
        contact.get('tel'),
        contact.get('email'),
        contact.get('impp'),
        contact.get('lang'),
        contact.get('tz'),
        contact.get('geo'),
        contact.get('note')
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

def insert_is_in(cursor, contact_id, group_id, role_id):
    cursor.execute("""
        INSERT INTO is_in (contact_id, group_id, role_id)
        VALUES (?, ?, ?)
    """, (contact_id, group_id, role_id))

def insert_other(cursor, contact_id, other_data):
    cursor.execute("""
        INSERT INTO other (contact_id, categories, prodid, rev, sound, uid, clientpidmap, version, key, fburl, caladruri, caluri)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        contact_id,
        other_data.get('categories'),
        other_data.get('prodid'),
        other_data.get('rev'),
        other_data.get('sound'),
        other_data.get('uid'),
        other_data.get('clientpidmap'),
        other_data.get('version'),
        other_data.get('key'),
        other_data.get('fburl'),
        other_data.get('caladruri'),
        other_data.get('caluri')
    ))

def import_vcard(vcf_path):
    with open(vcf_path, 'r') as f:
        vcard_data = f.read()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    for vcard in vobject.readComponents(vcard_data):
        contact = {
            'fn': extract_property(vcard, 'fn'),
            'n': None,
            'nickname': extract_property(vcard, 'nickname'),
            'photo': None,
            'bday': None,
            'anniversary': None,
            'gender': extract_property(vcard, 'gender'),
            'adr': None,
            'tel': None,
            'email': None,
            'impp': None,
            'lang': None,
            'tz': extract_property(vcard, 'tz'),
            'geo': extract_property(vcard, 'geo'),
            'note': extract_property(vcard, 'note')
        }

        if hasattr(vcard, 'n'):
            n = vcard.n.value
            contact['n'] = ' '.join(n) if isinstance(n, (list, tuple)) else str(n)

        if hasattr(vcard, 'photo'):
            contact['photo'] = photo_to_blob(vcard.photo)

        if hasattr(vcard, 'bday'):
            val = vcard.bday.value
            contact['bday'] = val.strftime('%Y-%m-%d') if hasattr(val, 'strftime') else str(val)

        if hasattr(vcard, 'anniversary'):
            val = vcard.anniversary.value
            contact['anniversary'] = val.strftime('%Y-%m-%d') if hasattr(val, 'strftime') else str(val)

        for field in ['adr', 'tel', 'email', 'impp', 'lang']:
            val = extract_property(vcard, field)
            if isinstance(val, list):
                val = val[0] if val else None
            contact[field] = str(val) if val else None

        contact_id = insert_contact(cursor, contact)

        # Insert into 'other' table
        other_data = {
            'categories': str(extract_property(vcard, 'categories')),
            'prodid': extract_property(vcard, 'prodid'),
            'rev': extract_property(vcard, 'rev'),
            'sound': extract_property(vcard, 'sound'),
            'uid': extract_property(vcard, 'uid'),
            'clientpidmap': str(extract_property(vcard, 'clientpidmap')),
            'version': extract_property(vcard, 'version'),
            'key': extract_property(vcard, 'key'),
            'fburl': extract_property(vcard, 'fburl'),
            'caladruri': extract_property(vcard, 'caladruri'),
            'caluri': extract_property(vcard, 'caluri')
        }

        if any(other_data.values()):
            insert_other(cursor, contact_id, other_data)

        group = {
            'title': extract_property(vcard, 'title'),
            'logo': None,
            'org': extract_property(vcard, 'org'),
            'related': extract_property(vcard, 'related'),
            'url': extract_property(vcard, 'url')
        }

        if group['logo']:
            group['logo'] = photo_to_blob(group['logo'])

        group_id = insert_group(cursor, group) if any(group.values()) else None

        role = {
            'role': extract_property(vcard, 'role'),
            'member': extract_property(vcard, 'member')
        }

        role_id = insert_role(cursor, role) if any(role.values()) else None

        if contact_id and group_id and role_id:
            insert_is_in(cursor, contact_id, group_id, role_id)

    connection.commit()
    connection.close()
    print("Import complete.")
