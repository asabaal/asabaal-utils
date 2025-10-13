#!/bin/bash

# Build documentation script for Asabaal Video Utilities

echo "Building documentation for Asabaal Video Utilities..."

# Ensure MkDocs and plugins are installed
pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python

# Handle command-line arguments
WARNINGS_AS_ERRORS=false

for arg in "$@"; do
  case $arg in
    --warnings-as-errors)
      WARNINGS_AS_ERRORS=true
      shift
      ;;
    --serve)
      SERVE=true
      shift
      ;;
    --deploy)
      DEPLOY=true
      shift
      ;;
  esac
done

# Build the documentation
if [ "$WARNINGS_AS_ERRORS" = true ]; then
  echo "Treating warnings as errors..."
  # Use grep to check for warnings and fail if found
  mkdocs build 2>&1 | tee build_output.log
  if grep -q "WARNING" build_output.log; then
    echo "Build failed due to warnings."
    rm build_output.log
    exit 1
  fi
  rm build_output.log
else
  mkdocs build
fi

# Serve locally for testing (optional)
if [ "$SERVE" = true ]; then
    echo "Starting local documentation server..."
    mkdocs serve
fi

# Deploy to GitHub Pages (optional)
if [ "$DEPLOY" = true ]; then
    echo "Deploying documentation to GitHub Pages..."
    mkdocs gh-deploy
fi

echo "Documentation build complete. Find the built site in the 'site' directory."