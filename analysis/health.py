"""Relationship health analysis - fading and emerging connections."""
import pandas as pd
from datetime import timedelta


def detect_fading_friendships(df: pd.DataFrame, min_messages: int = 100, max_inactive_days: int = 365) -> list:
    """
    Identify relationships that were recently active but have gone quiet.

    Criteria (tuned for meaningful relationships):
    - At least 100 total messages (real relationship, not casual acquaintance)
    - Had sustained activity (not just bursts) - require messages across multiple months
    - Recent activity significantly below historical rate
    - Last contact within past year (not ancient dormant contacts)
    """
    latest_date = df['datetime'].max()
    now = pd.Timestamp.now(tz=latest_date.tzinfo) if latest_date.tzinfo else pd.Timestamp.now()
    one_year_ago = now - timedelta(days=365)
    two_years_ago = now - timedelta(days=730)

    fading = []

    for contact in df['contact_name'].unique():
        # Skip business/URN identifiers
        if contact.startswith('urn:') or contact.startswith('+'):
            continue

        contact_df = df[df['contact_name'] == contact].copy()

        # Skip if not enough messages total - require meaningful history
        if len(contact_df) < min_messages:
            continue

        last_msg = contact_df['datetime'].max()
        days_since = (now - last_msg).days

        # Skip if last contact was more than max_inactive_days ago
        # These are dormant relationships, not "fading" ones
        if days_since > max_inactive_days:
            continue

        # Require sustained history - messages across multiple months, not just bursts
        # Check that they have messages in at least 3 different months over the history
        contact_df['month'] = contact_df['datetime'].dt.to_period('M')
        active_months = contact_df['month'].nunique()
        if active_months < 3:
            continue

        # Must have had meaningful activity in the 1-2 year period before going quiet
        active_period = contact_df[contact_df['datetime'] >= two_years_ago]
        if len(active_period) < 30:  # Raised from 20
            continue

        # Compare last 90 days to the prior year
        recent_90 = contact_df[contact_df['datetime'] >= now - timedelta(days=90)]
        prior_year = contact_df[
            (contact_df['datetime'] >= one_year_ago - timedelta(days=365)) &
            (contact_df['datetime'] < one_year_ago)
        ]

        if len(prior_year) < 15:  # Raised from 10
            # Try comparing to 6 months before the quiet period
            prior_period = contact_df[
                (contact_df['datetime'] >= now - timedelta(days=270)) &
                (contact_df['datetime'] < now - timedelta(days=90))
            ]
            if len(prior_period) < 15:
                continue
            prior_rate = len(prior_period) / 180 * 7  # msgs per week
        else:
            prior_rate = len(prior_year) / 365 * 7  # msgs per week

        recent_rate = len(recent_90) / 90 * 7  # msgs per week

        # Fading = recent rate is less than 30% of prior rate, and prior rate was meaningful
        # Raised minimum prior rate to 1.0 msgs/week (from 0.5)
        if prior_rate >= 1.0 and recent_rate < prior_rate * 0.3:
            drop_pct = (1 - recent_rate / prior_rate) * 100

            fading.append({
                'contact_name': contact,
                'total_messages': len(contact_df),
                'active_months': active_months,
                'baseline_rate': round(prior_rate, 1),  # msgs per week
                'recent_rate': round(recent_rate, 1),  # msgs per week
                'drop_percentage': round(drop_pct, 1),
                'days_since_contact': days_since,
                'last_contact_date': last_msg.strftime('%Y-%m-%d'),
            })

    # Sort by drop percentage (biggest drops first - most significant fading)
    fading.sort(key=lambda x: x['drop_percentage'], reverse=True)

    return fading[:10]


def detect_new_connections(df: pd.DataFrame, min_recent_messages: int = 4) -> list:
    """
    Identify emerging/revived relationships.

    Two patterns we're looking for:
    1. REVIVED: Known contact who went dormant, now active again
       - Known for 60+ days
       - Prior 6 months had very little activity (<0.2 msgs/wk)
       - Recent 30 days has meaningful activity (4+ msgs)

    2. GROWING: Existing contact with big activity increase
       - Known for 60+ days
       - Had some baseline activity (>0.2 msgs/wk)
       - Recent rate is 5x+ their baseline
       - Recent 30 days has meaningful activity (4+ msgs)
    """
    latest_date = df['datetime'].max()
    now = pd.Timestamp.now(tz=latest_date.tzinfo) if latest_date.tzinfo else pd.Timestamp.now()

    emerging = []

    for contact in df['contact_name'].unique():
        # Skip business/URN identifiers and phone numbers
        if contact.startswith('urn:') or contact.startswith('+'):
            continue
        # Skip if looks like a number/code
        if contact.replace(' ', '').isdigit():
            continue

        contact_df = df[df['contact_name'] == contact].copy()

        first_msg = contact_df['datetime'].min()
        last_msg = contact_df['datetime'].max()
        relationship_days = (now - first_msg).days

        # Skip if no recent activity (within last 30 days)
        days_since_last = (now - last_msg).days
        if days_since_last > 30:
            continue

        # Need to be known for at least 60 days to be "revived" or "growing"
        if relationship_days < 60:
            continue

        # Compare last 30 days to the 6 months before that
        recent_30 = contact_df[contact_df['datetime'] >= now - timedelta(days=30)]
        prior_period = contact_df[
            (contact_df['datetime'] >= now - timedelta(days=210)) &
            (contact_df['datetime'] < now - timedelta(days=30))
        ]

        recent_count = len(recent_30)
        prior_count = len(prior_period)

        # Need meaningful recent activity
        if recent_count < min_recent_messages:
            continue

        prior_rate = prior_count / 180 * 7  # msgs per week over 6 months
        recent_rate = recent_count / 30 * 7  # msgs per week over last month

        # REVIVED: Was dormant (very low prior rate), now active
        if prior_rate < 0.2 and recent_rate >= 0.5:
            emerging.append({
                'contact_name': contact,
                'total_messages': len(contact_df),
                'recent_messages': recent_count,
                'baseline_rate': round(prior_rate, 1),
                'msgs_per_week': round(recent_rate, 1),
                'growth': 'Revived',
                'is_new': False,
                'is_revived': True,
                'relationship_days': relationship_days
            })
            continue

        # GROWING: Had baseline activity, now much higher (5x+)
        if prior_rate >= 0.2 and recent_rate >= prior_rate * 5:
            growth_factor = recent_rate / prior_rate
            emerging.append({
                'contact_name': contact,
                'total_messages': len(contact_df),
                'recent_messages': recent_count,
                'baseline_rate': round(prior_rate, 1),
                'msgs_per_week': round(recent_rate, 1),
                'growth': f'{growth_factor:.0f}x',
                'is_new': False,
                'is_revived': False,
                'relationship_days': relationship_days
            })

    # Sort by recent message rate (most active first)
    emerging.sort(key=lambda x: -x['msgs_per_week'])

    return emerging[:10]


def generate_health_insights(df: pd.DataFrame) -> dict:
    """
    Generate health insights for relationships.
    """
    fading = detect_fading_friendships(df)
    emerging = detect_new_connections(df)

    return {
        'fading_friendships': fading,
        'emerging_connections': emerging,
        'summary': {
            'fading_count': len(fading),
            'emerging_count': len(emerging)
        }
    }
