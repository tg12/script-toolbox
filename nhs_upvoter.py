
""" 
Streams comments from specified subreddits on Reddit using the Python Reddit API Wrapper (PRAW).

Analyzes the sentiment of each comment using the VADER sentiment analysis tool.

Upvotes comments with a positive sentiment.

Prints a message for each upvoted comment and each comment that was not upvoted.

Uses a regular expression pattern to match keywords in comments. 

"""

import datetime
import re

import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def analyze_and_upvote(post):
    # Set up the sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()

    # Analyze the sentiment of the comment
    sentiment = analyzer.polarity_scores(post.body)

    # Check if the post is positive (i.e., has a high compound score)
    if sentiment["compound"] > 0.5:
        post.upvote()
        # Print upvoted post plus a timestamp
        print(f"[+]Upvoted post at {datetime.datetime.now()}")
    else:
        print(f"[-]Post not upvoted: {post.title}")


# Create a Reddit instance
reddit = praw.Reddit(
    client_id="",
    client_secret="",
    password="",
    user_agent="",
    username="",
)

# Define the subreddits to stream from
subreddits = ["ukpolitics", "LabourUK", "unitedkingdom", "GreenAndPleasant"]

# Compile a regular expression pattern to match keywords
keyword_pattern = re.compile(
    r"\b(NHS|National Health Service|NHSUK)\b",
    re.IGNORECASE,
)

# Stream posts from the specified subreddits
for subreddit in subreddits:
    subreddit = reddit.subreddit(subreddit)
    for comment in subreddit.stream.comments(skip_existing=True):
        # Check if the comment contains the keyword
        if keyword_pattern.search(comment.body):
            # Analyze the sentiment of the comment
            analyze_and_upvote(comment)
