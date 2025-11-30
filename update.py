#!/usr/bin/env python3
import subprocess
import sys
import os
import re

def run_command(cmd, check=True):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def get_current_version():
    """Extract version from library.properties"""
    try:
        with open('library.properties', 'r') as f:
            content = f.read()
            match = re.search(r'version=([^\s\n\r]+)', content)
            if match:
                return match.group(1)
    except FileNotFoundError:
        print("Error: library.properties not found")
        sys.exit(1)
    
    print("Error: Could not find version in library.properties")
    sys.exit(1)

def bump_version(version, bump_type='patch'):
    """Bump version number"""
    parts = version.split('.')
    if len(parts) < 3:
        parts.extend(['0'] * (3 - len(parts)))
    
    if bump_type == 'major':
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = '0'
        parts[2] = '0'
    elif bump_type == 'minor':
        parts[1] = str(int(parts[1]) + 1)
        parts[2] = '0'
    else:  # patch
        parts[2] = str(int(parts[2]) + 1)
    
    return '.'.join(parts)

def update_version_in_library_properties(new_version):
    """Update version in library.properties"""
    try:
        with open('library.properties', 'r') as f:
            content = f.read()
        
        new_content = re.sub(
            r'version=[^\s\n\r]+',
            f'version={new_version}',
            content
        )
        
        if new_content != content:
            with open('library.properties', 'w') as f:
                f.write(new_content)
            print(f"✓ Updated library.properties to version {new_version}")
            return True
        else:
            print("⚠ No version found in library.properties to update")
            return False
    except FileNotFoundError:
        print("Error: library.properties not found")
        return False



def get_yes_no(prompt, default=False):
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if response == '':
        return default
    return response.startswith('y')

def commit_and_push_changes(commit_message):
    """Commit changes and push to both upstream and origin"""
    try:
        # Check if there are changes to commit
        status = run_command("git status --porcelain", check=False)
        if not status:
            print("No changes to commit.")
            return False
        
        print("Changes to commit:")
        print(run_command("git status --short", check=False))
        
        # Add and commit
        run_command("git add .")
        run_command(f'git commit -m "{commit_message}"')
        print(f"✓ Committed changes: {commit_message}")
        
        # Push to upstream (acidtech)
        print("Pushing to upstream (acidtech)...")
        run_command("git push upstream main")
        print("✓ Pushed to upstream repository")
        
        # Push to origin (basicmicrosupport)
        print("Pushing to origin (basicmicrosupport)...")
        run_command("git push origin main")
        print("✓ Pushed to origin repository")
        
        return True
        
    except Exception as e:
        print(f"Error in commit/push process: {e}")
        return False

def create_github_release(version, release_notes):
    """Create GitHub release on the basicmicrosupport fork (public repository)"""
    try:
        print("Creating release on basicmicrosupport fork (public repository)...")
        
        tag = f"v{version}"
        
        release_cmd = f'gh release create {tag} --title "Release {version}" --repo basicmicrosupport/basicmicro_arduino'
        
        if release_notes:
            release_cmd += f' --notes "{release_notes}"'
        else:
            release_cmd += ' --generate-notes'
        
        run_command(release_cmd)
        print(f"✓ Created GitHub release {tag} on basicmicrosupport/basicmicro_arduino")
        return True
        
    except Exception as e:
        print(f"Error creating GitHub release: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure GitHub CLI is authenticated: gh auth login")
        print("2. Verify you have access to basicmicrosupport/basicmicro_arduino")
        return False

def setup_remotes():
    """Ensure both upstream (acidtech) and fork (basicmicrosupport) remotes are configured"""
    try:
        UPSTREAM_URL = "https://github.com/acidtech/basicmicro_arduino"
        ORIGIN_URL = "https://github.com/basicmicrosupport/basicmicro_arduino"
        
        remotes_output = run_command("git remote -v", check=False)
        print("Current remotes:")
        print(remotes_output)
        
        has_upstream = 'upstream' in remotes_output
        has_origin = 'origin' in remotes_output
        
        if not has_upstream:
            print(f"\nAdding upstream remote (acidtech): {UPSTREAM_URL}")
            run_command(f"git remote add upstream {UPSTREAM_URL}")
            print("✓ Added upstream remote (acidtech)")
        else:
            print("✓ Upstream remote already configured")
        
        if not has_origin:
            print(f"\nAdding origin remote (basicmicrosupport): {ORIGIN_URL}")
            run_command(f"git remote add origin {ORIGIN_URL}")
            print("✓ Added origin remote (basicmicrosupport)")
        else:
            print("✓ Origin remote already configured")
        
        return True
        
    except Exception as e:
        print(f"Error setting up remotes: {e}")
        return False

def check_arduino_library_format():
    """Check if this looks like a valid Arduino library"""
    required_files = ['library.properties']
    recommended_dirs = ['src', 'examples']
    
    issues = []
    
    for file in required_files:
        if not os.path.exists(file):
            issues.append(f"Missing required file: {file}")
    
    if issues:
        print("⚠ Arduino library format issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        
        if not get_yes_no("Continue anyway?", default=False):
            return False
    
    print("✓ Arduino library format looks good")
    return True

def main():
    print("=== BasicMicro Arduino Library Release Script ===")
    print("This script will:")
    print("- Update version in library.properties")
    print("- Commit and push to upstream (acidtech) and origin (basicmicrosupport)")
    print("- Create a GitHub release on the public repository")
    print()
    
    # Check if we're in a git repository
    try:
        run_command("git rev-parse --git-dir")
    except:
        print("Error: Not in a git repository")
        sys.exit(1)
    
    # Check Arduino library format
    if not check_arduino_library_format():
        sys.exit(1)
    
    # Setup remotes
    print("Setting up repository remotes...")
    setup_remotes()
    
    # Get current version and bump type
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    bump_type = input("Bump type (major/minor/patch) [patch]: ").strip() or 'patch'
    new_version = bump_version(current_version, bump_type)
    
    print(f"New version will be: {new_version}")
    
    if not get_yes_no("Continue with this version?", default=True):
        print("Aborted.")
        sys.exit(0)
    
    # Update version files
    if update_version_in_library_properties(new_version):
        print("✓ Updated library.properties")
    else:
        print("Error: Could not update library.properties")
        sys.exit(1)
    
    # Get commit message
    commit_message = input(f"Commit message [Bump version to {new_version}]: ").strip()
    if not commit_message:
        commit_message = f"Bump version to {new_version}"
    
    # Commit and push changes
    if not commit_and_push_changes(commit_message):
        print("Error: Failed to commit and push changes")
        sys.exit(1)
    
    # Create GitHub release
    release_notes = input("Release notes (optional): ").strip()
    create_github_release(new_version, release_notes)
    
    print("\n" + "="*50)
    print("🎉 Arduino Library Release Completed!")
    print("="*50)
    print(f"✓ Version bumped to {new_version}")
    print("✓ Changes committed and pushed to both repositories")
    print("✓ GitHub release created on basicmicrosupport/basicmicro_arduino")
    print(f"\nArduino library version {new_version} is now available! 🚀")
    print("\nThe library should be available in the Arduino Library Manager shortly.")

if __name__ == "__main__":
    main()