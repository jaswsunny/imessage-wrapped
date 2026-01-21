"""Generate Plotly visualizations for the report."""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

COLORS = px.colors.qualitative.Set2
BG_COLOR = '#1a1a2e'
PAPER_COLOR = '#16213e'
TEXT_COLOR = '#eaeaea'
GRID_COLOR = '#2d3a4f'

def style_fig(fig):
    """Apply consistent dark theme styling."""
    fig.update_layout(
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR, family='Inter, sans-serif'),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    return fig

def create_bump_chart(rankings_df, title="Contact Rankings Over Time"):
    """Create bump chart showing ranking changes over years."""
    fig = go.Figure()

    contacts = rankings_df['contact_name'].unique().tolist()

    for i, contact in enumerate(contacts):
        contact_data = rankings_df[rankings_df['contact_name'] == contact]
        fig.add_trace(go.Scatter(
            x=contact_data['year'].tolist(),
            y=contact_data['rank'].tolist(),
            mode='lines+markers',
            name=contact,
            line=dict(width=3, color=COLORS[i % len(COLORS)]),
            marker=dict(size=10),
            hovertemplate=f'{contact}<br>Year: %{{x}}<br>Rank: %{{y}}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Rank',
        yaxis=dict(autorange='reversed', dtick=1),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    return style_fig(fig)

def create_stacked_area(monthly_df, title="Message Volume Over Time"):
    """Create stacked area chart of message volume by contact."""
    pivot = monthly_df.pivot(index='year_month', columns='contact_name', values='count').fillna(0)

    fig = go.Figure()

    # Convert index to string for proper JSON serialization
    x_values = [str(x) for x in pivot.index.tolist()]

    for i, contact in enumerate(pivot.columns):
        fig.add_trace(go.Scatter(
            x=x_values,
            y=pivot[contact].tolist(),
            mode='lines',
            name=contact,
            stackgroup='one',
            line=dict(width=0.5, color=COLORS[i % len(COLORS)]),
            fillcolor=COLORS[i % len(COLORS)],
            hovertemplate=f'{contact}<br>%{{x}}<br>Messages: %{{y}}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Messages',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    return style_fig(fig)

def create_lopsidedness_scatter(lopsidedness_df, title="Conversation Balance"):
    """Create scatter plot of lopsidedness vs total messages."""
    df = lopsidedness_df.copy()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['total'].tolist(),
        y=df['lopsidedness'].tolist(),
        mode='markers+text',
        text=df['contact_name'].tolist(),
        textposition='top center',
        textfont=dict(size=9),
        marker=dict(
            size=10,
            color=df['lopsidedness'].tolist(),
            colorscale='RdYlGn',
            cmid=1.0,
            showscale=True,
            colorbar=dict(title='Lopsidedness'),
        ),
        hovertemplate='%{text}<br>Total: %{x}<br>Lopsidedness: %{y:.2f}<extra></extra>'
    ))

    fig.add_hline(y=1.0, line_dash='dash', line_color='white', opacity=0.5,
                  annotation_text='Balanced', annotation_position='right')

    fig.update_layout(
        title=title,
        xaxis_title='Total Messages',
        yaxis_title='Lopsidedness Ratio (>1 = you send more)',
        xaxis_type='log',
        yaxis_type='log',
        showlegend=False,
    )

    return style_fig(fig)

def create_hour_day_heatmap(heatmap_df, title="When You Text"):
    """Create hour x day of week heatmap."""
    # Convert to lists for proper JSON serialization
    z_data = heatmap_df.values.tolist()
    y_labels = list(heatmap_df.index)
    x_labels = [f"{h}:00" for h in range(24)]

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        colorscale='Viridis',
        hovertemplate='%{y} at %{x}<br>Messages: %{z}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week',
        xaxis=dict(dtick=2),
    )

    return style_fig(fig)

def create_yearly_volume_bar(yearly_df, title="Messages Per Year"):
    """Create bar chart of sent vs received per year."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=yearly_df['year'].tolist(),
        y=yearly_df['sent'].tolist(),
        name='Sent',
        marker_color='#4ecdc4',
    ))

    fig.add_trace(go.Bar(
        x=yearly_df['year'].tolist(),
        y=yearly_df['received'].tolist(),
        name='Received',
        marker_color='#ff6b6b',
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Messages',
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    return style_fig(fig)

def create_peak_hours_small_multiples(hourly_by_year_df, title="Peak Hours By Year"):
    """Create small multiples showing hourly distribution per year."""
    years = sorted(hourly_by_year_df['year'].unique().tolist())
    n_years = len(years)
    cols = 3
    rows = (n_years + cols - 1) // cols

    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[str(y) for y in years],
        shared_xaxes=True,
        shared_yaxes=True,
        vertical_spacing=0.08,
        horizontal_spacing=0.05,
    )

    for i, year in enumerate(years):
        row = i // cols + 1
        col = i % cols + 1

        year_data = hourly_by_year_df[hourly_by_year_df['year'] == year]

        fig.add_trace(
            go.Bar(
                x=year_data['hour'].tolist(),
                y=year_data['count'].tolist(),
                marker_color='#4ecdc4',
                showlegend=False,
            ),
            row=row, col=col
        )

    fig.update_layout(
        title=title,
        height=200 * rows,
    )

    return style_fig(fig)

def create_sentiment_bar(sentiment_df, title="Best Vibes", top_n=15, worst=False):
    """Create horizontal bar chart of sentiment by contact."""
    if worst:
        # Get worst (lowest) sentiment contacts
        df = sentiment_df.tail(top_n).copy()
        title = "Worst Vibes" if title == "Best Vibes" else title
    else:
        # Get best (highest) sentiment contacts
        df = sentiment_df.head(top_n).copy()

    df = df.sort_values('avg_sentiment')

    sentiments = df['avg_sentiment'].tolist()
    colors = ['#ff6b6b' if x < 0 else '#4ecdc4' for x in sentiments]

    fig = go.Figure(go.Bar(
        x=sentiments,
        y=df['contact_name'].tolist(),
        orientation='h',
        marker_color=colors,
        hovertemplate='%{y}<br>Sentiment: %{x:.3f}<extra></extra>'
    ))

    fig.add_vline(x=0, line_color='white', opacity=0.5)

    fig.update_layout(
        title=title,
        xaxis_title='Average Sentiment (negative ← → positive)',
        yaxis_title='',
        height=max(400, top_n * 30),
    )

    return style_fig(fig)

def create_emoji_grid(emoji_df, title="Your Emoji Story"):
    """Create emoji grid by year."""
    years = sorted(emoji_df['year'].unique().tolist())

    fig = go.Figure()

    for i, year in enumerate(years):
        year_emojis = emoji_df[emoji_df['year'] == year].sort_values('rank').head(5)
        for j, (_, row) in enumerate(year_emojis.iterrows()):
            fig.add_annotation(
                x=j, y=len(years) - i - 1,
                text=str(row['emojis']),
                font=dict(size=24),
                showarrow=False,
            )

    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 5.5]),
        yaxis=dict(
            showgrid=False, zeroline=False,
            tickmode='array',
            tickvals=list(range(len(years))),
            ticktext=[str(y) for y in reversed(years)],
        ),
        height=50 * len(years) + 100,
    )

    return style_fig(fig)

def create_question_ratio_line(question_df, title="Questions Over Time"):
    """Create line chart of question percentage by year."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=question_df['year'].tolist(),
        y=question_df['question_pct'].tolist(),
        mode='lines+markers',
        line=dict(color='#4ecdc4', width=3, shape='spline'),
        marker=dict(size=10),
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='% of Messages That Are Questions',
    )

    return style_fig(fig)

def create_monthly_top_contacts(monthly_data, title="Top Contact Each Month (2025)"):
    """Create a bar chart showing top contact per month."""
    months = monthly_data['month_name'].tolist()
    contacts = monthly_data['contact_name'].tolist()
    counts = monthly_data['count'].tolist()

    fig = go.Figure(go.Bar(
        x=months,
        y=counts,
        text=contacts,
        textposition='inside',
        marker_color='#4ecdc4',
        hovertemplate='%{x}<br>%{text}: %{y} messages<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Month',
        yaxis_title='Messages',
    )

    return style_fig(fig)

if __name__ == "__main__":
    print("Visualization module loaded successfully")
