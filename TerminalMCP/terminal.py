import subprocess


def run_command(command: str) -> dict:

    result = subprocess.run(command,
                            shell=True,
                            capture_output=True,
                            text=True)

    return result.__dict__

result = run_command("dir")
print(result["stdout"])