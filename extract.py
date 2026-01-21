"""Extract iMessage data from chat.db."""
import sqlite3
import pandas as pd
import re
from datetime import datetime
from config import CHAT_DB_PATH, START_YEAR

# Apple's Cocoa epoch: 2001-01-01 00:00:00 UTC
COCOA_EPOCH_OFFSET = 978307200


def extract_text_from_attributed_body(blob):
    """Extract plain text from NSAttributedString blob."""
    if blob is None:
        return None

    try:
        # The text is stored after 'NSString' marker in the blob
        # Look for the pattern: NSString followed by length byte(s) and then text

        # Method 1: Find text after NSString marker
        text_marker = b'NSString'
        idx = blob.find(text_marker)
        if idx != -1:
            # Skip past NSString and some header bytes
            start = idx + len(text_marker)
            # Look for the actual text content
            # Usually format is: NSString + some bytes + length + text
            remaining = blob[start:start+500]

            # Find printable text sequences
            decoded = remaining.decode('utf-8', errors='ignore')
            # Remove control characters but keep the text
            # Text usually starts after a few bytes
            for i in range(min(20, len(decoded))):
                substring = decoded[i:]
                # Check if this looks like the start of real text
                if substring and substring[0].isprintable() and not substring[0].isspace():
                    # Find where the text ends (usually at a control character)
                    end = 0
                    for j, c in enumerate(substring):
                        if ord(c) < 32 and c not in '\n\r\t':
                            end = j
                            break
                    else:
                        end = len(substring)

                    if end > 0:
                        text = substring[:end].strip()
                        if len(text) > 0:
                            return text

        # Method 2: Try to find text between common delimiters
        decoded = blob.decode('utf-8', errors='ignore')
        # Look for substantial printable sequences
        matches = re.findall(r'[\x20-\x7e\n]{5,}', decoded)
        # Filter out known non-text patterns
        for match in matches:
            if not any(skip in match.lower() for skip in ['nsstring', 'nsattributed', 'nsdictionary', 'streamtyped', 'nsmutable', '__kim']):
                cleaned = match.strip()
                if cleaned and len(cleaned) > 1:
                    return cleaned

        return None

    except Exception as e:
        return None


def connect_db():
    """Connect to iMessage database (read-only)."""
    return sqlite3.connect(f"file:{CHAT_DB_PATH}?mode=ro", uri=True)


def extract_messages():
    """Extract all 1:1 messages with metadata."""
    query = """
    SELECT
        m.ROWID as message_id,
        m.text,
        m.attributedBody,
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
        c.chat_identifier NOT LIKE 'chat%'
        AND (m.text IS NOT NULL OR m.attributedBody IS NOT NULL)
    ORDER BY m.date
    """

    with connect_db() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params=(COCOA_EPOCH_OFFSET, COCOA_EPOCH_OFFSET, COCOA_EPOCH_OFFSET)
        )

    print(f"Raw messages fetched: {len(df):,}")

    # Extract text from attributedBody where text is NULL
    def get_message_text(row):
        if row['text'] and str(row['text']).strip():
            return str(row['text'])
        if row['attributedBody']:
            extracted = extract_text_from_attributed_body(row['attributedBody'])
            if extracted:
                return extracted
        return None

    df['text'] = df.apply(get_message_text, axis=1)

    # Drop the blob column and filter out messages with no text
    df = df.drop(columns=['attributedBody'])
    df = df[df['text'].notna() & (df['text'] != '')]

    print(f"Messages with text content: {len(df):,}")

    # Convert timestamps to datetime
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert('America/Los_Angeles')
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day_of_week'] = df['datetime'].dt.dayofweek
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
