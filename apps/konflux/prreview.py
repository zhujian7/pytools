import subprocess
import json
import click


# Function to list open PRs containing "Konflux" in the title
def list_prs(repo):
    try:
        # Using gh command to list open PRs in JSON format
        result = subprocess.run(
            ['gh', 'pr', 'list', '--repo', repo, '--state', 'open', '--json', 'number,title,baseRefName'],
            capture_output=True, text=True, check=True
        )
        prs = json.loads(result.stdout)
        return prs
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PRs for {repo}: {e}")
        return []

# Function to change the base branch of a PR
def change_base_branch(repo, pr_number, new_base_branch):
    try:
        # Using gh command to change the base branch of a PR
        subprocess.run(
            ['gh', 'pr', 'edit', str(pr_number), '--repo', repo, '--base', new_base_branch],
            check=True
        )
        print(f"Successfully updated PR #{pr_number} in {repo} to base branch {new_base_branch}.")
    except subprocess.CalledProcessError as e:
        print(f"Error updating PR #{pr_number} in {repo}: {e}")


# Function to check if a PR has the 'lgtm' and 'approved' labels
def has_lgtm_and_approved_labels(repo, pr_number):
    try:
        # Using gh command to get the PR details, specifically the labels
        result = subprocess.run(
            ['gh', 'pr', 'view', str(pr_number), '--repo', repo, '--json', 'labels'],
            capture_output=True, text=True, check=True
        )
        pr_data = json.loads(result.stdout)
        labels = [label['name'] for label in pr_data['labels']]
        return 'lgtm' in labels, 'approved' in labels
    except subprocess.CalledProcessError as e:
        print(f"Error checking labels for PR #{pr_number} in {repo}: {e}")
        return False, False


# Function to comment "/lgtm" on a PR
def comment_lgtm_approve(repo, pr_number):
    try:
        # Using gh command to comment "/lgtm" on the PR
        subprocess.run(
            ['gh', 'pr', 'comment', str(pr_number), '--repo', repo, '--body', '/lgtm\n/approve'],
            check=True
        )
        print(f"Successfully commented '/lgtm' on PR #{pr_number} in {repo}.")
    except subprocess.CalledProcessError as e:
        print(f"Error commenting '/lgtm' on PR #{pr_number} in {repo}: {e}")


# Function to change PR title to start with "🌱" if it doesn't start with ":seeding:"
def update_pr_title(repo, pr_number, title):
    if not title.startswith('🌱') and not title.startswith(':seedling:'):
        new_title = '🌱 ' + title
        try:
            subprocess.run(
                ['gh', 'pr', 'edit', str(pr_number), '--repo', repo, '--title', new_title],
                check=True
            )
            print(f"Successfully updated title of PR #{pr_number} in {repo} to '{new_title}'.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating title of PR #{pr_number} in {repo}: {e}")


# Function to check if the PR has any failed status checks, and comment on the PR to notify the owners
def check_failed_status(repo, pr_number, owners):
    try:
        # Get the list of checks for this PR using the GitHub CLI
        result = subprocess.run(
            ['gh', 'pr', 'view', str(pr_number), '--repo', repo, '--json', 'statusCheckRollup'],
            capture_output=True, text=True, check=True
        )

        if result.returncode != 0:
            print(f"Error retrieving PR status for {pr_url}: {result.stderr}")
            return False
    
        # Parse the JSON response
        pr_data = json.loads(result.stdout)
    
        # Check if the status checks have failed
        failed_checks = []
        
        for index, check in enumerate(pr_data.get('statusCheckRollup', {})):
            status = check.get('conclusion', check.get('state'))
            if not status:
                continue
            if status.lower() == 'failure':
                name = check.get('name', check.get('context', str(index)))
                failed_checks.append(name)
        print(f"PR #{pr_number} in {repo} has the following failed checks: {failed_checks}")
        
        if failed_checks:
            # Comment on the PR with the failed checks with format:
            # "Hello @owner1 @owner2, the following checks have failed for this PR: check1, check2"
            owners_mention = ' '.join([f'@{owner}' for owner in owners])
            failed_checks_str = ', '.join(failed_checks)
            comment = f"Hello {owners_mention}, the following checks have failed for this PR: {failed_checks_str}"
            subprocess.run(
                ['gh', 'pr', 'comment', str(pr_number), '--repo', repo, '--body', comment],
                check=True
            )
            print(f"Commented on PR #{pr_number} in {repo} with failed checks.")
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking status for PR #{pr_number} in {repo}: {e}")
        return False


# Function to get a list of changed files in a PR
def get_changed_files(repo, pr_number):
    try:
        # Using gh command to get the list of changed files in the PR
        result = subprocess.run(
            ['gh', 'pr', 'view', str(pr_number), '--repo', repo, '--json', 'files'],
            capture_output=True, text=True, check=True
        )
        pr_data = json.loads(result.stdout)
        files = [file['path'] for file in pr_data['files']]
        return files
    except subprocess.CalledProcessError as e:
        print(f"Error fetching changed files for PR #{pr_number} in {repo}: {e}")
        return []

# Function to check if all changed files are in the ".tekton" directory
def all_files_in_tekton(files):
    for file in files:
        if not file.startswith('.tekton/'):
            return False
    return True


@click.command()
@click.argument("repos", nargs=-1)
@click.option("--approve", is_flag=True, default=False, help="set to true will comment /lgtm on the PR")
@click.option("--seedling", is_flag=True, default=False, help="set to true will update PR title to start with 🌱")
@click.option("--check-status", is_flag=True, default=True, help="set to true will check if PR has failed status checks")
@click.option("--extra-keyword", type=click.STRING, help="the extra keyword to search for in PR titles")
# Main function to list and modify PRs
# Example usage: python -m apps.konflux.prreview --approve --seedling --extra-keyword="Konflux Test" stolostron/ocm stolostron/managed-serviceaccount
def main(repos, approve, seedling, check_status, extra_keyword):
    branches_before_changing = ["backplane-2.8", "release-2.13"]
    branch_after_changing = "main"
    print(f"Repos: {repos}, Approve: {approve}, Branches Before: {branches_before_changing}, Branch After: {branch_after_changing}")
    keywords = ['Update Konflux references', 'Red Hat Konflux', 'update konflux references', 'update konflux files']
    if extra_keyword:
        keywords.append(extra_keyword)
        print(f"Keywords: {keywords}")

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
            print(f"Error: Repo {e} not found in the list of supported repos. please add it to the 'reposmap' dictionary manually.")
            return

    for repo, owners in reposmap.items():
        prs = list_prs(repo)
        for pr in prs:
            title_match = False
            content_match = False
            # Check if all files changed are in the ".tekton" directory, and comment "/lgtm" if true
            changed_files = get_changed_files(repo, pr['number'])
            if all_files_in_tekton(changed_files):
                content_match = True
            if any(keyword in pr['title'] for keyword in keywords):
                title_match = True
            print(f"PR #{pr['number']} in {repo}, content_match: {content_match}, title_match: {title_match}, title: {pr['title']}")
            if title_match and content_match:
                if pr['baseRefName'] in branches_before_changing:
                    if pr['baseRefName'] == branch_after_changing:
                        print(f"PR #{pr['number']} in {repo} already targets {branch_after_changing}. Skipping.")
                    else:
                        print(f"PR #{pr['number']} in {repo} targets {pr['baseRefName']}. Changing to {branch_after_changing}.")
                        change_base_branch(repo, pr['number'], branch_after_changing)

                if seedling:
                    # Check if the PR title starts with ":seeding:" and update it if not
                    update_pr_title(repo, pr['number'], pr['title'])

                ci_failed = False
                if check_status:
                    # Check if the PR has any failed status checks
                   ci_failed = check_failed_status(repo, pr['number'], owners)

                if approve and not ci_failed:
                    lgtm, approved = has_lgtm_and_approved_labels(repo, pr['number'])
                    if lgtm and approved:
                        print(f"PR #{pr['number']} in {repo} already has 'lgtm' and 'approved' labels. Skipping.")
                    else:
                        print(f"Approving PR #{pr['number']} in {repo}.")
                        comment_lgtm_approve(repo, pr['number'])


if __name__ == '__main__':
    main()
