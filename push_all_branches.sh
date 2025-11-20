#!/bin/bash
# Push all 60 session branches to remote

echo "================================================================================"
echo "Pushing all 60 session branches to remote repository..."
echo "================================================================================"

SESSION_ID="01Ee5VFdXvTFxTYjX4N8bMmo"
success=0
failed=0

# Get all session branches
branches=$(git branch | grep "claude/.*-${SESSION_ID}" | tr -d ' *' | sort)

for branch in $branches; do
    echo -n "Pushing $branch... "
    if git push -u origin "$branch" 2>&1 | grep -qE "(new branch|up-to-date|Everything up-to-date)"; then
        echo "✓"
        ((success++))
    else
        echo "✗"
        ((failed++))
    fi
done

echo "================================================================================"
echo "✓ Successfully pushed: $success branches"
if [ $failed -gt 0 ]; then
    echo "✗ Failed: $failed branches"
fi
echo "================================================================================"
