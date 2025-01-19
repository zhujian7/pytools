import subprocess
import os
import click
import os
from ruamel.yaml import YAML
import json
import re

# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 256
yaml.indent(mapping=2, sequence=2, offset=0)


# Function to run gh command and get PRs for a repo
def get_prs(repo):
    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--json",
            "title,url,headRefName",
            "--jq",
            ".[] | {title, url, headRefName}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error fetching PRs: {result.stderr}")
        return []
    return [pr.strip() for pr in result.stdout.splitlines()]


# Function to check if a PR title and description match the criteria
def check_pr_title_and_description(repo, pr):
    pr_title = pr["title"]
    pr_url = pr["url"]

    # Check if the PR title contains the specific text
    if (
        "chore(deps): update konflux references" not in pr_title
        and "Update Konflux references" not in pr_title
    ):
        print(f"{repo} PR title does not match for {pr_url}")
        return False

    # Fetch the PR description (body) and check for the specific migration update
    result = subprocess.run(
        ["gh", "pr", "view", pr_url, "--repo", repo, "--json", "body"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        print(f"{repo} Error fetching PR description for {pr_url}: {result.stderr}")
        return False

    pr_description = result.stdout
    if (
        "tekton-catalog/task-buildah | `0.2` -> `0.3` | :warning:[migration]"
        not in pr_description
    ):
        print(f"{repo} PR description does not match for {pr_url}")
        return False

    print(f"{repo} PR {pr_url} matches the title and description criteria.")
    return True


# Function to check if a PR is trying to update the version of tekton-catalog/task-buildah
def check_update_pr(repo, pr):

    # Check if the PR title and description match the specified patterns
    return check_pr_title_and_description(repo, pr)


# Function to update YAML file
def update_yaml_file(repo_dir):
    tekton_dir = os.path.join(repo_dir, ".tekton")
    if not os.path.exists(tekton_dir):
        print(f"No .tekton directory found. Skipping...")
        return ""

    # Iterate through the files in the .tekton directory
    for root, dirs, files in os.walk(tekton_dir):
        for yaml_file in files:
            file_path = os.path.join(root, yaml_file)
            with open(file_path, "r") as file:
                content = file.readlines()

            # Regular expression to find the target line and the lines before and after
            regex = re.compile(r".*JAVA_COMMUNITY_DEPENDENCIES.*")

            new_content = []
            skip_next = False
            for i, line in enumerate(content):
                if skip_next:
                    skip_next = False
                    continue
                if regex.match(line):
                    # Skip this line and the one before and after it
                    if i > 0:
                        new_content.pop()  # Remove the previous line
                    skip_next = True  # Skip this line
                else:
                    new_content.append(line)

            # Write the updated content back to the file
            with open(file_path, "w") as file:
                file.writelines(new_content)
            print(f"File {file_path} has been updated.")


def has_changes(repo_dir):
    result = subprocess.run(
        ["git", "-C", repo_dir, "diff", "--exit-code", "--quiet"],
        capture_output=True,
        text=True,
    )
    return result.returncode != 0


# Function to commit and push changes
def commit_and_push_changes(
    repo_dir,
    pr_ref,
    commit_message="Migrate task buildah from 0.2 to 0.3",
    dry_run=False,
):
    # Make sure we are on the correct branch for the PR
    result = subprocess.run(
        ["git", "-C", repo_dir, "checkout", pr_ref],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error checking out branch {pr_ref}: {result.stderr}")
        return

    if not has_changes(repo_dir):
        print(
            f"No changes for migration tekton files to commit in {repo_dir}. Skipping..."
        )
        return ""

    # Stage changes
    result = subprocess.run(
        ["git", "-C", repo_dir, "add", ".tekton"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error adding file: {result.stderr}")
        return

    # Commit changes
    result = subprocess.run(
        ["git", "-C", repo_dir, "commit", "--signoff", "-m", commit_message],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # text=True,
        check=True,
    )
    # result = subprocess.run(
    #     ["git", "-C", repo_dir, "commit", "--signoff", "-m", message], check=True
    # )
    if result.returncode != 0:
        print(f"Error committing changes: {result.stderr}")
        return

    if not dry_run:
        # Push changes to the remote branch
        result = subprocess.run(
            ["git", "-C", repo_dir, "push", "upstream", pr_ref],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error pushing changes to PR: {result.stderr}")
            return

    print(f"Changes successfully pushed to PR branch {pr_ref}")


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


# Function to clone a repo from the forked repository
def clone_repo_from_fork(repo, fork_user, repo_dir, pr_ref):
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

    original_directory = os.getcwd()
    try:
        # Change to the specified directory
        os.chdir(repo_dir)

        # Checkout the PR branch using gh pr checkout
        result = subprocess.run(
            ["gh", "pr", "--repo", repo, "checkout", pr_ref],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error checking out PR branch {pr_ref}: {result.stderr}")
        print(f"{repo} checkouted to {pr_ref}")
    finally:
        # Return to the original directory
        os.chdir(original_directory)
        print(f"Changing dir to {original_directory}")


# Main function
@click.command()
@click.argument("repos", nargs=-1)  # Accepts multiple repositories as arguments
@click.option(
    "--github_user",
    type=click.STRING,
    default="zhujian7",
    prompt="Your github user name",
    help="The GitHub username of the forked repository",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="set to true will not create PR and push changes",
)
def main(repos, github_user, dry_run):
    reposmap = {
        # supportted repos, repo: owners
        "stolostron/ocm": ["zhujian7", "xuezhaojun"],
        "stolostron/managed-serviceaccount": ["zhujian7", "xuezhaojun"],
        "stolostron/multicloud-operators-foundation": ["elgnay"],
        "stolostron/managedcluster-import-controller": ["xuezhaojun"],
        "stolostron/cluster-proxy-addon": ["xuezhaojun"],
        "stolostron/cluster-proxy": ["xuezhaojun"],
        "stolostron/clusterlifecycle-state-metrics": ["haoqing0110"],
        "stolostron/klusterlet-addon-controller": ["zhujian7", "zhiweiyin318"],
    }
    if repos:
        try:
            reposmap = {repo: reposmap[repo] for repo in repos}
        except KeyError as e:
            print(
                f"Error: Repo {e} not found in the list of supported repos. please add it to the 'reposmap' dictionary manually."
            )
            return

    print(f"Repos: {reposmap}, GitHub User: {github_user}, Dry Run: {dry_run}")

    tmp_dir = "_tmp"
    # Ensure the temporary directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # for repo in repos:
    for repo, owners in reposmap.items():
        repo_dir = os.path.join(
            tmp_dir, repo.split("/")[1]
        )  # Use repo name as directory name

        # Step 1: Get PRs
        prs = get_prs(repo)
        if not prs:
            return

        # Step 2: Check each PR for the task-buildah version change
        for pr in prs:
            pr_data = yaml.load(pr)
            if check_update_pr(repo, pr_data):
                pr_ref = pr_data["headRefName"]
                print(f"Debug: {pr_data}")
                # Step 3: Clone the repository from the forked version
                clone_repo_from_fork(repo, github_user, repo_dir, pr_ref)

                # Step 4: Update the YAML file if a matching PR is found
                update_yaml_file(repo_dir)

                # Step 5: Commit and push changes to the PR
                commit_and_push_changes(
                    repo_dir,
                    pr_ref,
                    commit_message="Migrate task buildah from 0.2 to 0.3",
                    dry_run=dry_run,
                )


if __name__ == "__main__":
    main()
