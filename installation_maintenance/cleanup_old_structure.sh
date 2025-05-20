#!/bin/bash
# Cleanup script to remove duplicate files from root directory after transition

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Files to keep in root
KEEP_FILES=(
  ".gitignore"
  "README.md"
  "README_NEW_STRUCTURE.md"
  "MIGRATION_GUIDE.md"
  "requirements.txt"
  ".git"
  "logs"
  "webull_token.json"  # Keep token files in root for now
  "did.bin"            # Keep device ID file in root for now
  ".watchdog.pid"      # Keep PID file in root for now
  "com.webull.killswitch.plist"
  "WebullNotifier.app"
)

# Function to check if we should keep a file
should_keep() {
  local file="$1"
  local base_name=$(basename "$file")
  
  # Check if it's a directory we created for organization
  if [[ -d "$file" && "$base_name" =~ ^(core_monitoring|watchdog_components|authentication|installation_maintenance|system_tools|applescripts|testing_utilities|debugging_tools)$ ]]; then
    return 0 # True - keep
  fi
  
  # Check if it's in the keep list
  for keep in "${KEEP_FILES[@]}"; do
    if [[ "$base_name" == "$keep" || "$base_name" == ".$keep" ]]; then
      return 0 # True - keep
    fi
  done
  
  # Also keep any hidden files that don't belong to us
  if [[ "$base_name" == .* && "$base_name" != ".watchdog.pid" && "$base_name" != ".gitignore" ]]; then
    return 0 # True - keep
  fi
  
  return 1 # False - don't keep
}

# Prompt for confirmation
read -p "This will remove the duplicate files from the root directory after transition to the new structure. Are you sure? (y/n) " answer
if [[ ! "$answer" =~ ^[Yy]$ ]]; then
  echo "Aborting."
  exit 1
fi

echo "Cleaning up duplicated files in root directory..."

# Check each file/directory in the root
for file in "$ROOT_DIR"/*; do
  if should_keep "$file"; then
    echo "Keeping: $(basename "$file")"
    continue
  else
    # Check if it's a duplicate (exists in one of our organized directories)
    base_name=$(basename "$file")
    found=0
    
    for dir in core_monitoring watchdog_components authentication installation_maintenance system_tools applescripts testing_utilities debugging_tools; do
      if [[ -f "$ROOT_DIR/$dir/$base_name" ]]; then
        found=1
        break
      fi
    done
    
    if [[ $found -eq 1 ]]; then
      echo "Removing duplicate: $base_name"
      rm -f "$file"
    else
      # If it's not in our directories but not in keep list, ask what to do
      read -p "File $base_name is not in the new directory structure. Remove? (y/n/q) " choice
      case "$choice" in
        [Yy]) rm -f "$file"; echo "Removed: $base_name" ;;
        [Qq]) echo "Aborting."; exit 0 ;;
        *) echo "Keeping: $base_name" ;;
      esac
    fi
  fi
done

echo "Cleanup complete!"
echo "Note: If there are any issues, you can restore files from Git or rerun the organization script."
exit 0 