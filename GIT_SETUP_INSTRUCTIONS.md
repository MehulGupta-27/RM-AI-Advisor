# Git Setup Instructions - Fix for Push Error

## The Problem
You're on the `master` branch locally, but trying to push to `main` branch on GitHub.

## Solution: Rename master to main

Run these commands in order:

```bash
# 1. Make sure .gitignore changes are committed
git add .gitignore
git commit -m "Update .gitignore with better exclusions"

# 2. Rename your local branch from master to main
git branch -M main

# 3. Push to GitHub (first time with -u to set upstream)
git push -u origin main

# 4. Verify the push worked
git status
```

## What Each Command Does

- `git branch -M main` - Renames your current branch (master) to main
- `git push -u origin main` - Pushes the main branch and sets it as the upstream
- `-u` flag creates the tracking relationship between local and remote

## After First Push

For subsequent pushes, you only need:
```bash
git add .
git commit -m "Your commit message"
git push
```

## Check What Will Be Committed

Before committing, check what files will be included:
```bash
git status
git diff
```

## Important Files That Should NOT Be Committed

The `.gitignore` file prevents these from being committed:
- ✅ `.env` files (contains API keys)
- ✅ `__pycache__/` folders
- ✅ `node_modules/`
- ✅ `test_*.py` files
- ✅ Virtual environment (`venv/`)
- ✅ Build artifacts

## Verify .env Is Not Committed

**CRITICAL**: Make sure your `.env` files with API keys are not in Git:
```bash
git ls-files | grep .env
```

If this returns anything, you need to remove them:
```bash
git rm --cached backend/.env
git rm --cached frontend/.env
git commit -m "Remove .env files from Git"
```

## Current Repository State

- Local branch: `master` → will become `main`
- Remote: `origin` → https://github.com/MehulGupta-27/RM-AI-Advisor.git
- Commits: ✅ Has initial commit
- Changes: `.gitignore` updated (needs commit)

## Quick Reference

```bash
# See what branch you're on
git branch

# See remote URL
git remote -v

# See what's staged for commit
git status

# See what changed
git diff

# Add all changes
git add .

# Commit with message
git commit -m "Your message"

# Push to GitHub
git push
```
