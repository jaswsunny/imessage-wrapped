"""Generate the final HTML report with iMessage-style design."""
import json
from pathlib import Path
from config import OUTPUT_DIR, START_YEAR, END_YEAR

# iOS System Colors
COLORS = {
    'blue': '#007AFF',
    'purple': '#5856D6',
    'green': '#34C759',
    'pink': '#FF2D55',
    'orange': '#FF9500',
    'teal': '#5AC8FA',
    'red': '#FF3B30',
    'yellow': '#FFD60A',
    'gray': '#8E8E93',
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iMessage Wrapped {start_year}-{end_year}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', sans-serif;
            background: #F2F2F7;
            color: #1C1C1E;
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}

        /* Header */
        header {{
            text-align: center;
            padding: 4rem 2rem;
            background: linear-gradient(180deg, #007AFF 0%, #5856D6 100%);
            color: white;
            position: relative;
        }}

        .logo-icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.9;
        }}

        h1 {{
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }}

        .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 2rem;
        }}

        .hero-stats {{
            display: flex;
            justify-content: center;
            gap: 3rem;
            flex-wrap: wrap;
        }}

        .hero-stat {{
            text-align: center;
            padding: 1.5rem 2rem;
            background: rgba(255,255,255,0.15);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }}

        .hero-number {{
            font-size: 2.8rem;
            font-weight: 700;
        }}

        .hero-label {{
            font-size: 0.85rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Sections */
        section {{
            margin: 2rem 0;
            padding: 2rem;
            background: white;
            border-radius: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .section-icon {{
            width: 50px;
            height: 50px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            color: white;
        }}

        .section-icon.blue {{ background: #007AFF; }}
        .section-icon.purple {{ background: #5856D6; }}
        .section-icon.green {{ background: #34C759; }}
        .section-icon.pink {{ background: #FF2D55; }}
        .section-icon.orange {{ background: #FF9500; }}
        .section-icon.teal {{ background: #5AC8FA; }}
        .section-icon.red {{ background: #FF3B30; }}

        h2 {{
            font-size: 1.8rem;
            font-weight: 600;
            color: #1C1C1E;
        }}

        h3 {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #1C1C1E;
            margin: 1.5rem 0 1rem;
        }}

        .section-subtitle {{
            color: #8E8E93;
            margin-bottom: 1.5rem;
            font-size: 1rem;
        }}

        /* Podium */
        .podium {{
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 1.5rem;
            margin: 2rem 0;
            padding: 2rem 0;
        }}

        .podium-item {{
            text-align: center;
            padding: 2rem 1.5rem;
            border-radius: 20px;
            min-width: 200px;
            transition: transform 0.3s ease;
        }}

        .podium-item:hover {{ transform: translateY(-5px); }}

        .podium-item.gold {{
            order: 2;
            background: linear-gradient(135deg, #FFD60A, #FFCC00);
            transform: scale(1.1);
            box-shadow: 0 8px 30px rgba(255, 214, 10, 0.4);
        }}

        .podium-item.silver {{
            order: 1;
            background: #E5E5EA;
        }}

        .podium-item.bronze {{
            order: 3;
            background: linear-gradient(135deg, #FF9500, #FF9F0A);
            color: white;
        }}

        .podium-medal {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        .podium-name {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; }}
        .podium-count {{ font-size: 0.9rem; opacity: 0.8; }}

        /* Contact Grid */
        .contact-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
        }}

        .contact-card {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem 1.25rem;
            background: #F2F2F7;
            border-radius: 14px;
            transition: all 0.2s ease;
        }}

        .contact-card:hover {{
            background: #E5E5EA;
            transform: translateX(5px);
        }}

        .contact-rank {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #007AFF;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .contact-name {{ font-weight: 600; font-size: 1rem; }}
        .contact-stats {{ font-size: 0.85rem; color: #8E8E93; }}

        /* Party Cards */
        .party-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
        }}

        .party-card {{
            padding: 1.5rem;
            border-radius: 16px;
            background: #F2F2F7;
            border-left: 4px solid #007AFF;
        }}

        .party-card.ideas {{ border-left-color: #007AFF; }}
        .party-card.ride-or-dies {{ border-left-color: #FF2D55; }}
        .party-card.chaos {{ border-left-color: #FF9500; }}
        .party-card.work {{ border-left-color: #34C759; }}

        .party-emoji {{ font-size: 2rem; margin-bottom: 0.75rem; }}
        .party-title {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; }}
        .party-vibe {{ font-size: 0.85rem; color: #8E8E93; font-style: italic; margin-bottom: 1rem; }}

        .party-guests {{ list-style: none; }}
        .party-guests li {{
            padding: 0.4rem 0;
            border-bottom: 1px solid #E5E5EA;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.95rem;
        }}
        .party-guests li:last-child {{ border-bottom: none; }}
        .party-guests .guest-icon {{ opacity: 0.6; }}

        /* Genre Cards */
        .genre-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 1rem;
        }}

        .genre-card {{
            background: #F2F2F7;
            border-radius: 14px;
            padding: 1.25rem;
        }}

        .genre-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }}

        .genre-emoji {{ font-size: 1.4rem; }}
        .genre-name {{ font-weight: 600; font-size: 1rem; }}
        .genre-desc {{ font-size: 0.85rem; color: #8E8E93; font-style: italic; margin-bottom: 0.5rem; }}
        .genre-people {{ font-size: 0.9rem; color: #3C3C43; }}

        /* Grammar Cards */
        .grammar-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }}

        .grammar-card {{
            padding: 1.5rem;
            border-radius: 16px;
        }}

        .grammar-card.formal {{
            background: linear-gradient(135deg, rgba(52, 199, 89, 0.1), rgba(52, 199, 89, 0.05));
            border: 1px solid rgba(52, 199, 89, 0.3);
        }}

        .grammar-card.casual {{
            background: linear-gradient(135deg, rgba(255, 149, 0, 0.1), rgba(255, 149, 0, 0.05));
            border: 1px solid rgba(255, 149, 0, 0.3);
        }}

        .grammar-header {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }}
        .grammar-icon {{ font-size: 1.5rem; }}
        .grammar-title {{ font-weight: 600; font-size: 1.1rem; }}

        .grammar-list {{ list-style: none; }}
        .grammar-list li {{
            display: flex;
            justify-content: space-between;
            padding: 0.6rem 0;
            border-bottom: 1px solid rgba(0,0,0,0.06);
            font-size: 0.95rem;
        }}
        .grammar-list li:last-child {{ border-bottom: none; }}
        .grammar-score {{ color: #8E8E93; font-size: 0.85rem; }}

        /* Word Cloud Comparison */
        .word-comparison {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 2rem;
            align-items: center;
        }}

        .word-box {{
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
        }}

        .word-box.old {{
            background: #E5E5EA;
        }}

        .word-box.new {{
            background: linear-gradient(135deg, rgba(0, 122, 255, 0.1), rgba(88, 86, 214, 0.1));
            border: 2px solid #007AFF;
        }}

        .word-year {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }}

        .word-box.old .word-year {{ color: #8E8E93; }}
        .word-box.new .word-year {{ color: #007AFF; }}

        .wordcloud-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 0.75rem;
            min-height: 200px;
        }}

        .word {{ transition: transform 0.2s ease; }}
        .word:hover {{ transform: scale(1.1); }}

        .word-arrow {{ font-size: 3rem; color: #C7C7CC; }}

        .word-summary {{ font-size: 0.85rem; color: #8E8E93; margin-top: 1rem; font-style: italic; }}

        /* Key Shifts */
        .shifts-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-top: 2rem;
        }}

        .shift-card {{
            padding: 1rem 1.25rem;
            border-radius: 14px;
            text-align: center;
        }}

        .shift-card.disappeared {{ background: rgba(255, 59, 48, 0.1); }}
        .shift-card.emerged {{ background: rgba(52, 199, 89, 0.1); }}
        .shift-card.constant {{ background: rgba(0, 122, 255, 0.1); }}

        .shift-label {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
        }}

        .shift-card.disappeared .shift-label {{ color: #FF3B30; }}
        .shift-card.emerged .shift-label {{ color: #34C759; }}
        .shift-card.constant .shift-label {{ color: #007AFF; }}

        .shift-words {{ font-size: 0.95rem; color: #3C3C43; }}

        /* Vocabulary Timeline */
        .vocab-section {{ margin-bottom: 2rem; }}

        .vocab-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .vocab-title.ai {{ color: #007AFF; }}
        .vocab-title.politics {{ color: #FF3B30; }}
        .vocab-title.culture {{ color: #AF52DE; }}

        .vocab-timeline {{
            position: relative;
            padding-left: 2rem;
        }}

        .vocab-timeline::before {{
            content: '';
            position: absolute;
            left: 0.5rem;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #E5E5EA;
        }}

        .vocab-year-item {{
            position: relative;
            margin-bottom: 1.25rem;
            padding-left: 1.5rem;
        }}

        .vocab-year-item::before {{
            content: '';
            position: absolute;
            left: -1.5rem;
            top: 0.5rem;
            width: 12px;
            height: 12px;
            background: #007AFF;
            border-radius: 50%;
        }}

        .vocab-year-label {{ font-weight: 700; font-size: 1rem; color: #007AFF; margin-bottom: 0.35rem; }}
        .vocab-tags {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.25rem; }}

        .vocab-tag {{
            padding: 0.3rem 0.7rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }}

        .vocab-tag.ai {{ background: rgba(0, 122, 255, 0.15); color: #007AFF; }}
        .vocab-tag.politics {{ background: rgba(255, 59, 48, 0.15); color: #FF3B30; }}
        .vocab-tag.culture {{ background: rgba(175, 82, 222, 0.15); color: #AF52DE; }}

        .vocab-note {{ font-size: 0.85rem; color: #8E8E93; font-style: italic; }}

        /* Highlight Box */
        .highlight-box {{
            background: linear-gradient(135deg, rgba(0, 122, 255, 0.1), rgba(88, 86, 214, 0.1));
            border: 1px solid rgba(0, 122, 255, 0.3);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            margin: 1.5rem 0;
        }}

        .highlight-quote {{
            font-size: 1.3rem;
            font-weight: 600;
            color: #007AFF;
        }}

        /* Agreement/Debate Grid */
        .debate-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}

        .debate-column h4 {{
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .debate-column.agree h4 {{ color: #34C759; }}
        .debate-column.debate h4 {{ color: #FF9500; }}

        .debate-subtitle {{
            font-size: 0.85rem;
            color: #8E8E93;
            font-style: italic;
            margin-bottom: 1rem;
        }}

        .debate-card {{
            background: #F2F2F7;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .debate-rank {{
            font-size: 1.5rem;
            font-weight: 700;
            min-width: 2rem;
        }}

        .debate-column.agree .debate-rank {{ color: #34C759; }}
        .debate-column.debate .debate-rank {{ color: #FF9500; }}

        .debate-name {{ font-weight: 600; }}
        .debate-stats {{ font-size: 0.85rem; color: #8E8E93; }}

        /* Churn Grid */
        .churn-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}

        .churn-column h4 {{
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .churn-column.fadeout h4 {{ color: #FF3B30; }}
        .churn-column.newfriend h4 {{ color: #34C759; }}

        .churn-subtitle {{
            font-size: 0.85rem;
            color: #8E8E93;
            margin-bottom: 1rem;
        }}

        .churn-card {{
            background: #F2F2F7;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .churn-column.fadeout .churn-card {{ border-left: 3px solid #FF3B30; }}
        .churn-column.newfriend .churn-card {{ border-left: 3px solid #34C759; }}

        .churn-name {{ font-weight: 600; }}
        .churn-stats {{ font-size: 0.85rem; color: #8E8E93; }}

        /* Insights Grid */
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.25rem;
        }}

        .insight-card {{
            padding: 1.5rem;
            background: #F2F2F7;
            border-radius: 16px;
            border-left: 4px solid #007AFF;
        }}

        .insight-title {{
            font-weight: 600;
            color: #007AFF;
            margin-bottom: 0.75rem;
            font-size: 1rem;
        }}

        .insight-content {{
            font-size: 0.95rem;
            color: #3C3C43;
            line-height: 1.7;
        }}

        /* Chart Container */
        .chart-container {{
            margin: 1.5rem 0;
            background: #F9F9F9;
            border-radius: 16px;
            padding: 1rem;
        }}

        /* Stats Row */
        .stats-row {{
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}

        .stat-card {{
            flex: 1;
            min-width: 150px;
            padding: 1rem 1.25rem;
            border-radius: 14px;
            text-align: center;
        }}

        .stat-card.green {{ background: rgba(52, 199, 89, 0.1); }}
        .stat-card.blue {{ background: rgba(0, 122, 255, 0.1); }}
        .stat-card.orange {{ background: rgba(255, 149, 0, 0.1); }}

        .stat-value {{ font-size: 1.5rem; font-weight: 700; }}
        .stat-card.green .stat-value {{ color: #34C759; }}
        .stat-card.blue .stat-value {{ color: #007AFF; }}
        .stat-card.orange .stat-value {{ color: #FF9500; }}

        .stat-label {{
            font-size: 0.75rem;
            color: #8E8E93;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-desc {{ font-size: 0.8rem; color: #8E8E93; margin-top: 0.25rem; }}

        /* Year sections */
        .year-section {{
            margin: 1.5rem 0;
            padding: 1.5rem;
            background: #F2F2F7;
            border-radius: 14px;
        }}

        .year-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #007AFF;
            margin-bottom: 0.75rem;
        }}

        .year-list {{
            list-style: none;
        }}

        .year-list li {{
            padding: 0.5rem 0;
            border-bottom: 1px solid #E5E5EA;
            font-size: 0.95rem;
        }}

        .year-list li:last-child {{ border-bottom: none; }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 3rem 2rem;
            color: #8E8E93;
            font-size: 0.9rem;
        }}

        footer .heart {{ color: #FF2D55; }}

        @media (max-width: 768px) {{
            .podium {{ flex-direction: column; align-items: center; }}
            .podium-item {{ order: unset !important; transform: none !important; }}
            .podium-item.gold {{ transform: none; }}
            .word-comparison {{ grid-template-columns: 1fr; }}
            .word-arrow {{ transform: rotate(90deg); }}
            .debate-grid, .churn-grid {{ grid-template-columns: 1fr; }}
            .shifts-grid {{ grid-template-columns: 1fr; }}
            h1 {{ font-size: 2.5rem; }}
            .hero-stats {{ gap: 1rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="logo-icon"><i class="fas fa-comment"></i></div>
        <h1>iMessage Wrapped</h1>
        <p class="subtitle">{start_year} - {end_year}</p>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-number">{total_messages:,}</div>
                <div class="hero-label">Messages</div>
            </div>
            <div class="hero-stat">
                <div class="hero-number">{total_contacts:,}</div>
                <div class="hero-label">People</div>
            </div>
            <div class="hero-stat">
                <div class="hero-number">{num_years}</div>
                <div class="hero-label">Years</div>
            </div>
        </div>
    </header>

    <div class="container">
        {sections}
    </div>

    <footer>
        <p>{total_messages:,} messages. {total_contacts:,} people. {num_years} years. One life, rendered in text.</p>
        <p style="margin-top: 0.5rem;">Generated with <span class="heart">&#9829;</span> by Claude Code</p>
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
        <div class="podium-item silver">
            <div class="podium-medal">&#129352;</div>
            <div class="podium-name">{top3[1]['contact_name']}</div>
            <div class="podium-count">{top3[1]['total_messages']:,} messages</div>
        </div>
        <div class="podium-item gold">
            <div class="podium-medal">&#129351;</div>
            <div class="podium-name">{top3[0]['contact_name']}</div>
            <div class="podium-count">{top3[0]['total_messages']:,} messages</div>
        </div>
        <div class="podium-item bronze">
            <div class="podium-medal">&#129353;</div>
            <div class="podium-name">{top3[2]['contact_name']}</div>
            <div class="podium-count">{top3[2]['total_messages']:,} messages</div>
        </div>
    </div>
    """


def create_contact_grid_html(contacts, start_rank=4, max_contacts=6):
    """Create contact grid HTML."""
    cards = []
    contact_list = contacts.iloc[start_rank-1:start_rank-1+max_contacts].to_dict('records')
    for i, contact in enumerate(contact_list, start=start_rank):
        cards.append(f"""
        <div class="contact-card">
            <div class="contact-rank">{i}</div>
            <div class="contact-info">
                <div class="contact-name">{contact['contact_name']}</div>
                <div class="contact-stats">{contact['total_messages']:,} messages</div>
            </div>
        </div>
        """)
    return '<div class="contact-grid">' + ''.join(cards) + '</div>'


def create_insight_cards_html(insights):
    """Create insight cards from AI insights."""
    if not insights or 'ai_insights' not in insights:
        return ""

    cards = []
    for i, (title, content) in enumerate(insights['ai_insights'][:10], 1):
        cards.append(f"""
        <div class="insight-card">
            <div class="insight-title">{i}. {title}</div>
            <div class="insight-content">{content}</div>
        </div>
        """)
    return '<div class="insights-grid">' + ''.join(cards) + '</div>'


def create_top_by_year_html(top_by_year):
    """Create yearly top contacts sections."""
    if top_by_year is None or top_by_year.empty:
        return ""

    html_parts = []
    years = sorted(top_by_year['year'].unique())

    for year in years:
        year_data = top_by_year[top_by_year['year'] == year].sort_values('rank').head(5)
        items = [f"<li>{row['contact_name']} ({row['total_messages']:,} msgs)</li>"
                 for _, row in year_data.iterrows()]
        html_parts.append(f"""
        <div class="year-section">
            <div class="year-title">{year}</div>
            <ol class="year-list">{''.join(items)}</ol>
        </div>
        """)

    return ''.join(html_parts)


def create_wordcloud_html(wordcloud_old, wordcloud_new, year_old, year_new):
    """Create word cloud comparison section."""
    if not wordcloud_old or not wordcloud_new:
        return ""

    # Word sizes based on frequency rank
    sizes_old = ['2rem', '1.8rem', '1.6rem', '1.5rem', '1.4rem', '1.3rem', '1.25rem', '1.2rem', '1.15rem', '1.1rem', '1.05rem', '1rem']
    colors_old = ['#636366', '#8E8E93', '#636366', '#8E8E93', '#636366', '#AEAEB2', '#8E8E93', '#AEAEB2', '#C7C7CC', '#AEAEB2', '#C7C7CC', '#C7C7CC']

    sizes_new = ['2rem', '1.8rem', '1.6rem', '1.5rem', '1.4rem', '1.3rem', '1.25rem', '1.2rem', '1.15rem', '1.1rem', '1.05rem', '1rem']
    colors_new = ['#007AFF', '#5856D6', '#007AFF', '#FF2D55', '#34C759', '#FF9500', '#5856D6', '#5AC8FA', '#FF2D55', '#007AFF', '#FF9500', '#34C759']

    old_words = []
    for i, (word, count) in enumerate(wordcloud_old[:12]):
        size = sizes_old[i] if i < len(sizes_old) else '1rem'
        color = colors_old[i] if i < len(colors_old) else '#8E8E93'
        weight = 700 - (i * 50) if i < 4 else 400
        old_words.append(f'<span class="word" style="font-size: {size}; font-weight: {weight}; color: {color};">{word}</span>')

    new_words = []
    for i, (word, count) in enumerate(wordcloud_new[:12]):
        size = sizes_new[i] if i < len(sizes_new) else '1rem'
        color = colors_new[i] if i < len(colors_new) else '#007AFF'
        weight = 700 - (i * 50) if i < 4 else 400
        new_words.append(f'<span class="word" style="font-size: {size}; font-weight: {weight}; color: {color};">{word}</span>')

    return f"""
    <div class="word-comparison">
        <div class="word-box old">
            <div class="word-year">{year_old}</div>
            <div class="wordcloud-container">
                {' '.join(old_words)}
            </div>
        </div>
        <div class="word-arrow">→</div>
        <div class="word-box new">
            <div class="word-year">{year_new}</div>
            <div class="wordcloud-container">
                {' '.join(new_words)}
            </div>
        </div>
    </div>
    """


def create_grammar_html(formal_contacts, casual_contacts):
    """Create grammar comparison section."""
    if not formal_contacts and not casual_contacts:
        return ""

    formal_items = ""
    if formal_contacts:
        for name, score in formal_contacts[:5]:
            formal_items += f'<li><span>{name}</span><span class="grammar-score">Score: {score:.1f}</span></li>'

    casual_items = ""
    if casual_contacts:
        for name, pct in casual_contacts[:5]:
            casual_items += f'<li><span>{name}</span><span class="grammar-score">{pct:.0f}% lowercase</span></li>'

    return f"""
    <div class="grammar-grid">
        <div class="grammar-card formal">
            <div class="grammar-header">
                <span class="grammar-icon">&#128221;</span>
                <span class="grammar-title">Most Formal</span>
            </div>
            <ul class="grammar-list">
                {formal_items}
            </ul>
            <p style="font-size: 0.85rem; color: #8E8E93; margin-top: 1rem; font-style: italic;">Proper punctuation, longer sentences, zero slang</p>
        </div>
        <div class="grammar-card casual">
            <div class="grammar-header">
                <span class="grammar-icon">&#128293;</span>
                <span class="grammar-title">Most Casual</span>
            </div>
            <ul class="grammar-list">
                {casual_items}
            </ul>
            <p style="font-size: 0.85rem; color: #8E8E93; margin-top: 1rem; font-style: italic;">All lowercase, slang-heavy, zero pretense</p>
        </div>
    </div>
    """


def create_debate_html(agreers, debaters):
    """Create agreement vs debate section."""
    if not agreers and not debaters:
        return ""

    agree_cards = ""
    for i, (name, rate) in enumerate(agreers[:3], 1):
        agree_cards += f"""
        <div class="debate-card">
            <div class="debate-rank">{i}</div>
            <div>
                <div class="debate-name">{name}</div>
                <div class="debate-stats">{rate:.1f}% agreement rate</div>
            </div>
        </div>
        """

    debate_cards = ""
    for i, (name, rate) in enumerate(debaters[:3], 1):
        debate_cards += f"""
        <div class="debate-card">
            <div class="debate-rank">{i}</div>
            <div>
                <div class="debate-name">{name}</div>
                <div class="debate-stats">{rate:.1f}% debate rate</div>
            </div>
        </div>
        """

    return f"""
    <div class="debate-grid">
        <div class="debate-column agree">
            <h4><i class="fas fa-handshake"></i> You Agree With</h4>
            <div class="debate-subtitle">"totally" "exactly" "so true" "100%"</div>
            {agree_cards}
        </div>
        <div class="debate-column debate">
            <h4><i class="fas fa-bolt"></i> You Debate With</h4>
            <div class="debate-subtitle">"actually" "but" "I disagree" "not sure"</div>
            {debate_cards}
        </div>
    </div>
    """


def create_churn_html(fadeouts, new_friends):
    """Create social churn section."""
    if not fadeouts and not new_friends:
        return ""

    fadeout_cards = ""
    for name, old_count, new_count in fadeouts[:4]:
        if old_count > 0:
            drop_pct = int((1 - new_count / old_count) * 100)
            fadeout_cards += f"""
            <div class="churn-card">
                <span class="churn-name">{name}</span>
                <span class="churn-stats">{old_count:,} → {new_count} msgs ({drop_pct}% drop)</span>
            </div>
            """

    newfriend_cards = ""
    for name, old_count, new_count in new_friends[:4]:
        newfriend_cards += f"""
        <div class="churn-card">
            <span class="churn-name">{name}</span>
            <span class="churn-stats">{old_count:,} → {new_count:,} msgs</span>
        </div>
        """

    return f"""
    <div class="churn-grid">
        <div class="churn-column fadeout">
            <h4><i class="fas fa-moon"></i> Fadeouts</h4>
            <div class="churn-subtitle">Active before, quiet now</div>
            {fadeout_cards}
        </div>
        <div class="churn-column newfriend">
            <h4><i class="fas fa-sun"></i> New Friends</h4>
            <div class="churn-subtitle">Barely existed before, now central</div>
            {newfriend_cards}
        </div>
    </div>
    """


def embed_plotly_chart(fig, div_id, height=400):
    """Convert plotly figure to embedded HTML with iMessage styling."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1C1C1E', family='-apple-system, BlinkMacSystemFont, sans-serif'),
        margin=dict(l=60, r=30, t=20, b=60),
    )
    fig.update_xaxes(gridcolor='#E5E5EA')
    fig.update_yaxes(gridcolor='#E5E5EA')

    return f"""
    <div class="chart-container" id="{div_id}" style="height: {height}px;"></div>
    <script>
        var data = {fig.to_json()};
        Plotly.newPlot('{div_id}', data.data, data.layout, {{responsive: true, displayModeBar: false}});
    </script>
    """


def generate_report(total_messages, total_sent, total_received, total_contacts,
                   top_contacts, charts, phrases_df, emojis_df, topics_df, insights,
                   top_2025=None, df_2025=None, top_by_year=None, monthly_top_2025=None,
                   wordcloud_old=None, wordcloud_new=None,
                   formal_contacts=None, casual_contacts=None,
                   agreers=None, debaters=None,
                   fadeouts=None, new_friends=None):
    """Generate the complete HTML report."""
    sections = []

    num_years = END_YEAR - START_YEAR

    # Section 1: Top People
    section1 = f"""
    <section>
        <div class="section-header">
            <div class="section-icon purple"><i class="fas fa-trophy"></i></div>
            <h2>Your Top People</h2>
        </div>
        {create_podium_html(top_contacts)}
        {create_contact_grid_html(top_contacts, start_rank=4, max_contacts=6)}
    </section>
    """
    sections.append(section1)

    # Section 2: Relationships Over Time
    stacked_chart = ""
    if 'stacked_area' in charts and charts['stacked_area'] is not None:
        stacked_chart = embed_plotly_chart(charts['stacked_area'], 'stacked-chart', height=500)

    section2 = f"""
    <section>
        <div class="section-header">
            <div class="section-icon blue"><i class="fas fa-chart-area"></i></div>
            <h2>Relationships Over Time</h2>
        </div>
        <p class="section-subtitle">How your top relationships have evolved year by year.</p>
        {stacked_chart}
        <h3>Top 5 Each Year</h3>
        {create_top_by_year_html(top_by_year)}
    </section>
    """
    sections.append(section2)

    # Section 3: When You Text (Heatmap)
    heatmap_chart = ""
    if 'heatmap' in charts and charts['heatmap'] is not None:
        heatmap_chart = embed_plotly_chart(charts['heatmap'], 'heatmap-chart', height=320)

    yearly_chart = ""
    if 'yearly_volume' in charts and charts['yearly_volume'] is not None:
        yearly_chart = embed_plotly_chart(charts['yearly_volume'], 'yearly-chart', height=350)

    section3 = f"""
    <section>
        <div class="section-header">
            <div class="section-icon orange"><i class="fas fa-clock"></i></div>
            <h2>When You Text</h2>
        </div>
        <p class="section-subtitle">Your messaging rhythm across hours and days.</p>
        {heatmap_chart}
        {yearly_chart}
    </section>
    """
    sections.append(section3)

    # Section 4: Word Cloud Comparison
    if wordcloud_old and wordcloud_new:
        section4 = f"""
        <section>
            <div class="section-header">
                <div class="section-icon purple"><i class="fas fa-cloud"></i></div>
                <h2>Vocabulary Evolution: {START_YEAR} → {END_YEAR - 1}</h2>
            </div>
            <p class="section-subtitle">How your words changed over the years (excluding boring filler words).</p>
            {create_wordcloud_html(wordcloud_old, wordcloud_new, START_YEAR, END_YEAR - 1)}
        </section>
        """
        sections.append(section4)

    # Section 5: Grammar
    if formal_contacts or casual_contacts:
        section5 = f"""
        <section>
            <div class="section-header">
                <div class="section-icon green"><i class="fas fa-spell-check"></i></div>
                <h2>Grammar: Who Gets Your Best English</h2>
            </div>
            <p class="section-subtitle">Your grammar changes dramatically depending on who you're texting.</p>
            {create_grammar_html(formal_contacts, casual_contacts)}
        </section>
        """
        sections.append(section5)

    # Section 6: Agreement vs Debate
    if agreers or debaters:
        section6 = f"""
        <section>
            <div class="section-header">
                <div class="section-icon orange"><i class="fas fa-comments"></i></div>
                <h2>Agreement vs Debate</h2>
            </div>
            <p class="section-subtitle">Who brings out your "totally!" vs your "actually..."</p>
            {create_debate_html(agreers, debaters)}
        </section>
        """
        sections.append(section6)

    # Section 7: Social Churn
    if fadeouts or new_friends:
        section7 = f"""
        <section>
            <div class="section-header">
                <div class="section-icon pink"><i class="fas fa-exchange-alt"></i></div>
                <h2>The Social Churn</h2>
            </div>
            <p class="section-subtitle">Your social circle is constantly evolving. Who faded and who emerged.</p>
            {create_churn_html(fadeouts, new_friends)}
        </section>
        """
        sections.append(section7)

    # Section 8: AI Insights
    insights_html = create_insight_cards_html(insights)
    if insights_html:
        section8 = f"""
        <section>
            <div class="section-header">
                <div class="section-icon teal"><i class="fas fa-lightbulb"></i></div>
                <h2>Surprising Relationship Dynamics</h2>
            </div>
            {insights_html}
        </section>
        """
        sections.append(section8)

    # Generate final HTML
    html = HTML_TEMPLATE.format(
        start_year=START_YEAR,
        end_year=END_YEAR,
        total_messages=total_messages,
        total_sent=total_sent,
        total_received=total_received,
        total_contacts=total_contacts,
        num_years=num_years,
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
