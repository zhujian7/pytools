# Python tools to improve productivity

## changetargetbranch
Change the target branch for PRs raised by Konflux bot.

### prerequisite

1. Ensure [`gh`](https://cli.github.com/) is installed and authenticated:
Make sure that you have `gh` installed and authenticated with your GitHub account. If you haven't already authenticated, you can do so by running:

```
gh auth login
```

2. Install packages

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Examples

1. Find all PRs whose titles containing `Konflux test` in repos `stolostron/ocm` and `stolostron/managed-serviceaccount`, change the PRs target branch from `backplane-2.8` to `main`, and leave a comment `/lgtm`.
```
python -m apps.changetargetbranch --branch-before-changing=backplane-2.8 --branch-after-changing=main --approve stolostron/ocm stolostron/managed-serviceaccount --extra-keyword="Konflux test"
```
