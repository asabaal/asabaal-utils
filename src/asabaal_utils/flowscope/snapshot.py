import json
import networkx as nx
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def save_graph(graph: nx.DiGraph, path: Path, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Save a NetworkX DiGraph to JSON format.
    
    Args:
        graph: NetworkX DiGraph to save
        path: Output file path
        metadata: Optional metadata to include in the snapshot
    """
    # Prepare graph data
    nodes_data = []
    for node, attrs in graph.nodes(data=True):
        node_data = {"id": node}
        if attrs:
            node_data.update(attrs)
        nodes_data.append(node_data)
    
    edges_data = []
    for source, target, attrs in graph.edges(data=True):
        edge_data = {"source": source, "target": target}
        if attrs:
            edge_data.update(attrs)
        edges_data.append(edge_data)
    
    # Prepare snapshot data
    snapshot = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "metadata": metadata or {},
        "graph": {
            "nodes": nodes_data,
            "edges": edges_data,
            "directed": graph.is_directed(),
            "multigraph": graph.is_multigraph()
        }
    }
    
    # Write to file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)


def load_graph(path: Path) -> nx.DiGraph:
    """Load a NetworkX DiGraph from JSON format.
    
    Args:
        path: Input file path
        
    Returns:
        Loaded NetworkX DiGraph
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the file format is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
    
    # Validate snapshot format
    if "graph" not in snapshot:
        raise ValueError("Invalid snapshot format: missing 'graph' section")
    
    graph_data = snapshot["graph"]
    if "nodes" not in graph_data or "edges" not in graph_data:
        raise ValueError("Invalid snapshot format: missing 'nodes' or 'edges'")
    
    # Create graph
    directed = graph_data.get("directed", True)
    multigraph = graph_data.get("multigraph", False)
    
    if multigraph:
        temp_graph = nx.MultiDiGraph()
    elif directed:
        temp_graph = nx.DiGraph()
    else:
        temp_graph = nx.Graph()
    
    # Add nodes
    for node_data in graph_data["nodes"]:
        node_id = node_data.pop("id")
        temp_graph.add_node(node_id, **node_data)
    
    # Add edges
    for edge_data in graph_data["edges"]:
        source = edge_data.pop("source")
        target = edge_data.pop("target")
        temp_graph.add_edge(source, target, **edge_data)
    
    # Convert to DiGraph if needed
    if not isinstance(temp_graph, nx.DiGraph):
        graph = nx.DiGraph(temp_graph)
    else:
        graph = temp_graph
    
    return graph


def get_snapshot_metadata(path: Path) -> Dict[str, Any]:
    """Get metadata from a snapshot file without loading the full graph.
    
    Args:
        path: Snapshot file path
        
    Returns:
        Dictionary containing metadata
    """
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
    
    return {
        "version": snapshot.get("version"),
        "created_at": snapshot.get("created_at"),
        "metadata": snapshot.get("metadata", {}),
        "node_count": len(snapshot.get("graph", {}).get("nodes", [])),
        "edge_count": len(snapshot.get("graph", {}).get("edges", []))
    }


def compare_snapshots(path1: Path, path2: Path) -> Dict[str, Any]:
    """Compare two snapshot files without loading full graphs.
    
    Args:
        path1: First snapshot file path
        path2: Second snapshot file path
        
    Returns:
        Dictionary containing comparison results
    """
    metadata1 = get_snapshot_metadata(path1)
    metadata2 = get_snapshot_metadata(path2)
    
    return {
        "file1": str(path1),
        "file2": str(path2),
        "created_at_diff": {
            "file1": metadata1["created_at"],
            "file2": metadata2["created_at"]
        },
        "node_count_diff": metadata2["node_count"] - metadata1["node_count"],
        "edge_count_diff": metadata2["edge_count"] - metadata1["edge_count"],
        "metadata_diff": {
            "file1": metadata1["metadata"],
            "file2": metadata2["metadata"]
        }
    }


def create_snapshot_with_context(graph: nx.DiGraph, path: Path, 
                                source_path: Optional[Path] = None,
                                description: Optional[str] = None,
                                tags: Optional[list] = None) -> None:
    """Create a snapshot with additional context information.
    
    Args:
        graph: NetworkX DiGraph to save
        path: Output file path
        source_path: Path to the source code that was analyzed
        description: Description of this snapshot
        tags: List of tags for categorization
    """
    metadata = {
        "description": description,
        "tags": tags or [],
        "source_path": str(source_path) if source_path else None
    }
    
    # Add source path statistics if available
    if source_path and source_path.exists():
        if source_path.is_file():
            metadata["source_stats"] = {
                "type": "file",
                "size": source_path.stat().st_size,
                "modified": source_path.stat().st_mtime
            }
        elif source_path.is_dir():
            py_files = list(source_path.rglob("*.py"))
            metadata["source_stats"] = {
                "type": "directory",
                "python_files": len(py_files),
                "total_size": sum(f.stat().st_size for f in py_files)
            }
    
    save_graph(graph, path, metadata)


def list_snapshots(directory: Path) -> list:
    """List all snapshot files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of snapshot file information
    """
    snapshots = []
    
    for file_path in directory.rglob("*.json"):
        try:
            metadata = get_snapshot_metadata(file_path)
            snapshots.append({
                "path": str(file_path),
                "filename": file_path.name,
                "created_at": metadata["created_at"],
                "node_count": metadata["node_count"],
                "edge_count": metadata["edge_count"],
                "metadata": metadata["metadata"]
            })
        except (json.JSONDecodeError, ValueError):
            # Skip invalid JSON files
            continue
    
    # Sort by creation time (newest first)
    snapshots.sort(key=lambda x: x["created_at"], reverse=True)
    return snapshots