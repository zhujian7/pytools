import subprocess
import os
import click
import os
from ruamel.yaml import YAML
import json

# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=4, offset=2)


def local_branch_name(from_branch, to_branch):
    return f"konflux_cel_{from_branch}_{to_branch}"


# Function to check if the "upstream" remote exists, if not, add it
def check_upstream_remote(repo_dir, upstream_url):
    try:
        # Check if the upstream remote already exists
        result = subprocess.run(
            ['git', '-C', repo_dir, 'remote', 'get-url', 'upstream'],
            capture_output=True, text=True
        )
        
        # If the upstream remote does not exist, the command will fail
        if result.returncode != 0:
            print(f"Upstream remote not found. Adding upstream remote: {upstream_url}")
            subprocess.run(
                ['git', '-C', repo_dir, 'remote', 'add', 'upstream', upstream_url],
                check=True
            )
        else:
            print("Upstream remote already exists.")
    except subprocess.CalledProcessError as e:
        print(f"Error checking or adding upstream remote: {e}")


# Function to create a new branch, commit changes, and push the branch
def checkout_or_rebase_branch(repo_dir, from_branch, to_branch):
    local_branch = local_branch_name(from_branch, to_branch)
    # Check if the branch exists locally
    result = subprocess.run(
        ['git', '-C', repo_dir, 'rev-parse', '--verify', local_branch],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        # Branch exists locally, perform rebase
        print(f"Branch {local_branch} exists locally. Rebasing with upstream/{to_branch}...")
        subprocess.run(['git', '-C', repo_dir, 'rebase', f'upstream/{to_branch}', local_branch], check=True)
    else:
        # Branch does not exist, create and checkout new branch
        print(f"Branch {local_branch} does not exist locally. Creating and checking out...")
        subprocess.run(['git', '-C', repo_dir, 'checkout', '-b', local_branch, f'upstream/{to_branch}'], check=True)


# Function to clone a repo from the forked repository
def clone_repo_from_fork(repo, fork_user, repo_dir, from_branch, to_branch):
    # Construct the URL for the forked repository
    forked_repo_url = f"git@github.com:{fork_user}/{repo.split('/')[1]}.git"
    if not os.path.exists(repo_dir):
        print(f"Cloning {forked_repo_url} into {repo_dir}...")
        subprocess.run(['git', 'clone', forked_repo_url, repo_dir], check=True)
    # else:
    #     print(f"Repository {repo_dir} already exists. Pulling latest changes...")
    #     subprocess.run(['git', '-C', repo_dir, 'pull'], check=True)

    # Add the original repository as the upstream remote
    original_repo_url = f"git@github.com:{repo}.git"
    check_upstream_remote(repo_dir, original_repo_url)

    subprocess.run(['git', '-C', repo_dir, 'fetch', "upstream"], check=True)

    checkout_or_rebase_branch(repo_dir, from_branch, to_branch)


# Function to format a YAML file
def format_yaml_file(file_path, remove_elements=True):
    with open(file_path, 'r') as f:
        data = yaml.load(f)

    # Save changes to the YAML file
    with open(file_path, 'w') as f:
        yaml.dump(data, f)


# Function to find and replace "backplane-2.8" with "main" in .tekton files
def update_tekton_files(repo_dir, from_branch, to_branch):
    tekton_dir = os.path.join(repo_dir, '.tekton')
    if not os.path.exists(tekton_dir):
        print(f"No .tekton directory found in {repo_dir}. Skipping...")
        return False

    changes_made = False
    # Iterate through the files in the .tekton directory
    for root, dirs, files in os.walk(tekton_dir):
        for file in files:
            if not file.endswith('.yaml'):
                continue

            file_path = os.path.join(root, file)
            format_yaml_file(file_path)

            with open(file_path, 'r') as f:
                content = f.read()

            # Replace from_branch with to_branch
            source = f'target_branch == "{from_branch}"'
            target = f'target_branch == "{to_branch}"'
            if source in content:
                print(f"Updating {file_path}...")
                updated_content = content.replace(source, target)
                with open(file_path, 'w') as f:
                    f.write(updated_content)
                changes_made = True
    return changes_made

# Function to create a new branch, commit changes, and push the branch
def commit_and_push_changes(repo_dir, from_branch, to_branch):
    subprocess.run(['git', '-C', repo_dir, 'add', '.'], check=True)
    subprocess.run(['git', '-C', repo_dir, 'commit', '--signoff', '-m', f"Update konflux CEL from {from_branch} to {to_branch}"], check=True)
    local_branch = local_branch_name(from_branch, to_branch)
    subprocess.run(['git', '-C', repo_dir, 'push', '-u', 'origin', local_branch], check=True)

# Function to check if a PR already exists for the given branch
def pr_exists(repo, from_branch, to_branch):
    local_branch = local_branch_name(from_branch, to_branch)
    try:
        result = subprocess.run(
            ['gh', 'pr', 'list', '--repo', repo, '--head', local_branch, '--json', 'number'],
            capture_output=True, text=True, check=True
        )

        prs = json.loads(result.stdout.strip())
        if not prs:
            print(f"PR does not exist for branch {local_branch} in {repo}. Proceeding with PR creation.")
            return False
        print(f"PR already exists for branch {local_branch} in {repo}. Skipping PR creation.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking for existing PRs in {repo}: {e}")
        return False


# Function to create a PR
def create_pull_request(repo, github_user, from_branch, to_branch):
    local_branch = local_branch_name(from_branch, to_branch)
    try:
        result = subprocess.run(
            ['gh', 'pr', 'create', '--repo', repo, '--head', f'{github_user}:{local_branch}', '--base', to_branch,
             '--title', f':seedling: Update konflux CEL from {from_branch} to {to_branch}', '--body', f'This PR:\n- formats the tekton files\n- updates konflux CEL {from_branch} to {to_branch} in .tekton files'],
            check=True
        )
        print(f"PR created successfully for {repo} with branch {local_branch}.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating PR for {repo}: {e}")


# Main function
@click.command()
@click.argument('repos', nargs=-1)  # Accepts multiple repositories as arguments
@click.option('--github_user', type=click.STRING, default='zhujian7', prompt='Your github user name', help="The GitHub username of the forked repository")
@click.option('--from_branch', type=click.STRING, default='backplane-2.8', help="The branch name of the konflux CEL to be updated from")
@click.option('--to_branch', type=click.STRING, default='main', help="The branch name of the konflux CEL to be updated to")
def main(repos, github_user, from_branch, to_branch):
    if not repos:
        repos = [
            # "stolostron/ocm", # zhujian7
            # "stolostron/managed-serviceaccount", # zhujian7
            # "stolostron/multicloud-operators-foundation", # elgnay
            # "stolostron/managedcluster-import-controller", # xuezhaojun
            # "stolostron/clusterlifecycle-state-metrics", # haoqing0110
            # "stolostron/klusterlet-addon-controller", # zhiweiyin318
            # "stolostron/cluster-proxy-addon", # xuezhaojun
            "stolostron/cluster-proxy", # xuezhaojun
        ]

    tmp_dir = "_tmp"
    # Ensure the temporary directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    for repo in repos:
        repo_url = repo
        repo_dir = os.path.join(tmp_dir, repo.split('/')[1]) # Use repo name as directory name

        # Step 1: Clone the repository from the forked version
        clone_repo_from_fork(repo, github_user, repo_dir, from_branch, to_branch)

        # Step 2: Modify files in the .tekton folder
        changes_made = update_tekton_files(repo_dir, from_branch, to_branch)
        if not changes_made:
            print(f"No changes made in .tekton files for {repo}. Skipping...")
            continue

        # Step 3: Commit and push the changes
        commit_and_push_changes(repo_dir, from_branch, to_branch)

        # Step 4: Check if a PR already exists for the branch
        if not pr_exists(repo, from_branch, to_branch):
            # If no PR exists, create one
            create_pull_request(repo, github_user, from_branch, to_branch)


if __name__ == '__main__':
    main()
