import sys
import subprocess
import json
import os
from collections import defaultdict

# For now, we use a local mock password store.
# In the future, this will be replaced with the real path.
PASSWORD_STORE_PATH = os.path.join(os.path.dirname(__file__), '.password-store')

def list_secrets():
    """
    Finds all .gpg files, parses them into namespaces and resources,
    and returns them in the specified JSON format.
    """
    try:
        # The spec explicitly requires using `find` to locate .gpg files.
        cmd = ["find", PASSWORD_STORE_PATH, "-type", "f", "-name", "*.gpg"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        paths = result.stdout.strip().split('\n')
        
        namespaces_map = defaultdict(list)
        
        base_path = os.path.join(PASSWORD_STORE_PATH, '')

        for path in paths:
            if not path:
                continue

            relative_path = path.replace(base_path, '', 1)
            resource_path = relative_path.replace('.gpg', '', 1)
            
            if os.path.sep not in resource_path:
                continue
                
            parts = resource_path.split(os.path.sep, 1)
            namespace = parts[0]
            resource = parts[1]
            
            namespaces_map[namespace].append(resource)

        dir_cmd = ["find", PASSWORD_STORE_PATH, "-mindepth", "1", "-maxdepth", "1", "-type", "d"]
        dir_result = subprocess.run(dir_cmd, capture_output=True, text=True, check=True)
        dir_paths = dir_result.stdout.strip().split('\n')

        for dir_path in dir_paths:
            if not dir_path:
                continue
            namespace = os.path.basename(dir_path)
            if namespace not in namespaces_map:
                namespaces_map[namespace] = []

        output_json = [
            {"namespace": ns, "resources": res} for ns, res in sorted(namespaces_map.items())
        ]
        
        print(json.dumps(output_json, indent=2))

    except subprocess.CalledProcessError as e:
        error_output = {
            "status": "error",
            "message": "Failed to execute find command.",
            "stderr": e.stderr
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_output = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        sys.exit(1)

def show_secret():
    """
    Reads a JSON object from stdin specifying the secret to show,
    retrieves its content, parses it, and prints the resulting JSON.
    """
    try:
        request_data = json.load(sys.stdin)
        namespace = request_data.get("namespace")
        resource = request_data.get("resource")

        if not namespace or not resource:
            raise ValueError("Request must include 'namespace' and 'resource'.")

        resource_path = os.path.join(namespace, resource)
        secret_file_path = os.path.join(PASSWORD_STORE_PATH, f"{resource_path}.gpg")

        if not os.path.exists(secret_file_path):
            raise FileNotFoundError(f"Secret '{resource_path}' not found.")

        # In this mock version, we read the file directly.
        with open(secret_file_path, 'r') as f:
            content = f.read().strip()
        
        lines = content.split('\n')
        if not lines or not lines[0]:
            raise ValueError("Secret is empty or invalid.")

        secret = lines[0]
        metadata = {}
        if len(lines) > 1:
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        
        output_json = {"secret": secret, **metadata}
        print(json.dumps(output_json, indent=2))

    except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
        error_output = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_output = {
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        sys.exit(1)

def main():
    """
    Main function to handle command-line arguments.
    """
    if len(sys.argv) < 2:
        print("Usage: python pass_backend.py [list|show|create|edit|delete]", file=sys.stderr)
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "list":
        list_secrets()
    elif command == "show":
        show_secret()
    else:
        print(f"Command '{command}' not implemented yet.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()