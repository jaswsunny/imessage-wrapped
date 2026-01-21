"""Main orchestration script for iMessage Wrapped."""
import pandas as pd
from pathlib import Path
import json

from config import DATA_DIR, START_YEAR, END_YEAR, EXCLUDED_CONTACTS, MIN_TWO_WAY_RATIO, MIN_MESSAGES_FOR_SENTIMENT
import re
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
    create_monthly_top_contacts,
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

    unresolved = prompt_for_unresolved(df, mappings, top_n=20)
    if unresolved:
        print("\nNote: Some top contacts couldn't be resolved to names:")
        for contact_id, count in unresolved[:5]:
            print(f"  {contact_id}: {count:,} messages")
        print("  (You can manually edit output/data/contacts.json to add names)")

    # Filter out excluded contacts (self, businesses, etc.)
    before_filter = len(df)
    df = df[~df['contact_name'].str.lower().isin([c.lower() for c in EXCLUDED_CONTACTS])]
    print(f"\nFiltered out excluded contacts: {before_filter - len(df):,} messages removed")

    # Filter out contacts that look like phone numbers or short codes (keep only named contacts)
    def is_phone_or_code(name):
        if not name:
            return True
        name_str = str(name).strip()
        # If it's all digits, it's a phone number or short code
        if name_str.isdigit():
            return True
        # If it starts with +, it's a phone number
        if name_str.startswith('+'):
            return True
        # If it's mostly digits (more than 50% digits), treat as number
        digits = re.sub(r'\D', '', name_str)
        if len(digits) > 0 and len(digits) / len(name_str) > 0.5:
            return True
        return False

    before_filter = len(df)
    df = df[~df['contact_name'].apply(is_phone_or_code)]
    print(f"Filtered out unnamed contacts (numbers/codes): {before_filter - len(df):,} messages removed")

    # Filter out one-sided contacts (notifications, etc.)
    contact_stats = df.groupby('contact_name').agg(
        total=('message_id', 'count'),
        sent=('is_from_me', 'sum')
    )
    contact_stats['received'] = contact_stats['total'] - contact_stats['sent']
    contact_stats['sent_ratio'] = contact_stats['sent'] / contact_stats['total']

    # Keep contacts where both sent and received are at least MIN_TWO_WAY_RATIO of total
    two_way_contacts = contact_stats[
        (contact_stats['sent_ratio'] >= MIN_TWO_WAY_RATIO) &
        (contact_stats['sent_ratio'] <= (1 - MIN_TWO_WAY_RATIO))
    ].index.tolist()

    before_filter = len(df)
    df = df[df['contact_name'].isin(two_way_contacts)]
    print(f"Filtered out one-sided contacts: {before_filter - len(df):,} messages removed")
    print(f"Remaining: {len(df):,} messages with {df['contact_name'].nunique()} contacts")

    # Step 3: People analysis
    print("\n[3/8] Analyzing relationships...")
    top_contacts = get_top_contacts_alltime(df)
    top_by_year = get_top_contacts_by_year(df)
    lopsidedness = calculate_lopsidedness(df)
    initiators = get_conversation_initiator_stats(df)
    response_times = calculate_response_times(df)

    top_names = top_contacts['contact_name'].head(10).tolist()
    monthly_volume = get_message_volume_over_time(df, contacts=top_names)

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
    sentiment_by_contact = get_sentiment_by_contact(df, min_messages=MIN_MESSAGES_FOR_SENTIMENT)

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
    with open(DATA_DIR / "yearly_stats.json", 'w') as f:
        json.dump(yearly_stats, f, indent=2, default=str)

    # 2025 Deep Dive Analysis
    print("\n[6.5/8] Generating 2025 deep dive...")
    df_2025 = df[df['year'] == 2025].copy()

    # Top 10 people in 2025
    top_2025 = df_2025.groupby('contact_name').agg(
        total_messages=('message_id', 'count'),
        sent=('is_from_me', 'sum'),
    ).reset_index()
    top_2025['received'] = top_2025['total_messages'] - top_2025['sent']
    top_2025 = top_2025.sort_values('total_messages', ascending=False).head(10)

    # Monthly breakdown for 2025
    df_2025['month'] = df_2025['datetime'].dt.month
    df_2025['month_name'] = df_2025['datetime'].dt.strftime('%b')

    monthly_top = df_2025.groupby(['month', 'month_name', 'contact_name']).size().reset_index(name='count')
    monthly_top['rank'] = monthly_top.groupby('month')['count'].rank(ascending=False, method='first')
    monthly_top_1 = monthly_top[monthly_top['rank'] == 1].sort_values('month')

    # Calculate fastest response times for 2025 (who you respond to fastest)
    response_times_2025 = calculate_response_times(df_2025)
    fastest_responses_2025 = []
    if not response_times_2025.empty:
        valid = response_times_2025.dropna(subset=['your_response_time_min'])
        if not valid.empty:
            fastest = valid.sort_values('your_response_time_min').head(3)
            fastest_responses_2025 = [
                {'contact_name': row['contact_name'], 'response_time_min': row['your_response_time_min']}
                for _, row in fastest.iterrows()
            ]

    # Step 7: Generate visualizations
    print("\n[7/8] Generating visualizations...")
    charts = {
        'stacked_area': create_stacked_area(monthly_volume),
        'lopsidedness': create_lopsidedness_scatter(lopsidedness.head(30)),
        'heatmap': create_hour_day_heatmap(heatmap_data),
        'yearly_volume': create_yearly_volume_bar(yearly_volume),
        'peak_hours': create_peak_hours_small_multiples(hourly_by_year),
        'sentiment_best': create_sentiment_bar(sentiment_by_contact, title="Best Vibes", top_n=15),
        'sentiment_worst': create_sentiment_bar(sentiment_by_contact, title="Worst Vibes", top_n=15, worst=True),
        'emoji_grid': create_emoji_grid(emojis_by_year),
        'question_ratio': create_question_ratio_line(question_ratio),
        'fastest_responses_2025': fastest_responses_2025,
    }

    # Build AI-generated insights about surprising relationship dynamics (2023-2025)
    print("  - Generating relationship insights...")
    insights = {'ai_insights': []}

    df_recent = df[df['year'].isin([2023, 2024, 2025])].copy()

    # 1. Find dramatic relationship changes - people who exploded in 2025
    yearly_counts = df_recent.groupby(['year', 'contact_name']).size().unstack(fill_value=0)
    if 2024 in yearly_counts.columns and 2025 in yearly_counts.columns:
        yearly_counts['change_2024_2025'] = yearly_counts[2025] - yearly_counts[2024]
        yearly_counts['ratio_2024_2025'] = (yearly_counts[2025] + 1) / (yearly_counts[2024] + 1)

        # Biggest explosions (absolute) - people with >1000 increase
        explosions = yearly_counts[yearly_counts['change_2024_2025'] > 1000].sort_values('change_2024_2025', ascending=False)
        if not explosions.empty:
            for name in explosions.head(3).index:
                old = int(yearly_counts.loc[name, 2024])
                new = int(yearly_counts.loc[name, 2025])
                if old < 100:  # Truly new relationship
                    insights['ai_insights'].append((
                        f"New Major Relationship: {name}",
                        f"From {old} messages in 2024 to {new:,} in 2025. This person went from barely on your radar to one of your most frequent contacts."
                    ))
                else:
                    insights['ai_insights'].append((
                        f"Relationship Intensified: {name}",
                        f"Jumped from {old:,} to {new:,} messages (+{new-old:,}). Something changed significantly in this relationship."
                    ))

    # 2. Find the Lucas Gelfond pattern - dropped then came back
    if 2023 in yearly_counts.columns and 2024 in yearly_counts.columns and 2025 in yearly_counts.columns:
        comebacks = yearly_counts[
            (yearly_counts[2023] > 1000) &
            (yearly_counts[2024] < yearly_counts[2023] * 0.3) &
            (yearly_counts[2025] > yearly_counts[2023] * 0.8)
        ]
        for name in comebacks.index:
            y23 = int(yearly_counts.loc[name, 2023])
            y24 = int(yearly_counts.loc[name, 2024])
            y25 = int(yearly_counts.loc[name, 2025])
            insights['ai_insights'].append((
                f"The Comeback: {name}",
                f"A friendship that nearly went silent. {y23:,} msgs in 2023, dropped to just {y24} in 2024, then roared back to {y25:,} in 2025."
            ))

    # 3. Find complete fadeouts - top 10 in 2023, nearly zero now
    if 2023 in yearly_counts.columns and 2025 in yearly_counts.columns:
        top_2023 = yearly_counts[2023].sort_values(ascending=False).head(15).index
        fadeouts = yearly_counts.loc[top_2023]
        fadeouts = fadeouts[(fadeouts[2023] > 500) & (fadeouts[2025] < 50)]
        for name in fadeouts.index[:2]:
            y23 = int(yearly_counts.loc[name, 2023])
            y25 = int(yearly_counts.loc[name, 2025])
            insights['ai_insights'].append((
                f"Faded Connection: {name}",
                f"Once a top contact with {y23:,} messages in 2023, now down to just {y25} in 2025. This relationship has gone quiet."
            ))

    # 4. Late night confidant pattern
    df_recent['hour'] = df_recent['datetime'].dt.hour
    late_night = df_recent[(df_recent['hour'] >= 0) & (df_recent['hour'] < 4)]
    late_counts = late_night.groupby('contact_name').size()
    total_counts = df_recent.groupby('contact_name').size()
    late_pct = (late_counts / total_counts).dropna()

    # Find people with high late-night % AND significant volume
    late_heavy = late_pct[(late_pct > 0.15) & (total_counts > 200)]
    if not late_heavy.empty:
        name = late_heavy.sort_values(ascending=False).index[0]
        pct = late_heavy[name] * 100
        count = int(late_counts.get(name, 0))
        insights['ai_insights'].append((
            f"Late Night Confidant: {name}",
            f"{pct:.0f}% of your messages ({count} total) are between midnight and 4am. This is your go-to person for those sleepless nights."
        ))

    # 5. Work hours vs personal relationship patterns
    df_recent['is_weekend'] = df_recent['datetime'].dt.dayofweek >= 5
    df_recent['is_work_hours'] = (
        (df_recent['hour'] >= 9) &
        (df_recent['hour'] < 18) &
        (~df_recent['is_weekend'])
    )
    work_msgs = df_recent[df_recent['is_work_hours']].groupby('contact_name').size()
    total = df_recent.groupby('contact_name').size()
    work_ratio = (work_msgs / total).dropna()

    # Find people who are almost exclusively work hours AND became big in 2025
    if 2025 in yearly_counts.columns:
        work_heavy = work_ratio[work_ratio > 0.75]
        new_work_contacts = work_heavy[work_heavy.index.isin(yearly_counts[yearly_counts[2025] > 500].index)]
        if not new_work_contacts.empty:
            top_work = new_work_contacts.sort_values(ascending=False)
            for name in top_work.head(2).index:
                pct = work_ratio[name] * 100
                msgs_2025 = int(yearly_counts.loc[name, 2025])
                insights['ai_insights'].append((
                    f"Professional Relationship: {name}",
                    f"{pct:.0f}% of your {msgs_2025:,} messages are during work hours (9-6 weekdays). This relationship lives in your professional life."
                ))

    # 6. Response time asymmetries
    df_sorted = df_recent.sort_values(['contact_name', 'datetime']).copy()
    df_sorted['prev_time'] = df_sorted.groupby('contact_name')['datetime'].shift(1)
    df_sorted['prev_from_me'] = df_sorted.groupby('contact_name')['is_from_me'].shift(1)
    df_sorted['is_response'] = df_sorted['is_from_me'] != df_sorted['prev_from_me']
    df_sorted['response_min'] = (df_sorted['datetime'] - df_sorted['prev_time']).dt.total_seconds() / 60

    responses = df_sorted[df_sorted['is_response'] & (df_sorted['response_min'] > 0) & (df_sorted['response_min'] < 1440)]
    your_resp = responses[responses['is_from_me'] == 1].groupby('contact_name')['response_min'].median()
    their_resp = responses[responses['is_from_me'] == 0].groupby('contact_name')['response_min'].median()

    combined = pd.DataFrame({'you': your_resp, 'them': their_resp}).dropna()
    combined = combined[combined.index.isin(total[total > 300].index)]
    combined['ratio'] = combined['them'] / combined['you']

    # You respond faster
    eager = combined[combined['ratio'] > 3].sort_values('ratio', ascending=False)
    if not eager.empty:
        name = eager.index[0]
        your_time = combined.loc[name, 'you']
        their_time = combined.loc[name, 'them']
        insights['ai_insights'].append((
            f"You're Eager: {name}",
            f"You respond in {your_time:.0f} min on average, but they take {their_time:.0f} min. You're {their_time/your_time:.1f}x faster to respond."
        ))

    # They respond faster
    patient = combined[combined['ratio'] < 0.3].sort_values('ratio')
    if not patient.empty:
        name = patient.index[0]
        your_time = combined.loc[name, 'you']
        their_time = combined.loc[name, 'them']
        insights['ai_insights'].append((
            f"They're Waiting: {name}",
            f"They respond in {their_time:.0f} min, but you take {your_time:.0f} min. They're {your_time/their_time:.1f}x faster than you."
        ))

    # 7. Your texting volume is exploding
    yearly_totals = df.groupby('year').size()
    if 2023 in yearly_totals.index and 2025 in yearly_totals.index:
        y23_total = yearly_totals[2023]
        y25_total = yearly_totals[2025]
        if y25_total > y23_total * 1.3:
            insights['ai_insights'].append((
                "Your Texting Has Exploded",
                f"You sent {y25_total:,} messages in 2025 vs {y23_total:,} in 2023. That's a {(y25_total/y23_total - 1)*100:.0f}% increase in how much you text."
            ))

    # 8. Burst vs Consistent relationships (all-time analysis 2017-2025)
    print("  - Analyzing burst vs consistent relationships...")
    all_years = list(range(2017, 2026))
    yearly_by_contact = df.groupby(['contact_name', 'year']).size().unstack(fill_value=0)

    # For each contact, calculate consistency metrics
    consistency_data = []
    for contact in yearly_by_contact.index:
        yearly_msgs = yearly_by_contact.loc[contact]
        years_active = (yearly_msgs > 50).sum()  # Years with meaningful contact
        total_msgs = yearly_msgs.sum()
        max_year_msgs = yearly_msgs.max()
        max_year = yearly_msgs.idxmax()

        if total_msgs >= 500:  # Only analyze people with significant history
            # Coefficient of variation - lower = more consistent
            mean_msgs = yearly_msgs[yearly_msgs > 0].mean()
            std_msgs = yearly_msgs[yearly_msgs > 0].std()
            cv = std_msgs / mean_msgs if mean_msgs > 0 else 0

            # Concentration - what % of all messages were in the peak year
            concentration = max_year_msgs / total_msgs

            consistency_data.append({
                'contact': contact,
                'total_msgs': total_msgs,
                'years_active': years_active,
                'max_year': max_year,
                'max_year_msgs': max_year_msgs,
                'concentration': concentration,
                'cv': cv
            })

    if consistency_data:
        consistency_df = pd.DataFrame(consistency_data)

        # Most consistent long-term friendships: many years active, low concentration
        consistent = consistency_df[
            (consistency_df['years_active'] >= 5) &
            (consistency_df['concentration'] < 0.4)
        ].sort_values('total_msgs', ascending=False)

        if not consistent.empty:
            insights['ai_insights'].append((
                "Your Ride-or-Dies",
                "These friendships have stayed consistent across 5+ years without major peaks or valleys:"
            ))
            for _, row in consistent.head(4).iterrows():
                insights['ai_insights'].append((
                    f"Consistent: {row['contact']}",
                    f"{int(row['total_msgs']):,} total messages across {int(row['years_active'])} years. Peak year ({int(row['max_year'])}) was only {row['concentration']*100:.0f}% of total - steady throughout."
                ))

        # Intense burst relationships: high concentration in one year
        bursts = consistency_df[
            (consistency_df['concentration'] > 0.7) &
            (consistency_df['total_msgs'] >= 500)
        ].sort_values('concentration', ascending=False)

        if not bursts.empty:
            insights['ai_insights'].append((
                "Intense But Brief",
                "These relationships burned bright for a moment then faded:"
            ))
            for _, row in bursts.head(4).iterrows():
                insights['ai_insights'].append((
                    f"Burst: {row['contact']}",
                    f"{row['concentration']*100:.0f}% of your {int(row['total_msgs']):,} messages were in {int(row['max_year'])} ({int(row['max_year_msgs']):,} that year). A concentrated chapter of your life."
                ))

    # 9. Content-based psychoanalysis
    print("  - Analyzing message content patterns...")

    def count_pattern(text, pattern):
        if not text:
            return 0
        return len(re.findall(pattern, str(text).lower()))

    sent_msgs = df[df['is_from_me'] == 1].copy()
    contact_msg_counts = df.groupby('contact_name').size()
    valid_contacts = contact_msg_counts[contact_msg_counts >= 100].index
    sent_msgs = sent_msgs[sent_msgs['contact_name'].isin(valid_contacts)]

    # Question rate per contact
    sent_msgs['has_question'] = sent_msgs['text'].fillna('').str.contains(r'\?')
    question_rate = sent_msgs.groupby('contact_name')['has_question'].mean()

    # Message length
    sent_msgs['msg_length'] = sent_msgs['text'].fillna('').str.len()
    avg_length = sent_msgs.groupby('contact_name')['msg_length'].mean()

    # I vs you ratio (self vs other focused)
    sent_msgs['i_count'] = sent_msgs['text'].apply(lambda x: count_pattern(x, r'\bi\b|\bi\'|\bmy\b|\bme\b'))
    sent_msgs['you_count'] = sent_msgs['text'].apply(lambda x: count_pattern(x, r'\byou\b|\byour\b'))
    i_rate = sent_msgs.groupby('contact_name')['i_count'].mean()
    you_rate = sent_msgs.groupby('contact_name')['you_count'].mean()
    i_you_ratio = (i_rate / (you_rate + 0.1))

    # Vulnerable words
    vulnerable_pattern = r'\bfeel\b|\bfeeling\b|\bworried\b|\bscared\b|\banxious\b|\bstressed\b|\bsad\b|\bupset\b|\bhurt\b|\bafraid\b|\blonely\b'
    sent_msgs['vulnerable'] = sent_msgs['text'].apply(lambda x: count_pattern(x, vulnerable_pattern))
    vulnerable_rate = sent_msgs.groupby('contact_name')['vulnerable'].mean()

    # Advice seeking
    advice_pattern = r'\bshould i\b|\bwhat do you think\b|\badvice\b|\bwhat should\b|\bdo you think\b'
    sent_msgs['advice'] = sent_msgs['text'].apply(lambda x: count_pattern(x, advice_pattern))
    advice_rate = sent_msgs.groupby('contact_name')['advice'].mean()

    # Intellectual words
    intellectual_pattern = r'\bthink\b|\binteresting\b|\bwonder\b|\bidea\b|\bargument\b|\breason\b|\btheory\b|\bconcept\b'
    sent_msgs['intellectual'] = sent_msgs['text'].apply(lambda x: count_pattern(x, intellectual_pattern))
    intellectual_rate = sent_msgs.groupby('contact_name')['intellectual'].mean()

    # "we" vs "I" - collaboration
    sent_msgs['we_count'] = sent_msgs['text'].apply(lambda x: count_pattern(x, r'\bwe\b|\bour\b|\bus\b'))
    we_rate = sent_msgs.groupby('contact_name')['we_count'].mean()
    we_i_ratio = (we_rate / (i_rate + 0.1))

    # Get top contacts for context
    top_500 = contact_msg_counts[contact_msg_counts >= 500].index

    # Insight: Who you go to for advice vs who you just talk at
    advice_seekers = advice_rate[advice_rate.index.isin(top_500)].nlargest(3)
    declarative = question_rate[question_rate.index.isin(top_500)].nsmallest(3)

    if not advice_seekers.empty:
        names = ', '.join(advice_seekers.index[:3].tolist())
        insights['ai_insights'].append((
            "Your Advisors",
            f"You seek advice and opinions most from: {names}. These are relationships where you're uncertain and looking for guidance."
        ))

    if not declarative.empty:
        names = list(declarative.index[:3])
        rates = [f"{question_rate[n]*100:.0f}%" for n in names]
        insights['ai_insights'].append((
            "No Questions Asked",
            f"With {names[0]} ({rates[0]} questions), {names[1]} ({rates[1]}), and {names[2]} ({rates[2]}), you rarely ask questions. You're declarative, certain, just sharing rather than seeking."
        ))

    # Insight: Self-focused vs other-focused conversations
    most_self = i_you_ratio[i_you_ratio.index.isin(top_500)].nlargest(3)
    most_other = i_you_ratio[i_you_ratio.index.isin(top_500)].nsmallest(3)

    if not most_self.empty and most_self.iloc[0] > 1.5:
        name = most_self.index[0]
        ratio = most_self.iloc[0]
        insights['ai_insights'].append((
            f"It's About You: {name}",
            f"You use 'I/my/me' {ratio:.1f}x more than 'you/your' in this relationship. This might be a space where you process your own life out loud."
        ))

    if not most_other.empty and most_other.iloc[0] < 0.7:
        name = most_other.index[0]
        ratio = 1/most_other.iloc[0]
        insights['ai_insights'].append((
            f"Focused on Them: {name}",
            f"You use 'you/your' {ratio:.1f}x more than 'I/my' here. This relationship is oriented around them - their life, their needs, their updates."
        ))

    # Insight: Emotional vulnerability patterns
    most_vulnerable = vulnerable_rate[vulnerable_rate.index.isin(valid_contacts)].nlargest(3)
    if not most_vulnerable.empty and most_vulnerable.iloc[0] > 0.02:
        names = ', '.join(most_vulnerable.index[:3].tolist())
        insights['ai_insights'].append((
            "Where You're Vulnerable",
            f"Your most emotionally open conversations (feeling words like worried, scared, stressed) are with: {names}. These people see a side of you others don't."
        ))

    # Insight: Intellectual sparring partners
    most_intellectual = intellectual_rate[intellectual_rate.index.isin(top_500)].nlargest(3)
    if not most_intellectual.empty:
        names = ', '.join(most_intellectual.index[:3].tolist())
        insights['ai_insights'].append((
            "Your Intellectual Sparring Partners",
            f"Highest density of 'think', 'interesting', 'idea', 'argument': {names}. These are the people you do your thinking with."
        ))

    # Insight: Collaborative "we" relationships
    most_collaborative = we_i_ratio[we_i_ratio.index.isin(top_500)].nlargest(3)
    if not most_collaborative.empty and most_collaborative.iloc[0] > 0.15:
        names = ', '.join(most_collaborative.index[:3].tolist())
        insights['ai_insights'].append((
            "Partnership Mode",
            f"You use 'we/us/our' most with: {names}. These feel like true partnerships - you're building something together, not just talking."
        ))

    # Insight: Short message rapid-fire relationships
    shortest_msgs = avg_length.nsmallest(10)
    shortest_with_volume = shortest_msgs[shortest_msgs.index.isin(top_500)]
    if not shortest_with_volume.empty:
        name = shortest_with_volume.index[0]
        length = shortest_with_volume.iloc[0]
        count = int(contact_msg_counts[name])
        insights['ai_insights'].append((
            f"Rapid Fire: {name}",
            f"Average message length: {length:.0f} characters across {count:,} messages. This is staccato conversation - quick exchanges, not essays."
        ))

    # Insight: Late night confidant
    late_night_sent = df_recent[(df_recent['hour'] >= 0) & (df_recent['hour'] < 4) & (df_recent['is_from_me'] == 1)]
    late_counts = late_night_sent.groupby('contact_name').size()
    total_sent_counts = df_recent[df_recent['is_from_me'] == 1].groupby('contact_name').size()
    late_pct = (late_counts / total_sent_counts).dropna()

    high_late = late_pct[(late_pct > 0.1) & (late_counts > 50)]
    if not high_late.empty:
        name = high_late.sort_values(ascending=False).index[0]
        pct = high_late[name] * 100
        count = int(late_counts[name])
        insights['ai_insights'].append((
            f"3am Thoughts: {name}",
            f"{pct:.0f}% of your messages to them are between midnight-4am ({count} messages). When you can't sleep, this is who you reach for."
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
        top_2025=top_2025,
        df_2025=df_2025,
        top_by_year=top_by_year,
        monthly_top_2025=monthly_top_1,
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
