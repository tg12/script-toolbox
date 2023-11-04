#!/bin/bash

# Check if the current directory is a git repository
if [ ! -d ".git" ]; then
  echo "Error: Current directory is not a git repository."
  exit 1
fi

# Verify that the script is being run intentionally
read -p "This will DESTROY your git history and cannot be undone. Are you sure? (y/n) " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
  # Fetch the name of the current branch
  current_branch=$(git rev-parse --abbrev-ref HEAD)
  if [ -z "$current_branch" ]; then
    echo "Error: Failed to determine the current branch."
    exit 1
  fi

  # Create a fresh temporary branch
  git checkout --orphan temp_branch

  # Add all the files
  git add -A

  # Commit the changes
  git commit -am "Initial commit"

  # Delete the old branch
  git branch -D "$current_branch"

  # Rename the temporary branch to the original branch name
  git branch -m "$current_branch"

  # Force update the repository to overwrite the history
  git push -f origin "$current_branch"

  # Optionally, prune the reflog and run garbage collection to free up space
  git reflog expire --expire=now --all
  git gc --prune=now

  echo "Git history has been successfully removed."
else
  echo "Script aborted."
fi
