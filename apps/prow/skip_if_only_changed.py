import os
from ruamel.yaml import YAML
import click


# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=2, offset=0)

test_steps = [
    "check",
    "verify",
    "verify-deps",
    "unit",
    "unit-test",
    "build",
    "sonarcloud",
    # "sonar-pre-submit",
    # "sonar-post-submit",
    "integration",
    "e2e",
]

skip_if_only_changed_value = (
    r"^\.tekton/|\.rhtap$|^docs/|\.md$|^(?:.*/)?(?:\.gitignore|OWNERS|PROJECT|LICENSE)$"
)


# Function to format a YAML file
def format_yaml_file(file_path):
    with open(file_path, "r") as f:
        data = yaml.load(f)

    # Save changes to the YAML file
    with open(file_path, "w") as f:
        yaml.dump(data, f)


def skip_if_not_changed(file_path):
    with open(file_path, "r") as f:
        data = yaml.load(f)

    # Add or update the skip_if_only_changed in the tests element
    if "tests" in data:
        for test in data["tests"]:
            if "as" in test:
                if test["as"] in test_steps:
                    test["skip_if_only_changed"] = skip_if_only_changed_value
                    print(
                        f"Updated skip_if_only_changed in {file_path} for {test['as']}"
                    )
                elif "skip_if_only_changed" in test:
                    del test["skip_if_only_changed"]
                    print(
                        f"Removed skip_if_only_changed in {file_path} for {test['as']}"
                    )

    # Save changes to the YAML file
    with open(file_path, "w") as f:
        yaml.dump(data, f)


def handle_one_repo(repo_config_dir):
    # wark through the repo_config_dir for all .yaml files
    print(f"Start to process {repo_config_dir}")
    for root, dirs, files in os.walk(repo_config_dir):
        for file_name in files:
            if file_name.endswith(".yaml"):
                file_path = os.path.join(root, file_name)
                print(f"Processing {file_path}")
                # Process the YAML file
                skip_if_not_changed(file_path)


@click.command()
@click.argument("repos", nargs=-1)
@click.option(
    "--path",
    type=click.STRING,
    default="/Users/jiazhu/go/src/github.com/openshift/release",
    help="the local path to the openshift/release repo",
)
# Main function to configure acm repos skip tests if only non-code files change
# Example usage: python -m apps.prow.skip_if_only_changed ocm,managedcluster-import-controller
def main(repos, path):
    # if repos is not provided, use the default list
    if not repos:
        repos = [
            "ocm",  # zhujian7
            "managed-serviceaccount",  # zhujian7
            "multicloud-operators-foundation",  # elgnay
            "managedcluster-import-controller",  # xuezhaojun
            "clusterlifecycle-state-metrics",  # haoqing0110
            "klusterlet-addon-controller",  # zhiweiyin318
            "cluster-proxy-addon",  # xuezhaojun
            "cluster-proxy",  # xuezhaojun
        ]

    print(f"Repos: {repos}, Path: {path}")

    for repo in repos:
        # repo folder path = path/ci-operator/config/stolostron/repo
        repo_config_dir = os.path.join(
            path, "ci-operator", "config", "stolostron", repo
        )
        handle_one_repo(repo_config_dir)


if __name__ == "__main__":
    main()
