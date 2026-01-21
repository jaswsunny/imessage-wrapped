"""Resolve phone numbers/emails to contact names."""
import json
import re
from pathlib import Path
from config import DATA_DIR

def normalize_phone(phone: str) -> str:
    """Normalize phone number to digits only."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    return digits

def get_contacts_from_macos():
    """Attempt to get contacts from macOS Contacts app."""
    try:
        import Contacts

        store = Contacts.CNContactStore.alloc().init()

        keys = [
            Contacts.CNContactGivenNameKey,
            Contacts.CNContactFamilyNameKey,
            Contacts.CNContactPhoneNumbersKey,
            Contacts.CNContactEmailAddressesKey,
        ]

        request = Contacts.CNContactFetchRequest.alloc().initWithKeysToFetch_(keys)

        contacts_map = {}

        def enumerate_handler(contact, stop):
            name = f"{contact.givenName()} {contact.familyName()}".strip()
            if not name:
                return

            for phone in contact.phoneNumbers():
                number = phone.value().stringValue()
                normalized = normalize_phone(number)
                if normalized:
                    contacts_map[normalized] = name
                    contacts_map[f"+1{normalized}"] = name

            for email in contact.emailAddresses():
                email_str = str(email.value()).lower()
                contacts_map[email_str] = name

        store.enumerateContactsWithFetchRequest_error_usingBlock_(
            request, None, enumerate_handler
        )

        print(f"Loaded {len(contacts_map)} contact mappings from macOS Contacts")
        return contacts_map

    except Exception as e:
        print(f"Could not access macOS Contacts: {e}")
        return {}

def resolve_contact_id(contact_id: str, contacts_map: dict) -> str:
    """Resolve a contact_id to a name."""
    if not contact_id:
        return "Unknown"

    if contact_id in contacts_map:
        return contacts_map[contact_id]

    normalized = normalize_phone(contact_id)
    if normalized in contacts_map:
        return contacts_map[normalized]

    lower = contact_id.lower()
    if lower in contacts_map:
        return contacts_map[lower]

    return contact_id

def create_contact_mappings(df, contacts_map: dict) -> dict:
    """Create final contact mappings for all contacts in dataframe."""
    unique_contacts = df['contact_id'].unique()

    mappings = {}
    unresolved = []

    for contact_id in unique_contacts:
        resolved = resolve_contact_id(str(contact_id), contacts_map)
        mappings[str(contact_id)] = resolved
        if resolved == str(contact_id):
            unresolved.append(contact_id)

    print(f"Resolved {len(mappings) - len(unresolved)}/{len(mappings)} contacts")

    if unresolved:
        print(f"Unresolved contacts: {len(unresolved)}")

    return mappings

def save_contact_mappings(mappings: dict):
    """Save contact mappings to JSON."""
    output_path = DATA_DIR / "contacts.json"
    with open(output_path, 'w') as f:
        json.dump(mappings, f, indent=2)
    print(f"Saved contact mappings to {output_path}")

def load_contact_mappings() -> dict:
    """Load contact mappings from JSON."""
    path = DATA_DIR / "contacts.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

def prompt_for_unresolved(df, mappings: dict, top_n: int = 30):
    """Identify top unresolved contacts for manual mapping."""
    contact_counts = df.groupby('contact_id').size().sort_values(ascending=False)

    unresolved_top = []
    for contact_id, count in contact_counts.head(top_n).items():
        contact_str = str(contact_id)
        if mappings.get(contact_str) == contact_str:
            unresolved_top.append((contact_str, count))

    return unresolved_top

if __name__ == "__main__":
    contacts_map = get_contacts_from_macos()
    from extract import extract_messages
    df = extract_messages()
    mappings = create_contact_mappings(df, contacts_map)
    save_contact_mappings(mappings)
    unresolved = prompt_for_unresolved(df, mappings)
    if unresolved:
        print("\nTop unresolved contacts:")
        for contact_id, count in unresolved[:10]:
            print(f"  {contact_id}: {count:,} messages")
