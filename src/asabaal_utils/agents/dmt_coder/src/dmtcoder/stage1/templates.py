
CODE_STUB = '''\"\"\"AUTO-GENERATED STUB
Function: {function_name}
ID: {function_id}
IO: {io_summary}

Behavior (intended):
{behavior_block}
\"\"\"

def {function_name}(*args, **kwargs):
    \"\"\"TODO implement function logic.\"\"\"
    raise NotImplementedError(\"Implement {function_name}\")
'''

TEST_STUB = '''# AUTO-GENERATED TEST STUB for {function_name}
import pytest

# Validation intentions derived from spec:
{validation_block}

def test_{function_name}_todo():
    # TODO write concrete tests to satisfy validation intentions above
    assert True
'''

TEACH_STUB = '''# AUTO-GENERATED TEACH SCRIPT for {function_name}
# Lesson: {lesson_name}
# Expected artifacts:
{expects_block}

def run():
    # TODO import your function and produce expected artifacts deterministically
    # Make sure to save artifacts to the declared paths
    pass

if __name__ == \"__main__\":
    run()
'''

DOC_STUB = '''# {function_name}\n\nThis page documents `{function_name}` and links to its teaching artifacts.\n\n- Teaching lesson: {lesson_hint}\n- Expected artifacts:\n{expects_block}\n'''
