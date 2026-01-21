# iMessage Wrapped Design

## Overview
A "Spotify Wrapped" style analysis of 8+ years of iMessage data (2017-2025), generating an interactive HTML report with insights about texting patterns, relationships, and content.

**Data source:** `~/Library/Messages/chat.db` (~390k messages, 1:1 chats only, excluding group chats)

## Tech Stack
- Python 3 with pandas
- SQLite (read-only access to chat.db)
- Plotly for interactive charts
- NLTK + VADER for sentiment analysis
- scikit-learn for topic modeling (LDA/NMF)
- pyobjc for macOS Contacts integration
- Parquet for data persistence

## Project Structure
```
imessage-wrapped/
├── extract.py          # Pull data from chat.db into clean DataFrame
├── contacts.py         # Resolve phone numbers to names
├── analysis/
│   ├── people.py       # Relationship stats
│   ├── temporal.py     # Time-based patterns
│   └── content.py      # Phrases, emoji, sentiment, topics
├── visualize.py        # Generate all Plotly charts
├── report.py           # Assemble final HTML
├── config.py           # Date ranges, thresholds, exclusion lists
├── main.py             # Orchestrate full pipeline
├── docs/plans/
└── output/
    ├── wrapped.html
    └── data/
        ├── messages.parquet
        ├── contacts.json
        ├── yearly_stats.json
        ├── sentiment_scores.parquet
        └── topics.parquet
```

---

## Analysis Modules

### 1. People & Relationships (`analysis/people.py`)

**Core Metrics:**
- All-time top contacts (ranked by total messages sent + received)
- Top 5-10 contacts per year (2017-2025)
- Yearly message volume per contact

**Relationship Dynamics:**
- Lopsidedness ratio: `messages_sent / messages_received` per contact
- Conversation initiators: who sends first message after 4+ hour gap
- Response time: average reply time per contact (both directions)

**Trajectory Stats:**
- Rising stars: significant ranking jumps year-over-year
- Faded connections: former top contacts now rarely texted
- Consistency score: years in top 10 consecutively

**Visualizations:**
- Stacked area chart: message volume over time by person
- Bump chart: ranking changes per year
- Scatter plot: lopsidedness vs total volume

### 2. Temporal Patterns (`analysis/temporal.py`)

**Metrics:**
- Hour × Day of week heatmap (primary visualization)
- Peak texting hours per year (how they've shifted)
- Total volume per year (sent vs received)
- Longest daily streaks per contact
- Active days per year

**Visualizations:**
- 24×7 heatmap (hour vs day of week)
- Small multiples: hourly distribution per year
- Bar chart: yearly totals (sent vs received)

### 3. Content Analysis (`analysis/content.py`)

**Phrases & Words:**
- Top 2-4 word phrases per year (excluding boring phrases like "sounds good", "on my way", "haha", "ok", etc.)
- Words unique to each year (spike detection)

**Emoji:**
- Top emojis per year
- Emoji usage by contact

**Question vs Statement:**
- Question ratio per year (% messages ending in ?)
- Question ratio by contact

**Sentiment (VADER):**
- Average sentiment score per contact
- Most positive vs negative-sentiment conversations

**Topics (LDA/NMF):**
- Top 3-5 topics per year
- Topic distribution by contact

---

## HTML Report Structure

Single-page scrolling report, dark theme:

```
1. HEADER
   - Title: "Your iMessage Wrapped: 2017-2025"
   - Total messages sent/received, total contacts

2. YOUR TOP PEOPLE (ALL-TIME)
   - Podium-style top 3
   - List for ranks 4-10
   - Mini stats per person

3. RELATIONSHIPS OVER TIME
   - Bump chart: yearly rankings
   - Stacked area: volume by top contacts

4. RELATIONSHIP DYNAMICS
   - Lopsidedness scatter plot
   - Rising stars & faded connections
   - Response time leaderboard

5. WHEN YOU TEXT
   - Hour × Day heatmap
   - Peak hours by year (small multiples)
   - Yearly volume chart
   - Longest streaks

6. WHAT YOU SAY
   - Top phrases per year (cards)
   - Words unique to each year
   - Question ratio trends

7. EMOJI STORY
   - Top emojis per year (grid)
   - Emoji by contact

8. VIBES & TOPICS
   - Sentiment by contact
   - Topics per year
   - Topic × contact breakdown
```

---

## Data Persistence

Save processed data for follow-up queries:
- `messages.parquet` - cleaned messages with computed fields
- `contacts.json` - phone/email to name mappings
- `yearly_stats.json` - pre-computed aggregates
- `sentiment_scores.parquet` - per-message sentiment
- `topics.parquet` - topic assignments

---

## Privacy
- All processing runs locally
- chat.db accessed read-only
- No data sent to external APIs (local ML models only)

## Contact Resolution
1. Query macOS Contacts database via pyobjc
2. Match phone numbers/emails to contact names
3. For unmatched top contacts, prompt user for manual mapping
