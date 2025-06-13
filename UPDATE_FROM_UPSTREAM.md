# Updating from Upstream Repository

This guide explains how to update your forked/cloned repository with changes from the original author while preserving your customizations.

## Initial Setup (Already Done)

```bash
# Add the original repository as 'upstream' remote
git remote add upstream https://github.com/The-Pocket/Tutorial-Codebase-Knowledge.git
```

## Regular Update Process

### 1. Save Your Current Work
```bash
# Commit any uncommitted changes
git add .
git commit -m "Save work before upstream merge"
```

### 2. Fetch Upstream Changes
```bash
# Fetch all branches from upstream
git fetch upstream

# View available branches
git branch -r
```

### 3. Merge Upstream Changes

**Option A: Merge Strategy (Recommended)**
```bash
# Merge upstream main into your main branch
git checkout main
git merge upstream/main

# Resolve any conflicts if they occur
# After resolving conflicts:
git add .
git commit -m "Merge upstream changes"
```

**Option B: Rebase Strategy (Cleaner History)**
```bash
# Rebase your changes on top of upstream
git checkout main
git rebase upstream/main

# Resolve conflicts if any, then:
git rebase --continue
```

### 4. Handle Conflicts

When conflicts occur, Git will mark them in files like this:
```
<<<<<<< HEAD
Your local changes
=======
Upstream changes
>>>>>>> upstream/main
```

To resolve:
1. Edit the files to keep the desired changes
2. Remove the conflict markers
3. Stage the resolved files: `git add <filename>`
4. Continue the merge/rebase

## Tracking Your Customizations

### 1. Document Your Changes
Create a `CUSTOMIZATIONS.md` file listing all your modifications:

```markdown
# Our Customizations

## Added Features
- MCP server implementation (MCP/ directory)
- MoveToDocs workflow node
- Multi-language support enhancements

## Modified Files
- `nodes.py`: Added MoveToDocs class
- `flow.py`: Added MoveToDocs to workflow
- `.env`: Custom LLM configurations

## Configuration Changes
- Changed default LLM provider to OpenRouter
- Added custom file patterns
```

### 2. Use Feature Branches
For significant customizations:
```bash
# Create feature branch for your changes
git checkout -b feature/mcp-server
# Work on your feature
git add .
git commit -m "Add MCP server implementation"
# Merge back to main
git checkout main
git merge feature/mcp-server
```

### 3. Cherry-Pick Specific Updates
To selectively apply upstream commits:
```bash
# List upstream commits
git log upstream/main --oneline

# Cherry-pick specific commits
git cherry-pick <commit-hash>
```

## Best Practices

1. **Regular Updates**: Fetch upstream changes frequently to avoid large conflicts
2. **Clean Commits**: Keep your customizations in clear, logical commits
3. **Backup**: Before major merges, create a backup branch:
   ```bash
   git checkout -b backup-before-merge
   ```
4. **Test After Merge**: Always test functionality after merging upstream changes

## Viewing Differences

```bash
# See what's different between your branch and upstream
git diff main upstream/main

# See commit differences
git log main..upstream/main --oneline

# See which files changed
git diff --name-only main upstream/main
```

## Emergency Rollback

If something goes wrong:
```bash
# Reset to before the merge (if not pushed)
git reset --hard HEAD~1

# Or revert the merge commit (if already pushed)
git revert -m 1 <merge-commit-hash>
```

## Automating Updates

Create a script `update-from-upstream.sh`:
```bash
#!/bin/bash
echo "Fetching upstream changes..."
git fetch upstream

echo "Current branch: $(git branch --show-current)"
echo "Commits behind upstream: $(git rev-list --count HEAD..upstream/main)"

echo "Do you want to merge upstream/main? (y/n)"
read -r response
if [[ "$response" == "y" ]]; then
    git merge upstream/main
    echo "Merge complete. Please resolve any conflicts if present."
fi
```

Make it executable: `chmod +x update-from-upstream.sh`