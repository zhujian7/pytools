# Python tools to improve productivity

## prerequisite

- Ensure `git` is installed and authenticated

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

## 🛠️ Review Konflux PRs

konfluxprreview.py is a tool to help review PRs raised by Konflux bot. it can:

- change the target branch for PRs raised by Konflux bot from `backplane-2.8` or `release-2.13` to `main`
- add a prefix 🌱 to PRs title if the PRs title do not start with 🌱
- add a comment `/lgtm` `/approve` to the PRs if the PRs do not have the `/lgtm` `/approved` labels

### Examples of using the review tool

There are 4 options/arguments you can specify:

#### repositories

A list of repositories to process, if not specified, all foundation repositories will be processed.

- Find all PRs in all foundation repos, change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`.

```python
python -m apps.konflux.prreview
```

Note: Default foundation repos list, you the input repo is not in the list, you need to add it to the 'reposmap':

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
python -m apps.konflux.prreview stolostron/ocm
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
python -m apps.konflux.prreview --extra-keywords="Konflux Test"
```

#### comment `/lgtm` --approve

A flag to leave a `/lgtm` and `approve` comment in PRs, if not specified, no comment will be left.

- Find all PRs in all foundation repos, change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`, and leave a `/lgtm` comment in the PRs.

```python
python -m apps.konflux.prreview --approve
```

#### cc the repo owners to review the PR when there are failed CI checks --check-status

After the tool comments `/lgtm` and `approve` in the PRs, we expect the PRs to be merged automatically by prow. However, if there are any failed CI checking in the PRs, prow will not merge the PRs, which requires manual intervention. This flag is used to check the PRs status and cc the repo owners to handle the failed CI checks.

```python
python -m apps.konflux.prreview --check-status stolostron/ocm
```

#### PRs title 🌱 prefix --seedling

A flag to add a prefix 🌱 to PRs title if the PRs title do not start with 🌱, if not specified, no prefix will be added.

- Find all PRs in all foundation repos, change the PRs target branch from `backplane-2.8`/`release-2.13` to `main`, and add a prefix 🌱 to PRs title if the PRs title do not start with 🌱.

```python
python -m apps.konflux.prreview --seedling
```

## 🛠️ Create Konflux PRs to update konflux files

konfluxprupdate.py is a tool to help create a PR to update tekton files for konflux. it can:

- yaml format the tekton files
- add a OWNER file to the .tekton folder
- purge unnecessary files in the .tekton folder
- change the cel match pattern in the tekton files, current release branch -> main, or verse visa

And then it will create a PR and cc the repo owner to review.

Supportted repos and owners:

```yaml
stolostron/ocm # zhujian7
stolostron/managed-serviceaccount # zhujian7
stolostron/multicloud-operators-foundation # elgnay
stolostron/managedcluster-import-controller # xuezhaojun
stolostron/clusterlifecycle-state-metrics # haoqing0110
stolostron/cluster-proxy-addon # xuezhaojun
stolostron/cluster-proxy # xuezhaojun
stolostron/klusterlet-addon-controller # zhiweiyin318
```

### Examples of using the update tool

There are 4 options/arguments you can specify:

1. `--github-user`: Your GitHub username, if not specified, the default value is `zhujian7`. The tool will clone the repos from the forked repo of the user.
2. `--from-branch`: The branch name of the konflux CEL to be updated from, if not specified, the default value is `backplane-2.8`
3. `--to-branch`: The branch name of the konflux CEL to be updated to, if not specified, the default value is `main`. It is also the PR's target branch.
4. `--dry-run`: Run the tool in dry-run mode, will not create PRs and push changes to the forked repo when specified.
5. `repositories`: A list of repositories to process, if not specified, all foundation **MCE** repositories will be processed.

#### Example1: create a PR for all foundation MCE repos to update the CEL from `backplane-2.8` to `main`

This is used for the first time to update the CEL from `backplane-2.8` to `main` after a new release starts and the konflux onboarding PR for this release is merged.

```python
python -m apps.konflux.prupdate --from_branch=backplane-2.8 --to_branch=main
```

#### Example2: create a PR for all foundation MCE repos to update the CEL from `main` to `backplane-2.8`

This is used for update the CEL from `main` to `backplane-2.8` after the ff changes to the new release, and the old release CEL is still matching the `main`.

```python
python -m apps.konflux.prupdate --from_branch=main --to_branch=backplane-2.8
```

#### Example3: process the foundation ACM repos

Because the default `from_branch` is `backplane-2.8`, which is the value for MCE, we can not use the default value for ACM.
To process the ACM repos, we need to specify the `from_branch` and the repos.

```python
python -m apps.konflux.prupdate --from_branch=release-2.13 --to_branch=main stolostron/klusterlet-addon-controller
```

#### Example4: not change the CEL

If you want to create a PR to update the tekton files without changing the CEL, you can specify the `from_branch` and `to_branch` to the same value.
The following command will only format the tekton files, add the OWNER file to the .tekton folder, and purge unnecessary files in the `.tekton` folder for the `backplane-2.7` branch of the `cluster-proxy` and `cluster-proxy-addon` repos.

```python
python -m apps.konflux.prupdate --from_branch=backplane-2.7 --to_branch=backplane-2.7 stolostron/cluster-proxy stolostron/cluster-proxy-addon
```

#### Example5: dry-run mode

If you want to test the tool without creating PRs and pushing changes to the forked repo, you can specify the `--dry-run` flag.

```python
python -m apps.konflux.prupdate --from_branch=backplane-2.8 --to_branch=main --dry-run stolostron/ocm
```

## 🛠️ Update skip_if_only_changed for prow tests

prowtestskip.py is a tool to help update the `skip_if_only_changed` for prow tests steps.

```python
python -m apps.prow.skip_if_only_changed --path=/Users/test/go/src/github.com/openshift/release cluster-proxy-addon cluster-proxy
```

## 📝 What can’t these tools do?

- If there are any failed CI checking in the PRs, the tools will not be able to merge the PRs, which requires manual intervention.
