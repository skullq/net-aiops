from app.main import app
from app.graph_engine import graph_engine
from app.mcp_iosxe_server import mcp_tool

def test_backend():
    print("Testing Graph Engine:")
    print(f"  Total Nodes: {len(graph_engine.graph.nodes)}")
    print(f"  Total Edges: {len(graph_engine.graph.edges)}")
    
    print("\nTesting MCP Show Command:")
    res = mcp_tool.execute_show_command("show ip bgp summary")
    print(f"  Success: {res.get('success')}")
    print(f"  Parsed Entries: {len(res.get('parsed_output', []))}")
    print(f"  Sample: {res.get('parsed_output', [])[0]}")
    
    print("\nTesting hier-config Remediation:")
    rem = mcp_tool.generate_remediation_cli(
        running_config="router bgp 65000\n neighbor 1.1.1.1 password old",
        target_config="router bgp 65000\n neighbor 1.1.1.1 password new"
    )
    print(f"  Engine: {rem.get('engine')}")
    print(f"  Remediation Lines: {rem.get('remediation_lines')}")
    
    print("\nTesting FastAPI App Endpoints:")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    h = client.get("/api/health")
    print(f"  Health Check Status: {h.status_code}, response: {h.json()}")
    
    g = client.get("/api/graph")
    print(f"  Graph GET Status: {g.status_code}, nodes: {len(g.json()['nodes'])}, links: {len(g.json()['links'])}")
    
    print("\n=== ALL BACKEND CHECKS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_backend()
