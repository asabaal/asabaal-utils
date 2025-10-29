FlowScope Graph Analysis Report
========================================

Basic Statistics:
  Total Functions: 4
  Total Calls: 2
  Graph Density: 0.1667
  Strongly Connected: False
  Weak Components: 2

Entry Points (2):
  - math_ops.subtract
  - math_ops.calculator

Leaf Functions (3):
  - math_ops.add
  - math_ops.subtract
  - math_ops.multiply

Most Called Functions (Top 10):
  math_ops.add: 1 calls
  math_ops.multiply: 1 calls
  math_ops.subtract: 0 calls
  math_ops.calculator: 0 calls

Functions with Most Calls (Top 10):
  math_ops.add: [('math_ops.add', 0), ('math_ops.subtract', 0), ('math_ops.calculator', 2), ('math_ops.multiply', 0)] outgoing calls
  math_ops.subtract: [('math_ops.add', 0), ('math_ops.subtract', 0), ('math_ops.calculator', 2), ('math_ops.multiply', 0)] outgoing calls
  math_ops.calculator: [('math_ops.add', 0), ('math_ops.subtract', 0), ('math_ops.calculator', 2), ('math_ops.multiply', 0)] outgoing calls
  math_ops.multiply: [('math_ops.add', 0), ('math_ops.subtract', 0), ('math_ops.calculator', 2), ('math_ops.multiply', 0)] outgoing calls
