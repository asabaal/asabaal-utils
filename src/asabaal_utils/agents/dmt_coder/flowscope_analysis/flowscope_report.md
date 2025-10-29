FlowScope Graph Analysis Report
========================================

Basic Statistics:
  Total Functions: 25
  Total Calls: 13
  Graph Density: 0.0217
  Strongly Connected: False
  Weak Components: 13

Entry Points (13):
  - test_stage1_planner.test_plan_shapes
  - test_stage1_validator.test_validator_catches_missing
  - test_stage1_integration.test_integration_minimal
  - test_stage1_parser.test_sig_parts
  - validator.validate_spec
  - schema.validate_doc
  - renderer.render_plan_to_disk
  - planner.build_plan
  - runner.check
  - runner.plan
  ... and 3 more

Leaf Functions (19):
  - test_stage1_planner.test_plan_shapes
  - test_stage1_validator.test_validator_catches_missing
  - test_stage1_integration.test_integration_minimal
  - test_stage1_parser.test_sig_parts
  - validator.validate_spec
  - schema._is_list
  - schema._is_dict
  - schema._is_str
  - renderer._ensure_dir
  - renderer._summarize_io
  ... and 9 more

Most Called Functions (Top 10):
  schema._is_list: 2 calls
  schema._is_dict: 1 calls
  schema._is_str: 1 calls
  schema.validate_top: 1 calls
  schema.validate_function: 1 calls
  renderer._ensure_dir: 1 calls
  renderer._summarize_io: 1 calls
  renderer._block: 1 calls
  renderer._behavior_lines: 1 calls
  renderer._validation_lines: 1 calls

Functions with Most Calls (Top 10):
  test_stage1_planner.test_plan_shapes: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  test_stage1_validator.test_validator_catches_missing: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  test_stage1_integration.test_integration_minimal: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  test_stage1_parser.test_sig_parts: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  validator.validate_spec: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema._is_list: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema._is_dict: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema._is_str: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema.validate_top: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema.validate_function: [('test_stage1_planner.test_plan_shapes', 0), ('test_stage1_validator.test_validator_catches_missing', 0), ('test_stage1_integration.test_integration_minimal', 0), ('test_stage1_parser.test_sig_parts', 0), ('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
