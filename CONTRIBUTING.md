# Contributing to Zulip Python API 🎉

Welcome! We're excited to have you contribute. This guide will help you make your first contribution in just a few steps.

## I'm New to Open Source! Where Do I Start?

No worries! Here's the path:

1. **Set up the project** → Follow the [README.md](README.md) quick start (5 minutes)
2. **Find an issue** → Look for issues labeled `good first issue` or `newcomer-friendly`
3. **Make your change** → Edit code, run tests, ensure everything works
4. **Submit a PR** → Push to GitHub and create a pull request

That's it! 🎊

---

## 📋 Step-by-Step Guide to Your First Contribution

### Step 1: Fork & Clone
```bash
# Go to https://github.com/zulip/python-zulip-api and click "Fork"

git clone https://github.com/YOUR_USERNAME/python-zulip-api.git
cd python-zulip-api
git remote add upstream https://github.com/zulip/python-zulip-api.git
```

### Step 2: Set Up Development Environment
```bash
python3 ./tools/provision
source zulip-api-py3-venv/bin/activate  # or appropriate path from provision output
```

### Step 3: Create a Branch
```bash
git checkout -b fix/issue-name-here
# Example: git checkout -b fix/typo-in-readme
```

### Step 4: Make Your Changes
Edit the files you need to change. Some common areas:
- **Documentation fixes?** → Edit `.md` files or docstrings
- **Bug fix?** → Find the relevant `.py` file
- **New feature?** → Check the package structure in [README.md](README.md)

### Step 5: Test Your Changes
```bash
# Run all tests
pytest

# Run tests for specific package
pytest zulip
pytest zulip_bots
pytest zulip_botserver

# Check code style
./tools/lint

# Check type annotations
./tools/run-mypy
```

✅ **All tests passing?** Great! Move to the next step.

### Step 6: Commit Your Changes
```bash
git add .
git commit -m "Brief description of what you changed"
```

Good commit messages:
- ✅ "Fix typo in README"
- ✅ "Add validation for user input"
- ❌ "Fixed stuff" (too vague)
- ❌ "asdfgh" (not descriptive)

### Step 7: Push & Create Pull Request
```bash
git push origin fix/issue-name-here
```

Then:
1. Go to https://github.com/zulip/python-zulip-api
2. Click "Compare & pull request"
3. Write a clear title and description
4. Click "Create pull request"

**Example PR description:**
```
Fixes #123

This PR fixes the issue where the bot server wouldn't start on Python 3.10.

Changes:
- Updated version check in server.py
- Added test for Python 3.10 compatibility

Related PR: #120
```

---

## 🎯 Types of Contributions We Love

### 🐛 Bug Fixes
- Find a bug, fix it, add a test case
- Example: "This function crashes with empty input"

### 📚 Documentation
- Improve README files
- Fix typos or unclear explanations
- Add code comments
- Write examples

### ✅ Tests
- Add test cases for untested code
- Improve test coverage

### 🧹 Code Quality
- Fix style issues (run `./tools/lint`)
- Improve type annotations
- Refactor unclear code

### ✨ New Features
- Discuss with maintainers first (open an issue)
- Then implement and test

---

## ❓ Common Questions

### "How do I find a good first issue?"
1. Go to https://github.com/zulip/python-zulip-api/issues
2. Filter by label: `good first issue` or `help wanted`
3. Read the issue description
4. Comment "I'd like to work on this" to claim it

### "What if I need help?"
- Comment on the GitHub issue
- Ask in [Zulip's development community](https://chat.zulip.org/)
- Open a draft PR and describe your question in the description

### "My PR was rejected. What now?"
- Read the feedback carefully
- Make the requested changes
- Push the changes to your branch (PR updates automatically)
- The maintainers will review again

### "How long does review take?"
- Usually 1-7 days depending on complexity
- Be patient! Maintainers are volunteers

---

## 📏 Code Style & Standards

### Follow These Rules
1. **Python style** → Run `./tools/lint` (follows PEP 8)
2. **Type hints** → Add type annotations to functions
3. **Tests** → Write tests for new code
4. **Commit messages** → Be clear and descriptive

### Example Code
```python
# ✅ Good
def get_user_message(user_id: int, limit: int = 10) -> list[str]:
    """
    Fetch messages from a user.
    
    Args:
        user_id: The ID of the user
        limit: Maximum number of messages to fetch (default: 10)
    
    Returns:
        A list of message strings
    """
    if user_id < 0:
        raise ValueError("user_id must be positive")
    return fetch_messages(user_id, limit)


# ❌ Bad
def get_msg(id, lim=10):
    """Get messages"""
    return fetch_messages(id, lim)
```

---

## 🔄 Staying Updated

Before you start work, keep your fork updated:
```bash
git fetch upstream
git rebase upstream/main
```

If your PR has conflicts:
```bash
git fetch upstream
git rebase upstream/main
# Resolve conflicts in your editor
git add .
git rebase --continue
git push -f origin fix/issue-name-here
```

---

## 🏆 Contribution Recognition

- Your name will appear in commit history
- Significant contributors are listed in the project
- Great contributions strengthen your GSOC/Outreachy application!

---

## 📚 Resources

- [Main Zulip Contributing Guide](https://zulip.readthedocs.io/en/latest/overview/contributing.html)
- [Git & Commit Guidelines](https://zulip.readthedocs.io/en/latest/contributing/version-control.html)
- [Code Review Guide](https://zulip.readthedocs.io/en/latest/contributing/code-reviewing.html)
- [Zulip Development Community](https://chat.zulip.org/)

---

## 💡 Pro Tips

1. **Start small** → Fix a typo, improve a comment
2. **Read existing code** → Understand the patterns used
3. **Ask questions** → It's okay to be confused!
4. **Be polite** → Kindness makes the community better
5. **Keep learning** → Each PR teaches you something new

---

## 🚀 Ready to Contribute?

1. Pick an issue from [GitHub Issues](https://github.com/zulip/python-zulip-api/issues)
2. Follow the steps above
3. Make your first contribution
4. Celebrate! 🎉

**We believe in you! Every expert was once a beginner.** 🌟

---

*Questions? Open an issue or ask in our community. Happy contributing!*
