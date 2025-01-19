from kubernetes import client, config
import sys
import click

# Load kubeconfig
config.load_kube_config()

# Create an API client for custom resources
api_instance = client.CustomObjectsApi()

# Define the group, version, and plural for ManagedCluster
GROUP = "cluster.open-cluster-management.io"
VERSION = "v1"
PLURAL = "managedclusters"

# Namespace is not required for cluster-scoped resources
namespace = None


# Define a base ManagedCluster spec
def create_managed_cluster_spec(name):
    return {
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": "ManagedCluster",
        "metadata": {"name": name},
        "spec": {
            "hubAcceptsClient": True,
        },
    }


# Function to create ManagedClusters
def create_managed_clusters(start=1, count=1000):
    for i in range(start, count + start):
        name = f"managedcluster-{i}"
        body = create_managed_cluster_spec(name)
        try:
            api_instance.create_cluster_custom_object(GROUP, VERSION, PLURAL, body)
            print(f"Created ManagedCluster: {name}")
        except client.exceptions.ApiException as e:
            if e.status == 409:  # 409 Conflict means "AlreadyExists"
                print(f"ManagedCluster {name} already exists, skipping.")
            else:
                print(
                    f"Exception when creating ManagedCluster: {name}: {e}",
                    file=sys.stderr,
                )


# Function to delete all ManagedClusters
def delete_managed_clusters(start=1, count=1000):
    for i in range(start, count + start):
        name = f"managedcluster-{i}"
        try:
            api_instance.delete_cluster_custom_object(GROUP, VERSION, PLURAL, name)
            print(f"Deleted ManagedCluster: {name}")
        except client.exceptions.ApiException as e:
            if e.status == 404:  # 404 NotFound
                print(f"ManagedCluster {name} not found, skipping.")
            else:
                print(
                    f"Exception when deleting ManagedCluster: {name}: {e}",
                    file=sys.stderr,
                )


# Main function
# Examples:
# - export KUBECONFIG=$HOME/Downloads/kubeconfig.yaml; python -m apps.perf.prepare_clusters --action=create --count=10
@click.command()
@click.option(
    "--action",
    type=click.STRING,
    default="create",
    help="The action on the managedclusters, create, delete",
)
@click.option(
    "--start",
    type=click.INT,
    default="1",
    help="The start number of the managedclusters",
)
@click.option(
    "--count",
    type=click.INT,
    default="5",
    help="The count of the managedclusters",
)
def main(action, start, count):
    if action == "create":
        print(f"Start to prepare managed clusters for performance tests.")
        create_managed_clusters(start, count)
    elif action == "delete":
        delete_managed_clusters(start, count)


if __name__ == "__main__":
    main()
