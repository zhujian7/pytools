import os
from ruamel.yaml import YAML

# Define the list of repository directories
repos = [
    "/Users/jiazhu/go/src/open-cluster-management.io/ocm",
    # "/Users/jiazhu/go/src/open-cluster-management.io/managed-serviceaccount",
    ]


# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=4, offset=2)

# Function to recursively remove only the innermost elements with the specified keyword
def remove_innermost_elements(data, keyword="BASE_IMAGES"):
    if isinstance(data, dict):
        # Recurse into nested dictionaries and lists first
        for key, value in list(data.items()):
            if isinstance(value, (dict, list)):
                remove_innermost_elements(value, keyword)
        
        # Now check and delete if this is an innermost level containing the keyword
        keys_to_delete = [key for key, value in data.items() if keyword in str(value)]
        for key in keys_to_delete:
            print(f"Deleting {key} from {data}")
            # del data[key]

        # # Remove empty dictionaries after deletion
        # keys_to_delete = [key for key, value in data.items() if value == {} or value == []]
        # for key in keys_to_delete:
        #     del data[key]

    elif isinstance(data, list):
        # Recurse into each item in the list first
        for item in data:
            if isinstance(item, (dict, list)):
                remove_innermost_elements(item, keyword)
        
        # Delete dictionaries that contain the keyword as innermost elements
        items_to_delete = [index for index, item in enumerate(data)
                           if isinstance(item, dict) and any(keyword in str(v) for v in item.values())]
        for index in reversed(items_to_delete):
            print(f"Deleting {data[index]} from {data}")
            del data[index]
        
        # Remove empty dictionaries and lists after deletion
        # data[:] = [item for item in data if item != {} and item != []]
        # data[:] = [item for item in data if item not in ({}, [], None)]

# Function to process a YAML file
def process_yaml_file(file_path, remove_elements=True):
    with open(file_path, 'r') as f:
        data = yaml.load(f)

    # Remove innermost elements with the keyword
    if remove_elements:
        remove_innermost_elements(data)

    # Save changes to the YAML file
    with open(file_path, 'w') as f:
        yaml.dump(data, f)

# Function to process a rhtap Dockerfile
def process_dockerfile(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Replace line with rhel_8_1.21 to rhel_8_1.22, with ubi8 to ubi9
    for index, line in enumerate(lines):
        if "rhel_8_1.21" in line:
            lines[index] = line.replace("rhel_8_1.21", "rhel_8_1.22")
        if "ubi8" in line:
            lines[index] = line.replace("ubi8", "ubi9")

    # Save changes to the Dockerfile
    with open(file_path, 'w') as f:
        f.writelines(lines)

# Iterate over each repository
for repo in repos:
    tekton_dir = os.path.join(repo, '.tekton')
    # Check if .tekton directory exists
    if os.path.isdir(tekton_dir):
        # Iterate over each file in the .tekton directory
        for file_name in os.listdir(tekton_dir):
            # Process only .yaml files
            if file_name.endswith('.yaml'):
                file_path = os.path.join(tekton_dir, file_name)
                # Process the YAML file
                process_yaml_file(file_path)
                print(f"Updated {file_path}")
    # Iterate over each file in the repository to find files with .rhtap extension
    for root, dirs, files in os.walk(repo):
        for file_name in files:
            if file_name.endswith('.rhtap'):
                file_path = os.path.join(root, file_name)
                # Process the Dockerfile
                process_dockerfile(file_path)
                print(f"Updated {file_path}")
    else:
        print(f"Directory {tekton_dir} does not exist in {repo}")
