from mcp.server.fastmcp import FastMCP
import importlib

# Create all MCP servers
mcp = FastMCP('rhoai-jenkins')
mcp_analysis = FastMCP('analysis')
mcp_job_run_analyser = FastMCP('job-run-analyser')
mcp_infra_monitoring = FastMCP('infra-monitoring')
mcp_infra_maintainer = FastMCP('infra-maintainer')

# Import tool definitions
print(f"Importing Jenkins tools")
importlib.import_module("jenkins_mcp.server.basic_tools")
importlib.import_module("jenkins_mcp.server.rhoai_tools")

print(f"Importing Analysis tools")
importlib.import_module("jenkins_mcp.server.analysis_tools")

print(f"Importing Job Run Analyser tools")
importlib.import_module("jenkins_mcp.server.job_run_analyser_tools")

print(f"Importing Infrastructure Monitoring tools")
importlib.import_module("jenkins_mcp.server.infra_monitoring_tools")

print(f"Importing Infrastructure Maintainer tools")
importlib.import_module("jenkins_mcp.server.infra_maintainer_tools")
