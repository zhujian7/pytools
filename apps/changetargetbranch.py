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


@click.command()
@click.argument("repos", nargs=-1)
@click.option("--approve", is_flag=True, default=False, help="set to true will comment /lgtm on the PR")
@click.option("--branch-before-changing", type=click.STRING, default="backplane-2.8", help="the target branch name of the PR before changing")
@click.option("--branch-after-changing", type=click.STRING, default="main", help="the target branch name of the PR after changing")
@click.option("--extra-keyword", type=click.STRING, help="the extra keyword to search for in PR titles")
# Main function to list and modify PRs
# Example usage: python -m apps.changetargetbranch --approve --extra-keyword="Konflux ..." stolostron/ocm stolostron/managed-serviceaccount
def main(repos, approve, branch_before_changing, branch_after_changing, extra_keyword):
    print(f"Repos: {repos}, Approve: {approve}, Branch Before: {branch_before_changing}, Branch After: {branch_after_changing}")
    keywords = ['Update Konflux references', 'Red Hat Konflux', 'chore(deps): update konflux references']
    if extra_keyword:
        keywords.append(extra_keyword)
        print(f"Keywords: {keywords}")
    # if repos is not provided, use the default list
    if not repos:
        repos = [
            # "stolostron/ocm", # zhujian7
            "stolostron/managed-serviceaccount", # zhujian7
            "stolostron/multicloud-operators-foundation", # elgnay
        ]
    for repo in repos:
        prs = list_prs(repo)
        for pr in prs:
            if any(keyword in pr['title'] for keyword in keywords):
                # print(f"PR #{pr['number']} in {repo} targets {pr['title']}")

                # Check if the PR title starts with ":seeding:" and update it if not
                update_pr_title(repo, pr['number'], pr['title'])

                if pr['baseRefName'] == branch_before_changing:
                    if branch_before_changing == branch_after_changing:
                        print(f"PR #{pr['number']} in {repo} already targets {branch_before_changing}. Skipping.")
                    else:
                        print(f"PR #{pr['number']} in {repo} targets {branch_before_changing}. Changing to {branch_after_changing}.")
                        change_base_branch(repo, pr['number'], branch_after_changing)

                if approve:
                    lgtm, approved = has_lgtm_and_approved_labels(repo, pr['number'])
                    if lgtm and approved:
                        print(f"PR #{pr['number']} in {repo} already has 'lgtm' and 'approved' labels. Skipping.")
                    else:
                        print(f"Approving PR #{pr['number']} in {repo}.")
                        comment_lgtm_approve(repo, pr['number'])


if __name__ == '__main__':
    main()
