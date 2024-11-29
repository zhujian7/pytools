import subprocess
import json
import click

# List of repositories to check
REPOS = ['stolostron/ocm']  # Specify the repositories

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


# Function to comment "/lgtm" on a PR
def comment_lgtm(repo, pr_number):
    try:
        # Using gh command to comment "/lgtm" on the PR
        subprocess.run(
            ['gh', 'pr', 'comment', str(pr_number), '--repo', repo, '--body', '/lgtm\n/approve'],
            check=True
        )
        print(f"Successfully commented '/lgtm' on PR #{pr_number} in {repo}.")
    except subprocess.CalledProcessError as e:
        print(f"Error commenting '/lgtm' on PR #{pr_number} in {repo}: {e}")


@click.command()
@click.argument("repos", nargs=-1)
@click.option("--approve", is_flag=True, default=False, help="set to true will comment /lgtm on the PR")
@click.option("--branch-before-changing", type=click.STRING, default="backplane-2.8", help="the target branch name of the PR before changing")
@click.option("--branch-after-changing", type=click.STRING, default="main", help="the target branch name of the PR after changing")
@click.option("--extra-keyword", type=click.STRING, help="the extra keyword to search for in PR titles")
# Main function to list and modify PRs
# Example usage: python -m apps.changetargetbranch --branch-before-changing=backplane-2.8 --branch-after-changing=main --approve --extra-keyword="Konflux ..." stolostron/ocm stolostron/managed-serviceaccount
def main(repos, approve, branch_before_changing, branch_after_changing, extra_keyword):
    print(f"Repos: {repos}, Approve: {approve}, Branch Before: {branch_before_changing}, Branch After: {branch_after_changing}")
    for repo in repos:
        prs = list_prs(repo)
        for pr in prs:
            if 'Update Konflux references' in pr['title'] or 'Red Hat Konflux' in pr['title'] or extra_keyword in pr['title']:
                # Check if the target branch is matching the one before changing
                if pr['baseRefName'] == branch_before_changing:
                    print(f"PR #{pr['number']} in {repo} targets {branch_before_changing}. Changing to {branch_after_changing}.")
                    change_base_branch(repo, pr['number'], branch_after_changing)
                    comment_lgtm(repo, pr['number'])

if __name__ == '__main__':
    main()
