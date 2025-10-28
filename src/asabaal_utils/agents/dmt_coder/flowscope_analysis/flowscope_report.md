FlowScope Graph Analysis Report
========================================

Basic Statistics:
  Total Functions: 21
  Total Calls: 13
  Graph Density: 0.0310
  Strongly Connected: False
  Weak Components: 9

Entry Points (9):
  - validator.validate_spec
  - schema.validate_doc
  - renderer.render_plan_to_disk
  - planner.build_plan
  - runner.check
  - runner.plan
  - runner.generate
  - cli.main
  - parser.load_spec

Leaf Functions (15):
  - validator.validate_spec
  - schema._is_list
  - schema._is_dict
  - schema._is_str
  - renderer._ensure_dir
  - renderer._summarize_io
  - renderer._block
  - renderer._behavior_lines
  - renderer._validation_lines
  - planner._norm_pkg
  ... and 5 more

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
  validator.validate_spec: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema._is_list: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema._is_dict: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema._is_str: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema.validate_top: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema.validate_function: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  schema.validate_doc: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  renderer._ensure_dir: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  renderer._summarize_io: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
  renderer._block: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 1), ('schema.validate_function', 3), ('schema.validate_doc', 2), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 5), ('planner._norm_pkg', 0), ('planner.build_plan', 1), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 1)] outgoing calls
