# Description: Simple script to detect spam comments on Reddit
# Author: James Sawyer
# Email: githubtools@jamessawyer.co.uk
# Website: http://www.jamessawyer.co.uk/

""" Use of this tool is at your own risk.
I are not responsible for any damage or data loss that may result from using this tool.
Please make sure to backup your router settings before using this tool.  """


import datetime

import pandas as pd
import praw

# Create a Reddit instance
reddit = praw.Reddit(
    client_id="",
    client_secret="",
    password="",
    user_agent="",
    username=""
)

spam_df = pd.DataFrame(columns=["author", "comment_body", "subreddit"])

# Set the maximum number of comments to check
max_comments = 10000
SPAM_THRESHOLD = 3

# Create a dataframe to store the comments
df = pd.DataFrame(columns=["comment_id", "comment_hash"])

# Start streaming comments from the API
for comment in reddit.subreddit("all").stream.comments():
    # Check if the maximum number of comments has been reached and start again

    if len(df) >= max_comments:
        df = pd.DataFrame(columns=["comment_id", "comment_hash"])
        print("[-] Resetting Dataframe")

    # Hash the comment text and add it to the dataframe
    comment_hash = hash(comment.body)

    # Print a debug with the comment hash include a timestamp

    # print(
    #     f"[+] Comment Hash: {comment_hash} at {datetime.datetime.now()}"
    # )

    df = pd.concat([df,
                    pd.DataFrame({"comment_id": comment.id,
                                  "comment_hash": comment_hash},
                                 index=[0])],
                   ignore_index=True)

    # Check if the comment hash has been seen more than x times
    if df["comment_hash"].value_counts()[comment_hash] > SPAM_THRESHOLD:
        # Print the potential spam comment
        # print(f"Comment by {comment.author}: {comment.body}")
        # print(f"Comment on {comment.subreddit}")
        # print("-------------------------------------------------")
        # add the author, comment body and and subreddit to the spam dataframe
        spam_df = pd.concat([spam_df,
                             pd.DataFrame({"author": comment.author,
                                           "comment_body": comment.body,
                                           "subreddit": comment.subreddit},
                                          index=[0])],
                            ignore_index=True)
        # using tabulate to print the dataframe
        from tabulate import tabulate
        print(tabulate(spam_df, headers="keys", tablefmt="psql"))