import argparse
import sys
import os
from jenkins_mcp.jenkins.client import JenkinsClient


def main():
    parser = argparse.ArgumentParser(
        description="RHOAI Jenkins MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio transport (default)
  python main.py --jenkins-url http://localhost:8080 --jenkins-user admin --jenkins-password secret

  # Run with HTTP transport for container networking
  python main.py --transport http --jenkins-url http://localhost:8080 --jenkins-user admin --jenkins-password secret
        """
    )
    parser.add_argument(
        "--transport",
        help="Transport type (stdio or http)",
        required=False,
        dest="transport",
        default="stdio",
        choices=["stdio", "http"]
    )
    parser.add_argument("--jenkins-url", help="Jenkins Server URL", required=False, dest="jenkins_url")
    parser.add_argument("--jenkins-user", help="Jenkins Server User", required=False, dest="jenkins_user")
    parser.add_argument("--jenkins-password", help="Jenkins Server Password", required=False, dest="jenkins_password")
    args = parser.parse_args()

    # Allow environment variables as fallback
    jenkins_url = args.jenkins_url or os.environ.get("JENKINS_URL")
    jenkins_user = args.jenkins_user or os.environ.get("JENKINS_USER")
    jenkins_password = args.jenkins_password or os.environ.get("JENKINS_PASSWORD")

    if jenkins_url is None or jenkins_user is None or jenkins_password is None:
        sys.stderr.write("Error: Jenkins Server Parameters are not set\n")
        sys.stderr.write("Provide --jenkins-url, --jenkins-user, --jenkins-password or set JENKINS_URL, JENKINS_USER, JENKINS_PASSWORD env vars\n")
        sys.exit(1)

    # Only output to stderr to avoid interfering with stdio protocol
    sys.stderr.write("Starting RHOAI Jenkins MCP Server\n")
    sys.stderr.write(f"Jenkins URL: {jenkins_url}\n")
    sys.stderr.write(f"Jenkins User: {jenkins_user}\n")
    sys.stderr.write(f"Transport: {args.transport}\n")
    sys.stderr.write("\n")
    sys.stderr.flush()

    # Set environment variables for the Jenkins client
    os.environ["JENKINS_URL"] = jenkins_url
    os.environ["JENKINS_USER"] = jenkins_user
    os.environ["JENKINS_PASSWORD"] = jenkins_password

    # Initialize Jenkins client
    jenkins_client = JenkinsClient(jenkins_url, jenkins_user, jenkins_password)

    # Import the MCP server
    from jenkins_mcp.server import mcp

    sys.stderr.write("Running RHOAI Jenkins MCP server...\n")
    sys.stderr.flush()

    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        else:
            # For HTTP transport, get the ASGI app and run with uvicorn directly
            import uvicorn
            app = mcp.streamable_http_app()
            sys.stderr.write("Starting HTTP server on 0.0.0.0:8000\n")
            sys.stderr.flush()
            uvicorn.run(app, host="0.0.0.0", port=8000, server_header=False, forwarded_allow_ips="*")
    except KeyboardInterrupt:
        sys.stderr.write("\n\nShutting down server...\n")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"\n\nError running server: {e}\n")
        import traceback
        sys.stderr.write(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
