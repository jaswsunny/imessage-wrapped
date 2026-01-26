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

        .alerts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }}

        .alert-section h4 {{
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .alert-card {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: #F2F2F7;
            border-radius: 12px;
            margin-bottom: 0.75rem;
        }}

        .alert-card.fading {{ border-left: 3px solid #FF9500; }}
        .alert-card.emerging {{ border-left: 3px solid #34C759; }}

        .alert-icon {{ font-size: 1.5rem; }}
        .alert-content {{ flex: 1; }}
        .alert-name {{ font-weight: 600; }}
        .alert-detail {{ font-size: 0.9rem; color: #3C3C43; }}
        .alert-time {{ font-size: 0.8rem; color: #8E8E93; }}

        /* LLM Narratives */
        .llm-narrative {{
            background: linear-gradient(135deg, rgba(88, 86, 214, 0.05), rgba(0, 122, 255, 0.05));
            border: 1px solid rgba(88, 86, 214, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .llm-narrative h3 {{
            color: #5856D6;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }}

        .llm-narrative p {{
            line-height: 1.8;
            color: #3C3C43;
            margin-bottom: 1rem;
        }}

        .llm-narrative p:last-child {{
            margin-bottom: 0;
        }}

        .llm-placeholder {{
            text-align: center;
            padding: 2rem;
            color: #666;
            background: rgba(88, 86, 214, 0.05);
            border-radius: 12px;
        }}

        .llm-placeholder code {{
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }}

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
            h1 {{ font-size: 2.5rem; }}
            .hero-stats {{ gap: 1rem; }}
        }}

        /* Interactive Controls */
        .interactive-controls {{
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}

        .control-row {{
            display: flex;
            gap: 1.5rem;
            align-items: center;
            flex-wrap: wrap;
        }}

        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .control-label {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #8E8E93;
        }}

        .contact-select {{
            padding: 0.5rem 1rem;
            border: 2px solid #E5E5EA;
            border-radius: 8px;
            font-size: 0.95rem;
            min-width: 200px;
            background: white;
        }}

        .contact-select:focus {{
            border-color: #007AFF;
            outline: none;
        }}

        /* Comparison Panel */
        .comparison-panel {{
            display: none;
            background: #F2F2F7;
            border-radius: 16px;
            padding: 1.5rem;
            margin-top: 1rem;
        }}

        .comparison-panel.active {{
            display: block;
        }}

        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 2rem;
            align-items: center;
        }}

        .comparison-side {{
            text-align: center;
        }}

        .comparison-name {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #007AFF;
            margin-bottom: 1rem;
        }}

        .comparison-stat {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #E5E5EA;
        }}

        .comparison-vs {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #8E8E93;
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
    {interactive_js}
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


def create_health_section_html(health_data):
    """Create relationship health section HTML - simplified to just fading/emerging."""
    if not health_data:
        return ""

    fading = health_data.get('fading_friendships', [])[:5]
    emerging = health_data.get('emerging_connections', [])[:5]

    if not fading and not emerging:
        return ""

    def format_days_ago(days):
        """Convert days to human-readable format."""
        if days == 0:
            return "today"
        elif days == 1:
            return "yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 14:
            return "last week"
        elif days < 30:
            return f"{days // 7} weeks ago"
        elif days < 60:
            return "last month"
        elif days < 365:
            return f"{days // 30} months ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"

    # To Rekindle (formerly "Fading Friendships" - reframed positively)
    fading_html = ""
    if fading:
        fading_items = ""
        for f in fading:
            days = f['days_since_contact']
            time_ago = format_days_ago(days)
            baseline = f.get('baseline_rate', 0)
            recent = f.get('recent_rate', 0)
            total = f.get('total_messages', 0)
            drop = f.get('drop_percentage', 0)
            fading_items += f"""
            <div class="alert-card fading">
                <div class="alert-icon">💬</div>
                <div class="alert-content">
                    <div class="alert-name">{f['contact_name']}</div>
                    <div class="alert-detail">{total:,} total msgs • Was ~{baseline:.0f}/wk → now ~{recent:.0f}/wk ({drop:.0f}% drop)</div>
                    <div class="alert-time">Last message: {time_ago}</div>
                </div>
            </div>
            """
        fading_html = f"""
        <div class="alert-section">
            <h4>💛 To Rekindle?</h4>
            <p style="color: #8E8E93; font-size: 14px; margin-bottom: 16px;">People you used to talk to more — might be worth reaching out.</p>
            {fading_items}
        </div>
        """

    # Emerging connections
    emerging_html = ""
    if emerging:
        emerging_items = ""
        for e in emerging:
            total = e.get('total_messages', 0)
            recent = e.get('recent_messages', 0)
            rate = e.get('msgs_per_week', 0)
            baseline = e.get('baseline_rate', 0)
            growth = e.get('growth', '')

            if e.get('is_revived'):
                label = f"Revived! Was quiet, now ~{rate:.0f} msgs/wk"
                icon = "&#128260;"  # counterclockwise arrows
            elif growth and 'x' in str(growth):
                label = f"{growth} growth • Was ~{baseline:.0f}/wk → now ~{rate:.0f}/wk"
                icon = "&#128200;"  # chart increasing
            else:
                label = f"~{rate:.0f} msgs/wk"
                icon = "&#127775;"  # star

            emerging_items += f"""
            <div class="alert-card emerging">
                <div class="alert-icon">{icon}</div>
                <div class="alert-content">
                    <div class="alert-name">{e['contact_name']}</div>
                    <div class="alert-detail">{label}</div>
                    <div class="alert-time">{total:,} total messages • {recent} in last 30 days</div>
                </div>
            </div>
            """
        emerging_html = f"""
        <div class="alert-section">
            <h4><i class="fas fa-star" style="color: #34C759;"></i> Emerging Connections</h4>
            {emerging_items}
        </div>
        """

    return f"""
    <div class="alerts-container">
        {fading_html}
        {emerging_html}
    </div>
    """


def create_interactive_controls_html(contacts, years):
    """Create interactive control panel HTML."""
    # First contact options - preselect first contact
    contact1_options = '\n'.join([
        f'<option value="{c}" {"selected" if i == 0 else ""}>{c}</option>'
        for i, c in enumerate(contacts[:30])
    ])
    # Second contact options - preselect second contact
    contact2_options = '\n'.join([
        f'<option value="{c}" {"selected" if i == 1 else ""}>{c}</option>'
        for i, c in enumerate(contacts[:30])
    ])

    return f"""
    <div class="interactive-controls" id="interactive-panel">
        <div class="control-row">
            <div class="control-group">
                <span class="control-label">Compare Two Contacts</span>
                <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
                    <select class="contact-select" id="contact1" onchange="compareContacts()">
                        {contact1_options}
                    </select>
                    <span style="color: #8E8E93;">vs</span>
                    <select class="contact-select" id="contact2" onchange="compareContacts()">
                        {contact2_options}
                    </select>
                </div>
            </div>
        </div>
        <div class="comparison-panel" id="comparison-panel"></div>
    </div>
    """


def create_interactive_js(contact_data):
    """Create JavaScript for interactive features."""
    import json as json_module
    contact_json = json_module.dumps(contact_data)

    return f"""
    <script>
    // Contact data for interactive features
    const contactData = {contact_json};

    // Contact comparison
    function formatResponseTime(mins) {{
        if (mins === null || mins === undefined) return 'N/A';
        if (mins < 1) return Math.round(mins * 60) + 's';
        if (mins < 60) return Math.round(mins) + 'm';
        if (mins < 1440) return (mins / 60).toFixed(1) + 'h';
        return (mins / 1440).toFixed(1) + 'd';
    }}

    function formatSentiment(val) {{
        if (val === null || val === undefined) return 'N/A';
        const sign = val >= 0 ? '+' : '';
        // Thresholds tuned for casual text messages (VADER scores cluster 0.1-0.2)
        if (val > 0.18) return `Positive (${{sign}}${{val.toFixed(2)}})`;
        if (val < 0.05) return `Negative (${{val.toFixed(2)}})`;
        return `Neutral (${{sign}}${{val.toFixed(2)}})`;
    }}

    function formatImessagePct(val) {{
        if (val === null || val === undefined) return 'N/A';
        const smsPct = 100 - val;
        if (smsPct < 1) return 'iMessage only';
        if (val < 1) return 'SMS only';
        return `${{val.toFixed(0)}}% iMessage`;
    }}

    function formatLopsidedness(val) {{
        if (!val || val === 1) return 'Balanced';
        if (val > 1) return `You +${{((val - 1) * 100).toFixed(0)}}%`;
        return `They +${{((1/val - 1) * 100).toFixed(0)}}%`;
    }}

    function compareContacts() {{
        const contact1 = document.getElementById('contact1')?.value;
        const contact2 = document.getElementById('contact2')?.value;
        const panel = document.getElementById('comparison-panel');

        if (!contact1 || !contact2 || !panel) return;

        const data1 = contactData[contact1] || {{}};
        const data2 = contactData[contact2] || {{}};

        panel.innerHTML = `
            <div class="comparison-grid">
                <div class="comparison-side">
                    <div class="comparison-name">${{contact1}}</div>
                    <div class="comparison-stat"><span>Total Messages</span><span>${{(data1.total || 0).toLocaleString()}}</span></div>
                    <div class="comparison-stat"><span>Sent / Received</span><span>${{(data1.sent || 0).toLocaleString()}} / ${{(data1.received || 0).toLocaleString()}}</span></div>
                    <div class="comparison-stat"><span>Balance</span><span>${{formatLopsidedness(data1.lopsidedness)}}</span></div>
                    <div class="comparison-stat"><span>Years Active</span><span>${{data1.years_active || 'N/A'}}</span></div>
                    <div class="comparison-stat"><span>First Message</span><span>${{data1.first_message || 'N/A'}}</span></div>
                    <div class="comparison-stat"><span>Last Message</span><span>${{data1.last_message || 'N/A'}}</span></div>
                    <div class="comparison-stat"><span>Your Response</span><span>${{formatResponseTime(data1.your_response_min)}}</span></div>
                    <div class="comparison-stat"><span>Their Response</span><span>${{formatResponseTime(data1.their_response_min)}}</span></div>
                    <div class="comparison-stat"><span>Vibe</span><span>${{formatSentiment(data1.sentiment)}}</span></div>
                    <div class="comparison-stat"><span>Service</span><span>${{formatImessagePct(data1.imessage_pct)}}</span></div>
                    <div class="comparison-stat"><span>Attachments</span><span>${{(data1.attachments || 0).toLocaleString()}}</span></div>
                    <div class="comparison-stat"><span>Links Shared</span><span>${{(data1.links || 0).toLocaleString()}}</span></div>
                </div>
                <div class="comparison-vs">VS</div>
                <div class="comparison-side">
                    <div class="comparison-name">${{contact2}}</div>
                    <div class="comparison-stat"><span>Total Messages</span><span>${{(data2.total || 0).toLocaleString()}}</span></div>
                    <div class="comparison-stat"><span>Sent / Received</span><span>${{(data2.sent || 0).toLocaleString()}} / ${{(data2.received || 0).toLocaleString()}}</span></div>
                    <div class="comparison-stat"><span>Balance</span><span>${{formatLopsidedness(data2.lopsidedness)}}</span></div>
                    <div class="comparison-stat"><span>Years Active</span><span>${{data2.years_active || 'N/A'}}</span></div>
                    <div class="comparison-stat"><span>First Message</span><span>${{data2.first_message || 'N/A'}}</span></div>
                    <div class="comparison-stat"><span>Last Message</span><span>${{data2.last_message || 'N/A'}}</span></div>
                    <div class="comparison-stat"><span>Your Response</span><span>${{formatResponseTime(data2.your_response_min)}}</span></div>
                    <div class="comparison-stat"><span>Their Response</span><span>${{formatResponseTime(data2.their_response_min)}}</span></div>
                    <div class="comparison-stat"><span>Vibe</span><span>${{formatSentiment(data2.sentiment)}}</span></div>
                    <div class="comparison-stat"><span>Service</span><span>${{formatImessagePct(data2.imessage_pct)}}</span></div>
                    <div class="comparison-stat"><span>Attachments</span><span>${{(data2.attachments || 0).toLocaleString()}}</span></div>
                    <div class="comparison-stat"><span>Links Shared</span><span>${{(data2.links || 0).toLocaleString()}}</span></div>
                </div>
            </div>
        `;
        panel.classList.add('active');
    }}

    // Load comparison on page load
    document.addEventListener('DOMContentLoaded', compareContacts);
    </script>
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


def create_extended_insights_html(extended_insights):
    """Create HTML for extended insights (links, attachments, SMS breakdown)."""
    if not extended_insights:
        return ""

    cards = []

    # Links - top domains with sent/received breakdown
    links = extended_insights.get('links', {})
    if links.get('available'):
        top_domains = links.get('top_domains_detailed', [])

        domain_list = ''.join([
            f"<li>{d['domain']} <span class='stat-detail'>({d['total']:,} - {d['sent']} sent, {d['received']} received)</span></li>"
            for d in top_domains[:5]
        ]) if top_domains else '<li>None</li>'

        cards.append(f"""
        <div class="insight-card" style="border-left-color: #5856D6;">
            <div class="insight-title">🔗 Link Sharing</div>
            <div class="insight-content">
                <p style="margin-bottom: 0.5rem;">{links.get('total_links', 0):,} links shared across {links.get('unique_domains', 0)} domains</p>
                <p style="margin-top: 0.5rem;"><strong>Top Domains:</strong></p>
                <ol style="margin: 0; padding-left: 1.2rem;">{domain_list}</ol>
            </div>
        </div>
        """)

    # Attachments
    attachments = extended_insights.get('attachments', {})
    if attachments.get('available'):
        type_counts = attachments.get('type_counts', {})
        total = attachments.get('total_attachments', 0)

        type_breakdown = ', '.join([f"{count:,} {t}s" for t, count in type_counts.items() if count > 0])

        # Photo contacts breakdown
        top_photo = attachments.get('top_photo_contacts', [])
        photo_list = ''.join([
            f"<li>{p['contact_name']} <span class='stat-detail'>({p['total']:,} - {p['sent']} sent, {p['received']} received)</span></li>"
            for p in top_photo[:8]
        ]) if top_photo else '<li>None</li>'

        # Video contacts breakdown
        top_video = attachments.get('top_video_contacts', [])
        video_list = ''.join([
            f"<li>{v['contact_name']} <span class='stat-detail'>({v['total']:,} - {v['sent']} sent, {v['received']} received)</span></li>"
            for v in top_video[:5]
        ]) if top_video else ''

        video_section = f"""
            <p style="margin-top: 1rem;"><strong>📹 Top Video Sharers:</strong></p>
            <ol style="margin: 0; padding-left: 1.2rem;">{video_list}</ol>
        """ if video_list else ''

        cards.append(f"""
        <div class="insight-card" style="border-left-color: #FF2D55;">
            <div class="insight-title">📎 Attachments</div>
            <div class="insight-content">
                <p><strong>{total:,}</strong> total attachments shared</p>
                <p style="font-size: 0.9rem; color: #666;">{type_breakdown}</p>
                <p style="margin-top: 1rem;"><strong>📸 Top Photo Sharers:</strong></p>
                <ol style="margin: 0; padding-left: 1.2rem;">{photo_list}</ol>
                {video_section}
            </div>
        </div>
        """)

    # SMS vs iMessage
    service = extended_insights.get('service_breakdown', {})
    if service.get('available'):
        overall_pct = service.get('overall_pct', {})
        imessage_pct = overall_pct.get('iMessage', 0)
        sms_pct = overall_pct.get('SMS', 0)
        sms_contacts = service.get('sms_heavy_contacts', [])

        sms_people = ', '.join([c['contact_name'] for c in sms_contacts[:3]]) if sms_contacts else 'None'

        cards.append(f"""
        <div class="insight-card" style="border-left-color: #5AC8FA;">
            <div class="insight-title">💬 iMessage vs SMS</div>
            <div class="insight-content">
                <p><strong>{imessage_pct}%</strong> iMessage, <strong>{sms_pct}%</strong> SMS</p>
                <p style="margin-top: 0.5rem;">Android friends (SMS-heavy): <strong>{sms_people}</strong></p>
            </div>
        </div>
        """)

    # Response times
    response = extended_insights.get('response_times', {})
    if response.get('available'):
        they_fast = response.get('they_respond_fast', [])
        they_slow = response.get('they_respond_slow', [])
        you_fast = response.get('you_respond_fast', [])
        you_slow = response.get('you_respond_slow', [])

        # Build lists
        they_fast_list = ''.join([
            f"<li>{r['contact_name']} <span class='stat-detail'>({r['time_formatted']})</span></li>"
            for r in they_fast[:4]
        ]) if they_fast else '<li>N/A</li>'

        they_slow_list = ''.join([
            f"<li>{r['contact_name']} <span class='stat-detail'>({r['time_formatted']})</span></li>"
            for r in they_slow[:4]
        ]) if they_slow else '<li>N/A</li>'

        you_fast_list = ''.join([
            f"<li>{r['contact_name']} <span class='stat-detail'>({r['time_formatted']})</span></li>"
            for r in you_fast[:4]
        ]) if you_fast else '<li>N/A</li>'

        you_slow_list = ''.join([
            f"<li>{r['contact_name']} <span class='stat-detail'>({r['time_formatted']})</span></li>"
            for r in you_slow[:4]
        ]) if you_slow else '<li>N/A</li>'

        cards.append(f"""
        <div class="insight-card" style="border-left-color: #34C759;">
            <div class="insight-title">⏱️ Response Times</div>
            <div class="insight-content">
                <p><strong>🏃 Quick to Reply to You:</strong></p>
                <ol style="margin: 0 0 0.5rem 0; padding-left: 1.2rem;">{they_fast_list}</ol>
                <p><strong>🐢 Slow to Reply to You:</strong></p>
                <ol style="margin: 0 0 0.5rem 0; padding-left: 1.2rem;">{they_slow_list}</ol>
                <p><strong>⚡ You Reply Fastest To:</strong></p>
                <ol style="margin: 0 0 0.5rem 0; padding-left: 1.2rem;">{you_fast_list}</ol>
                <p><strong>😅 You Leave Hanging:</strong></p>
                <ol style="margin: 0; padding-left: 1.2rem;">{you_slow_list}</ol>
            </div>
        </div>
        """)

    if not cards:
        return ""

    return f"""
    <section>
        <div class="section-header">
            <div class="section-icon teal"><i class="fas fa-microscope"></i></div>
            <h2>Hidden Data Insights</h2>
        </div>
        <p class="section-subtitle">Response times, attachments, and link sharing patterns.</p>
        <div class="insights-grid">
            {''.join(cards)}
        </div>
    </section>
    """


def generate_report(total_messages, total_sent, total_received, total_contacts,
                   top_contacts, charts, phrases_df, emojis_df, topics_df, insights,
                   top_2025=None, df_2025=None, top_by_year=None, monthly_top_2025=None,
                   wordcloud_old=None, wordcloud_new=None,
                   formal_contacts=None, casual_contacts=None,
                   agreers=None, debaters=None,
                   fadeouts=None, new_friends=None,
                   health_data=None, llm_narratives=None,
                   interactive_data=None, extended_insights=None,
                   lopsidedness_df=None, sentiment_df=None, response_times_df=None):
    """Generate the complete HTML report."""
    sections = []

    num_years = END_YEAR - START_YEAR

    # Build lopsidedness lookup
    lopsidedness_lookup = {}
    if lopsidedness_df is not None and hasattr(lopsidedness_df, 'iterrows'):
        for _, row in lopsidedness_df.iterrows():
            name = row.get('contact_name')
            if name:
                lopsidedness_lookup[name] = round(row.get('lopsidedness', 1.0), 2)

    # Build sentiment lookup
    sentiment_lookup = {}
    if sentiment_df is not None and hasattr(sentiment_df, 'iterrows'):
        for _, row in sentiment_df.iterrows():
            name = row.get('contact_name')
            if name:
                sentiment_lookup[name] = round(row.get('avg_sentiment', 0), 3)

    # Build response times lookup
    response_times_lookup = {}
    if response_times_df is not None and hasattr(response_times_df, 'iterrows'):
        for _, row in response_times_df.iterrows():
            name = row.get('contact_name')
            if name:
                response_times_lookup[name] = {
                    'your_response_min': round(row.get('your_response_time_min', 0) or 0, 1),
                    'their_response_min': round(row.get('their_response_time_min', 0) or 0, 1),
                }

    # Build extended lookups from extended_insights
    imessage_pct_lookup = {}
    attachments_lookup = {}
    links_lookup = {}
    if extended_insights:
        service_data = extended_insights.get('service_breakdown', {})
        if service_data.get('available'):
            imessage_pct_lookup = service_data.get('imessage_pct_by_contact', {})
        attachments_data = extended_insights.get('attachments', {})
        if attachments_data.get('available'):
            attachments_lookup = attachments_data.get('attachments_by_contact', {})
        links_data = extended_insights.get('links', {})
        if links_data.get('available'):
            links_lookup = links_data.get('links_by_contact', {})

    # Prepare interactive data for JS - build from top_contacts with all available stats
    contact_js_data = {}
    if interactive_data:
        contact_js_data = interactive_data.get('contacts', {})
    elif hasattr(top_contacts, 'iterrows'):
        for _, row in top_contacts.head(30).iterrows():
            name = row.get('contact_name')
            if name:
                # Format dates
                first_msg = row.get('first_message')
                last_msg = row.get('last_message')
                first_date = first_msg.strftime('%Y-%m-%d') if hasattr(first_msg, 'strftime') else str(first_msg)[:10]
                last_date = last_msg.strftime('%Y-%m-%d') if hasattr(last_msg, 'strftime') else str(last_msg)[:10]

                contact_js_data[name] = {
                    'total': int(row.get('total_messages', 0)),
                    'sent': int(row.get('sent', 0)),
                    'received': int(row.get('received', 0)),
                    'years_active': int(row.get('years_active', 0)),
                    'first_message': first_date,
                    'last_message': last_date,
                    'lopsidedness': lopsidedness_lookup.get(name, 1.0),
                    'sentiment': sentiment_lookup.get(name),
                    'your_response_min': response_times_lookup.get(name, {}).get('your_response_min'),
                    'their_response_min': response_times_lookup.get(name, {}).get('their_response_min'),
                    'imessage_pct': imessage_pct_lookup.get(name),
                    'attachments': attachments_lookup.get(name, 0),
                    'links': links_lookup.get(name, 0),
                }

    # Get years for interactive controls
    years_list = list(range(START_YEAR, END_YEAR))
    contact_names = list(contact_js_data.keys())[:30]

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

    # Section 9: Connection Changes (To Rekindle + Emerging)
    if health_data:
        health_html = create_health_section_html(health_data)
        if health_html:
            section9 = f"""
            <section>
                <div class="section-header">
                    <div class="section-icon green"><i class="fas fa-heart"></i></div>
                    <h2>Connection Changes</h2>
                </div>
                <p class="section-subtitle">Relationships that have shifted recently.</p>
                {health_html}
            </section>
            """
            sections.append(section9)

    # Section 10: Extended Insights (read receipts, links, attachments)
    extended_html = create_extended_insights_html(extended_insights)
    if extended_html:
        sections.append(extended_html)

    # Section 11: LLM Narratives (if available) or placeholder
    if llm_narratives:
        llm_sections = []
        if llm_narratives.get('wrapped_reflection'):
            text = llm_narratives['wrapped_reflection'].replace('\n\n', '</p><p>').replace('\n', '</p><p>')
            llm_sections.append(f"""
            <div class="llm-narrative">
                <h3>Your iMessage Wrapped</h3>
                <p>{text}</p>
            </div>
            """)
        if llm_narratives.get('psychological_profile'):
            text = llm_narratives['psychological_profile'].replace('\n\n', '</p><p>').replace('\n', '</p><p>')
            llm_sections.append(f"""
            <div class="llm-narrative">
                <h3>Communication Style Profile</h3>
                <p>{text}</p>
            </div>
            """)
        if llm_sections:
            section11 = f"""
            <section>
                <div class="section-header">
                    <div class="section-icon purple"><i class="fas fa-brain"></i></div>
                    <h2>AI-Generated Insights</h2>
                </div>
                <p class="section-subtitle">Personalized narratives generated by Claude.</p>
                {''.join(llm_sections)}
            </section>
            """
            sections.append(section11)
    else:
        # Show placeholder when LLM is disabled
        section11 = """
        <section>
            <div class="section-header">
                <div class="section-icon purple"><i class="fas fa-brain"></i></div>
                <h2>AI-Generated Insights</h2>
            </div>
            <div class="llm-narrative">
                <p class="llm-placeholder">
                    <strong>Want personalized AI insights?</strong><br><br>
                    Run with the <code>--llm</code> flag to generate AI-powered narratives about your messaging patterns.<br><br>
                    <em>Requirements:</em> Claude Code CLI installed<br>
                    <em>Model:</em> Claude Opus (for best quality on personal reflections)<br>
                    <em>Usage:</em> ~250k tokens
                </p>
            </div>
        </section>
        """
        sections.append(section11)

    # Section 12: Interactive Controls (at the end)
    if contact_js_data:
        interactive_section = f"""
        <section>
            <div class="section-header">
                <div class="section-icon blue"><i class="fas fa-sliders-h"></i></div>
                <h2>Explore Your Data</h2>
            </div>
            {create_interactive_controls_html(contact_names, years_list)}
        </section>
        """
        sections.append(interactive_section)

    # Generate interactive JavaScript
    interactive_js = create_interactive_js(contact_js_data) if contact_js_data else ""

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
        interactive_js=interactive_js,
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
