import argparse
import os
from jenkins_mcp.jenkins.client import JenkinsClient

def main():
    parser = argparse.ArgumentParser(description="MCP Server Parameters")
    parser.add_argument("--server", help="Server name to run", required=False, dest="server", 
                       default="jenkins", choices=["jenkins", "analysis", "job-run-analyser", 
                                                   "infra-monitoring", "infra-maintainer"])
    parser.add_argument("--jenkins-url", help="Jenkins Server URL", required=False, dest="jenkins_url")
    parser.add_argument("--jenkins-user", help="Jenkins Server User", required=False, dest="jenkins_user")
    parser.add_argument("--jenkins-password", help="Jenkins Server Password", required=False, dest="jenkins_password")
    args = parser.parse_args()

    if args.jenkins_url is None or args.jenkins_user is None or args.jenkins_password is None:
        print("Jenkins Server Parameters are not set")
        return

    print(f"Starting {args.server} MCP Server")
    print(f"Jenkins Server URL: {args.jenkins_url}")
    print(f"Jenkins Server User: {args.jenkins_user}")

    # Initialize Jenkins client for servers that need it
    if args.server == "jenkins":
        jenkins_client = JenkinsClient(args.jenkins_url, args.jenkins_user, args.jenkins_password)
    
    # Import all servers
    from jenkins_mcp.server import (
        mcp, 
        mcp_analysis, 
        mcp_job_run_analyser, 
        mcp_infra_monitoring, 
        mcp_infra_maintainer
    )
    
    # Select and run the appropriate server
    servers = {
        "jenkins": mcp,
        "analysis": mcp_analysis,
        "job-run-analyser": mcp_job_run_analyser,
        "infra-monitoring": mcp_infra_monitoring,
        "infra-maintainer": mcp_infra_maintainer
    }
    
    server = servers[args.server]
    print(f"Running {args.server} server...")
    server.run(transport="stdio")

if __name__ == "__main__":
    main()
