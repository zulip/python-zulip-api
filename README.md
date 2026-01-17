# Zulip Python API 🚀

[![Build status](https://github.com/zulip/python-zulip-api/workflows/build/badge.svg)](
https://github.com/zulip/python-zulip-api/actions?query=branch%3Amain+workflow%3Abuild)
[![Coverage status](https://img.shields.io/codecov/c/github/zulip/python-zulip-api)](
https://codecov.io/gh/zulip/python-zulip-api)

## What is this?

This repository contains Python packages for interacting with [Zulip](https://zulip.com/), an open-source team chat platform.

**Three main packages:**
- **`zulip`** - API bindings to send messages and interact with Zulip
- **`zulip_bots`** - Framework to build and run chatbots
- **`zulip_botserver`** - Server for hosting multiple bots

> 💡 **New to open source?** This is a beginner-friendly project perfect for your first contribution!

---

## ⚡ Quick Start (5 minutes)

### Prerequisites
- Python 3.7+ installed
- Git installed
- ~200MB disk space

### Step 1: Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/python-zulip-api.git
cd python-zulip-api
git remote add upstream https://github.com/zulip/python-zulip-api.git
```

### Step 2: Run setup (one command!)
```bash
python3 ./tools/provision
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Set up the project automatically

### Step 3: Activate the environment
After setup completes, copy and run the activation command shown in your terminal. It will look something like:
```bash
source zulip-api-py3-venv/bin/activate
```

✅ **Done!** You're ready to develop.

---

## 🛠️ Common Commands

### Run all tests
```bash
pytest
```

### Run tests for specific package
```bash
pytest zulip           # Test the main zulip package
pytest zulip_bots      # Test the bots package
pytest zulip_botserver # Test the botserver
```

### Check code style
```bash
./tools/lint
```

### Check type annotations
```bash
./tools/run-mypy
```

---

## 📖 Next Steps

- **Want to contribute?** → Read [CONTRIBUTING.md](CONTRIBUTING.md)
- **Learn the codebase?** → Check out individual README files in each package folder
- **Need help?** → See the [main Zulip contributing guide](https://zulip.readthedocs.io/en/latest/overview/contributing.html)

---

## 📝 Project Structure

```
zulip/                 # Main API client
zulip_bots/            # Bot framework
zulip_botserver/       # Bot server
tools/                 # Helper scripts (provision, lint, etc.)
```

---

## 💬 Questions?

- Open an issue on GitHub
- Ask in [Zulip's development community](https://chat.zulip.org/)
