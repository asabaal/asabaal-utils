#!/usr/bin/env python3
import argparse
import sys

parser = argparse.ArgumentParser(description='Test argument parsing')
parser.add_argument('--repo', dest='repo_path', default='.')
parser.add_argument('--from', dest='from_branch', default='main')
parser.add_argument('--to', dest='to_branch', default=None)
parser.add_argument('--output', dest='output_file')

args = parser.parse_args()

print(f"Repo: {args.repo_path}")
print(f"From: {args.from_branch}")
print(f"To: {args.to_branch}")
print(f"Output: {args.output_file}")
print(f"Args: {sys.argv}")