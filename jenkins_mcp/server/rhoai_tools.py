from collections import defaultdict
import re
from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp
from typing import Dict, Any


def get_jenkins_client() -> JenkinsClient:
    """Get the Jenkins client instance."""
    return JenkinsClient.getJenkinsClient()


@mcp.tool()
async def run_test_matrix(rhoai_version: str, build_image_url: str, providers: dict, team: str, mode: str = "auto") -> list:
    """
    Run the test_matrix_run job on the given build image URL.
    Validate a RHOAI build against the given providers.

    Args:
        rhoai_version (str): The RHOAI version to validate.
        build_image_url (str): The URL of the build image to validate.
        mode (str): The mode to run the test matrix in.
        providers (dict): The providers to validate the build against.
        team (str): The team to run the test matrix for. Default to devtestops
    Returns:
        String: The jenkins job run URL.
    """
    # Trigger the Jenkins job with the image URL as a parameter
    job_name = "devops/test_matrix_run"
    # name,enabled,ocp,fips,sno@@@
    print(providers)
    prov_strs = ""
    if providers:
        for provider, config_dict in providers.items():
            config_dict = defaultdict(int, config_dict)
            prov_str = f"{provider},"
            prov_str += f"{config_dict.get('enabled', 'true')},"
            prov_str += f"{config_dict.get('ocp', None)},"
            prov_str += f"{config_dict.get('fips', 'false')},"
            prov_str += f"{config_dict.get('sno', 'false')}"
            prov_str += "@@@"
            prov_strs += prov_str

    fetch = True if mode.lower() == "auto" else False
    params = {
        "OVERRIDE_ODS_BUILD_URL": build_image_url,
        "RHOAI_VERSION_XY": rhoai_version,
        "FETCH_TEST_MATRIX": fetch,
        "CLOUD_PROVIDERS_TABLE": prov_strs
    }
    client = get_jenkins_client()
    build_info = client.jenkins.build_job(job_name, parameters=params)
    return f"Triggered {job_name} for {build_image_url}. Build info: {build_info}"
