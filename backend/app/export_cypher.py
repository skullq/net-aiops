import json
from app.graph_engine import CausalGraphEngine

def main():
    engine = CausalGraphEngine()
    data = engine.get_graph_data()
    print(f"Loaded {len(data['nodes'])} nodes and {len(data['links'])} links from current graph engine.")

    lines = []
    lines.append("// =====================================================================")
    lines.append("// Cisco IOS-XE Causal GraphDB - openCypher Definition")
    lines.append("// Generated for Kùzu In-Memory GraphDB & NetworkX Topology Sync")
    lines.append("// =====================================================================\n")

    lines.append("// 1. Schema Definition")
    lines.append("CREATE NODE TABLE IF NOT EXISTS CausalNode(")
    lines.append("    id STRING,")
    lines.append("    label STRING,")
    lines.append("    type STRING,")
    lines.append("    description STRING,")
    lines.append("    details STRING,")
    lines.append("    PRIMARY KEY (id)")
    lines.append(");\n")

    lines.append("CREATE REL TABLE IF NOT EXISTS Rel(")
    lines.append("    FROM CausalNode TO CausalNode,")
    lines.append("    relationship STRING,")
    lines.append("    description STRING")
    lines.append(");\n")

    lines.append("// 2. Causal Nodes")
    for n in data["nodes"]:
        nid = n["id"].replace("'", "\\'")
        label = n["label"].replace("'", "\\'")
        ntype = n["type"].replace("'", "\\'")
        desc = (n.get("description") or "").replace("'", "\\'")
        details_str = json.dumps(n.get("details") or {}, ensure_ascii=False).replace("'", "\\'")
        lines.append(f"CREATE (:CausalNode {{id: '{nid}', label: '{label}', type: '{ntype}', description: '{desc}', details: '{details_str}'}});")

    lines.append("\n// 3. Causal Relationships")
    for link in data["links"]:
        src = link["source"].replace("'", "\\'")
        tgt = link["target"].replace("'", "\\'")
        rel = (link.get("relationship") or "leads_to").replace("'", "\\'")
        desc = (link.get("description") or "").replace("'", "\\'")
        lines.append(f"MATCH (s:CausalNode {{id: '{src}'}}), (t:CausalNode {{id: '{tgt}'}}) CREATE (s)-[:Rel {{relationship: '{rel}', description: '{desc}'}}]->(t);")

    output_path = "/root/Net-AIOps/backend/app/causal_graph.cypher"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Successfully generated {output_path} with {len(lines)} lines.")

if __name__ == "__main__":
    main()
