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
    stats['lopsidedness'] = stats['sent'] / (stats['received'] + 0.1)
    stats = stats[stats['total'] >= MIN_MESSAGES_FOR_TOP_CONTACT]

    return stats.sort_values('lopsidedness', ascending=False)

def identify_conversation_starts(df):
    """Identify conversation initiators (first message after gap)."""
    df = df.sort_values(['contact_name', 'datetime']).copy()

    df['prev_time'] = df.groupby('contact_name')['datetime'].shift(1)
    df['hours_since_last'] = (df['datetime'] - df['prev_time']).dt.total_seconds() / 3600

    df['is_conversation_start'] = df['hours_since_last'] > CONVERSATION_GAP_HOURS
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
    stats = stats[stats['total_conversations'] >= 10]

    return stats.sort_values('you_initiate_pct', ascending=False)

def calculate_response_times(df):
    """Calculate average response times per contact."""
    df = df.sort_values(['contact_name', 'datetime']).copy()

    df['prev_time'] = df.groupby('contact_name')['datetime'].shift(1)
    df['prev_from_me'] = df.groupby('contact_name')['is_from_me'].shift(1)

    df['is_response'] = df['is_from_me'] != df['prev_from_me']
    df['response_seconds'] = (df['datetime'] - df['prev_time']).dt.total_seconds()

    responses = df[df['is_response'] & (df['response_seconds'] < 86400) & (df['response_seconds'] > 0)]

    your_responses = responses[responses['is_from_me'] == 1]
    your_avg = your_responses.groupby('contact_name')['response_seconds'].median().reset_index()
    your_avg.columns = ['contact_name', 'your_response_time_sec']

    their_responses = responses[responses['is_from_me'] == 0]
    their_avg = their_responses.groupby('contact_name')['response_seconds'].median().reset_index()
    their_avg.columns = ['contact_name', 'their_response_time_sec']

    response_stats = your_avg.merge(their_avg, on='contact_name', how='outer')
    response_stats['your_response_time_min'] = response_stats['your_response_time_sec'] / 60
    response_stats['their_response_time_min'] = response_stats['their_response_time_sec'] / 60

    return response_stats

def find_rising_stars(df, year1, year2, top_n=20):
    """Find contacts who rose significantly in rankings between years."""
    yearly = get_top_contacts_by_year(df, n=100)

    y1 = yearly[yearly['year'] == year1][['contact_name', 'rank']].rename(columns={'rank': 'rank_y1'})
    y2 = yearly[yearly['year'] == year2][['contact_name', 'rank']].rename(columns={'rank': 'rank_y2'})

    merged = y1.merge(y2, on='contact_name', how='outer')

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

    faded = merged[
        (merged['rank_y1'] <= top_n) &
        ((merged['rank_y2'] > 20) | merged['rank_y2'].isna())
    ]

    return faded.sort_values('rank_y1')

def get_ranking_over_time(df, contacts=None, top_n=10):
    """Get ranking trajectories for specified contacts."""
    yearly = get_top_contacts_by_year(df, n=50)

    if contacts is None:
        top = get_top_contacts_alltime(df, n=top_n)
        contacts = top['contact_name'].tolist()

    yearly = yearly[yearly['contact_name'].isin(contacts)]
    pivot = yearly.pivot(index='year', columns='contact_name', values='rank')

    return pivot, yearly

def get_message_volume_over_time(df, contacts=None, top_n=10):
    """Get message volume by month for top contacts."""
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
