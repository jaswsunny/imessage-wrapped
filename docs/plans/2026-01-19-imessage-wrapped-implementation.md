# iMessage Wrapped Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate an interactive HTML report analyzing 8 years of iMessage data with relationship insights, temporal patterns, and content analysis.

**Architecture:** Extract messages from SQLite chat.db → resolve contacts via macOS Contacts → run analysis modules (people, temporal, content) → generate Plotly visualizations → assemble single-page HTML report. Save processed data as parquet for follow-up queries.

**Tech Stack:** Python 3, pandas, sqlite3, plotly, nltk (VADER), scikit-learn (LDA), pyobjc-framework-Contacts, pyarrow

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `config.py`

**Step 1: Create requirements.txt**

```txt
pandas>=2.0.0
plotly>=5.18.0
nltk>=3.8.0
scikit-learn>=1.3.0
pyobjc-framework-Contacts>=10.0
pyarrow>=14.0.0
emoji>=2.8.0
```

**Step 2: Create virtual environment and install**

Run:
```bash
cd ~/imessage-wrapped && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

**Step 3: Download NLTK data**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"
```

**Step 4: Create config.py**

```python
"""Configuration for iMessage Wrapped analysis."""
from pathlib import Path
from datetime import datetime

# Paths
CHAT_DB_PATH = Path.home() / "Library/Messages/chat.db"
OUTPUT_DIR = Path(__file__).parent / "output"
DATA_DIR = OUTPUT_DIR / "data"

# Date range
START_YEAR = 2017
END_YEAR = 2025

# Analysis thresholds
MIN_MESSAGES_FOR_TOP_CONTACT = 50
CONVERSATION_GAP_HOURS = 4  # Hours of silence before new conversation
TOP_CONTACTS_COUNT = 15

# Boring phrases to exclude from phrase analysis
BORING_PHRASES = {
    "sounds good", "on my way", "be there", "see you", "got it",
    "ok", "okay", "yeah", "yep", "yea", "ya", "haha", "hahaha", "lol",
    "omg", "idk", "i know", "i think", "thank you", "thanks", "no problem",
    "good morning", "good night", "have a good", "talk to you",
    "let me know", "i will", "i can", "i don't", "do you", "are you",
    "what time", "how are", "i'm good", "that's good", "sounds great",
    "see you soon", "on the way", "almost there", "be right there",
    "i'm here", "where are", "what's up", "not much", "same here",
}

# Boring single words to exclude
BORING_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "just", "i", "me",
    "my", "myself", "we", "our", "you", "your", "he", "him", "his", "she",
    "her", "it", "its", "they", "them", "their", "what", "which", "who",
    "this", "that", "these", "those", "am", "but", "if", "or", "because",
    "and", "up", "down", "out", "off", "over", "now", "get", "got", "like",
    "going", "go", "come", "back", "want", "know", "think", "see", "look",
    "make", "take", "give", "well", "also", "way", "even", "new", "any",
    "say", "said", "one", "two", "first", "last", "long", "great", "little",
    "right", "still", "find", "tell", "ask", "work", "seem", "feel",
    "try", "leave", "call", "keep", "let", "begin", "show", "hear",
    "play", "run", "move", "live", "believe", "bring", "happen", "write",
    "provide", "sit", "stand", "lose", "pay", "meet", "include", "continue",
    "set", "learn", "change", "lead", "understand", "watch", "follow",
    "stop", "create", "speak", "read", "allow", "add", "spend", "grow",
    "open", "walk", "win", "offer", "remember", "love", "consider", "appear",
    "buy", "wait", "serve", "die", "send", "expect", "build", "stay",
    "fall", "cut", "reach", "kill", "remain", "yeah", "yes", "no", "oh",
    "ok", "okay", "um", "uh", "ah", "haha", "lol", "gonna", "wanna",
    "gotta", "kinda", "sorta", "maybe", "probably", "really", "actually",
    "basically", "literally", "definitely", "absolutely", "totally",
    "completely", "exactly", "simply", "highly", "likely", "certainly",
    "usually", "always", "never", "sometimes", "often", "already",
    "today", "tomorrow", "yesterday", "tonight", "morning", "night",
    "day", "week", "month", "year", "time", "thing", "things", "stuff",
    "lot", "bit", "much", "many", "people", "person", "man", "woman",
    "child", "world", "life", "hand", "part", "place", "case", "point",
    "government", "company", "number", "group", "problem", "fact",
}

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
```

**Step 5: Verify setup**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 -c "import pandas; import plotly; import nltk; import sklearn; print('All imports successful')"
```
Expected: "All imports successful"

---

## Task 2: Data Extraction

**Files:**
- Create: `extract.py`

**Step 1: Create extract.py with database connection and query**

```python
"""Extract iMessage data from chat.db."""
import sqlite3
import pandas as pd
from datetime import datetime
from config import CHAT_DB_PATH, START_YEAR

# Apple's Cocoa epoch: 2001-01-01 00:00:00 UTC
COCOA_EPOCH_OFFSET = 978307200

def connect_db():
    """Connect to iMessage database (read-only)."""
    return sqlite3.connect(f"file:{CHAT_DB_PATH}?mode=ro", uri=True)

def extract_messages():
    """Extract all 1:1 messages with metadata."""
    query = """
    SELECT
        m.ROWID as message_id,
        m.text,
        m.is_from_me,
        m.date / 1000000000 + ? as timestamp,
        m.date_read / 1000000000 + ? as timestamp_read,
        m.date_delivered / 1000000000 + ? as timestamp_delivered,
        h.id as handle_id,
        h.service,
        c.ROWID as chat_id,
        c.chat_identifier
    FROM message m
    JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    JOIN chat c ON cmj.chat_id = c.ROWID
    LEFT JOIN handle h ON m.handle_id = h.ROWID
    WHERE
        c.chat_identifier NOT LIKE 'chat%'  -- Exclude group chats
        AND m.text IS NOT NULL
        AND m.text != ''
    ORDER BY m.date
    """

    with connect_db() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params=(COCOA_EPOCH_OFFSET, COCOA_EPOCH_OFFSET, COCOA_EPOCH_OFFSET)
        )

    # Convert timestamps to datetime
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert('America/Los_Angeles')
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['hour'] = df['datetime'].dt.hour
    df['date'] = df['datetime'].dt.date

    # Filter to our date range
    df = df[df['year'] >= START_YEAR]

    # Clean handle_id (use chat_identifier as fallback)
    df['contact_id'] = df['handle_id'].fillna(df['chat_identifier'])

    print(f"Extracted {len(df):,} messages from {df['year'].min()} to {df['year'].max()}")
    print(f"Unique contacts: {df['contact_id'].nunique()}")

    return df

if __name__ == "__main__":
    df = extract_messages()
    print(df.head())
    print(f"\nMessages per year:")
    print(df.groupby('year').size())
```

**Step 2: Test extraction**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 extract.py
```
Expected: Output showing message count, year range, and messages per year breakdown.

---

## Task 3: Contact Resolution

**Files:**
- Create: `contacts.py`

**Step 1: Create contacts.py**

```python
"""Resolve phone numbers/emails to contact names."""
import json
import re
from pathlib import Path
from config import DATA_DIR

def normalize_phone(phone: str) -> str:
    """Normalize phone number to digits only."""
    digits = re.sub(r'\D', '', phone)
    # Handle US numbers
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    return digits

def get_contacts_from_macos():
    """Attempt to get contacts from macOS Contacts app."""
    try:
        import Contacts

        store = Contacts.CNContactStore.alloc().init()

        # Request access
        granted = [False]
        def handler(success, error):
            granted[0] = success

        store.requestAccessForEntityType_completionHandler_(
            Contacts.CNEntityTypeContacts, handler
        )

        # Fetch contacts
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

            # Map phone numbers
            for phone in contact.phoneNumbers():
                number = phone.value().stringValue()
                normalized = normalize_phone(number)
                if normalized:
                    contacts_map[normalized] = name
                    # Also store with +1 prefix
                    contacts_map[f"+1{normalized}"] = name

            # Map emails
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

    # Direct lookup
    if contact_id in contacts_map:
        return contacts_map[contact_id]

    # Try normalized phone
    normalized = normalize_phone(contact_id)
    if normalized in contacts_map:
        return contacts_map[normalized]

    # Try lowercase (for emails)
    lower = contact_id.lower()
    if lower in contacts_map:
        return contacts_map[lower]

    # Return original (phone/email)
    return contact_id

def create_contact_mappings(df, contacts_map: dict) -> dict:
    """Create final contact mappings for all contacts in dataframe."""
    unique_contacts = df['contact_id'].unique()

    mappings = {}
    unresolved = []

    for contact_id in unique_contacts:
        resolved = resolve_contact_id(str(contact_id), contacts_map)
        mappings[str(contact_id)] = resolved
        if resolved == str(contact_id):  # Wasn't resolved
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
    """
    Identify top unresolved contacts for manual mapping.
    Returns list of (contact_id, message_count) for unresolved top contacts.
    """
    # Count messages per contact
    contact_counts = df.groupby('contact_id').size().sort_values(ascending=False)

    unresolved_top = []
    for contact_id, count in contact_counts.head(top_n).items():
        contact_str = str(contact_id)
        if mappings.get(contact_str) == contact_str:  # Still unresolved
            unresolved_top.append((contact_str, count))

    return unresolved_top

if __name__ == "__main__":
    # Test contact resolution
    contacts_map = get_contacts_from_macos()

    # Import extract to get sample data
    from extract import extract_messages
    df = extract_messages()

    mappings = create_contact_mappings(df, contacts_map)
    save_contact_mappings(mappings)

    # Show top unresolved
    unresolved = prompt_for_unresolved(df, mappings)
    if unresolved:
        print("\nTop unresolved contacts (may need manual mapping):")
        for contact_id, count in unresolved[:10]:
            print(f"  {contact_id}: {count:,} messages")
```

**Step 2: Test contact resolution**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 contacts.py
```
Expected: Output showing how many contacts were resolved, and listing any top unresolved contacts.

Note: macOS will prompt for Contacts access permission. Grant it.

---

## Task 4: People Analysis Module

**Files:**
- Create: `analysis/people.py`
- Create: `analysis/__init__.py`

**Step 1: Create analysis/__init__.py**

```python
"""Analysis modules for iMessage Wrapped."""
```

**Step 2: Create analysis/people.py**

```python
"""People and relationship analysis."""
import pandas as pd
import numpy as np
from config import CONVERSATION_GAP_HOURS, TOP_CONTACTS_COUNT, MIN_MESSAGES_FOR_TOP_CONTACT

def get_top_contacts_alltime(df, n=TOP_CONTACTS_COUNT):
    """Get top N contacts by total message count."""
    counts = df.groupby('contact_name').agg(
        total_messages=('message_id', 'count'),
        sent=('is_from_me', 'sum'),
        years_active=('year', 'nunique'),
        first_message=('datetime', 'min'),
        last_message=('datetime', 'max'),
    ).reset_index()

    counts['received'] = counts['total_messages'] - counts['sent']
    counts = counts.sort_values('total_messages', ascending=False)

    return counts.head(n)

def get_top_contacts_by_year(df, n=10):
    """Get top N contacts for each year."""
    yearly = df.groupby(['year', 'contact_name']).agg(
        total_messages=('message_id', 'count'),
        sent=('is_from_me', 'sum'),
    ).reset_index()

    yearly['received'] = yearly['total_messages'] - yearly['sent']

    # Rank within each year
    yearly['rank'] = yearly.groupby('year')['total_messages'].rank(
        ascending=False, method='min'
    )

    top_per_year = yearly[yearly['rank'] <= n].sort_values(['year', 'rank'])

    return top_per_year

def calculate_lopsidedness(df):
    """Calculate lopsidedness ratio for each contact."""
    stats = df.groupby('contact_name').agg(
        sent=('is_from_me', 'sum'),
        total=('message_id', 'count'),
    ).reset_index()

    stats['received'] = stats['total'] - stats['sent']

    # Lopsidedness: ratio of sent to received (>1 means you send more)
    # Add small epsilon to avoid division by zero
    stats['lopsidedness'] = stats['sent'] / (stats['received'] + 0.1)

    # Filter to contacts with minimum messages
    stats = stats[stats['total'] >= MIN_MESSAGES_FOR_TOP_CONTACT]

    return stats.sort_values('lopsidedness', ascending=False)

def identify_conversation_starts(df):
    """Identify conversation initiators (first message after gap)."""
    df = df.sort_values(['contact_name', 'datetime']).copy()

    # Calculate time since last message with same contact
    df['prev_time'] = df.groupby('contact_name')['datetime'].shift(1)
    df['hours_since_last'] = (df['datetime'] - df['prev_time']).dt.total_seconds() / 3600

    # Mark conversation starts
    df['is_conversation_start'] = df['hours_since_last'] > CONVERSATION_GAP_HOURS

    # First message with each contact is always a start
    df.loc[df['prev_time'].isna(), 'is_conversation_start'] = True

    return df

def get_conversation_initiator_stats(df):
    """Get stats on who initiates conversations more."""
    df_with_starts = identify_conversation_starts(df)

    starts = df_with_starts[df_with_starts['is_conversation_start']].copy()

    stats = starts.groupby('contact_name').agg(
        total_conversations=('message_id', 'count'),
        you_initiated=('is_from_me', 'sum'),
    ).reset_index()

    stats['they_initiated'] = stats['total_conversations'] - stats['you_initiated']
    stats['you_initiate_pct'] = stats['you_initiated'] / stats['total_conversations'] * 100

    # Filter to meaningful sample size
    stats = stats[stats['total_conversations'] >= 10]

    return stats.sort_values('you_initiate_pct', ascending=False)

def calculate_response_times(df):
    """Calculate average response times per contact."""
    df = df.sort_values(['contact_name', 'datetime']).copy()

    # Get previous message info
    df['prev_time'] = df.groupby('contact_name')['datetime'].shift(1)
    df['prev_from_me'] = df.groupby('contact_name')['is_from_me'].shift(1)

    # Response time only when direction changed
    df['is_response'] = df['is_from_me'] != df['prev_from_me']
    df['response_seconds'] = (df['datetime'] - df['prev_time']).dt.total_seconds()

    # Filter to actual responses within reasonable time (< 24 hours)
    responses = df[df['is_response'] & (df['response_seconds'] < 86400) & (df['response_seconds'] > 0)]

    # Your response times
    your_responses = responses[responses['is_from_me'] == 1]
    your_avg = your_responses.groupby('contact_name')['response_seconds'].median().reset_index()
    your_avg.columns = ['contact_name', 'your_response_time_sec']

    # Their response times
    their_responses = responses[responses['is_from_me'] == 0]
    their_avg = their_responses.groupby('contact_name')['response_seconds'].median().reset_index()
    their_avg.columns = ['contact_name', 'their_response_time_sec']

    # Merge
    response_stats = your_avg.merge(their_avg, on='contact_name', how='outer')

    # Convert to minutes for readability
    response_stats['your_response_time_min'] = response_stats['your_response_time_sec'] / 60
    response_stats['their_response_time_min'] = response_stats['their_response_time_sec'] / 60

    return response_stats

def find_rising_stars(df, year1, year2, top_n=20):
    """Find contacts who rose significantly in rankings between years."""
    yearly = get_top_contacts_by_year(df, n=100)

    y1 = yearly[yearly['year'] == year1][['contact_name', 'rank']].rename(columns={'rank': 'rank_y1'})
    y2 = yearly[yearly['year'] == year2][['contact_name', 'rank']].rename(columns={'rank': 'rank_y2'})

    merged = y1.merge(y2, on='contact_name', how='outer')

    # People not in top 20 in year1 but in top 10 in year2
    rising = merged[
        ((merged['rank_y1'] > top_n) | merged['rank_y1'].isna()) &
        (merged['rank_y2'] <= 10)
    ]

    return rising.sort_values('rank_y2')

def find_faded_connections(df, year1, year2, top_n=10):
    """Find contacts who were top contacts but faded."""
    yearly = get_top_contacts_by_year(df, n=100)

    y1 = yearly[yearly['year'] == year1][['contact_name', 'rank']].rename(columns={'rank': 'rank_y1'})
    y2 = yearly[yearly['year'] == year2][['contact_name', 'rank']].rename(columns={'rank': 'rank_y2'})

    merged = y1.merge(y2, on='contact_name', how='outer')

    # People in top 10 in year1 but not in top 20 in year2 (or absent)
    faded = merged[
        (merged['rank_y1'] <= top_n) &
        ((merged['rank_y2'] > 20) | merged['rank_y2'].isna())
    ]

    return faded.sort_values('rank_y1')

def get_ranking_over_time(df, contacts=None, top_n=10):
    """Get ranking trajectories for specified contacts (for bump chart)."""
    yearly = get_top_contacts_by_year(df, n=50)

    if contacts is None:
        # Use all-time top contacts
        top = get_top_contacts_alltime(df, n=top_n)
        contacts = top['contact_name'].tolist()

    # Filter to specified contacts
    yearly = yearly[yearly['contact_name'].isin(contacts)]

    # Pivot for visualization
    pivot = yearly.pivot(index='year', columns='contact_name', values='rank')

    return pivot, yearly

def get_message_volume_over_time(df, contacts=None, top_n=10):
    """Get message volume by month for top contacts (for stacked area)."""
    if contacts is None:
        top = get_top_contacts_alltime(df, n=top_n)
        contacts = top['contact_name'].tolist()

    df_filtered = df[df['contact_name'].isin(contacts)].copy()
    df_filtered['year_month'] = df_filtered['datetime'].dt.to_period('M')

    monthly = df_filtered.groupby(['year_month', 'contact_name']).size().reset_index(name='count')
    monthly['year_month'] = monthly['year_month'].dt.to_timestamp()

    return monthly

if __name__ == "__main__":
    from extract import extract_messages
    from contacts import get_contacts_from_macos, create_contact_mappings

    df = extract_messages()
    contacts_map = get_contacts_from_macos()
    mappings = create_contact_mappings(df, contacts_map)
    df['contact_name'] = df['contact_id'].astype(str).map(mappings)

    print("\n=== TOP CONTACTS (ALL-TIME) ===")
    print(get_top_contacts_alltime(df))

    print("\n=== LOPSIDEDNESS ===")
    lop = calculate_lopsidedness(df)
    print("Most lopsided (you send more):")
    print(lop.head(5))
    print("\nMost lopsided (they send more):")
    print(lop.tail(5))

    print("\n=== CONVERSATION INITIATORS ===")
    print(get_conversation_initiator_stats(df).head(10))
```

**Step 3: Test people analysis**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 -m analysis.people
```
Expected: Output showing top contacts, lopsidedness stats, and conversation initiator stats.

---

## Task 5: Temporal Analysis Module

**Files:**
- Create: `analysis/temporal.py`

**Step 1: Create analysis/temporal.py**

```python
"""Temporal pattern analysis."""
import pandas as pd
import numpy as np

def get_hour_day_heatmap(df):
    """Get message counts by hour and day of week."""
    heatmap = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')

    # Pivot for heatmap visualization
    pivot = heatmap.pivot(index='day_of_week', columns='hour', values='count').fillna(0)

    # Rename index to day names
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot.index = [day_names[i] for i in pivot.index]

    return pivot

def get_peak_hours_by_year(df):
    """Get peak texting hours for each year."""
    hourly_by_year = df.groupby(['year', 'hour']).size().reset_index(name='count')

    # Find peak hour per year
    idx = hourly_by_year.groupby('year')['count'].idxmax()
    peaks = hourly_by_year.loc[idx][['year', 'hour', 'count']]
    peaks.columns = ['year', 'peak_hour', 'messages_at_peak']

    return peaks, hourly_by_year

def get_yearly_volume(df):
    """Get total messages sent and received per year."""
    yearly = df.groupby('year').agg(
        total=('message_id', 'count'),
        sent=('is_from_me', 'sum'),
    ).reset_index()

    yearly['received'] = yearly['total'] - yearly['sent']

    return yearly

def get_longest_streaks(df, top_n=10):
    """Find longest daily texting streaks per contact."""
    # Get unique (contact, date) pairs
    daily = df.groupby(['contact_name', 'date']).size().reset_index(name='count')
    daily = daily.sort_values(['contact_name', 'date'])

    # Calculate streak ID (changes when there's a gap > 1 day)
    daily['prev_date'] = daily.groupby('contact_name')['date'].shift(1)
    daily['date_dt'] = pd.to_datetime(daily['date'])
    daily['prev_date_dt'] = pd.to_datetime(daily['prev_date'])
    daily['gap'] = (daily['date_dt'] - daily['prev_date_dt']).dt.days
    daily['new_streak'] = (daily['gap'] != 1) | daily['gap'].isna()
    daily['streak_id'] = daily.groupby('contact_name')['new_streak'].cumsum()

    # Calculate streak lengths
    streaks = daily.groupby(['contact_name', 'streak_id']).agg(
        streak_length=('date', 'count'),
        start_date=('date', 'min'),
        end_date=('date', 'max'),
    ).reset_index()

    # Get longest streak per contact
    idx = streaks.groupby('contact_name')['streak_length'].idxmax()
    longest = streaks.loc[idx][['contact_name', 'streak_length', 'start_date', 'end_date']]

    return longest.sort_values('streak_length', ascending=False).head(top_n)

def get_active_days_per_year(df):
    """Count days with at least one message sent per year."""
    sent = df[df['is_from_me'] == 1]
    daily = sent.groupby(['year', 'date']).size().reset_index()
    active_days = daily.groupby('year').size().reset_index(name='active_days')

    return active_days

if __name__ == "__main__":
    from extract import extract_messages
    from contacts import get_contacts_from_macos, create_contact_mappings

    df = extract_messages()
    contacts_map = get_contacts_from_macos()
    mappings = create_contact_mappings(df, contacts_map)
    df['contact_name'] = df['contact_id'].astype(str).map(mappings)

    print("\n=== HOUR x DAY HEATMAP ===")
    print(get_hour_day_heatmap(df))

    print("\n=== PEAK HOURS BY YEAR ===")
    peaks, _ = get_peak_hours_by_year(df)
    print(peaks)

    print("\n=== YEARLY VOLUME ===")
    print(get_yearly_volume(df))

    print("\n=== LONGEST STREAKS ===")
    print(get_longest_streaks(df))
```

**Step 2: Test temporal analysis**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 -m analysis.temporal
```
Expected: Output showing heatmap data, peak hours, yearly volumes, and longest streaks.

---

## Task 6: Content Analysis Module

**Files:**
- Create: `analysis/content.py`

**Step 1: Create analysis/content.py**

```python
"""Content and language analysis."""
import pandas as pd
import numpy as np
import re
from collections import Counter
import emoji
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from config import BORING_PHRASES, BORING_WORDS

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

def extract_emojis(text):
    """Extract all emojis from text."""
    if not text:
        return []
    return [c for c in text if c in emoji.EMOJI_DATA]

def get_top_emojis_by_year(df):
    """Get top emojis for each year."""
    df = df.copy()
    df['emojis'] = df['text'].apply(extract_emojis)

    # Explode to one row per emoji
    emoji_df = df[['year', 'emojis']].explode('emojis')
    emoji_df = emoji_df[emoji_df['emojis'].notna()]

    # Count by year
    counts = emoji_df.groupby(['year', 'emojis']).size().reset_index(name='count')

    # Rank within year
    counts['rank'] = counts.groupby('year')['count'].rank(ascending=False, method='min')

    top_per_year = counts[counts['rank'] <= 10].sort_values(['year', 'rank'])

    return top_per_year

def get_emoji_by_contact(df, top_n=10):
    """Get most used emojis per contact."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['emojis'] = sent['text'].apply(extract_emojis)

    emoji_df = sent[['contact_name', 'emojis']].explode('emojis')
    emoji_df = emoji_df[emoji_df['emojis'].notna()]

    # Get top emoji per contact
    counts = emoji_df.groupby(['contact_name', 'emojis']).size().reset_index(name='count')
    counts['rank'] = counts.groupby('contact_name')['count'].rank(ascending=False, method='min')

    top_per_contact = counts[counts['rank'] <= 5].sort_values(['contact_name', 'rank'])

    return top_per_contact

def is_question(text):
    """Check if text is a question."""
    if not text:
        return False
    return '?' in text

def get_question_ratio_by_year(df):
    """Get ratio of questions per year."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['is_question'] = sent['text'].apply(is_question)

    yearly = sent.groupby('year').agg(
        total=('message_id', 'count'),
        questions=('is_question', 'sum'),
    ).reset_index()

    yearly['question_pct'] = yearly['questions'] / yearly['total'] * 100

    return yearly

def get_question_ratio_by_contact(df, min_messages=50):
    """Get ratio of questions per contact."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['is_question'] = sent['text'].apply(is_question)

    by_contact = sent.groupby('contact_name').agg(
        total=('message_id', 'count'),
        questions=('is_question', 'sum'),
    ).reset_index()

    by_contact = by_contact[by_contact['total'] >= min_messages]
    by_contact['question_pct'] = by_contact['questions'] / by_contact['total'] * 100

    return by_contact.sort_values('question_pct', ascending=False)

def calculate_sentiment(text):
    """Calculate VADER sentiment score."""
    if not text:
        return {'compound': 0, 'pos': 0, 'neu': 0, 'neg': 0}
    try:
        return sia.polarity_scores(text)
    except:
        return {'compound': 0, 'pos': 0, 'neu': 0, 'neg': 0}

def get_sentiment_by_contact(df, min_messages=50):
    """Get average sentiment scores per contact."""
    df = df.copy()

    # Calculate sentiment for all messages
    sentiments = df['text'].apply(calculate_sentiment)
    df['sentiment_compound'] = sentiments.apply(lambda x: x['compound'])
    df['sentiment_pos'] = sentiments.apply(lambda x: x['pos'])
    df['sentiment_neg'] = sentiments.apply(lambda x: x['neg'])

    # Aggregate by contact
    by_contact = df.groupby('contact_name').agg(
        total_messages=('message_id', 'count'),
        avg_sentiment=('sentiment_compound', 'mean'),
        avg_positive=('sentiment_pos', 'mean'),
        avg_negative=('sentiment_neg', 'mean'),
    ).reset_index()

    by_contact = by_contact[by_contact['total_messages'] >= min_messages]

    return by_contact.sort_values('avg_sentiment', ascending=False)

def clean_text_for_phrases(text):
    """Clean text for phrase extraction."""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove special chars but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text

def get_top_phrases_by_year(df, n_phrases=20):
    """Get top phrases for each year, excluding boring ones."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    results = []

    for year in sorted(sent['year'].unique()):
        year_texts = sent[sent['year'] == year]['clean_text'].tolist()

        # Extract 2-4 word phrases
        vectorizer = CountVectorizer(ngram_range=(2, 4), min_df=3, max_df=0.5)
        try:
            X = vectorizer.fit_transform(year_texts)
            phrases = vectorizer.get_feature_names_out()
            counts = X.sum(axis=0).A1

            phrase_counts = list(zip(phrases, counts))
            phrase_counts.sort(key=lambda x: x[1], reverse=True)

            # Filter out boring phrases
            filtered = []
            for phrase, count in phrase_counts:
                # Check if phrase contains boring phrase
                is_boring = False
                for boring in BORING_PHRASES:
                    if boring in phrase or phrase in boring:
                        is_boring = True
                        break

                # Check if all words are boring
                words = phrase.split()
                if all(w in BORING_WORDS for w in words):
                    is_boring = True

                if not is_boring:
                    filtered.append({'year': year, 'phrase': phrase, 'count': int(count)})

                if len(filtered) >= n_phrases:
                    break

            results.extend(filtered)
        except:
            continue

    return pd.DataFrame(results)

def get_unique_words_by_year(df, n_words=10):
    """Find words that spiked in specific years using TF-IDF."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    # Combine all texts by year
    yearly_texts = sent.groupby('year')['clean_text'].apply(' '.join).reset_index()

    # TF-IDF across years
    vectorizer = TfidfVectorizer(min_df=1, stop_words='english', max_features=5000)
    X = vectorizer.fit_transform(yearly_texts['clean_text'])
    features = vectorizer.get_feature_names_out()

    results = []
    for idx, year in enumerate(yearly_texts['year']):
        scores = X[idx].toarray().flatten()
        top_indices = scores.argsort()[-n_words*3:][::-1]

        count = 0
        for i in top_indices:
            word = features[i]
            if word not in BORING_WORDS and len(word) > 2:
                results.append({
                    'year': year,
                    'word': word,
                    'tfidf_score': float(scores[i])
                })
                count += 1
                if count >= n_words:
                    break

    return pd.DataFrame(results)

def get_topics_by_year(df, n_topics=5, n_top_words=8):
    """Extract topics per year using NMF."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    results = []

    for year in sorted(sent['year'].unique()):
        year_texts = sent[sent['year'] == year]['clean_text'].tolist()

        if len(year_texts) < 100:
            continue

        try:
            # TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=1000,
                min_df=5,
                max_df=0.7,
                stop_words='english'
            )
            X = vectorizer.fit_transform(year_texts)
            features = vectorizer.get_feature_names_out()

            # NMF for topic modeling
            nmf = NMF(n_components=min(n_topics, len(year_texts)//20), random_state=42, max_iter=200)
            nmf.fit(X)

            for topic_idx, topic in enumerate(nmf.components_):
                top_word_indices = topic.argsort()[-n_top_words:][::-1]
                top_words = [features[i] for i in top_word_indices if features[i] not in BORING_WORDS][:5]

                if top_words:
                    results.append({
                        'year': year,
                        'topic_id': topic_idx,
                        'top_words': ', '.join(top_words),
                    })
        except Exception as e:
            print(f"Topic modeling failed for {year}: {e}")
            continue

    return pd.DataFrame(results)

def get_topics_by_contact(df, contacts=None, n_topics=3, n_top_words=5):
    """Extract topics per contact."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    if contacts is None:
        # Use top 10 contacts by message count
        top = sent.groupby('contact_name').size().sort_values(ascending=False).head(10)
        contacts = top.index.tolist()

    results = []

    for contact in contacts:
        contact_texts = sent[sent['contact_name'] == contact]['clean_text'].tolist()

        if len(contact_texts) < 50:
            continue

        try:
            vectorizer = TfidfVectorizer(
                max_features=500,
                min_df=3,
                max_df=0.8,
                stop_words='english'
            )
            X = vectorizer.fit_transform(contact_texts)
            features = vectorizer.get_feature_names_out()

            nmf = NMF(n_components=min(n_topics, len(contact_texts)//20), random_state=42, max_iter=200)
            nmf.fit(X)

            for topic_idx, topic in enumerate(nmf.components_):
                top_word_indices = topic.argsort()[-n_top_words*2:][::-1]
                top_words = [features[i] for i in top_word_indices if features[i] not in BORING_WORDS][:n_top_words]

                if top_words:
                    results.append({
                        'contact_name': contact,
                        'topic_id': topic_idx,
                        'top_words': ', '.join(top_words),
                    })
        except:
            continue

    return pd.DataFrame(results)

def add_sentiment_to_df(df):
    """Add sentiment scores to dataframe."""
    sentiments = df['text'].apply(calculate_sentiment)
    df = df.copy()
    df['sentiment_compound'] = sentiments.apply(lambda x: x['compound'])
    df['sentiment_pos'] = sentiments.apply(lambda x: x['pos'])
    df['sentiment_neg'] = sentiments.apply(lambda x: x['neg'])
    return df

if __name__ == "__main__":
    from extract import extract_messages
    from contacts import get_contacts_from_macos, create_contact_mappings

    df = extract_messages()
    contacts_map = get_contacts_from_macos()
    mappings = create_contact_mappings(df, contacts_map)
    df['contact_name'] = df['contact_id'].astype(str).map(mappings)

    print("\n=== TOP EMOJIS BY YEAR ===")
    print(get_top_emojis_by_year(df).head(20))

    print("\n=== QUESTION RATIO BY YEAR ===")
    print(get_question_ratio_by_year(df))

    print("\n=== SENTIMENT BY CONTACT ===")
    print(get_sentiment_by_contact(df).head(10))

    print("\n=== TOP PHRASES BY YEAR ===")
    print(get_top_phrases_by_year(df).head(30))

    print("\n=== TOPICS BY YEAR ===")
    print(get_topics_by_year(df))
```

**Step 2: Test content analysis**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 -m analysis.content
```
Expected: Output showing emojis, question ratios, sentiment, phrases, and topics.

Note: This may take a few minutes due to sentiment analysis and topic modeling.

---

## Task 7: Visualization Module

**Files:**
- Create: `visualize.py`

**Step 1: Create visualize.py**

```python
"""Generate Plotly visualizations for the report."""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Color scheme (dark theme friendly)
COLORS = px.colors.qualitative.Set2
BG_COLOR = '#1a1a2e'
PAPER_COLOR = '#16213e'
TEXT_COLOR = '#eaeaea'
GRID_COLOR = '#2d3a4f'

def style_fig(fig):
    """Apply consistent dark theme styling."""
    fig.update_layout(
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR, family='Inter, sans-serif'),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    return fig

def create_bump_chart(rankings_df, title="Contact Rankings Over Time"):
    """Create bump chart showing ranking changes over years."""
    fig = go.Figure()

    contacts = rankings_df['contact_name'].unique()

    for i, contact in enumerate(contacts):
        contact_data = rankings_df[rankings_df['contact_name'] == contact]
        fig.add_trace(go.Scatter(
            x=contact_data['year'],
            y=contact_data['rank'],
            mode='lines+markers',
            name=contact,
            line=dict(width=3, color=COLORS[i % len(COLORS)]),
            marker=dict(size=10),
            hovertemplate=f'{contact}<br>Year: %{{x}}<br>Rank: %{{y}}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Rank',
        yaxis=dict(autorange='reversed', dtick=1),  # Rank 1 at top
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    return style_fig(fig)

def create_stacked_area(monthly_df, title="Message Volume Over Time"):
    """Create stacked area chart of message volume by contact."""
    # Pivot data
    pivot = monthly_df.pivot(index='year_month', columns='contact_name', values='count').fillna(0)

    fig = go.Figure()

    for i, contact in enumerate(pivot.columns):
        fig.add_trace(go.Scatter(
            x=pivot.index,
            y=pivot[contact],
            mode='lines',
            name=contact,
            stackgroup='one',
            line=dict(width=0.5, color=COLORS[i % len(COLORS)]),
            fillcolor=COLORS[i % len(COLORS)],
            hovertemplate=f'{contact}<br>%{{x}}<br>Messages: %{{y}}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Messages',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    return style_fig(fig)

def create_lopsidedness_scatter(lopsidedness_df, title="Conversation Balance"):
    """Create scatter plot of lopsidedness vs total messages."""
    fig = px.scatter(
        lopsidedness_df,
        x='total',
        y='lopsidedness',
        text='contact_name',
        size='total',
        color='lopsidedness',
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=1.0,
        hover_data=['sent', 'received'],
    )

    fig.add_hline(y=1.0, line_dash='dash', line_color='white', opacity=0.5,
                  annotation_text='Balanced', annotation_position='right')

    fig.update_traces(textposition='top center', textfont_size=10)

    fig.update_layout(
        title=title,
        xaxis_title='Total Messages',
        yaxis_title='Lopsidedness Ratio (>1 = you send more)',
        xaxis_type='log',
        yaxis_type='log',
        showlegend=False,
    )

    return style_fig(fig)

def create_hour_day_heatmap(heatmap_df, title="When You Text"):
    """Create hour x day of week heatmap."""
    fig = px.imshow(
        heatmap_df.values,
        x=list(range(24)),
        y=heatmap_df.index,
        color_continuous_scale='Viridis',
        aspect='auto',
        labels=dict(x='Hour of Day', y='Day of Week', color='Messages'),
    )

    fig.update_layout(
        title=title,
        xaxis=dict(dtick=2, tickmode='linear'),
    )

    return style_fig(fig)

def create_yearly_volume_bar(yearly_df, title="Messages Per Year"):
    """Create bar chart of sent vs received per year."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=yearly_df['year'],
        y=yearly_df['sent'],
        name='Sent',
        marker_color='#4ecdc4',
    ))

    fig.add_trace(go.Bar(
        x=yearly_df['year'],
        y=yearly_df['received'],
        name='Received',
        marker_color='#ff6b6b',
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Messages',
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    return style_fig(fig)

def create_peak_hours_small_multiples(hourly_by_year_df, title="Peak Hours By Year"):
    """Create small multiples showing hourly distribution per year."""
    years = sorted(hourly_by_year_df['year'].unique())
    n_years = len(years)
    cols = 3
    rows = (n_years + cols - 1) // cols

    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[str(y) for y in years],
        shared_xaxes=True,
        shared_yaxes=True,
        vertical_spacing=0.08,
        horizontal_spacing=0.05,
    )

    for i, year in enumerate(years):
        row = i // cols + 1
        col = i % cols + 1

        year_data = hourly_by_year_df[hourly_by_year_df['year'] == year]

        fig.add_trace(
            go.Bar(
                x=year_data['hour'],
                y=year_data['count'],
                marker_color='#4ecdc4',
                showlegend=False,
            ),
            row=row, col=col
        )

    fig.update_layout(
        title=title,
        height=200 * rows,
    )

    return style_fig(fig)

def create_sentiment_bar(sentiment_df, title="Conversation Vibes", top_n=15):
    """Create horizontal bar chart of sentiment by contact."""
    df = sentiment_df.head(top_n).copy()
    df = df.sort_values('avg_sentiment')

    colors = ['#ff6b6b' if x < 0 else '#4ecdc4' for x in df['avg_sentiment']]

    fig = go.Figure(go.Bar(
        x=df['avg_sentiment'],
        y=df['contact_name'],
        orientation='h',
        marker_color=colors,
        hovertemplate='%{y}<br>Sentiment: %{x:.3f}<extra></extra>'
    ))

    fig.add_vline(x=0, line_color='white', opacity=0.5)

    fig.update_layout(
        title=title,
        xaxis_title='Average Sentiment (negative ← → positive)',
        yaxis_title='',
        height=max(400, top_n * 30),
    )

    return style_fig(fig)

def create_emoji_grid(emoji_df, title="Your Emoji Story"):
    """Create emoji grid by year."""
    years = sorted(emoji_df['year'].unique())

    # Create text representation
    text_rows = []
    for year in years:
        year_emojis = emoji_df[emoji_df['year'] == year].sort_values('rank').head(5)
        emoji_str = ' '.join(year_emojis['emojis'].tolist())
        text_rows.append(f"<b>{year}</b>: {emoji_str}")

    fig = go.Figure()

    # Use annotations for emojis (better rendering)
    for i, year in enumerate(years):
        year_emojis = emoji_df[emoji_df['year'] == year].sort_values('rank').head(5)
        for j, (_, row) in enumerate(year_emojis.iterrows()):
            fig.add_annotation(
                x=j, y=len(years) - i - 1,
                text=row['emojis'],
                font=dict(size=24),
                showarrow=False,
            )

    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 5.5]),
        yaxis=dict(
            showgrid=False, zeroline=False,
            tickmode='array',
            tickvals=list(range(len(years))),
            ticktext=[str(y) for y in reversed(years)],
        ),
        height=50 * len(years) + 100,
    )

    return style_fig(fig)

def create_question_ratio_line(question_df, title="Questions Over Time"):
    """Create line chart of question percentage by year."""
    fig = px.line(
        question_df,
        x='year',
        y='question_pct',
        markers=True,
        line_shape='spline',
    )

    fig.update_traces(
        line=dict(color='#4ecdc4', width=3),
        marker=dict(size=10),
    )

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='% of Messages That Are Questions',
    )

    return style_fig(fig)

if __name__ == "__main__":
    print("Visualization module loaded successfully")
```

**Step 2: Verify visualize module loads**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 -c "from visualize import *; print('Visualizations loaded successfully')"
```
Expected: "Visualizations loaded successfully"

---

## Task 8: HTML Report Generator

**Files:**
- Create: `report.py`

**Step 1: Create report.py**

```python
"""Generate the final HTML report."""
import json
from pathlib import Path
from config import OUTPUT_DIR, START_YEAR, END_YEAR

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iMessage Wrapped {start_year}-{end_year}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f0f23 100%);
            color: #eaeaea;
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            text-align: center;
            padding: 4rem 2rem;
            background: linear-gradient(180deg, rgba(78, 205, 196, 0.1) 0%, transparent 100%);
        }}

        h1 {{
            font-size: 3rem;
            background: linear-gradient(135deg, #4ecdc4, #44a08d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }}

        .stats-overview {{
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }}

        .stat-box {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #4ecdc4;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        section {{
            margin: 4rem 0;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        h2 {{
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            color: #4ecdc4;
        }}

        h3 {{
            font-size: 1.3rem;
            margin: 1.5rem 0 1rem;
            color: #fff;
        }}

        .podium {{
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 1rem;
            margin: 2rem 0;
        }}

        .podium-item {{
            text-align: center;
            padding: 1.5rem;
            border-radius: 12px;
            background: rgba(78, 205, 196, 0.1);
        }}

        .podium-item.first {{
            order: 2;
            transform: scale(1.1);
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 215, 0, 0.05));
            border: 1px solid rgba(255, 215, 0, 0.3);
        }}

        .podium-item.second {{
            order: 1;
            background: linear-gradient(135deg, rgba(192, 192, 192, 0.2), rgba(192, 192, 192, 0.05));
            border: 1px solid rgba(192, 192, 192, 0.3);
        }}

        .podium-item.third {{
            order: 3;
            background: linear-gradient(135deg, rgba(205, 127, 50, 0.2), rgba(205, 127, 50, 0.05));
            border: 1px solid rgba(205, 127, 50, 0.3);
        }}

        .podium-rank {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        .podium-name {{
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }}

        .podium-count {{
            font-size: 0.9rem;
            color: #888;
        }}

        .contact-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .contact-card {{
            padding: 1rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .contact-rank {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #4ecdc4;
            min-width: 2rem;
        }}

        .contact-info {{
            flex: 1;
        }}

        .contact-name {{
            font-weight: bold;
        }}

        .contact-stats {{
            font-size: 0.85rem;
            color: #888;
        }}

        .chart {{
            margin: 1.5rem 0;
            border-radius: 12px;
            overflow: hidden;
        }}

        .insights {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }}

        .insight-card {{
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            border-left: 3px solid #4ecdc4;
        }}

        .insight-title {{
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #4ecdc4;
        }}

        .phrase-cards {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }}

        .phrase-card {{
            padding: 0.5rem 1rem;
            background: rgba(78, 205, 196, 0.15);
            border-radius: 20px;
            font-size: 0.9rem;
        }}

        .year-section {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
        }}

        .year-title {{
            font-size: 1.4rem;
            color: #4ecdc4;
            margin-bottom: 1rem;
        }}

        .emoji-row {{
            font-size: 2rem;
            margin: 0.5rem 0;
        }}

        .topics-list {{
            list-style: none;
            padding: 0;
        }}

        .topics-list li {{
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .topics-list li:last-child {{
            border-bottom: none;
        }}

        footer {{
            text-align: center;
            padding: 3rem;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Your iMessage Wrapped</h1>
        <p>{start_year} - {end_year}</p>
        <div class="stats-overview">
            <div class="stat-box">
                <div class="stat-number">{total_messages:,}</div>
                <div class="stat-label">Total Messages</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_sent:,}</div>
                <div class="stat-label">Sent</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_received:,}</div>
                <div class="stat-label">Received</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_contacts:,}</div>
                <div class="stat-label">People</div>
            </div>
        </div>
    </header>

    <div class="container">
        {sections}
    </div>

    <footer>
        <p>Generated with iMessage Wrapped</p>
    </footer>
</body>
</html>
"""

def create_podium_html(top_contacts):
    """Create podium HTML for top 3 contacts."""
    if len(top_contacts) < 3:
        return ""

    top3 = top_contacts.head(3).to_dict('records')

    return f"""
    <div class="podium">
        <div class="podium-item second">
            <div class="podium-rank">2</div>
            <div class="podium-name">{top3[1]['contact_name']}</div>
            <div class="podium-count">{top3[1]['total_messages']:,} messages</div>
        </div>
        <div class="podium-item first">
            <div class="podium-rank">1</div>
            <div class="podium-name">{top3[0]['contact_name']}</div>
            <div class="podium-count">{top3[0]['total_messages']:,} messages</div>
        </div>
        <div class="podium-item third">
            <div class="podium-rank">3</div>
            <div class="podium-name">{top3[2]['contact_name']}</div>
            <div class="podium-count">{top3[2]['total_messages']:,} messages</div>
        </div>
    </div>
    """

def create_contact_list_html(contacts, start_rank=4):
    """Create contact list HTML."""
    cards = []
    for i, contact in enumerate(contacts.to_dict('records'), start=start_rank):
        cards.append(f"""
        <div class="contact-card">
            <div class="contact-rank">{i}</div>
            <div class="contact-info">
                <div class="contact-name">{contact['contact_name']}</div>
                <div class="contact-stats">{contact['total_messages']:,} messages</div>
            </div>
        </div>
        """)
    return '<div class="contact-list">' + ''.join(cards) + '</div>'

def create_insight_card(title, content):
    """Create an insight card."""
    return f"""
    <div class="insight-card">
        <div class="insight-title">{title}</div>
        <div>{content}</div>
    </div>
    """

def create_phrases_html(phrases_df, year):
    """Create phrase cards for a year."""
    year_phrases = phrases_df[phrases_df['year'] == year].head(10)
    if year_phrases.empty:
        return ""

    cards = [f'<span class="phrase-card">"{row["phrase"]}"</span>'
             for _, row in year_phrases.iterrows()]
    return '<div class="phrase-cards">' + ''.join(cards) + '</div>'

def embed_plotly_chart(fig, div_id):
    """Convert plotly figure to embedded HTML."""
    return f"""
    <div class="chart" id="{div_id}"></div>
    <script>
        var data = {fig.to_json()};
        Plotly.newPlot('{div_id}', data.data, data.layout, {{responsive: true}});
    </script>
    """

def generate_report(
    total_messages,
    total_sent,
    total_received,
    total_contacts,
    top_contacts,
    charts,
    phrases_df,
    emojis_df,
    topics_df,
    insights,
):
    """Generate the complete HTML report."""
    sections = []

    # Section 1: Top People
    section1 = f"""
    <section>
        <h2>Your Top People (All-Time)</h2>
        {create_podium_html(top_contacts)}
        {create_contact_list_html(top_contacts.iloc[3:15], start_rank=4)}
    </section>
    """
    sections.append(section1)

    # Section 2: Relationships Over Time
    section2 = f"""
    <section>
        <h2>Relationships Over Time</h2>
        {embed_plotly_chart(charts['bump'], 'bump-chart')}
        {embed_plotly_chart(charts['stacked_area'], 'stacked-area-chart')}
    </section>
    """
    sections.append(section2)

    # Section 3: Relationship Dynamics
    insights_html = '<div class="insights">' + ''.join([
        create_insight_card(title, content) for title, content in insights.get('dynamics', [])
    ]) + '</div>'

    section3 = f"""
    <section>
        <h2>Relationship Dynamics</h2>
        {embed_plotly_chart(charts['lopsidedness'], 'lopsidedness-chart')}
        <h3>Key Insights</h3>
        {insights_html}
    </section>
    """
    sections.append(section3)

    # Section 4: When You Text
    section4 = f"""
    <section>
        <h2>When You Text</h2>
        {embed_plotly_chart(charts['heatmap'], 'heatmap-chart')}
        {embed_plotly_chart(charts['peak_hours'], 'peak-hours-chart')}
        {embed_plotly_chart(charts['yearly_volume'], 'yearly-volume-chart')}
    </section>
    """
    sections.append(section4)

    # Section 5: What You Say
    years = sorted(phrases_df['year'].unique())
    phrase_sections = []
    for year in years:
        phrases_html = create_phrases_html(phrases_df, year)
        if phrases_html:
            phrase_sections.append(f"""
            <div class="year-section">
                <div class="year-title">{year}</div>
                {phrases_html}
            </div>
            """)

    section5 = f"""
    <section>
        <h2>What You Say</h2>
        <h3>Top Phrases By Year</h3>
        {''.join(phrase_sections)}
        {embed_plotly_chart(charts['question_ratio'], 'question-ratio-chart')}
    </section>
    """
    sections.append(section5)

    # Section 6: Emoji Story
    section6 = f"""
    <section>
        <h2>Your Emoji Story</h2>
        {embed_plotly_chart(charts['emoji_grid'], 'emoji-grid-chart')}
    </section>
    """
    sections.append(section6)

    # Section 7: Vibes & Topics
    topics_html = ""
    if not topics_df.empty:
        topics_by_year = topics_df.groupby('year').apply(
            lambda x: ', '.join(x['top_words'].head(3).tolist())
        ).reset_index()
        topics_by_year.columns = ['year', 'topics']

        topics_items = [f"<li><strong>{row['year']}</strong>: {row['topics']}</li>"
                       for _, row in topics_by_year.iterrows()]
        topics_html = '<ul class="topics-list">' + ''.join(topics_items) + '</ul>'

    section7 = f"""
    <section>
        <h2>Vibes & Topics</h2>
        {embed_plotly_chart(charts['sentiment'], 'sentiment-chart')}
        <h3>Topics By Year</h3>
        {topics_html}
    </section>
    """
    sections.append(section7)

    # Assemble final HTML
    html = HTML_TEMPLATE.format(
        start_year=START_YEAR,
        end_year=END_YEAR,
        total_messages=total_messages,
        total_sent=total_sent,
        total_received=total_received,
        total_contacts=total_contacts,
        sections=''.join(sections),
    )

    return html

def save_report(html, filename="wrapped.html"):
    """Save HTML report to file."""
    output_path = OUTPUT_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    print("Report module loaded successfully")
```

**Step 2: Verify report module loads**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 -c "from report import *; print('Report module loaded successfully')"
```
Expected: "Report module loaded successfully"

---

## Task 9: Main Orchestration Script

**Files:**
- Create: `main.py`

**Step 1: Create main.py**

```python
"""Main orchestration script for iMessage Wrapped."""
import pandas as pd
from pathlib import Path

from config import DATA_DIR, START_YEAR, END_YEAR
from extract import extract_messages
from contacts import (
    get_contacts_from_macos,
    create_contact_mappings,
    save_contact_mappings,
    prompt_for_unresolved,
)
from analysis.people import (
    get_top_contacts_alltime,
    get_top_contacts_by_year,
    calculate_lopsidedness,
    get_conversation_initiator_stats,
    calculate_response_times,
    find_rising_stars,
    find_faded_connections,
    get_message_volume_over_time,
)
from analysis.temporal import (
    get_hour_day_heatmap,
    get_peak_hours_by_year,
    get_yearly_volume,
    get_longest_streaks,
)
from analysis.content import (
    get_top_emojis_by_year,
    get_emoji_by_contact,
    get_question_ratio_by_year,
    get_question_ratio_by_contact,
    get_sentiment_by_contact,
    get_top_phrases_by_year,
    get_unique_words_by_year,
    get_topics_by_year,
    get_topics_by_contact,
    add_sentiment_to_df,
)
from visualize import (
    create_bump_chart,
    create_stacked_area,
    create_lopsidedness_scatter,
    create_hour_day_heatmap,
    create_yearly_volume_bar,
    create_peak_hours_small_multiples,
    create_sentiment_bar,
    create_emoji_grid,
    create_question_ratio_line,
)
from report import generate_report, save_report


def main():
    print("=" * 60)
    print("iMessage Wrapped Generator")
    print("=" * 60)

    # Step 1: Extract messages
    print("\n[1/8] Extracting messages...")
    df = extract_messages()

    # Step 2: Resolve contacts
    print("\n[2/8] Resolving contacts...")
    contacts_map = get_contacts_from_macos()
    mappings = create_contact_mappings(df, contacts_map)
    save_contact_mappings(mappings)
    df['contact_name'] = df['contact_id'].astype(str).map(mappings)

    # Check for unresolved top contacts
    unresolved = prompt_for_unresolved(df, mappings, top_n=20)
    if unresolved:
        print("\nNote: Some top contacts couldn't be resolved to names:")
        for contact_id, count in unresolved[:5]:
            print(f"  {contact_id}: {count:,} messages")
        print("  (You can manually edit output/data/contacts.json to add names)")

    # Step 3: People analysis
    print("\n[3/8] Analyzing relationships...")
    top_contacts = get_top_contacts_alltime(df)
    top_by_year = get_top_contacts_by_year(df)
    lopsidedness = calculate_lopsidedness(df)
    initiators = get_conversation_initiator_stats(df)
    response_times = calculate_response_times(df)

    # Get top contact names for charts
    top_names = top_contacts['contact_name'].head(10).tolist()
    monthly_volume = get_message_volume_over_time(df, contacts=top_names)

    # Rising stars and faded connections
    years = sorted(df['year'].unique())
    rising_stars = []
    faded = []
    for i in range(len(years) - 1):
        rs = find_rising_stars(df, years[i], years[i+1])
        if not rs.empty:
            rising_stars.append((years[i+1], rs))
        fd = find_faded_connections(df, years[i], years[i+1])
        if not fd.empty:
            faded.append((years[i+1], fd))

    # Step 4: Temporal analysis
    print("\n[4/8] Analyzing temporal patterns...")
    heatmap_data = get_hour_day_heatmap(df)
    peak_hours, hourly_by_year = get_peak_hours_by_year(df)
    yearly_volume = get_yearly_volume(df)
    streaks = get_longest_streaks(df)

    # Step 5: Content analysis
    print("\n[5/8] Analyzing content (this may take a while)...")
    emojis_by_year = get_top_emojis_by_year(df)
    emojis_by_contact = get_emoji_by_contact(df)
    question_ratio = get_question_ratio_by_year(df)
    question_by_contact = get_question_ratio_by_contact(df)

    print("  - Computing sentiment...")
    sentiment_by_contact = get_sentiment_by_contact(df)

    print("  - Extracting phrases...")
    phrases = get_top_phrases_by_year(df)
    unique_words = get_unique_words_by_year(df)

    print("  - Topic modeling...")
    topics_by_year = get_topics_by_year(df)
    topics_by_contact = get_topics_by_contact(df, contacts=top_names[:10])

    # Step 6: Save data for follow-up queries
    print("\n[6/8] Saving data for follow-up queries...")
    df_with_sentiment = add_sentiment_to_df(df)
    df_with_sentiment.to_parquet(DATA_DIR / "messages.parquet")
    sentiment_by_contact.to_parquet(DATA_DIR / "sentiment_scores.parquet")
    topics_by_year.to_parquet(DATA_DIR / "topics.parquet")

    yearly_stats = {
        'yearly_volume': yearly_volume.to_dict('records'),
        'top_by_year': top_by_year.to_dict('records'),
        'peak_hours': peak_hours.to_dict('records'),
    }
    import json
    with open(DATA_DIR / "yearly_stats.json", 'w') as f:
        json.dump(yearly_stats, f, indent=2, default=str)

    # Step 7: Generate visualizations
    print("\n[7/8] Generating visualizations...")
    charts = {
        'bump': create_bump_chart(top_by_year[top_by_year['contact_name'].isin(top_names)]),
        'stacked_area': create_stacked_area(monthly_volume),
        'lopsidedness': create_lopsidedness_scatter(lopsidedness.head(30)),
        'heatmap': create_hour_day_heatmap(heatmap_data),
        'yearly_volume': create_yearly_volume_bar(yearly_volume),
        'peak_hours': create_peak_hours_small_multiples(hourly_by_year),
        'sentiment': create_sentiment_bar(sentiment_by_contact, top_n=20),
        'emoji_grid': create_emoji_grid(emojis_by_year),
        'question_ratio': create_question_ratio_line(question_ratio),
    }

    # Build insights
    insights = {'dynamics': []}

    # Most balanced relationship
    balanced = lopsidedness[
        (lopsidedness['lopsidedness'] > 0.8) &
        (lopsidedness['lopsidedness'] < 1.2)
    ].sort_values('total', ascending=False)
    if not balanced.empty:
        top_balanced = balanced.iloc[0]
        insights['dynamics'].append((
            "Most Balanced",
            f"{top_balanced['contact_name']} - nearly equal messages sent and received"
        ))

    # You text them the most
    most_lopsided_you = lopsidedness.head(1)
    if not most_lopsided_you.empty:
        row = most_lopsided_you.iloc[0]
        insights['dynamics'].append((
            "You Text Most",
            f"{row['contact_name']} - you send {row['lopsidedness']:.1f}x more messages"
        ))

    # They text you the most
    most_lopsided_them = lopsidedness.tail(1)
    if not most_lopsided_them.empty:
        row = most_lopsided_them.iloc[0]
        insights['dynamics'].append((
            "They Text Most",
            f"{row['contact_name']} - they send {1/row['lopsidedness']:.1f}x more messages"
        ))

    # Fastest responder
    if not response_times.empty:
        valid_response = response_times.dropna(subset=['their_response_time_min'])
        if not valid_response.empty:
            fastest = valid_response.sort_values('their_response_time_min').iloc[0]
            insights['dynamics'].append((
                "Fastest Responder",
                f"{fastest['contact_name']} - median response time: {fastest['their_response_time_min']:.0f} min"
            ))

    # Longest streak
    if not streaks.empty:
        top_streak = streaks.iloc[0]
        insights['dynamics'].append((
            "Longest Streak",
            f"{top_streak['contact_name']} - {top_streak['streak_length']} consecutive days"
        ))

    # Step 8: Generate report
    print("\n[8/8] Generating HTML report...")

    total_messages = len(df)
    total_sent = df['is_from_me'].sum()
    total_received = total_messages - total_sent
    total_contacts = df['contact_name'].nunique()

    html = generate_report(
        total_messages=total_messages,
        total_sent=int(total_sent),
        total_received=int(total_received),
        total_contacts=total_contacts,
        top_contacts=top_contacts,
        charts=charts,
        phrases_df=phrases,
        emojis_df=emojis_by_year,
        topics_df=topics_by_year,
        insights=insights,
    )

    output_path = save_report(html)

    print("\n" + "=" * 60)
    print("Done!")
    print(f"Report saved to: {output_path}")
    print(f"Data saved to: {DATA_DIR}")
    print("\nOpen the report with:")
    print(f"  open {output_path}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    main()
```

**Step 2: Run the complete pipeline**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 main.py
```
Expected: Progress output for each step, ending with path to generated report.

**Step 3: Open and verify the report**

Run:
```bash
open ~/imessage-wrapped/output/wrapped.html
```
Expected: Report opens in browser showing all visualizations and stats.

---

## Task 10: Manual Contact Mapping (Optional)

If there are unresolved top contacts, you can manually map them:

**Step 1: Check unresolved contacts**

Run:
```bash
cd ~/imessage-wrapped && cat output/data/contacts.json | python3 -c "import json,sys; d=json.load(sys.stdin); print([k for k,v in d.items() if k==v][:20])"
```

**Step 2: Edit contacts.json**

Open `output/data/contacts.json` and replace phone numbers with names for your top contacts.

**Step 3: Re-run pipeline**

Run:
```bash
cd ~/imessage-wrapped && source venv/bin/activate && python3 main.py
```

---

## Summary

| Task | Description | Key Files |
|------|-------------|-----------|
| 1 | Project setup | requirements.txt, config.py |
| 2 | Data extraction | extract.py |
| 3 | Contact resolution | contacts.py |
| 4 | People analysis | analysis/people.py |
| 5 | Temporal analysis | analysis/temporal.py |
| 6 | Content analysis | analysis/content.py |
| 7 | Visualizations | visualize.py |
| 8 | HTML report | report.py |
| 9 | Orchestration | main.py |
| 10 | Manual mapping | (optional) |
