import subprocess

def get_current_branch(directory):
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=directory,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        print(f"Error getting current branch: {result.stderr}")
        return None

def get_committed_and_pushed_files(directory, folder):
    current_branch = get_current_branch(directory)
    if not current_branch:
        return []

    subprocess.run(["git", "fetch"], cwd=directory, capture_output=True, text=True, check=True)

    result = subprocess.run(
        ["git", "diff", "--name-only", f"main...{current_branch}", "--", folder],
        cwd=directory,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return result.stdout.strip().splitlines()
    else:
        print(f"Error getting committed and pushed files: {result.stderr}")
        return []