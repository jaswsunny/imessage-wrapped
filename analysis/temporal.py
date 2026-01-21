"""Temporal pattern analysis."""
import pandas as pd
import numpy as np

def get_hour_day_heatmap(df):
    """Get message counts by hour and day of week."""
    heatmap = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')

    pivot = heatmap.pivot(index='day_of_week', columns='hour', values='count').fillna(0)

    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot.index = [day_names[i] for i in pivot.index]

    return pivot

def get_peak_hours_by_year(df):
    """Get peak texting hours for each year."""
    hourly_by_year = df.groupby(['year', 'hour']).size().reset_index(name='count')

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
    daily = df.groupby(['contact_name', 'date']).size().reset_index(name='count')
    daily = daily.sort_values(['contact_name', 'date'])

    daily['prev_date'] = daily.groupby('contact_name')['date'].shift(1)
    daily['date_dt'] = pd.to_datetime(daily['date'])
    daily['prev_date_dt'] = pd.to_datetime(daily['prev_date'])
    daily['gap'] = (daily['date_dt'] - daily['prev_date_dt']).dt.days
    daily['new_streak'] = (daily['gap'] != 1) | daily['gap'].isna()
    daily['streak_id'] = daily.groupby('contact_name')['new_streak'].cumsum()

    streaks = daily.groupby(['contact_name', 'streak_id']).agg(
        streak_length=('date', 'count'),
        start_date=('date', 'min'),
        end_date=('date', 'max'),
    ).reset_index()

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
