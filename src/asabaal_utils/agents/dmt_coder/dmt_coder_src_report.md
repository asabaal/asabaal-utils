FlowScope Graph Analysis Report
========================================

Basic Statistics:
  Total Functions: 21
  Total Calls: 0
  Graph Density: 0.0000
  Strongly Connected: False
  Weak Components: 21

Entry Points (21):
  - validator.validate_spec
  - schema._is_list
  - schema._is_dict
  - schema._is_str
  - schema.validate_top
  - schema.validate_function
  - schema.validate_doc
  - renderer._ensure_dir
  - renderer._summarize_io
  - renderer._block
  ... and 11 more

Leaf Functions (21):
  - validator.validate_spec
  - schema._is_list
  - schema._is_dict
  - schema._is_str
  - schema.validate_top
  - schema.validate_function
  - schema.validate_doc
  - renderer._ensure_dir
  - renderer._summarize_io
  - renderer._block
  ... and 11 more

Most Called Functions (Top 10):
  validator.validate_spec: 0 calls
  schema._is_list: 0 calls
  schema._is_dict: 0 calls
  schema._is_str: 0 calls
  schema.validate_top: 0 calls
  schema.validate_function: 0 calls
  schema.validate_doc: 0 calls
  renderer._ensure_dir: 0 calls
  renderer._summarize_io: 0 calls
  renderer._block: 0 calls

Functions with Most Calls (Top 10):
  validator.validate_spec: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  schema._is_list: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  schema._is_dict: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  schema._is_str: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  schema.validate_top: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  schema.validate_function: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  schema.validate_doc: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  renderer._ensure_dir: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  renderer._summarize_io: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
  renderer._block: [('validator.validate_spec', 0), ('schema._is_list', 0), ('schema._is_dict', 0), ('schema._is_str', 0), ('schema.validate_top', 0), ('schema.validate_function', 0), ('schema.validate_doc', 0), ('renderer._ensure_dir', 0), ('renderer._summarize_io', 0), ('renderer._block', 0), ('renderer._behavior_lines', 0), ('renderer._validation_lines', 0), ('renderer.render_plan_to_disk', 0), ('planner._norm_pkg', 0), ('planner.build_plan', 0), ('runner.check', 0), ('runner.plan', 0), ('runner.generate', 0), ('cli.main', 0), ('parser._sig_parts', 0), ('parser.load_spec', 0)] outgoing calls
