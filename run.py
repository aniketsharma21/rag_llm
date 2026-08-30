#!/usr/bin/env python
import os
import sys
import subprocess
import threading
import time
import socket
import platform
import signal

# ANSI Color Codes
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_log(prefix, color, message):
    for line in message.rstrip().split('\n'):
        print(f"{color}{prefix}{RESET} {line}")

def stream_output(pipe, prefix, color):
    try:
        # Read line by line from the pipe
        for line in iter(pipe.readline, ''):
            if not line:
                break
            print_log(prefix, color, line.strip())
    except Exception:
        pass

import urllib.request

def wait_for_backend(url="http://127.0.0.1:8000/", timeout=120):
    start_time = time.time()
    last_print = 0
    while True:
        try:
            # We use urllib.request to make a quick HTTP GET request
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
            
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return False
            
        # Print a progress indicator every 10 seconds
        if int(elapsed) // 10 > last_print:
            last_print = int(elapsed) // 10
            print(f"{YELLOW}[Launcher] Still waiting for backend to initialize... ({int(elapsed)}s elapsed. Local HuggingFace/PyTorch models can take up to 1-2 minutes to load.){RESET}")
            
        time.sleep(0.5)

def kill_process_tree(process):
    if not process:
        return
    pid = process.pid
    if platform.system() == "Windows":
        try:
            # Forcefully terminate the process and all its sub-processes
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
        try:
            # Send SIGTERM to the process group
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                process.terminate()
            except Exception:
                pass

def find_python_executable():
    # If a virtual env or conda env is actively running this launcher script, use it!
    is_active_venv = (sys.prefix != sys.base_prefix) or (os.environ.get("CONDA_DEFAULT_ENV") and os.environ.get("CONDA_DEFAULT_ENV") != "base")
    if is_active_venv:
        return sys.executable

    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Check for local virtual environments in the root
    for venv_name in ["venv", ".venv"]:
        path = os.path.join(root_dir, venv_name, "Scripts", "python.exe") if platform.system() == "Windows" else os.path.join(root_dir, venv_name, "bin", "python")
        if os.path.exists(path):
            return path
            
    # 2. Check if the conda environment 'dl_gpu_min' exists and use its Python interpreter
    try:
        conda_cmd = "conda.bat" if platform.system() == "Windows" else "conda"
        result = subprocess.run(
            [conda_cmd, "env", "list", "--json"], 
            capture_output=True, 
            text=True, 
            shell=(platform.system() == "Windows")
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            envs = data.get("envs", [])
            for env in envs:
                if os.path.basename(env) == "dl_gpu_min":
                    conda_python = os.path.join(env, "python.exe") if platform.system() == "Windows" else os.path.join(env, "bin", "python")
                    if os.path.exists(conda_python):
                        return conda_python
    except Exception:
        pass

    return sys.executable

def run_app():
    print(f"{GREEN}============================================")
    print(f"🚀 Starting RAG LLM Application Launcher 🚀")
    print(f"============================================{RESET}\n")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    # Ensure python output is unbuffered so logs stream in real-time
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["FORCE_COLOR"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    # 1. Check and install frontend dependencies if node_modules is missing
    node_modules_dir = os.path.join(frontend_dir, "node_modules")
    if not os.path.exists(node_modules_dir):
        print(f"{YELLOW}[Launcher] 'node_modules' not found in frontend directory.{RESET}")
        print(f"{YELLOW}[Launcher] Running 'npm install' in frontend...{RESET}")
        
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        try:
            subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True, shell=(platform.system() == "Windows"))
            print(f"{GREEN}[Launcher] 'npm install' completed successfully.{RESET}")
        except Exception as e:
            print(f"{RED}[Launcher] Failed to run 'npm install'. Please run it manually inside the 'frontend' folder.{RESET}")
            print(e)
            sys.exit(1)

    backend_process = None
    frontend_process = None

    try:
        # Determine the correct Python interpreter
        python_exe = find_python_executable()
        
        # Log which environment we are using
        if "dl_gpu_min" in python_exe:
            print(f"{GREEN}[Launcher] Detected 'dl_gpu_min' conda environment. Using: {python_exe}{RESET}")
        elif "venv" in python_exe or ".venv" in python_exe:
            print(f"{GREEN}[Launcher] Detected local virtual environment. Using: {python_exe}{RESET}")
        else:
            print(f"{YELLOW}[Launcher] Using default/active Python environment: {python_exe}{RESET}")

        # 2. Start FastAPI Backend
        print(f"{BLUE}[Launcher] Starting FastAPI backend...{RESET}")
        backend_args = [python_exe, "main.py"]
        
        popen_kwargs = {}
        if platform.system() != "Windows":
            popen_kwargs["preexec_fn"] = os.setsid
            
        backend_process = subprocess.Popen(
            backend_args,
            cwd=root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=env,
            **popen_kwargs
        )

        # Stream backend logs in a background thread
        backend_thread = threading.Thread(
            target=stream_output, 
            args=(backend_process.stdout, "[Backend]", BLUE),
            daemon=True
        )
        backend_thread.start()

        # 3. Wait for backend to be ready on port 8000
        print(f"{BLUE}[Launcher] Waiting for backend to start responding at http://127.0.0.1:8000/...{RESET}")
        print(f"{YELLOW}[Launcher] Note: This may take up to 2 minutes on first run as AI/RAG models (embeddings and cross-encoders) load into memory.{RESET}")
        if wait_for_backend("http://127.0.0.1:8000/", timeout=120):
            print(f"{GREEN}[Launcher] Backend is ready and responding!{RESET}")
        else:
            print(f"{RED}[Launcher] Backend failed to start and respond at http://127.0.0.1:8000/ within 120 seconds.{RESET}")
            kill_process_tree(backend_process)
            sys.exit(1)

        # 4. Start React Frontend
        print(f"{GREEN}[Launcher] Starting React frontend dev server...{RESET}")
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        frontend_args = [npm_cmd, "start"]
        
        frontend_process = subprocess.Popen(
            frontend_args,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=env,
            shell=(platform.system() == "Windows"),
            **popen_kwargs
        )

        # Stream frontend logs in a background thread
        frontend_thread = threading.Thread(
            target=stream_output, 
            args=(frontend_process.stdout, "[Frontend]", GREEN),
            daemon=True
        )
        frontend_thread.start()

        print(f"\n{GREEN}============================================")
        print(f"🎉 RAG LLM App is running! 🎉")
        print(f"👉 Backend: http://localhost:8000")
        print(f"👉 Frontend: http://localhost:3000")
        print(f"Press Ctrl+C to stop both servers.")
        print(f"============================================{RESET}\n")

        # Keep launcher running and monitor subprocesses
        while True:
            backend_status = backend_process.poll()
            frontend_status = frontend_process.poll()
            
            if backend_status is not None:
                print(f"{RED}[Launcher] Backend process terminated with status {backend_status}.{RESET}")
                break
            if frontend_status is not None:
                print(f"{RED}[Launcher] Frontend process terminated with status {frontend_status}.{RESET}")
                break
                
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}[Launcher] Shutting down servers...{RESET}")
    finally:
        # Ensure both servers are shut down cleanly
        if backend_process:
            print(f"{BLUE}[Launcher] Stopping backend process...{RESET}")
            kill_process_tree(backend_process)
        if frontend_process:
            print(f"{GREEN}[Launcher] Stopping frontend process...{RESET}")
            kill_process_tree(frontend_process)
        print(f"{YELLOW}[Launcher] Shutdown complete.{RESET}")

if __name__ == "__main__":
    run_app()
