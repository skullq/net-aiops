#!/usr/bin/env bash
# ArangoDB Auto Import Script for Net-AIOps Causal Graph
ENDPOINT="${ARANGO_ENDPOINT:-http://localhost:8529}"
DATABASE="${ARANGO_DB:-_system}"
USER="${ARANGO_USER:-root}"
PASS="${ARANGO_PASS:-}"

echo "Importing CausalNode document collection into ArangoDB..."
arangoimport --server.endpoint "$ENDPOINT" --server.database "$DATABASE" --server.username "$USER" --server.password "$PASS" --collection CausalNode --create-collection true --file CausalNode.json --type json --overwrite true

echo "Importing CausalEdge edge collection into ArangoDB..."
arangoimport --server.endpoint "$ENDPOINT" --server.database "$DATABASE" --server.username "$USER" --server.password "$PASS" --collection CausalEdge --create-collection true --create-collection-type edge --file CausalEdge.json --type json --overwrite true

echo "ArangoDB Causal Graph import completed successfully."
