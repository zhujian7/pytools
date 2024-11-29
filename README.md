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

1. Find all PRs whose titles containing `Konflux test` and whose target branch is `backplane-2.8` in repos `stolostron/ocm` and `stolostron/managed-serviceaccount`, change the PRs target branch from `backplane-2.8` to `main`, and leave a comment `/lgtm`.
   
```
python -m apps.changetargetbranch --branch-before-changing=backplane-2.8 --branch-after-changing=main --approve stolostron/ocm stolostron/managed-serviceaccount --extra-keyword="Konflux test"
```

2. Find all PRs whose titles containing `Konflux test` and whose target branch is `backplane-2.7` in repos `stolostron/ocm` and `stolostron/managed-serviceaccount`, **NOT** change the PRs target branch, and leave a comment `/lgtm`.
   
```
python -m apps.changetargetbranch --branch-before-changing=backplane-2.7 --branch-after-changing=backplane-2.7 --approve stolostron/ocm stolostron/managed-serviceaccount --extra-keyword="Konflux test"
```

***Notes:***
- `extra-keyword` is not required, if not provided, the tool will find the keywords `Update Konflux references` and `Red Hat Konflux` in the PRs' title.
