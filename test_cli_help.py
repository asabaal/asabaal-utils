#!/usr/bin/env python
import argparse
import sys
from src.asabaal_utils.video_processing.cli import extract_clips_cli

# Override the existing argparse to capture help output
class CaptureHelpParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        print("HELP CAPTURED")
        if hasattr(self, '_action_groups'):
            for group in self._action_groups:
                print(f"\nGroup: {group.title}")
                for action in group._group_actions:
                    if action.dest != 'help':
                        print(f"  {action.dest}: {action.help}")

# Replace the original parser temporarily
old_parser = argparse.ArgumentParser
argparse.ArgumentParser = CaptureHelpParser

# Call the CLI function that will create the parser
try:
    sys.argv = ['extract-clips', '--help']
    extract_clips_cli()
except SystemExit:
    pass

# Restore the original parser
argparse.ArgumentParser = old_parser