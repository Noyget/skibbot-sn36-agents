#!/bin/bash
# Quick fix script for SN36 agent execution

echo "🚀 SN36 Agent Fix — Quick Start"
echo "======================================"
echo ""

# Step 1: Copy server file
echo "Step 1: Copying FastAPI server..."
if [ ! -f "$HOME/.openclaw/workspace/skibbot-server.py" ]; then
    echo "❌ ERROR: skibbot-server.py not found in workspace"
    exit 1
fi

# Step 2: Prompt for repo path
echo ""
echo "Step 2: Where is your skibbot-sn36-agents repo?"
echo "Example: /home/openclaw/code/skibbot-sn36-agents"
read -p "Enter path: " REPO_PATH

if [ ! -d "$REPO_PATH" ]; then
    echo "❌ ERROR: Directory $REPO_PATH not found"
    exit 1
fi

# Step 3: Copy server file
echo ""
echo "Step 3: Copying server.py to repo..."
cp "$HOME/.openclaw/workspace/skibbot-server.py" "$REPO_PATH/agents/server.py"
if [ $? -eq 0 ]; then
    echo "✅ Copied successfully"
else
    echo "❌ Copy failed"
    exit 1
fi

# Step 4: Git operations
echo ""
echo "Step 4: Committing to Git..."
cd "$REPO_PATH"

# Check git status
git status

echo ""
echo "Git status above. Ready to commit? (y/n)"
read -p "Continue? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add agents/server.py
    git commit -m "Add FastAPI server for validator Docker execution"
    
    if [ $? -eq 0 ]; then
        echo "✅ Commit successful"
        
        # Get new commit hash
        NEW_COMMIT=$(git log -1 --format=%h)
        echo ""
        echo "📝 New commit hash: $NEW_COMMIT"
        echo ""
        echo "Step 5: Push to GitHub..."
        echo "Run: git push origin main"
        echo ""
        echo "You can also update your miner config:"
        echo "sed -i 's/9cd0881/$NEW_COMMIT/g' ~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js"
        echo "pm2 restart skibbot-miner"
    else
        echo "❌ Commit failed"
        exit 1
    fi
else
    echo "Cancelled"
    exit 1
fi

echo ""
echo "🎉 Done! Push to GitHub to complete the fix."
