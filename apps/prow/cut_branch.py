import os
from ruamel.yaml import YAML
import click
import shutil


# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=2, offset=0)


def replace_in_file(file_path, old_release, new_release):
    with open(file_path, "r") as file:
        content = file.read()

    old_number = old_release.lstrip("backplane-").lstrip("release-")
    new_number = new_release.lstrip("backplane-").lstrip("release-")
    print(f"old release number {old_number}, new release number {new_number}")
    content = content.replace(old_release, new_release).replace(old_number, new_number)

    with open(file_path, "w") as file:
        file.write(content)


def handle_one_repo(repo_config_dir, old_release, new_release):
    # wark through the repo_config_dir for all .yaml files
    print(f"Start to process {repo_config_dir}")
    for root, dirs, files in os.walk(repo_config_dir):
        for file_name in files:
            if file_name.endswith("-main.yaml"):
                file_path = os.path.join(root, file_name)
                replace_in_file(file_path, old_release, new_release)
            elif file_name.endswith(old_release + ".yaml"):
                old_file_path = os.path.join(root, file_name)
                new_file_path = old_file_path.replace(old_release, new_release)
                # Copy the file to new name
                shutil.copy(old_file_path, new_file_path)
                replace_in_file(new_file_path, old_release, new_release)


@click.command()
@click.argument("repos", nargs=-1)
@click.option(
    "--path",
    type=click.STRING,
    default="/Users/jiazhu/go/src/github.com/openshift/release",
    help="the local path to the openshift/release repo",
)
# Main function to configure acm repos for the new release
# Example usage: python -m apps.prow.cut_branch ocm managedcluster-import-controller
def main(repos, path):

    reposmap = {
        # supportted repos, repo: [old_release, new_release]
        # TODO: update every release starts
        "cluster-proxy-addon": ["backplane-2.8", "backplane-2.9"],
        "cluster-proxy": ["backplane-2.8", "backplane-2.9"],
        "clusterlifecycle-state-metrics": ["backplane-2.8", "backplane-2.9"],
        "foundation-e2e": ["backplane-2.8", "backplane-2.9"],
        "managed-serviceaccount-e2e": ["backplane-2.8", "backplane-2.9"],
        "managed-serviceaccount": ["backplane-2.8", "backplane-2.9"],
        "managedcluster-import-controller": [
            "backplane-2.8",
            "backplane-2.9",
        ],
        "multicloud-operators-foundation": [
            "backplane-2.8",
            "backplane-2.9",
        ],
        "ocm": ["backplane-2.8", "backplane-2.9"],
        "acm-workload": ["release-2.12", "release-2.13"],
        "cluster-lifecycle-e2e": ["release-2.13", "release-2.14"],
        "klusterlet-addon-controller": ["release-2.13", "release-2.14"],
    }
    if repos:
        try:
            reposmap = {repo: reposmap[repo] for repo in repos}
        except KeyError as e:
            print(
                f"Error: Repo {e} not found in the list of supported repos. please add it to the 'reposmap' dictionary manually."
            )
            return

    for repo, releases in reposmap.items():
        # repo folder path = path/ci-operator/config/stolostron/repo
        repo_config_dir = os.path.join(
            path, "ci-operator", "config", "stolostron", repo
        )
        handle_one_repo(repo_config_dir, releases[0], releases[1])


if __name__ == "__main__":
    main()
