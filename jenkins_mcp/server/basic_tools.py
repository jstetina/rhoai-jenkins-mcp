"""FastMCP tools for basic Jenkins operations."""
import json
from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp


def get_jenkins_client() -> JenkinsClient:
    """Get the Jenkins client instance."""
    return JenkinsClient.getJenkinsClient()


@mcp.tool()
def get_all_job_full_paths() -> list:
    """
    Get all jobs full paths from Jenkins.

    Returns:
        list: A list of all jobs full paths
    """
    client = get_jenkins_client()
    return client.get_job_full_paths()


@mcp.tool()
def get_job_info(job_name: str) -> str:
    """
    Get the information about a given job.

    Args:
        job_name: The name of the job to get information about.
    
    Returns:
        str: Job information as a string
    """
    client = get_jenkins_client()
    result = client.get_job_info(job_name)
    # Convert dict to string for better readability
    if isinstance(result, dict):
        return json.dumps(result, indent=2)
    return str(result)


@mcp.tool()
def start_job(job_name: str) -> str:
    """
    Start a given job.

    Args:
        job_name: The name of the job to start.
    
    Returns:
        str: Status message about the triggered job
    """
    client = get_jenkins_client()
    return client.start_job(job_name)


@mcp.tool()
def test_connection() -> str:
    """
    Test the connection to Jenkins.

    Returns:
        str: A success message with Jenkins version
    """
    client = get_jenkins_client()
    return f"Connected to Jenkins. Version: {client.get_version()}"


@mcp.tool()
def get_build_info(job_name: str, build_number: int) -> str:
    """
    Get the build information for a specific job build.

    Args:
        job_name: The name of the job
        build_number: The build number to get information for
    """
    client = get_jenkins_client()
    result = client.get_build_info(job_name, build_number)
    # Convert dict to string for better readability
    if isinstance(result, dict):
        return json.dumps(result, indent=2)
    return str(result)


@mcp.tool()
def get_build_logs(job_name: str, build_number: int) -> str:
    """
    Get the console output logs for a specific job build.

    Args:
        job_name: The name of the job
        build_number: The build number to get logs for
    
    Returns:
        str: The console output logs
    """
    client = get_jenkins_client()
    return client.get_build_logs(job_name, build_number)


@mcp.tool()
def get_latest_build_logs(job_name: str) -> str:
    """
    Get the console output logs for the latest build of a job.

    Args:
        job_name: The name of the job
    
    Returns:
        str: The console output logs from the most recent build
    """
    client = get_jenkins_client()
    return client.get_build_logs(job_name, None)


@mcp.tool()
def get_recent_build_numbers(job_name: str, limit: int = 10) -> list:
    """
    Get the build numbers for the most recent builds of a job.

    Args:
        job_name: The name of the job
        limit: Maximum number of build numbers to return (default: 10)
    
    Returns:
        list: List of build numbers (most recent first)
    """
    client = get_jenkins_client()
    return client.get_recent_build_numbers(job_name, limit)

@mcp.tool()
def enable_job(job_name: str) -> str:
    """
    Enable a given job.

    Args:
        job_name: The name of the job to enable.
    
    Returns:
        str: Status message about the enabled job
    """
    client = get_jenkins_client()
    return client.enable_job(job_name)

@mcp.tool()
def disable_job(job_name: str) -> str:
    """
    Disable a given job.

    Args:
        job_name: The name of the job to disable.
    
    Returns:
        str: Status message about the disabled job
    """ 
    client = get_jenkins_client()
    return client.disable_job(job_name)