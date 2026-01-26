"""Configuration for iMessage Wrapped analysis."""
from pathlib import Path

# Paths
CHAT_DB_PATH = Path.home() / "Library/Messages/chat.db"
OUTPUT_DIR = Path(__file__).parent / "output"
DATA_DIR = OUTPUT_DIR / "data"

# Date range
START_YEAR = 2017
END_YEAR = 2026

# Analysis thresholds
MIN_MESSAGES_FOR_TOP_CONTACT = 10
CONVERSATION_GAP_HOURS = 4  # Hours of silence before new conversation
TOP_CONTACTS_COUNT = 15

# Filter out these contacts (self, notifications, businesses, etc.)
# Add your own name and any spam/business numbers
EXCLUDED_CONTACTS = {
    # "Your Name",  # Uncomment and add your name
    # "12345",  # Example: short codes for 2FA
}

# Minimum messages for sentiment analysis
MIN_MESSAGES_FOR_SENTIMENT = 20

# Minimum ratio of two-way messages to be included (filters out notification-only contacts)
# If you sent 0 messages to them, or they sent 0 to you, exclude them
MIN_TWO_WAY_RATIO = 0.05  # At least 5% of messages must be in each direction

# Boring phrases to exclude from phrase analysis
BORING_PHRASES = {
    # Greetings and closings
    "sounds good", "on my way", "be there", "see you", "got it",
    "ok", "okay", "yeah", "yep", "yea", "ya", "haha", "hahaha", "lol",
    "omg", "idk", "i know", "i think", "thank you", "thanks", "no problem",
    "good morning", "good night", "have a good", "talk to you",
    "let me know", "i will", "i can", "i don't", "do you", "are you",
    "what time", "how are", "i'm good", "that's good", "sounds great",
    "see you soon", "on the way", "almost there", "be right there",
    "i'm here", "where are", "what's up", "not much", "same here",
    # Filler phrases
    "i feel like", "trying to", "going to", "want to", "need to",
    "have to", "about it", "about that", "it was", "it is", "that is",
    "that was", "this is", "i was", "i am", "kind of", "sort of",
    "a lot", "a bit", "so much", "too much", "right now", "at least",
    "i mean", "you know", "i guess", "i just", "just like", "like that",
    "like this", "for the", "in the", "on the", "to the", "at the",
    "and the", "but the", "with the", "from the", "of the", "is the",
    "was the", "be like", "would be", "could be", "should be", "might be",
    "dont know", "didnt know", "im not", "im gonna", "im going",
    "thats so", "its so", "so good", "so bad", "so much", "so many",
    "to talk about", "talk about it", "think about it", "about this",
    "both of us", "one of us", "all of us", "any of us",
    "accept the invite", "gmail com", "yahoo com", "hotmail com",
}

# Boring single words to exclude
BORING_WORDS = {
    # Articles, prepositions, conjunctions
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "just", "i", "me",
    "my", "myself", "we", "our", "you", "your", "he", "him", "his", "she",
    "her", "it", "its", "they", "them", "their", "what", "which", "who",
    "this", "that", "these", "those", "am", "but", "if", "or", "because",
    "and", "up", "down", "out", "off", "over", "now", "get", "got", "like",
    # Common verbs
    "going", "go", "come", "back", "want", "know", "think", "see", "look",
    "make", "take", "give", "well", "also", "way", "even", "new", "any",
    "say", "said", "one", "two", "first", "last", "long", "great", "little",
    "right", "still", "find", "tell", "ask", "work", "seem", "feel",
    "try", "leave", "call", "keep", "let", "begin", "show", "hear",
    "play", "run", "move", "live", "believe", "bring", "happen", "write",
    "provide", "sit", "stand", "lose", "pay", "meet", "include", "continue",
    "set", "learn", "change", "lead", "understand", "watch", "follow",
    "stop", "create", "speak", "read", "allow", "add", "spend", "grow",
    "open", "walk", "win", "offer", "remember", "love", "consider", "appear",
    "buy", "wait", "serve", "die", "send", "expect", "build", "stay",
    "fall", "cut", "reach", "kill", "remain",
    # Casual/filler words and text speak
    "yeah", "yes", "no", "oh", "ok", "okay", "um", "uh", "ah", "haha", "lol",
    "gonna", "wanna", "gotta", "kinda", "sorta", "maybe", "probably",
    "really", "actually", "basically", "literally", "definitely", "absolutely",
    "totally", "completely", "exactly", "simply", "highly", "likely", "certainly",
    "usually", "always", "never", "sometimes", "often", "already",
    "honestly", "tbh", "idk", "bc", "tho", "rn", "omg", "lmao", "lmfao",
    "smh", "ngl", "imo", "imho", "btw", "fyi", "jk", "irl", "asap",
    "dont", "didnt", "cant", "couldnt", "wont", "wouldnt", "shouldnt",
    "don", "didn", "doesn", "hasn", "hadn", "isn", "aren", "wasn", "weren",
    "won", "wouldn", "couldn", "shouldn", "ll", "ve", "re", "em",
    "im", "ive", "youre", "youve", "hes", "shes", "theyre", "theyve",
    "thats", "whats", "hows", "whos", "wheres", "itll", "theyll", "youll",
    "feels", "sounds", "looks", "seems", "means", "goes", "comes", "gets",
    "makes", "takes", "gives", "puts", "says", "tells", "asks", "thinks",
    "knows", "wants", "needs", "tries", "starts", "keeps", "helps", "works",
    # More filler and casual expressions
    "ppl", "rly", "prob", "def", "obv", "sry", "thx", "plz", "pls", "ur",
    "cuz", "cus", "cos", "tht", "wht", "abt", "diff", "oops", "yay", "ooh",
    "ugh", "hmm", "hm", "mhm", "aww", "wow", "yikes", "damn", "dang", "gosh",
    "shit", "fuck", "crap", "hell", "god", "omfg", "wtf", "lmk", "hbu",
    "wbu", "gtg", "brb", "ttyl", "ily", "luv", "bday", "rip",
    "sorry", "thanks", "thank", "please", "hello", "hey", "hi", "bye",
    "sup", "yo", "dude", "bro", "sis", "fam", "babe", "hun",
    "cute", "nice", "cool", "awesome", "amazing", "sweet", "sick", "dope",
    "crazy", "insane", "wild", "weird", "random", "funny", "hilarious",
    "sad", "mad", "happy", "excited", "nervous", "scared", "tired", "bored",
    "busy", "free", "late", "early", "soon", "quick", "fast", "slow",
    "hard", "easy", "tough", "rough", "bad", "worse", "worst", "better", "best",
    "fun", "fair", "true", "false", "wrong", "guess", "bet", "hope",
    "loved", "liked", "hated", "forgot", "remembered", "realized", "noticed",
    "thought", "thinking", "feeling", "doing", "going", "coming", "getting",
    "trying", "talking", "saying", "asking", "telling", "looking", "seeing",
    "waiting", "checking", "working", "sleeping", "eating", "drinking",
    "half", "whole", "full", "empty", "couple", "few", "several",
    "just", "also", "even", "still", "already", "finally", "actually",
    "apparently", "obviously", "clearly", "basically", "essentially",
    "worries", "worry", "worried", "matters", "matter", "mattered",
    # Generic nouns
    "today", "tomorrow", "yesterday", "tonight", "morning", "night",
    "day", "week", "month", "year", "time", "thing", "things", "stuff",
    "lot", "bit", "much", "many", "people", "person", "man", "woman",
    "child", "world", "life", "hand", "part", "place", "case", "point",
    "government", "company", "number", "group", "problem", "fact",
    "something", "anything", "nothing", "everything", "someone", "anyone",
    "everyone", "way", "kind", "sort", "type", "sense", "idea", "reason",
    "good", "bad", "nice", "cool", "great", "fine", "sure", "real",
}

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
