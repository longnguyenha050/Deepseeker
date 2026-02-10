import os
import subprocess

PORT = "4000"
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.yaml")

def run_server():
    if not os.path.exists(config_path):
        print(f"Error: Config file not found'{config_path}'!")
        return

    print(f"🚀 Starting up LiteLLM Proxy...")
    print(f"📂 Config file: {config_path}")
    print(f"Connection port: http://localhost:{PORT}")
    
    # litellm --config config.yaml --port 4000
    cmd = ["litellm", "--config", config_path, "--port", PORT]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")

if __name__ == "__main__":
    run_server()