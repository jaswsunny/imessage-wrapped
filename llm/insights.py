"""LLM-powered insights using Claude Code CLI."""
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import tiktoken

from config import DATA_DIR


def is_noise(text):
    """Filter tapbacks, reactions, empty messages."""
    if not text:
        return True
    text = text.strip()
    if re.match(r'^\+[A-Z]?$', text):
        return True
    if text.startswith(('Loved "', 'Laughed at', 'Emphasized', 'Disliked', 'Liked "')):
        return True
    if re.match(r'^￼+$', text):
        return True
    return False


def extract_substantive_messages(df, top_contacts, target_tokens=100000):
    """
    Extract longest messages across top contacts, targeting ~target_tokens.
    Uses binary search to find the right character length threshold.
    Returns formatted string with [N skipped] annotations.
    """
    enc = tiktoken.get_encoding("cl100k_base")

    # Collect all clean messages from top contacts
    all_rows = []
    for contact in top_contacts:
        contact_df = df[df['contact_name'] == contact].sort_values('datetime')
        for _, row in contact_df.iterrows():
            if not is_noise(row['text']):
                all_rows.append({
                    'contact': contact,
                    'is_from_me': row['is_from_me'],
                    'text': row['text'] or '',
                    'datetime': row['datetime'],
                    'length': len(row['text'] or '')
                })

    if not all_rows:
        return ""

    lengths = sorted([r['length'] for r in all_rows])

    def build_output(min_length):
        """Build formatted output for messages >= min_length."""
        lines = []
        for contact in top_contacts:
            contact_msgs = sorted(
                [r for r in all_rows if r['contact'] == contact and r['length'] >= min_length],
                key=lambda x: x['datetime']
            )
            if not contact_msgs:
                continue

            lines.append(f"\n## Conversation with {contact}")

            # Get all messages for this contact to count skips
            all_contact_msgs = sorted(
                [r for r in all_rows if r['contact'] == contact],
                key=lambda x: x['datetime']
            )

            skip_count = 0
            kept_indices = set(
                i for i, r in enumerate(all_contact_msgs) if r['length'] >= min_length
            )

            for i, msg in enumerate(all_contact_msgs):
                if i in kept_indices:
                    if skip_count > 0:
                        lines.append(f"[{skip_count} messages skipped]")
                        skip_count = 0
                    sender = "You" if msg['is_from_me'] else contact
                    date_str = msg['datetime'].strftime('%Y-%m-%d')
                    lines.append(f"[{date_str}] {sender}: {msg['text'].replace('￼', '[img]')}")
                else:
                    skip_count += 1

            if skip_count > 0:
                lines.append(f"[{skip_count} messages skipped]")

        return "\n".join(lines)

    def calc_tokens(min_length):
        return len(enc.encode(build_output(min_length)))

    # Binary search for threshold
    tolerance = 0.05
    lo, hi = min(lengths), max(lengths)

    while lo < hi:
        mid = (lo + hi) // 2
        tokens = calc_tokens(mid)

        if tokens > target_tokens * (1 + tolerance):
            lo = mid + 1
        elif tokens < target_tokens * (1 - tolerance):
            hi = mid - 1
        else:
            break

    return build_output(mid)


def build_llm_context(
    total_messages,
    total_contacts,
    years_span,
    health_data,
    top_contacts,
    yearly_volume,
    message_content,
):
    """Build context string with stats + messages for LLM prompt."""
    lines = []

    # Stats section
    lines.append("# iMessage Data Context")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- Total messages: {total_messages:,}")
    lines.append(f"- Unique contacts: {total_contacts}")
    lines.append(f"- Years analyzed: {years_span}")

    # Top contacts
    if top_contacts:
        lines.append("")
        lines.append("## Top Contacts")
        for i, c in enumerate(top_contacts[:10], 1):
            name = c.get('contact_name', 'Unknown')
            total = c.get('total_messages', 0)
            sent = c.get('sent', 0)
            received = c.get('received', 0)
            lines.append(f"{i}. {name}: {total:,} messages (sent {sent:,}, received {received:,})")

    # Health summary
    if health_data:
        summary = health_data.get('summary', {})
        if summary:
            lines.append("")
            lines.append("## Relationship Health")
            lines.append(f"- Average score: {summary.get('average_health_score', 0)}/100")
            lines.append(f"- Healthy (60+): {summary.get('healthy_relationships', 0)}")
            lines.append(f"- At-risk (<40): {summary.get('at_risk_relationships', 0)}")

        fading = health_data.get('fading_friendships', [])
        if fading:
            lines.append("")
            lines.append("## Fading Relationships")
            for f in fading[:5]:
                lines.append(f"- {f['contact_name']}: was ~{f['baseline_rate']:.0f}/wk, now ~{f['recent_rate']:.0f}/wk")

        emerging = health_data.get('emerging_connections', [])
        if emerging:
            lines.append("")
            lines.append("## Emerging Connections")
            for e in emerging[:5]:
                lines.append(f"- {e['contact_name']}: {e['growth']}")

    # Yearly volume
    if yearly_volume:
        lines.append("")
        lines.append("## Yearly Volume")
        for y in yearly_volume[-5:]:
            lines.append(f"- {y.get('year')}: {y.get('total', 0):,} messages")

    # Message content
    lines.append("")
    lines.append("# Substantive Messages")
    lines.append("(Longest messages from top relationships, with skipped message counts)")
    lines.append(message_content)

    return '\n'.join(lines)


class LLMInsights:
    """Generate AI-powered narrative insights from messaging data."""

    def __init__(self):
        """Initialize LLM insights generator."""
        self.cache_path = DATA_DIR / 'llm_insights.json'
        self._cache = self._load_cache()
        self._cli_available = shutil.which('claude') is not None
        if not self._cli_available:
            print("Warning: Claude Code CLI not found. LLM features disabled.")
            print("Install from: https://claude.ai/cli")

    @property
    def is_available(self) -> bool:
        """Check if LLM features are available."""
        return self._cli_available

    def _load_cache(self) -> dict:
        """Load cached insights from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self):
        """Save insights cache to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(self._cache, f, indent=2)

    def _generate(self, prompt: str, cache_key: str) -> Optional[str]:
        """
        Generate text using Claude Code CLI with caching.

        Args:
            prompt: The full prompt to send
            cache_key: Key for caching results

        Returns:
            Generated text or None if unavailable
        """
        if not self.is_available:
            return None

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = subprocess.run(
                ['claude', '-p', prompt, '--model', 'opus'],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                response = result.stdout.strip()
                self._cache[cache_key] = response
                self._save_cache()
                return response
            else:
                print(f"Claude CLI error (code {result.returncode}): {result.stderr}")
                # Sometimes CLI returns non-zero but still has output
                if result.stdout.strip():
                    print(f"  But got output, using it anyway...")
                    response = result.stdout.strip()
                    self._cache[cache_key] = response
                    self._save_cache()
                    return response
                return None
        except Exception as e:
            print(f"LLM generation error: {e}")
            return None

    def generate_wrapped_reflection(self, context: str) -> Optional[str]:
        """Generate a narrative reflection on messaging history."""
        prompt = f"""Here is my iMessage data - stats and my most substantive messages (longest messages from top relationships):

{context}

Write a heartfelt 2-3 paragraph reflection on my iMessage history across the years. Be specific - reference actual conversations, names, and patterns you see. Don't be generic. No markdown formatting, just raw text."""

        cache_key = "wrapped_reflection"
        return self._generate(prompt, cache_key)

    def generate_psychological_profile(self, context: str) -> Optional[str]:
        """Generate a communication style profile."""
        prompt = f"""Here is my iMessage data - stats and my most substantive messages (longest messages from top relationships):

{context}

Write an in-depth, carefully considered 2-3 paragraph communication style profile about me. What patterns do you notice? Be specific to what you see in the messages. No markdown formatting, just raw text."""

        cache_key = "psychological_profile"
        return self._generate(prompt, cache_key)

    def clear_cache(self):
        """Clear all cached insights."""
        self._cache = {}
        if self.cache_path.exists():
            self.cache_path.unlink()


def generate_llm_insights(
    df,
    total_messages: int,
    total_contacts: int,
    years_span: int,
    health_data: dict = None,
    top_contacts: list = None,
    yearly_volume: list = None,
    message_samples: dict = None,
) -> dict:
    """
    Generate all LLM-powered insights.

    Returns dict with narrative sections, or empty dict if LLM unavailable.
    """
    llm = LLMInsights()

    if not llm.is_available:
        print("  - LLM features disabled (Claude Code CLI not found)")
        return {}

    print("  - Extracting substantive messages...")

    # Get top contact names
    top_contact_names = [c.get('contact_name') for c in (top_contacts or [])[:15]]

    # Extract substantive messages (~100k tokens)
    message_content = extract_substantive_messages(df, top_contact_names, target_tokens=100000)

    print("  - Building context...")

    # Build context string
    context = build_llm_context(
        total_messages=total_messages,
        total_contacts=total_contacts,
        years_span=years_span,
        health_data=health_data,
        top_contacts=top_contacts,
        yearly_volume=yearly_volume,
        message_content=message_content,
    )

    enc = tiktoken.get_encoding("cl100k_base")
    token_count = len(enc.encode(context))
    print(f"  - Context size: {token_count:,} tokens")

    # Write debug context for quality review
    debug_path = DATA_DIR / 'debug_llm_context.txt'
    with open(debug_path, 'w') as f:
        f.write(context)
    print(f"  - Debug context written to {debug_path}")

    narratives = {}

    print("  - Generating wrapped reflection...")
    narratives['wrapped_reflection'] = llm.generate_wrapped_reflection(context)

    print("  - Generating psychological profile...")
    narratives['psychological_profile'] = llm.generate_psychological_profile(context)

    # Filter out None values
    narratives = {k: v for k, v in narratives.items() if v is not None}

    return narratives
