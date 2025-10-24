#!/bin/bash

echo "Starting Stage 1 test (this may take 5+ minutes)..."
cd /home/asabaal/repos/asabaal-utils
python -m pytest src/asabaal_utils/agents/spec_coder/tests/test_orchestrator.py::TestIntegrationOrchestrator::test_stage1_spec_to_scaffold_success -xvs --tb=short

echo "Stage 1 test completed with exit code: $?"