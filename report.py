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


def embed_plotly_chart(fig, div_id, height=400):
    """Convert plotly figure to embedded HTML with iMessage styling."""
    # Update figure layout for iMessage aesthetic
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
                   top_2025=None, df_2025=None, top_by_year=None, monthly_top_2025=None):
    """Generate the complete HTML report."""
    sections = []

    # Calculate number of years
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

    # Section 4: AI Insights
    insights_html = create_insight_cards_html(insights)
    if insights_html:
        section4 = f"""
        <section>
            <div class="section-header">
                <div class="section-icon pink"><i class="fas fa-lightbulb"></i></div>
                <h2>Surprising Relationship Dynamics</h2>
            </div>
            {insights_html}
        </section>
        """
        sections.append(section4)

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
