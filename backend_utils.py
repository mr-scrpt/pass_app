import json
import os
import subprocess
import sys


def get_backend_command(command_name):
    python_executable = sys.executable
    backend_script = os.path.join(os.path.dirname(__file__), "pass_backend.py")
    return [python_executable, backend_script, command_name]


def get_list_from_backend():
    try:
        cmd = get_backend_command("list")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching list from backend: {e}", file=sys.stderr)
        return None


def get_secret_from_backend(namespace, resource):
    try:
        cmd = get_backend_command("show")
        input_data = json.dumps({"namespace": namespace, "resource": resource})
        result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching secret from backend: {e}", file=sys.stderr)
        return None


def save_secret_to_backend(namespace, resource, content):
    try:
        cmd = get_backend_command("create")  # 'create' uses 'pass insert' which handles updates
        input_data = json.dumps({"namespace": namespace, "resource": resource, "content": content})
        result = subprocess.run(cmd, input=input_data, capture_output=True, text=True)

        if result.returncode == 0:
            return {"status": "success"}
        else:
            # Try to parse JSON from stderr for a more detailed error message
            try:
                error_data = json.loads(result.stderr)
                return {"status": "error", "message": error_data.get("error", result.stderr)}
            except json.JSONDecodeError:
                return {"status": "error", "message": result.stderr or result.stdout}

    except Exception as e:
        print(f"Error saving secret to backend: {e}", file=sys.stderr)
        return {"status": "error", "message": str(e)}


def git_push_to_backend():
    """Push local changes to remote git repository."""
    try:
        cmd = get_backend_command("git-push")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            try:
                error_data = json.loads(result.stderr)
                return {"status": "error", "message": error_data.get("message", result.stderr)}
            except json.JSONDecodeError:
                return {"status": "error", "message": result.stderr or result.stdout}
    except Exception as e:
        print(f"Error pushing to git: {e}", file=sys.stderr)
        return {"status": "error", "message": str(e)}


def git_pull_from_backend():
    """Pull changes from remote git repository."""
    try:
        cmd = get_backend_command("git-pull")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            try:
                error_data = json.loads(result.stderr)
                return {"status": "error", "message": error_data.get("message", result.stderr)}
            except json.JSONDecodeError:
                return {"status": "error", "message": result.stderr or result.stdout}
    except Exception as e:
        print(f"Error pulling from git: {e}", file=sys.stderr)
        return {"status": "error", "message": str(e)}


def git_status_from_backend():
    """Check git status of password store."""
    try:
        cmd = get_backend_command("git-status")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"status": "success", "has_remote": False, "needs_push": False, "needs_pull": False}
    except Exception as e:
        print(f"Error checking git status: {e}", file=sys.stderr)
        return {"status": "success", "has_remote": False, "needs_push": False, "needs_pull": False}
