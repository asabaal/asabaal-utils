#!/usr/bin/env python
import sys

def main():
    # Get the target file from command-line arguments
    if len(sys.argv) < 2:
        print('Usage: {} TARGET_FILE'.format(sys.argv[0]))
        return 1

    target_file = sys.argv[1]

    # Read the file content
    with open(target_file, 'r') as f:
        content = f.read()

    # Apply the fix
    fixed_content = content.replace('print("This function has an issue"', 'print("This function has an issue")')

    # Write the fixed content back to the file
    with open(target_file, 'w') as f:
        f.write(fixed_content)

    return 0

if __name__ == '__main__':
    sys.exit(main())
