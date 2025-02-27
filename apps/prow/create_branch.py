import os
from ruamel.yaml import YAML
import click
import shutil
import subprocess


# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=2, offset=0)


def local_branch_name(from_branch, to_branch):
    return to_branch


# Function to check if the "upstream" remote exists, if not, add it
def check_upstream_remote(repo_dir, upstream_url):
    try:
        # Check if the upstream remote already exists
        result = subprocess.run(
            ["git", "-C", repo_dir, "remote", "get-url", "upstream"],
            capture_output=True,
            text=True,
        )

        # If the upstream remote does not exist, the command will fail
        if result.returncode != 0:
            print(f"Upstream remote not found. Adding upstream remote: {upstream_url}")
            subprocess.run(
                ["git", "-C", repo_dir, "remote", "add", "upstream", upstream_url],
                check=True,
            )
        else:
            print("Upstream remote already exists.")
    except subprocess.CalledProcessError as e:
        print(f"Error checking or adding upstream remote: {e}")


# Function to create a new branch, commit changes, and push the branch
def checkout_or_rebase_branch(
    repo_dir,
    from_branch,
    to_branch,
):
    local_branch = local_branch_name(from_branch, to_branch)
    # Check if the branch exists locally
    result = subprocess.run(
        ["git", "-C", repo_dir, "rev-parse", "--verify", local_branch],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        # Branch exists locally, perform rebase
        print(
            f"Branch {local_branch} exists locally. Rebasing with upstream/{from_branch}..."
        )
        rebase_result = subprocess.run(
            ["git", "-C", repo_dir, "rebase", f"upstream/{from_branch}", local_branch],
            check=True,
        )
        # Check if there are any changes to push
        if rebase_result.returncode != 0:
            print(f"Error rebasing {local_branch} with upstream/{from_branch}.")
    else:
        # Branch does not exist, create and checkout new branch
        print(
            f"Branch {local_branch} does not exist locally. Creating and checking out..."
        )
        subprocess.run(
            [
                "git",
                "-C",
                repo_dir,
                "checkout",
                "-b",
                local_branch,
                f"upstream/{from_branch}",
            ],
            check=True,
        )


def create_branch(repo_dir, from_branch, to_branch, dry_run):
    local_branch = local_branch_name(from_branch, to_branch)
    if dry_run:
        print(f"Dry run: successfully created branch {to_branch} for {repo_dir}.")
    else:
        subprocess.run(
            [
                "git",
                "-C",
                repo_dir,
                "push",
                "-u",
                "upstream",  # change origin to test
                local_branch + ":" + to_branch,
            ],
            check=True,
        )


# Function to clone a repo from the forked repository
def clone_repo_from_fork(
    repo,
    fork_user,
    repo_dir,
    from_branch,
    to_branch,
):
    # Construct the URL for the forked repository
    forked_repo_url = f"git@github.com:{fork_user}/{repo.split('/')[1]}.git"
    if not os.path.exists(repo_dir):
        print(f"Cloning {forked_repo_url} into {repo_dir}...")
        subprocess.run(["git", "clone", forked_repo_url, repo_dir], check=True)
    # else:
    #     print(f"Repository {repo_dir} already exists. Pulling latest changes...")
    #     subprocess.run(['git', '-C', repo_dir, 'pull'], check=True)

    # Add the original repository as the upstream remote
    original_repo_url = f"git@github.com:{repo}.git"
    check_upstream_remote(repo_dir, original_repo_url)

    subprocess.run(["git", "-C", repo_dir, "fetch", "upstream"], check=True)

    checkout_or_rebase_branch(
        repo_dir,
        from_branch,
        to_branch,
    )


@click.command()
@click.argument("repos", nargs=-1)
@click.option(
    "--github_user",
    type=click.STRING,
    default="zhujian7",
    prompt="Your github user name",
    help="The GitHub username of the forked repository",
)
# @click.option(
#     "--branch",
#     type=click.STRING,
#     default="main",
#     help="The branch name to create",
# )
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="set to true will not create PR and push changes",
)
# Main function to configure acm repos for the new release
# Example usage: python -m apps.prow.create_branch stolostron/ocm stolostron/managedcluster-import-controller
def main(
    repos,
    github_user,
    dry_run,
):
    reposmap = {
        # supportted repos, repo: branch name
        # TODO: update every release starts
        "stolostron/cluster-proxy-addon": "backplane-2.9",
        "stolostron/cluster-proxy": "backplane-2.9",
        "stolostron/clusterlifecycle-state-metrics": "backplane-2.9",
        "stolostron/foundation-e2e": "backplane-2.9",
        "stolostron/managed-serviceaccount-e2e": "backplane-2.9",
        "stolostron/managed-serviceaccount": "backplane-2.9",
        "stolostron/managedcluster-import-controller": "backplane-2.9",
        "stolostron/multicloud-operators-foundation": "backplane-2.9",
        "stolostron/ocm": "backplane-2.9",
        "stolostron/acm-workload": "release-2.13",
        "stolostron/cluster-lifecycle-e2e": "release-2.14",
        "stolostron/klusterlet-addon-controller": "release-2.14",
    }
    if repos:
        try:
            reposmap = {repo: reposmap[repo] for repo in repos}
        except KeyError as e:
            print(
                f"Error: Repo {e} not found in the list of supported repos. please add it to the 'reposmap' dictionary manually."
            )
            return

    print(f"Create branch for repos: {reposmap}, GitHub User: {github_user}")

    tmp_dir = "_tmp"
    # Ensure the temporary directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    from_branch = "main"
    # for repo in repos:
    for repo, branch in reposmap.items():
        repo_dir = os.path.join(
            tmp_dir, repo.split("/")[1]
        )  # Use repo name as directory name

        # Step 1: Clone the repository from the forked version
        clone_repo_from_fork(
            repo,
            github_user,
            repo_dir,
            from_branch,
            branch,
        )
        create_branch(repo_dir, from_branch, branch, dry_run)


if __name__ == "__main__":
    main()
