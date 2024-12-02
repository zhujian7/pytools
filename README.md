# Python tools to improve productivity

## Review Konflux PRs

konfluxprreview.py is a tool to help review PRs raised by Konflux bot. it can:

- change the target branch for PRs raised by Konflux bot from `backplane-2.8` or `release-2.13` to `main`
- add a prefix 🌱 to PRs title if the PRs title do not start with 🌱
- add a comment `/lgtm` `/approve` to the PRs if the PRs do not have the `/lgtm` `/approved` labels

### prerequisite

- Ensure [`gh`](https://cli.github.com/) is installed and authenticated:
Make sure that you have `gh` installed and authenticated with your GitHub account. If you haven't already authenticated, you can do so by running:

```sh
gh auth login
```

- Install packages

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Examples

There are 4 options/arguments you can specify:

#### repositories

A list of repositories to process, if not specified, all foundation repositories will be processed.

- Find all PRs in all foundation repos, change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`.

```python
python -m apps.konfluxprreview
```

Note: Default foundation repos list:

```yaml
stolostron/ocm # zhujian7
stolostron/managed-serviceaccount # zhujian7
stolostron/multicloud-operators-foundation # elgnay
stolostron/managedcluster-import-controller # xuezhaojun
stolostron/clusterlifecycle-state-metrics # haoqing0110
stolostron/klusterlet-addon-controller # zhiweiyin318
stolostron/cluster-proxy-addon # xuezhaojun
stolostron/cluster-proxy # xuezhaojun
```

- Find all PRs in repo `stolostron/ocm` , change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`.

```python
python -m apps.konfluxprreview stolostron/ocm
```

#### keywords in PRs title --extra-keywords

A list of keywords to filter PRs, if not specified, PRs containing default keywords will be processed.

Default keywords(case-sensitive):

```yaml
Update Konflux references
update konflux references
Red Hat Konflux
```

- Find all PRs whose title containing the default keywords or `Konflux Test` in all foundation repos, change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`.

```python
python -m apps.konfluxprreview --extra-keywords="Konflux Test"
```

#### comment `/lgtm` --approve

A flag to leave a `/lgtm` and `approve` comment in PRs, if not specified, no comment will be left.

- Find all PRs in all foundation repos, change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`, and leave a `/lgtm` comment in the PRs.

```python
python -m apps.konfluxprreview --approve
```

#### PRs title 🌱 prefix --seedling

A flag to add a prefix 🌱 to PRs title if the PRs title do not start with 🌱, if not specified, no prefix will be added.

- Find all PRs in all foundation repos, change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`, and add a prefix 🌱 to PRs title if the PRs title do not start with 🌱.

```python
python -m apps.konfluxprreview --seedling
```
