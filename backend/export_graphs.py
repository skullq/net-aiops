#!/usr/bin/env python3
"""
Net-AIOps Causal Graph Exporter
Exports the current In-Memory / NetworkX Causal Graph to:
1. Neo4j openCypher (.cypher) & CSV format (nodes.csv, edges.csv)
2. ArangoDB Document Collection (CausalNode.json) & Edge Collection (CausalEdge.json)
"""

import os
import json
import csv
from pathlib import Path
import sys

# Ensure backend root is in python path
sys.path.insert(0, str(Path(__file__).parent))
from app.graph_engine import graph_engine

def run_export():
    base_dir = Path("/root/Net-AIOps/exports")
    neo4j_dir = base_dir / "neo4j"
    arango_dir = base_dir / "arangodb"
    neo4j_dir.mkdir(parents=True, exist_ok=True)
    arango_dir.mkdir(parents=True, exist_ok=True)

    G = graph_engine.graph
    nodes = []
    for nid, attrs in G.nodes(data=True):
        nodes.append({
            "id": nid,
            "label": attrs.get("label", nid),
            "type": attrs.get("type", "Symptom"),
            "description": attrs.get("description", ""),
            "details": attrs.get("details", {})
        })

    edges = []
    for src, tgt, attrs in G.edges(data=True):
        edges.append({
            "source": src,
            "target": tgt,
            "relationship": attrs.get("relationship", "leads_to"),
            "description": attrs.get("description", "")
        })

    print(f"Exporting GraphDB: {len(nodes)} Nodes, {len(edges)} Edges")

    # =========================================================================
    # 1. Neo4j openCypher Script Export (.cypher)
    # =========================================================================
    cypher_path = neo4j_dir / "cisco_iosxe_causal_graph.cypher"
    with open(cypher_path, "w", encoding="utf-8") as f:
        f.write("// =====================================================================\n")
        f.write("// Cisco IOS-XE Causal GraphDB - Neo4j openCypher Import Script\n")
        f.write(f"// Generated Nodes: {len(nodes)} | Generated Edges: {len(edges)}\n")
        f.write("// =====================================================================\n\n")
        f.write("// 1. Constraints & Indexes\n")
        f.write("CREATE CONSTRAINT unique_causal_node_id IF NOT EXISTS FOR (n:CausalNode) REQUIRE n.id IS UNIQUE;\n\n")
        f.write("// 2. Nodes Import with Dual Labels (:CausalNode and :NodeType)\n")
        for n in nodes:
            nid = n["id"].replace("'", "\\'")
            nlabel = n["label"].replace("'", "\\'")
            ntype = n["type"].replace("'", "\\'")
            ndesc = n["description"].replace("'", "\\'")
            details_json = json.dumps(n["details"], ensure_ascii=False).replace("'", "\\'")
            cmd = (n["details"].get("command") or n["details"].get("cli_command") or "").replace("'", "\\'")
            layer = (n["details"].get("layer") or "").replace("'", "\\'")
            
            f.write(f"MERGE (n:CausalNode:{ntype} {{id: '{nid}'}}) ")
            f.write(f"ON CREATE SET n.label = '{nlabel}', n.type = '{ntype}', n.description = '{ndesc}', n.command = '{cmd}', n.layer = '{layer}', n.details = '{details_json}';\n")

        f.write("\n// 3. Relationships Import\n")
        for e in edges:
            src = e["source"].replace("'", "\\'")
            tgt = e["target"].replace("'", "\\'")
            rel_raw = e["relationship"] or "leads_to"
            rel_type = rel_raw.upper().replace("-", "_").replace(" ", "_")
            desc = e["description"].replace("'", "\\'")
            f.write(f"MATCH (s:CausalNode {{id: '{src}'}}), (t:CausalNode {{id: '{tgt}'}}) ")
            f.write(f"MERGE (s)-[r:{rel_type} {{relationship: '{rel_raw}', description: '{desc}'}}]->(t);\n")

    # =========================================================================
    # 1.1 Neo4j CSV Import Format (For neo4j-admin database import)
    # =========================================================================
    with open(neo4j_dir / "nodes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id:ID(CausalNode)", "label", "type", "description", "command", ":LABEL"])
        for n in nodes:
            cmd = n["details"].get("command") or n["details"].get("cli_command") or ""
            writer.writerow([n["id"], n["label"], n["type"], n["description"], cmd, f"CausalNode;{n['type']}"])

    with open(neo4j_dir / "edges.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID(CausalNode)", ":END_ID(CausalNode)", ":TYPE", "description"])
        for e in edges:
            rel_type = (e["relationship"] or "leads_to").upper().replace("-", "_").replace(" ", "_")
            writer.writerow([e["source"], e["target"], rel_type, e["description"]])

    # =========================================================================
    # 2. ArangoDB Multi-Model Export
    # =========================================================================
    # 2.1 CausalNode Document Collection
    arango_nodes = []
    for n in nodes:
        arango_nodes.append({
            "_key": n["id"],
            "id": n["id"],
            "label": n["label"],
            "type": n["type"],
            "description": n["description"],
            "details": n["details"]
        })

    with open(arango_dir / "CausalNode.json", "w", encoding="utf-8") as f:
        json.dump(arango_nodes, f, ensure_ascii=False, indent=2)

    # 2.2 CausalEdge Edge Collection
    arango_edges = []
    for idx, e in enumerate(edges):
        arango_edges.append({
            "_key": f"edge_{idx+1}",
            "_from": f"CausalNode/{e['source']}",
            "_to": f"CausalNode/{e['target']}",
            "source": e["source"],
            "target": e["target"],
            "relationship": e["relationship"],
            "description": e["description"]
        })

    with open(arango_dir / "CausalEdge.json", "w", encoding="utf-8") as f:
        json.dump(arango_edges, f, ensure_ascii=False, indent=2)

    # 2.3 ArangoDB Unified Complete Graph JSON
    with open(arango_dir / "causal_graph_complete.json", "w", encoding="utf-8") as f:
        json.dump({
            "collections": {
                "CausalNode": arango_nodes,
                "CausalEdge": arango_edges
            },
            "metadata": {
                "graph_name": "CausalAIOpsGraph",
                "edge_definitions": [{
                    "collection": "CausalEdge",
                    "from": ["CausalNode"],
                    "to": ["CausalNode"]
                }],
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }, f, ensure_ascii=False, indent=2)

    # 2.4 ArangoDB Bash Import Script
    with open(arango_dir / "import_arangodb.sh", "w", encoding="utf-8") as f:
        f.write('#!/usr/bin/env bash\n')
        f.write('# ArangoDB Auto Import Script for Net-AIOps Causal Graph\n')
        f.write('ENDPOINT="${ARANGO_ENDPOINT:-http://localhost:8529}"\n')
        f.write('DATABASE="${ARANGO_DB:-_system}"\n')
        f.write('USER="${ARANGO_USER:-root}"\n')
        f.write('PASS="${ARANGO_PASS:-}"\n\n')
        f.write('echo "Importing CausalNode document collection into ArangoDB..."\n')
        f.write('arangoimport --server.endpoint "$ENDPOINT" --server.database "$DATABASE" --server.username "$USER" --server.password "$PASS" --collection CausalNode --create-collection true --file CausalNode.json --type json --overwrite true\n\n')
        f.write('echo "Importing CausalEdge edge collection into ArangoDB..."\n')
        f.write('arangoimport --server.endpoint "$ENDPOINT" --server.database "$DATABASE" --server.username "$USER" --server.password "$PASS" --collection CausalEdge --create-collection true --create-collection-type edge --file CausalEdge.json --type json --overwrite true\n\n')
        f.write('echo "ArangoDB Causal Graph import completed successfully."\n')

    os.chmod(arango_dir / "import_arangodb.sh", 0o755)

    # Readme file documenting the export
    readme_path = base_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Net-AIOps Causal Graph Export (Neo4j & ArangoDB)\n\n")
        f.write(f"- **Total Causal Nodes**: {len(nodes)}\n")
        f.write(f"- **Total Causal Relationships**: {len(edges)}\n\n")
        f.write("## 1. Neo4j Format (`exports/neo4j/`)\n")
        f.write("- `cisco_iosxe_causal_graph.cypher`: Complete openCypher DDL/DML script with constraints, multi-labels (`:CausalNode`, `:Symptom`, `:RootCause`, `:Verification`, `:Command`, `:Remediation`), and typed relationships (`:CAUSES`, `:VERIFIED_BY`, `:EXECUTES_CLI`, etc.).\n")
        f.write("- `nodes.csv`, `edges.csv`: Header-annotated CSV files for `neo4j-admin database import`.\n\n")
        f.write("## 2. ArangoDB Format (`exports/arangodb/`)\n")
        f.write("- `CausalNode.json`: ArangoDB Document Collection format (`_key`, attributes, nested details).\n")
        f.write("- `CausalEdge.json`: ArangoDB Edge Collection format (`_from`, `_to`, `relationship`, `description`).\n")
        f.write("- `causal_graph_complete.json`: Multi-model graph definition with metadata.\n")
        f.write("- `import_arangodb.sh`: One-click CLI import script using `arangoimport`.\n")

    print(f"SUCCESS: Exported files to {neo4j_dir} and {arango_dir}")

if __name__ == "__main__":
    run_export()
