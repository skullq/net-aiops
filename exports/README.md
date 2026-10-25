# Net-AIOps Causal Graph Export (Neo4j & ArangoDB)

- **Total Causal Nodes**: 242
- **Total Causal Relationships**: 297

## 1. Neo4j Format (`exports/neo4j/`)
- `cisco_iosxe_causal_graph.cypher`: Complete openCypher DDL/DML script with constraints, multi-labels (`:CausalNode`, `:Symptom`, `:RootCause`, `:Verification`, `:Command`, `:Remediation`), and typed relationships (`:CAUSES`, `:VERIFIED_BY`, `:EXECUTES_CLI`, etc.).
- `nodes.csv`, `edges.csv`: Header-annotated CSV files for `neo4j-admin database import`.

## 2. ArangoDB Format (`exports/arangodb/`)
- `CausalNode.json`: ArangoDB Document Collection format (`_key`, attributes, nested details).
- `CausalEdge.json`: ArangoDB Edge Collection format (`_from`, `_to`, `relationship`, `description`).
- `causal_graph_complete.json`: Multi-model graph definition with metadata.
- `import_arangodb.sh`: One-click CLI import script using `arangoimport`.
