import networkx as nx
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict


def get_graph_stats(graph: nx.DiGraph) -> Dict[str, Any]:
    """Calculate basic statistics about the call graph.
    
    Args:
        graph: NetworkX DiGraph representing function calls
        
    Returns:
        Dictionary containing graph statistics
    """
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "is_strongly_connected": nx.is_strongly_connected(graph),
        "weakly_connected_components": nx.number_weakly_connected_components(graph),
        "average_clustering": nx.average_clustering(graph.to_undirected()),
    }


def get_function_metrics(graph: nx.DiGraph) -> Dict[str, Dict[str, Any]]:
    """Calculate metrics for each function in the graph.
    
    Args:
        graph: NetworkX DiGraph representing function calls
        
    Returns:
        Dictionary mapping function names to their metrics
    """
    metrics = {}
    
    for node in graph.nodes():
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)
        
        # Calculate centrality measures
        try:
            betweenness = nx.betweenness_centrality(graph)[node]
            closeness = nx.closeness_centrality(graph)[node]
        except:
            betweenness = 0.0
            closeness = 0.0
        
        metrics[node] = {
            "in_degree": in_degree,  # Number of functions calling this function
            "out_degree": out_degree,  # Number of functions this function calls
            "betweenness_centrality": betweenness,
            "closeness_centrality": closeness,
            "is_leaf": out_degree == 0,  # Function that doesn't call others
            "is_root": in_degree == 0,   # Function that isn't called by others
        }
    
    return metrics


def find_entry_points(graph: nx.DiGraph) -> List[str]:
    """Find entry points (functions with no incoming edges).
    
    Args:
        graph: NetworkX DiGraph representing function calls
        
    Returns:
        List of function names that are entry points
    """
    return [node for node in graph.nodes() if graph.in_degree(node) == 0]


def find_leaf_functions(graph: nx.DiGraph) -> List[str]:
    """Find leaf functions (functions with no outgoing edges).
    
    Args:
        graph: NetworkX DiGraph representing function calls
        
    Returns:
        List of function names that are leaf functions
    """
    return [node for node in graph.nodes() if graph.out_degree(node) == 0]


def get_call_chains(graph: nx.DiGraph, start_func: str, max_depth: int = 10) -> List[List[str]]:
    """Get all call chains starting from a given function.
    
    Args:
        graph: NetworkX DiGraph representing function calls
        start_func: Starting function name
        max_depth: Maximum depth to explore
        
    Returns:
        List of call chains (each chain is a list of function names)
    """
    chains = []
    
    def dfs(current: str, path: List[str], depth: int):
        if depth >= max_depth:
            chains.append(path.copy())
            return
            
        successors = list(graph.successors(current))
        if not successors:
            chains.append(path.copy())
            return
            
        for successor in successors:
            path.append(successor)
            dfs(successor, path, depth + 1)
            path.pop()
    
    if start_func in graph.nodes():
        dfs(start_func, [start_func], 0)
    
    return chains


def get_module_summary(graph: nx.DiGraph) -> Dict[str, Dict[str, Any]]:
    """Get summary statistics grouped by module.
    
    Args:
        graph: NetworkX DiGraph representing function calls
        
    Returns:
        Dictionary mapping module names to their statistics
    """
    module_stats = defaultdict(lambda: {
        "functions": [],
        "internal_calls": 0,
        "external_calls": 0,
        "incoming_calls": 0,
        "outgoing_calls": 0
    })
    
    # Group functions by module
    for node in graph.nodes():
        if "." in node:
            module = node.split(".")[0]
            functions_list = module_stats[module]["functions"]
            if isinstance(functions_list, list):
                functions_list.append(node)
    
    # Analyze calls
    for edge in graph.edges():
        source, target = edge
        
        if "." in source and "." in target:
            source_module = source.split(".")[0]
            target_module = target.split(".")[0]
            
            if source_module == target_module:
                internal_calls = module_stats[source_module]["internal_calls"]
                module_stats[source_module]["internal_calls"] = (internal_calls + 1) if isinstance(internal_calls, int) else 1
            else:
                external_calls = module_stats[source_module]["external_calls"]
                module_stats[source_module]["external_calls"] = (external_calls + 1) if isinstance(external_calls, int) else 1
                
                incoming_calls = module_stats[target_module]["incoming_calls"]
                module_stats[target_module]["incoming_calls"] = (incoming_calls + 1) if isinstance(incoming_calls, int) else 1
    
    # Calculate totals
    for module, stats in module_stats.items():
        functions = stats["functions"]
        stats["function_count"] = len(functions) if isinstance(functions, list) else 0
        internal_calls = stats["internal_calls"] if isinstance(stats["internal_calls"], int) else 0
        external_calls = stats["external_calls"] if isinstance(stats["external_calls"], int) else 0
        stats["total_outgoing"] = internal_calls + external_calls
    
    return dict(module_stats)


def detect_cycles(graph: nx.DiGraph) -> List[List[str]]:
    """Detect cycles in the call graph.
    
    Args:
        graph: NetworkX DiGraph representing function calls
        
    Returns:
        List of cycles (each cycle is a list of function names)
    """
    try:
        cycles = list(nx.simple_cycles(graph))
        return cycles
    except:
        return []


def get_critical_path(graph: nx.DiGraph) -> List[str]:
    """Find the critical path (longest path) in the DAG portion of the graph.
    
    Args:
        graph: NetworkX DiGraph representing function calls
        
    Returns:
        List of function names representing the critical path
    """
    # Create a copy and remove cycles for longest path analysis
    try:
        dag = nx.DiGraph()
        dag.add_nodes_from(graph.nodes(data=True))
        
        # Add only edges that don't create cycles
        for edge in graph.edges():
            temp_dag = dag.copy()
            temp_dag.add_edge(*edge)
            if nx.is_directed_acyclic_graph(temp_dag):
                dag = temp_dag
        
        if nx.is_directed_acyclic_graph(dag):
            longest_path = nx.dag_longest_path(dag)
            return longest_path
    except:
        pass
    
    return []


def filter_graph_by_module(graph: nx.DiGraph, module: str) -> nx.DiGraph:
    """Filter graph to include only functions from a specific module.
    
    Args:
        graph: NetworkX DiGraph representing function calls
        module: Module name to filter by
        
    Returns:
        Filtered NetworkX DiGraph
    """
    filtered_nodes = [node for node in graph.nodes() if node.startswith(f"{module}.")]
    subgraph = graph.subgraph(filtered_nodes)
    return nx.DiGraph(subgraph)


def merge_graphs(graphs: List[nx.DiGraph]) -> nx.DiGraph:
    """Merge multiple call graphs into one.
    
    Args:
        graphs: List of NetworkX DiGraphs to merge
        
    Returns:
        Merged NetworkX DiGraph
    """
    if not graphs:
        return nx.DiGraph()
    
    merged = nx.DiGraph()
    
    for graph in graphs:
        merged.add_nodes_from(graph.nodes(data=True))
        merged.add_edges_from(graph.edges(data=True))
    
    return merged