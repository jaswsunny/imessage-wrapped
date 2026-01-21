"""Content and language analysis."""
import pandas as pd
import numpy as np
import re
from collections import Counter
import emoji
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import NMF
from config import BORING_PHRASES, BORING_WORDS

sia = SentimentIntensityAnalyzer()

def extract_emojis(text):
    """Extract all emojis from text."""
    if not text:
        return []
    return [c for c in text if c in emoji.EMOJI_DATA]

def get_top_emojis_by_year(df):
    """Get top emojis for each year."""
    df = df.copy()
    df['emojis'] = df['text'].apply(extract_emojis)

    emoji_df = df[['year', 'emojis']].explode('emojis')
    emoji_df = emoji_df[emoji_df['emojis'].notna()]

    counts = emoji_df.groupby(['year', 'emojis']).size().reset_index(name='count')
    counts['rank'] = counts.groupby('year')['count'].rank(ascending=False, method='min')

    top_per_year = counts[counts['rank'] <= 10].sort_values(['year', 'rank'])

    return top_per_year

def get_emoji_by_contact(df, top_n=10):
    """Get most used emojis per contact."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['emojis'] = sent['text'].apply(extract_emojis)

    emoji_df = sent[['contact_name', 'emojis']].explode('emojis')
    emoji_df = emoji_df[emoji_df['emojis'].notna()]

    counts = emoji_df.groupby(['contact_name', 'emojis']).size().reset_index(name='count')
    counts['rank'] = counts.groupby('contact_name')['count'].rank(ascending=False, method='min')

    top_per_contact = counts[counts['rank'] <= 5].sort_values(['contact_name', 'rank'])

    return top_per_contact

def is_question(text):
    """Check if text is a question."""
    if not text:
        return False
    return '?' in text

def get_question_ratio_by_year(df):
    """Get ratio of questions per year."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['is_question'] = sent['text'].apply(is_question)

    yearly = sent.groupby('year').agg(
        total=('message_id', 'count'),
        questions=('is_question', 'sum'),
    ).reset_index()

    yearly['question_pct'] = yearly['questions'] / yearly['total'] * 100

    return yearly

def get_question_ratio_by_contact(df, min_messages=50):
    """Get ratio of questions per contact."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['is_question'] = sent['text'].apply(is_question)

    by_contact = sent.groupby('contact_name').agg(
        total=('message_id', 'count'),
        questions=('is_question', 'sum'),
    ).reset_index()

    by_contact = by_contact[by_contact['total'] >= min_messages]
    by_contact['question_pct'] = by_contact['questions'] / by_contact['total'] * 100

    return by_contact.sort_values('question_pct', ascending=False)

def calculate_sentiment(text):
    """Calculate VADER sentiment score."""
    if not text:
        return {'compound': 0, 'pos': 0, 'neu': 0, 'neg': 0}
    try:
        return sia.polarity_scores(text)
    except:
        return {'compound': 0, 'pos': 0, 'neu': 0, 'neg': 0}

def get_sentiment_by_contact(df, min_messages=50):
    """Get average sentiment scores per contact."""
    df = df.copy()

    sentiments = df['text'].apply(calculate_sentiment)
    df['sentiment_compound'] = sentiments.apply(lambda x: x['compound'])
    df['sentiment_pos'] = sentiments.apply(lambda x: x['pos'])
    df['sentiment_neg'] = sentiments.apply(lambda x: x['neg'])

    by_contact = df.groupby('contact_name').agg(
        total_messages=('message_id', 'count'),
        avg_sentiment=('sentiment_compound', 'mean'),
        avg_positive=('sentiment_pos', 'mean'),
        avg_negative=('sentiment_neg', 'mean'),
    ).reset_index()

    by_contact = by_contact[by_contact['total_messages'] >= min_messages]

    return by_contact.sort_values('avg_sentiment', ascending=False)

def clean_text_for_phrases(text):
    """Clean text for phrase extraction, preserving contractions."""
    if not text:
        return ""
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    # Convert contractions to expanded form for better analysis
    contractions = {
        "don't": "dont", "didn't": "didnt", "doesn't": "doesnt",
        "won't": "wont", "wouldn't": "wouldnt", "couldn't": "couldnt",
        "shouldn't": "shouldnt", "can't": "cant", "haven't": "havent",
        "hasn't": "hasnt", "hadn't": "hadnt", "isn't": "isnt",
        "aren't": "arent", "wasn't": "wasnt", "weren't": "werent",
        "i'm": "im", "i've": "ive", "i'll": "ill", "i'd": "id",
        "you're": "youre", "you've": "youve", "you'll": "youll", "you'd": "youd",
        "he's": "hes", "she's": "shes", "it's": "its",
        "we're": "were", "we've": "weve", "we'll": "well", "we'd": "wed",
        "they're": "theyre", "they've": "theyve", "they'll": "theyll", "they'd": "theyd",
        "that's": "thats", "there's": "theres", "here's": "heres",
        "what's": "whats", "who's": "whos", "let's": "lets",
    }
    for contraction, expanded in contractions.items():
        text = text.replace(contraction, expanded)
    # Remove remaining punctuation except spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def is_substring_of_existing(phrase, existing_phrases):
    """Check if phrase is a substring of any existing phrase or vice versa."""
    for existing in existing_phrases:
        if phrase in existing or existing in phrase:
            return True
    return False

def get_top_phrases_by_year(df, n_phrases=20):
    """Get top phrases for each year, excluding boring ones and deduplicating."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    results = []

    for year in sorted(sent['year'].unique()):
        year_texts = sent[sent['year'] == year]['clean_text'].tolist()

        # Require 3-5 word phrases
        vectorizer = CountVectorizer(ngram_range=(3, 5), min_df=3, max_df=0.5)
        try:
            X = vectorizer.fit_transform(year_texts)
            phrases = vectorizer.get_feature_names_out()
            counts = X.sum(axis=0).A1

            phrase_counts = list(zip(phrases, counts))
            phrase_counts.sort(key=lambda x: x[1], reverse=True)

            filtered = []
            filtered_phrases = []  # Track phrases for deduplication
            for phrase, count in phrase_counts:
                is_boring = False

                # Check if phrase contains boring phrase
                for boring in BORING_PHRASES:
                    if boring in phrase or phrase in boring:
                        is_boring = True
                        break

                words = phrase.split()

                # Skip if ALL words are boring
                if all(w in BORING_WORDS for w in words):
                    is_boring = True

                # Also skip if fewer than 2 non-boring words
                non_boring_count = sum(1 for w in words if w not in BORING_WORDS)
                if non_boring_count < 2:
                    is_boring = True

                # Skip if this phrase is a substring of existing or vice versa
                if is_substring_of_existing(phrase, filtered_phrases):
                    is_boring = True

                if not is_boring:
                    filtered.append({'year': year, 'phrase': phrase, 'count': int(count)})
                    filtered_phrases.append(phrase)

                if len(filtered) >= n_phrases:
                    break

            results.extend(filtered)
        except:
            continue

    return pd.DataFrame(results)

def get_unique_words_by_year(df, n_words=10):
    """Find words that spiked in specific years using TF-IDF."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    yearly_texts = sent.groupby('year')['clean_text'].apply(' '.join).reset_index()

    vectorizer = TfidfVectorizer(min_df=1, stop_words='english', max_features=5000)
    X = vectorizer.fit_transform(yearly_texts['clean_text'])
    features = vectorizer.get_feature_names_out()

    results = []
    for idx, year in enumerate(yearly_texts['year']):
        scores = X[idx].toarray().flatten()
        top_indices = scores.argsort()[-n_words*3:][::-1]

        count = 0
        for i in top_indices:
            word = features[i]
            if word not in BORING_WORDS and len(word) > 2:
                results.append({
                    'year': year,
                    'word': word,
                    'tfidf_score': float(scores[i])
                })
                count += 1
                if count >= n_words:
                    break

    return pd.DataFrame(results)

def normalize_word(word):
    """Normalize word for deduplication (handle singular/plural)."""
    word = word.lower().strip()
    # Simple plural handling
    if word.endswith('ies'):
        return word[:-3] + 'y'  # companies -> company
    if word.endswith('es') and len(word) > 3:
        return word[:-2]  # boxes -> box
    if word.endswith('s') and not word.endswith('ss') and len(word) > 2:
        return word[:-1]  # friends -> friend
    return word

def is_duplicate_word(word, existing_words):
    """Check if word is a duplicate (including singular/plural variants)."""
    norm_word = normalize_word(word)
    for existing in existing_words:
        norm_existing = normalize_word(existing)
        if norm_word == norm_existing:
            return True
        # Also check if one contains the other
        if norm_word in norm_existing or norm_existing in norm_word:
            return True
    return False

def get_topics_by_year(df, n_topics=5, n_top_words=8):
    """Extract topics per year using NMF, focusing on meaningful nouns/topics."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    results = []

    for year in sorted(sent['year'].unique()):
        year_texts = sent[sent['year'] == year]['clean_text'].tolist()

        if len(year_texts) < 100:
            continue

        try:
            # Use both unigrams and bigrams to capture compound topics like "machine learning"
            vectorizer = TfidfVectorizer(
                max_features=2000,
                min_df=5,
                max_df=0.7,
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams for compound terms
            )
            X = vectorizer.fit_transform(year_texts)
            features = vectorizer.get_feature_names_out()

            nmf = NMF(n_components=min(n_topics, len(year_texts)//20), random_state=42, max_iter=200)
            nmf.fit(X)

            for topic_idx, topic in enumerate(nmf.components_):
                top_word_indices = topic.argsort()[-n_top_words*3:][::-1]

                # Filter to meaningful words, deduplicating singular/plural
                top_words = []
                for i in top_word_indices:
                    word = features[i]
                    # Skip if single word and in boring words
                    if ' ' not in word and word in BORING_WORDS:
                        continue
                    # Skip if bigram and both words are boring
                    if ' ' in word:
                        parts = word.split()
                        if all(p in BORING_WORDS for p in parts):
                            continue
                    # Skip very short words
                    if len(word.replace(' ', '')) < 3:
                        continue
                    # Skip duplicates (singular/plural)
                    if is_duplicate_word(word, top_words):
                        continue
                    top_words.append(word)
                    if len(top_words) >= 5:
                        break

                if top_words:
                    results.append({
                        'year': year,
                        'topic_id': topic_idx,
                        'top_words': ', '.join(top_words),
                    })
        except Exception as e:
            print(f"Topic modeling failed for {year}: {e}")
            continue

    return pd.DataFrame(results)

def get_topics_by_contact(df, contacts=None, n_topics=3, n_top_words=5):
    """Extract topics per contact, focusing on meaningful nouns/topics."""
    sent = df[df['is_from_me'] == 1].copy()
    sent['clean_text'] = sent['text'].apply(clean_text_for_phrases)

    if contacts is None:
        top = sent.groupby('contact_name').size().sort_values(ascending=False).head(10)
        contacts = top.index.tolist()

    results = []

    for contact in contacts:
        contact_texts = sent[sent['contact_name'] == contact]['clean_text'].tolist()

        if len(contact_texts) < 50:
            continue

        try:
            vectorizer = TfidfVectorizer(
                max_features=500,
                min_df=3,
                max_df=0.8,
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams
            )
            X = vectorizer.fit_transform(contact_texts)
            features = vectorizer.get_feature_names_out()

            nmf = NMF(n_components=min(n_topics, len(contact_texts)//20), random_state=42, max_iter=200)
            nmf.fit(X)

            for topic_idx, topic in enumerate(nmf.components_):
                top_word_indices = topic.argsort()[-n_top_words*3:][::-1]

                # Filter to meaningful words
                top_words = []
                for i in top_word_indices:
                    word = features[i]
                    if ' ' not in word and word in BORING_WORDS:
                        continue
                    if ' ' in word:
                        parts = word.split()
                        if all(p in BORING_WORDS for p in parts):
                            continue
                    if len(word.replace(' ', '')) < 3:
                        continue
                    top_words.append(word)
                    if len(top_words) >= n_top_words:
                        break

                if top_words:
                    results.append({
                        'contact_name': contact,
                        'topic_id': topic_idx,
                        'top_words': ', '.join(top_words),
                    })
        except:
            continue

    return pd.DataFrame(results)

def add_sentiment_to_df(df):
    """Add sentiment scores to dataframe."""
    sentiments = df['text'].apply(calculate_sentiment)
    df = df.copy()
    df['sentiment_compound'] = sentiments.apply(lambda x: x['compound'])
    df['sentiment_pos'] = sentiments.apply(lambda x: x['pos'])
    df['sentiment_neg'] = sentiments.apply(lambda x: x['neg'])
    return df

if __name__ == "__main__":
    from extract import extract_messages
    from contacts import get_contacts_from_macos, create_contact_mappings

    df = extract_messages()
    contacts_map = get_contacts_from_macos()
    mappings = create_contact_mappings(df, contacts_map)
    df['contact_name'] = df['contact_id'].astype(str).map(mappings)

    print("\n=== TOP EMOJIS BY YEAR ===")
    print(get_top_emojis_by_year(df).head(20))

    print("\n=== SENTIMENT BY CONTACT ===")
    print(get_sentiment_by_contact(df).head(10))
