import os
import subprocess
import json
import sys

def get_backend_command(command_name):
    python_executable = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
    backend_script = os.path.join(os.path.dirname(__file__), 'pass_backend.py')
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
        cmd = get_backend_command("create") # 'create' uses 'pass insert' which handles updates
        input_data = json.dumps({"namespace": namespace, "resource": resource, "content": content})
        result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error saving secret to backend: {e}", file=sys.stderr)
        return {"status": "error", "message": str(e)}
