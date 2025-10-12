import sys
import subprocess
import json
import os
from collections import defaultdict

# --- CONFIGURATION ---
# Respect the PASSWORD_STORE_DIR environment variable, just like `pass` does.
store_dir_from_env = os.environ.get('PASSWORD_STORE_DIR')
if store_dir_from_env:
    PASSWORD_STORE_PATH = os.path.expanduser(store_dir_from_env)
else:
    PASSWORD_STORE_PATH = os.path.expanduser('~/.password-store')

# --- HELPER FUNCTIONS ---

def handle_error(e, status_msg="error"):
    """Prints a JSON error message to stderr and exits."""
    message = e.stderr.strip() if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
    print(json.dumps({"status": status_msg, "message": message}, indent=2), file=sys.stderr)
    sys.exit(1)

# --- COMMAND IMPLEMENTATIONS ---

def list_secrets():
    """Lists secrets by finding .gpg files in the real password store."""
    try:
        # FIX: Handle case where password store does not exist.
        if not os.path.isdir(PASSWORD_STORE_PATH):
            print(json.dumps([])) # Return empty list if store is not initialized
            return

        # Add -L to follow symbolic links, as the password store can be a symlink.
        cmd = ["find", "-L", PASSWORD_STORE_PATH, "-type", "f", "-name", "*.gpg"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        paths = result.stdout.strip().split('\n')
        
        namespaces_map = defaultdict(list)
        base_path = os.path.join(PASSWORD_STORE_PATH, '')

        for path in paths:
            if not path: continue
            relative_path = path.replace(base_path, '', 1)
            resource_path = relative_path.replace('.gpg', '', 1)
            if os.path.sep not in resource_path: continue
            parts = resource_path.split(os.path.sep, 1)
            namespaces_map[parts[0]].append(parts[1])

        dir_cmd = ["find", "-L", PASSWORD_STORE_PATH, "-mindepth", "1", "-maxdepth", "1", "-type", "d"]
        dir_result = subprocess.run(dir_cmd, capture_output=True, text=True, check=True)

        for dir_path in dir_result.stdout.strip().split('\n'):
            if not dir_path: continue
            namespace = os.path.basename(dir_path)
            if namespace not in namespaces_map:
                namespaces_map[namespace] = []

        output_json = [{"namespace": ns, "resources": res} for ns, res in sorted(namespaces_map.items())]
        print(json.dumps(output_json, indent=2))

    except Exception as e:
        handle_error(e)

def show_secret():
    """Shows a secret by calling `pass show`."""
    try:
        data = json.load(sys.stdin)
        secret_path = os.path.join(data["namespace"], data["resource"])
        result = subprocess.run(["pass", "show", secret_path], capture_output=True, text=True, check=True)
        content = result.stdout.strip()
        lines = content.split('\n')
        secret = lines[0]
        metadata = {k.strip(): v.strip() for line in lines[1:] if ':' in line for k, v in [line.split(':', 1)]}
        print(json.dumps({"secret": secret, **metadata}, indent=2))
    except Exception as e:
        handle_error(e)

def create_secret():
    """Creates a secret by calling `pass insert`."""
    try:
        data = json.load(sys.stdin)
        secret_path = os.path.join(data["namespace"], data["resource"])
        if '/' in data["resource"] or '\'' in data["resource"]:
            raise ValueError("Resource name cannot contain slashes.")
        subprocess.run(["pass", "insert", "--multiline", secret_path], input=data["content"], text=True, check=True)
        print(json.dumps({"status": "success", "path": secret_path}, indent=2))
    except Exception as e:
        handle_error(e)

def edit_secret():
    """Edits a secret by calling `pass edit`."""
    try:
        data = json.load(sys.stdin)
        secret_path = os.path.join(data["namespace"], data["resource"])
        subprocess.run(["pass", "edit", secret_path], check=True)
        print(json.dumps({"status": "success", "message": f"Successfully launched editor for '{secret_path}'"}, indent=2))
    except Exception as e:
        handle_error(e)

def delete_secret():
    """Deletes a secret by calling `pass rm --force`."""
    try:
        data = json.load(sys.stdin)
        secret_path = os.path.join(data["namespace"], data["resource"])
        subprocess.run(["pass", "rm", "--force", secret_path], check=True)
        print(json.dumps({"status": "success", "message": f"Secret '{secret_path}' deleted." }, indent=2))
    except Exception as e:
        handle_error(e)

def main():
    """Main command router."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} [list|show|create|edit|delete]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    actions = {
        "list": list_secrets,
        "show": show_secret,
        "create": create_secret,
        "edit": edit_secret,
        "delete": delete_secret,
    }
    if command in actions:
        actions[command]()
    else:
        print(f"Command '{command}' not implemented yet.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()