import subprocess
import os
import click
import os
from ruamel.yaml import YAML
import json

# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 256
yaml.indent(mapping=2, sequence=2, offset=0)

acm_mce_release = ["release-2.13", "backplane-2.8"]

def local_branch_name(from_branch, to_branch):
    return f"konflux_update_{from_branch}_{to_branch}"


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
def format_yaml_file(file_path):
    with open(file_path, 'r') as f:
        data = yaml.load(f)

    # Save changes to the YAML file
    with open(file_path, 'w') as f:
        yaml.dump(data, f)


# Function to format all *.yaml files in the .tekton folder
def format_tekton_files(repo_dir, from_branch, to_branch):
    tekton_dir = os.path.join(repo_dir, '.tekton')
    if not os.path.exists(tekton_dir):
        print(f"No .tekton directory found in {repo_dir}. Skipping...")
        return ""

    # Iterate through the files in the .tekton directory
    for root, dirs, files in os.walk(tekton_dir):
        for file in files:
            if not file.endswith('.yaml'):
                continue

            file_path = os.path.join(root, file)
            format_yaml_file(file_path)

    if not has_changes(repo_dir):
        print(f"No changes for formatting tekton files to commit in {repo_dir}. Skipping...")
        return ""
    message = "Formatting all tekton files"
    commit_and_push_changes(repo_dir, from_branch, to_branch, message)
    return message


# Function to find and replace "backplane-2.8" with "main" in .tekton files
def update_tekton_files(repo_dir, from_branch, to_branch):
    tekton_dir = os.path.join(repo_dir, '.tekton')
    if not os.path.exists(tekton_dir):
        print(f"No .tekton directory found in {repo_dir}. Skipping...")
        return ""

    # Iterate through the files in the .tekton directory
    for root, dirs, files in os.walk(tekton_dir):
        for file in files:
            if not file.endswith('.yaml'):
                continue

            file_path = os.path.join(root, file)
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

    if not has_changes(repo_dir):
        print(f"No changes to commit in {repo_dir}. Skipping...")
        return ""
    message = f"Update konflux CEL from {from_branch} to {to_branch}"
    commit_and_push_changes(repo_dir, from_branch, to_branch, message)
    return message


# Function to find and replace "backplane-2.8" with "main" in .tekton files
def update_tekton_files(repo_dir, from_branch, to_branch):
    tekton_dir = os.path.join(repo_dir, '.tekton')
    if not os.path.exists(tekton_dir):
        print(f"No .tekton directory found in {repo_dir}. Skipping...")
        return ""

    # Iterate through the files in the .tekton directory
    for root, dirs, files in os.walk(tekton_dir):
        for file in files:
            if not file.endswith('.yaml'):
                continue

            file_path = os.path.join(root, file)
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

    if not has_changes(repo_dir):
        print(f"No changes to commit in {repo_dir}. Skipping...")
        return ""
    message = f"Update konflux CEL from {from_branch} to {to_branch}"
    commit_and_push_changes(repo_dir, from_branch, to_branch, message)
    return message


# Function to delete unnecessary files in the .tekton directory
def purge_tekton_files(repo_dir, from_branch, to_branch):
    tekton_dir = os.path.join(repo_dir, '.tekton')
    if not os.path.exists(tekton_dir):
        print(f"No .tekton directory found in {repo_dir}. Skipping...")
        return ""

    # Iterate through the files in the .tekton directory
    for root, dirs, files in os.walk(tekton_dir):
        for file in files:
            if not file.endswith('.yaml'):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                content = f.read()

            releases = [to_branch]
            if to_branch == "main":
                releases += acm_mce_release

            # keep the file if any of the releases is in the file
            if any(f'target_branch == "{release}"' in content for release in releases):
                print(f"Keeping {file_path}...")
                continue
            os.remove(file_path)

    if not has_changes(repo_dir):
        print(f"No changes to commit in {repo_dir}. Skipping...")
        return ""
    message = f"Purge konflux files"
    commit_and_push_changes(repo_dir, from_branch, to_branch, message)
    return message


def create_owners_file(repo_dir, from_branch, to_branch):
    # Define the path to the OWNERS file in the .tekton directory
    owners_file_path = os.path.join(repo_dir, '.tekton', 'OWNERS')
    
    # Check if the OWNERS file exists
    if os.path.exists(owners_file_path):
        return

    print(f"OWNERS file does not exist. Creating {owners_file_path}.")
    # Define the content of the OWNERS file
    owners_content = """approvers:
- zhujian7
- zhiweiyin318
- haoqing0110
- elgnay
- xuezhaojun
- qiujian16

reviewers:
- zhujian7
- zhiweiyin318
- haoqing0110
- elgnay
- xuezhaojun
- qiujian16
"""
    # Create the .tekton directory if it doesn't exist
    os.makedirs(os.path.dirname(owners_file_path), exist_ok=True)
        
    # Write the content to the OWNERS file
    with open(owners_file_path, 'w') as f:
        f.write(owners_content)
        
    print("OWNERS file created successfully.")
    message = f"Create an OWNERS file for tekton files"
    commit_and_push_changes(repo_dir, from_branch, to_branch, message)
    return message


def has_changes(repo_dir):
    result = subprocess.run(['git', '-C', repo_dir, 'diff', '--exit-code', '--quiet'], capture_output=True, text=True)
    return result.returncode != 0


# Function to create a new branch, commit changes, and push the branch
def commit_and_push_changes(repo_dir, from_branch, to_branch, message):
    subprocess.run(['git', '-C', repo_dir, 'add', '.'], check=True)
    subprocess.run(['git', '-C', repo_dir, 'commit', '--signoff', '-m', message], check=True)
    local_branch = local_branch_name(from_branch, to_branch)
    subprocess.run(['git', '-C', repo_dir, 'push', '-u', 'origin', local_branch, '-f'], check=True)


# Function to check if a PR already exists for the given branch, if exists, return the pr number
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
            return
        print(f"PR already exists for branch {local_branch} in {repo}. Skipping PR creation.")
        return prs[0]['number']
    except subprocess.CalledProcessError as e:
        print(f"Error checking for existing PRs in {repo}: {e}")
        return


# Function to comment "/cc" on a PR
def comment_cc(repo, pr_number, owners):
    try:
        # Using gh command to comment "/cc @user1 @user2" on the PR
        owners_mention = ' '.join([f'@{owner}' for owner in owners])
        subprocess.run(
            ['gh', 'pr', 'comment', str(pr_number), '--repo', repo, '--body', f"/cc {owners_mention}"],
            check=True
        )
        print(f"Successfully commented '/cc' on PR #{pr_number} in {repo}.")
    except subprocess.CalledProcessError as e:
        print(f"Error commenting '/cc' on PR #{pr_number} in {repo}: {e}")


# Function to create a PR and cc the owner to review
def create_pull_request(repo, github_user, from_branch, to_branch, messages, owners):
    local_branch = local_branch_name(from_branch, to_branch)
    body = construct_pr_body(repo, from_branch, to_branch, messages)
    try:
        result = subprocess.run(
            ['gh', 'pr', 'create', '--repo', repo, '--head', f'{github_user}:{local_branch}', '--base', to_branch,
             '--title', f':seedling: [{to_branch}] update konflux files', '--body', body],
            check=True
        )
        # get PR number from the result
        print(f"PR created successfully for {repo} with branch {local_branch}. stdout: {result}")

        pr_number = pr_exists(repo, from_branch, to_branch)
        if pr_number:
            comment_cc(repo, pr_number, owners)
    except subprocess.CalledProcessError as e:
        print(f"Error creating PR for {repo}: {e}")


def construct_pr_body(repo, from_branch, to_branch, messages):
    pr_body = f"This PR:\n"
    for m in messages:
        if m:
            pr_body += f"- {m}\n"
    return pr_body


# Main function
@click.command()
@click.argument('repos', nargs=-1)  # Accepts multiple repositories as arguments
@click.option('--github_user', type=click.STRING, default='zhujian7', prompt='Your github user name', help="The GitHub username of the forked repository")
@click.option('--from_branch', type=click.STRING, default='backplane-2.8', help="The branch name of the konflux CEL to be updated from")
@click.option('--to_branch', type=click.STRING, default='main', help="The branch name of the konflux CEL to be updated to")
def main(repos, github_user, from_branch, to_branch):
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
        reposmap = {repo: reposmap[repo] for repo in repos}
    else:
        # remove "stolostron/klusterlet-addon-controller" since its default branch is not backplane-2.8
        reposmap.pop("stolostron/klusterlet-addon-controller")

    print(f"Repos: {reposmap}, GitHub User: {github_user}, From Branch: {from_branch}, To Branch: {to_branch}")

    tmp_dir = "_tmp"
    # Ensure the temporary directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # for repo in repos:
    for repo, owners in reposmap.items():
        repo_url = repo
        repo_dir = os.path.join(tmp_dir, repo.split('/')[1]) # Use repo name as directory name

        # Step 1: Clone the repository from the forked version
        clone_repo_from_fork(repo, github_user, repo_dir, from_branch, to_branch)

        # # Step 2: Modify files in the .tekton folder
        funcs = [format_tekton_files, update_tekton_files, create_owners_file, purge_tekton_files]
        # funcs = [format_tekton_files, update_tekton_files, create_owners_file]
        messages = []
        for func in funcs:
            m = func(repo_dir, from_branch, to_branch)
            if m:
                messages.append(m)

        # Step 4: Check if a PR already exists for the branch
        if not pr_exists(repo, from_branch, to_branch):
            # If no PR exists, create one
            create_pull_request(repo, github_user, from_branch, to_branch, messages, owners)


if __name__ == '__main__':
    main()
