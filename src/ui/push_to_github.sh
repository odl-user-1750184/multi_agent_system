#!/bin/bash

# Ensure the script stops if there's an error
set -e

# Stage the changes
git add index.html

# Commit with a default message
git commit -m "Auto-update: index.html pushed from multi-agent system"

# Push to the remote repository
git push https://$GITHUB_USERNAME:$GITHUB_PAT@github.com/$GITHUB_REPO_URL origin main  # change 'main' to 'master' or your branch name if needed
