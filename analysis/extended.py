"""Extended analysis using previously unused data fields."""
import pandas as pd
import numpy as np
import re
from urllib.parse import urlparse
from config import MIN_MESSAGES_FOR_TOP_CONTACT


def get_response_time_stats(df: pd.DataFrame, top_contacts: set = None) -> dict:
    """
    Analyze response time patterns - how quickly you and others reply.

    Args:
        df: Message dataframe
        top_contacts: Set of contact names to include (filters to top N by volume)

    Returns stats on:
    - Who responds to you fastest/slowest
    - Who you respond to fastest/slowest
    """
    if len(df) == 0:
        return {'available': False}

    def format_time(seconds):
        if pd.isna(seconds) or seconds < 0:
            return "N/A"
        elif seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        elif seconds < 86400:
            return f"{seconds / 3600:.1f}h"
        else:
            return f"{seconds / 86400:.1f}d"

    # Sort by contact and time
    df_sorted = df.sort_values(['contact_name', 'datetime']).copy()

    # Calculate time since previous message in conversation
    df_sorted['prev_time'] = df_sorted.groupby('contact_name')['datetime'].shift(1)
    df_sorted['prev_sender'] = df_sorted.groupby('contact_name')['is_from_me'].shift(1)
    df_sorted['time_diff'] = (df_sorted['datetime'] - df_sorted['prev_time']).dt.total_seconds()

    # A "response" is when the sender changes (reply to the other person)
    # Filter to only responses (sender changed) within reasonable time (< 1 week)
    responses = df_sorted[
        (df_sorted['prev_sender'].notna()) &
        (df_sorted['is_from_me'] != df_sorted['prev_sender']) &
        (df_sorted['time_diff'] > 0) &
        (df_sorted['time_diff'] < 86400 * 7)  # Within 1 week
    ].copy()

    if len(responses) == 0:
        return {'available': False}

    # Filter to top contacts if provided
    if top_contacts:
        responses = responses[responses['contact_name'].isin(top_contacts)]

    if len(responses) == 0:
        return {'available': False}

    # Their responses to you (they reply after you message)
    their_responses = responses[responses['is_from_me'] == 0]
    # Your responses to them (you reply after they message)
    your_responses = responses[responses['is_from_me'] == 1]

    # Aggregate by contact
    def get_response_stats(resp_df, min_responses=5):
        if len(resp_df) == 0:
            return []
        stats = resp_df.groupby('contact_name').agg({
            'time_diff': ['median', 'count']
        }).reset_index()
        stats.columns = ['contact_name', 'median_seconds', 'response_count']
        stats = stats[stats['response_count'] >= min_responses]
        stats['time_formatted'] = stats['median_seconds'].apply(format_time)
        return stats

    their_stats = get_response_stats(their_responses)
    your_stats = get_response_stats(your_responses)

    # Who responds to you fastest/slowest
    they_respond_fast = []
    they_respond_slow = []
    if len(their_stats) > 0:
        they_respond_fast = their_stats.nsmallest(5, 'median_seconds')[
            ['contact_name', 'median_seconds', 'time_formatted', 'response_count']
        ].to_dict('records')
        they_respond_slow = their_stats.nlargest(5, 'median_seconds')[
            ['contact_name', 'median_seconds', 'time_formatted', 'response_count']
        ].to_dict('records')

    # Who you respond to fastest/slowest
    you_respond_fast = []
    you_respond_slow = []
    if len(your_stats) > 0:
        you_respond_fast = your_stats.nsmallest(5, 'median_seconds')[
            ['contact_name', 'median_seconds', 'time_formatted', 'response_count']
        ].to_dict('records')
        you_respond_slow = your_stats.nlargest(5, 'median_seconds')[
            ['contact_name', 'median_seconds', 'time_formatted', 'response_count']
        ].to_dict('records')

    return {
        'available': True,
        'they_respond_fast': they_respond_fast,
        'they_respond_slow': they_respond_slow,
        'you_respond_fast': you_respond_fast,
        'you_respond_slow': you_respond_slow,
        'total_responses_analyzed': len(responses),
    }


def get_sms_vs_imessage_breakdown(df: pd.DataFrame, top_contacts: set = None) -> dict:
    """
    Analyze SMS vs iMessage usage patterns.

    Args:
        df: Message dataframe
        top_contacts: Set of contact names to include (filters to top N by volume)

    Returns:
    - Overall breakdown
    - Per-contact breakdown
    - Trends over time
    """
    if 'service' not in df.columns:
        return {'available': False}

    # Only use incoming messages (service is None for outgoing messages)
    df_copy = df[df['service'].notna()].copy()
    if len(df_copy) == 0:
        return {'available': False}

    # Normalize service names
    df_copy['service_type'] = df_copy['service'].apply(
        lambda x: 'iMessage' if str(x).lower() == 'imessage' else 'SMS'
    )

    # Overall breakdown
    overall = df_copy['service_type'].value_counts().to_dict()
    total = sum(overall.values())
    overall_pct = {k: round(v / total * 100, 1) for k, v in overall.items()}

    # Per contact breakdown (who do you SMS vs iMessage)
    by_contact = df_copy.groupby(['contact_name', 'service_type']).size().unstack(fill_value=0)
    by_contact['total'] = by_contact.sum(axis=1)
    by_contact = by_contact[by_contact['total'] >= MIN_MESSAGES_FOR_TOP_CONTACT]

    # Filter to top contacts if provided
    if top_contacts:
        by_contact = by_contact[by_contact.index.isin(top_contacts)]

    # Identify SMS-heavy contacts (>50% SMS)
    sms_contacts = []
    if 'SMS' in by_contact.columns:
        by_contact['sms_pct'] = by_contact.get('SMS', 0) / by_contact['total'] * 100
        sms_heavy = by_contact[by_contact['sms_pct'] > 50].nlargest(10, 'sms_pct')
        sms_contacts = [
            {'contact_name': idx, 'sms_pct': round(row['sms_pct'], 1), 'total': int(row['total'])}
            for idx, row in sms_heavy.iterrows()
        ]

    # Yearly trend
    yearly_trend = df_copy.groupby(['year', 'service_type']).size().unstack(fill_value=0)
    yearly_trend_dict = yearly_trend.to_dict('index')

    # Per-contact iMessage percentage lookup
    by_contact['imessage_pct'] = by_contact.get('iMessage', 0) / by_contact['total'] * 100
    imessage_pct_lookup = {idx: round(row['imessage_pct'], 1) for idx, row in by_contact.iterrows()}

    return {
        'available': True,
        'overall': overall,
        'overall_pct': overall_pct,
        'sms_heavy_contacts': sms_contacts,
        'yearly_trend': yearly_trend_dict,
        'imessage_pct_by_contact': imessage_pct_lookup,
    }


def get_attachment_summary(df: pd.DataFrame, attachments_df: pd.DataFrame) -> dict:
    """
    Analyze attachment sharing patterns.

    Returns stats on:
    - Photo/video/file sharing by contact
    - Who sends you the most media
    - Who you send the most media to
    """
    if attachments_df is None or len(attachments_df) == 0:
        return {'available': False}

    # Resolve contact names in attachments
    if 'contact_name' not in attachments_df.columns and 'contact_id' in attachments_df.columns:
        # Create mapping from main df
        contact_map = df[['contact_id', 'contact_name']].drop_duplicates().set_index('contact_id')['contact_name'].to_dict()
        attachments_df = attachments_df.copy()
        attachments_df['contact_name'] = attachments_df['contact_id'].map(contact_map)

    attachments_df = attachments_df[attachments_df['contact_name'].notna()]

    if len(attachments_df) == 0:
        return {'available': False}

    # Overall type breakdown
    type_counts = attachments_df['attachment_type'].value_counts().to_dict()

    # Sent vs received
    sent_attachments = attachments_df[attachments_df['is_from_me'] == 1]
    received_attachments = attachments_df[attachments_df['is_from_me'] == 0]

    sent_by_type = sent_attachments['attachment_type'].value_counts().to_dict()
    received_by_type = received_attachments['attachment_type'].value_counts().to_dict()

    # Top contacts by attachment type
    def get_top_attachment_contacts(attachment_type, n=5):
        type_df = attachments_df[attachments_df['attachment_type'] == attachment_type]
        if len(type_df) == 0:
            return []

        by_contact = type_df.groupby('contact_name').agg({
            'message_id': 'count',
            'is_from_me': 'sum'
        }).rename(columns={'message_id': 'total', 'is_from_me': 'sent'})
        by_contact['received'] = by_contact['total'] - by_contact['sent']

        top = by_contact.nlargest(n, 'total')
        return [
            {
                'contact_name': idx,
                'total': int(row['total']),
                'sent': int(row['sent']),
                'received': int(row['received'])
            }
            for idx, row in top.iterrows()
        ]

    top_photo_contacts = get_top_attachment_contacts('photo')
    top_video_contacts = get_top_attachment_contacts('video')

    # Yearly trend
    yearly = attachments_df.groupby(['year', 'attachment_type']).size().unstack(fill_value=0)
    yearly_dict = yearly.to_dict('index')

    # Per-contact attachment totals lookup
    attachments_by_contact = attachments_df.groupby('contact_name').size().to_dict()

    return {
        'available': True,
        'total_attachments': len(attachments_df),
        'type_counts': type_counts,
        'sent_by_type': sent_by_type,
        'received_by_type': received_by_type,
        'top_photo_contacts': top_photo_contacts,
        'top_video_contacts': top_video_contacts,
        'yearly_trend': yearly_dict,
        'attachments_by_contact': attachments_by_contact,
    }


def extract_shared_links(df: pd.DataFrame) -> dict:
    """
    Extract and analyze URLs shared in messages.

    Returns:
    - Top domains shared
    - Top domains per contact
    - Link sharing patterns
    """
    # URL regex pattern
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

    # Extract URLs from messages
    df_with_text = df[df['text'].notna()].copy()
    df_with_text['urls'] = df_with_text['text'].apply(
        lambda x: re.findall(url_pattern, str(x)) if x else []
    )

    # Explode to get one row per URL
    url_rows = []
    for _, row in df_with_text[df_with_text['urls'].apply(len) > 0].iterrows():
        for url in row['urls']:
            url_rows.append({
                'contact_name': row.get('contact_name'),
                'is_from_me': row['is_from_me'],
                'year': row['year'],
                'url': url
            })

    if len(url_rows) == 0:
        return {'available': False}

    url_df = pd.DataFrame(url_rows)

    # Extract domains
    def get_domain(url):
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return None

    url_df['domain'] = url_df['url'].apply(get_domain)
    url_df = url_df[url_df['domain'].notna() & (url_df['domain'] != '')]

    if len(url_df) == 0:
        return {'available': False}

    # Top domains with sent/received breakdown
    domain_stats = url_df.groupby('domain').agg({
        'url': 'count',
        'is_from_me': 'sum'
    }).rename(columns={'url': 'total', 'is_from_me': 'sent'})
    domain_stats['received'] = domain_stats['total'] - domain_stats['sent']
    domain_stats = domain_stats.sort_values('total', ascending=False).head(10)

    top_domains_detailed = [
        {
            'domain': domain,
            'total': int(row['total']),
            'sent': int(row['sent']),
            'received': int(row['received'])
        }
        for domain, row in domain_stats.iterrows()
    ]

    # Yearly trend
    yearly_links = url_df.groupby('year').size().to_dict()

    # Per-contact links lookup
    links_by_contact = url_df.groupby('contact_name').size().to_dict()

    return {
        'available': True,
        'total_links': len(url_df),
        'unique_domains': url_df['domain'].nunique(),
        'top_domains_detailed': top_domains_detailed,
        'yearly_links': yearly_links,
        'links_by_contact': links_by_contact,
    }


def generate_extended_insights(df: pd.DataFrame, attachments_df: pd.DataFrame = None, top_n_filter: int = 50) -> dict:
    """
    Generate all extended insights from previously unused data.

    Args:
        df: Message dataframe
        attachments_df: Attachments dataframe
        top_n_filter: Only include contacts in top N by message volume for certain stats
    """
    # Get top N contacts by message volume for filtering
    top_contacts = set(
        df.groupby('contact_name').size()
        .nlargest(top_n_filter)
        .index.tolist()
    )

    insights = {
        'response_times': get_response_time_stats(df, top_contacts),
        'service_breakdown': get_sms_vs_imessage_breakdown(df, top_contacts),
        'attachments': get_attachment_summary(df, attachments_df),
        'links': extract_shared_links(df),
    }

    return insights
