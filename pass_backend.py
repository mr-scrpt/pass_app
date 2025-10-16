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
        
        # The first line is always the secret
        secret_data = [["secret", lines[0]]]
        
        # Subsequent lines are key-value pairs
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                secret_data.append([key.strip(), value.strip()])
            # You could add an else here to handle non-kv lines if needed

        print(json.dumps(secret_data, indent=2))
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

def git_push():
    """Push local changes to remote git repository."""
    try:
        result = subprocess.run(["pass", "git", "push"], capture_output=True, text=True, check=True)
        output = result.stdout.strip() + result.stderr.strip()
        print(json.dumps({"status": "success", "message": "Successfully pushed to remote.", "output": output}, indent=2))
    except subprocess.CalledProcessError as e:
        # Check if it's just "Everything up-to-date"
        if "up-to-date" in e.stderr.lower() or "up-to-date" in e.stdout.lower():
            print(json.dumps({"status": "success", "message": "Already up to date.", "output": e.stderr + e.stdout}, indent=2))
        else:
            handle_error(e)
    except Exception as e:
        handle_error(e)

def git_pull():
    """Pull changes from remote git repository."""
    try:
        result = subprocess.run(["pass", "git", "pull", "--rebase"], capture_output=True, text=True, check=True)
        output = result.stdout.strip() + result.stderr.strip()
        print(json.dumps({"status": "success", "message": "Successfully pulled from remote.", "output": output}, indent=2))
    except subprocess.CalledProcessError as e:
        # Check if it's just "Already up to date"
        if "up to date" in e.stderr.lower() or "up to date" in e.stdout.lower():
            print(json.dumps({"status": "success", "message": "Already up to date.", "output": e.stderr + e.stdout}, indent=2))
        else:
            handle_error(e)
    except Exception as e:
        handle_error(e)

def git_status():
    """Check git status of password store."""
    try:
        # Check if there are uncommitted changes
        result = subprocess.run(["pass", "git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        has_local_changes = bool(result.stdout.strip())
        
        # Check if local is ahead/behind remote
        fetch_result = subprocess.run(["pass", "git", "fetch"], capture_output=True, text=True)
        rev_list_result = subprocess.run(
            ["pass", "git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
            capture_output=True, text=True
        )
        
        ahead = 0
        behind = 0
        has_remote = True
        
        if rev_list_result.returncode == 0:
            counts = rev_list_result.stdout.strip().split()
            if len(counts) == 2:
                ahead = int(counts[0])
                behind = int(counts[1])
        else:
            # No remote configured or can't reach it
            has_remote = False
        
        status_info = {
            "status": "success",
            "has_local_changes": has_local_changes,
            "ahead": ahead,
            "behind": behind,
            "has_remote": has_remote,
            "needs_push": ahead > 0 or has_local_changes,
            "needs_pull": behind > 0
        }
        
        print(json.dumps(status_info, indent=2))
    except Exception as e:
        # If git is not configured, return a neutral status
        print(json.dumps({
            "status": "success",
            "has_local_changes": False,
            "ahead": 0,
            "behind": 0,
            "has_remote": False,
            "needs_push": False,
            "needs_pull": False,
            "error": str(e)
        }, indent=2))

def main():
    """Main command router."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} [list|show|create|edit|delete|git-push|git-pull|git-status]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    actions = {
        "list": list_secrets,
        "show": show_secret,
        "create": create_secret,
        "edit": edit_secret,
        "delete": delete_secret,
        "git-push": git_push,
        "git-pull": git_pull,
        "git-status": git_status,
    }
    if command in actions:
        actions[command]()
    else:
        print(f"Command '{command}' not implemented yet.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()