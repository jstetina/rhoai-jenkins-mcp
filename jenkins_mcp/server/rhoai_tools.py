from collections import defaultdict
from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp

jenkins_client = JenkinsClient.getJenkinsClient()

@mcp.tool()
async def run_test_matrix(rhoai_version: str, build_image_url: str, providers: dict, mode: str = "auto") -> list:
    """
    Run the test_matrix_run job on the given build image URL.
    Validate a RHOAI build against the given providers.

    Args:
        rhoai_version (str): The RHOAI version to validate.
        build_image_url (str): The URL of the build image to validate.
        mode (str): The mode to run the test matrix in.
        providers (dict): The providers to validate the build against.

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
            prov_str += f"{config_dict.get('enabled', "true")},"
            prov_str += f"{config_dict.get('ocp', None)},"
            prov_str += f"{config_dict.get('fips', "false")},"
            prov_str += f"{config_dict.get('sno', "false")}"
            prov_str += "@@@"
            prov_strs += prov_str

    fetch = True if mode.lower() == "auto" else False
    params = {
        "OVERRIDE_ODS_BUILD_URL": build_image_url,
        "RHOAI_VERSION_XY": rhoai_version,
        "FETCH_TEST_MATRIX": fetch,
        "CLOUD_PROVIDERS_TABLE": prov_strs
    }
    build_info = jenkins_client.jenkins.build_job(job_name, parameters=params)
    return f"Triggered {job_name} for {build_image_url}. Build info: {build_info}"



@mcp.tool(description="""
Provision and configure an OpenShift cluster with optional RHOAI/RHODS deployment.

This tool is strictly for cluster provisioning and RHOAI operator deployment - NOT for running tests.
It triggers the Jenkins job 'devops/rhoai-test-flow' which handles:
- Provisioning a new OpenShift cluster on the specified provider
- Optionally installing RHOAI/RHODS operator
- Configuring the cluster (GPU, NFS, IDP, etc.)
- Managing cluster lifecycle

Parameters:
    cluster_name: Unique cluster name (alphanumeric and dash only, max 15 chars)
    
    product: Product to install (default: "RHODS")
        Options: RHODS, ODH
    
    cluster_type: Type of cluster (default: "selfmanaged")
        Options: 
        - selfmanaged: Self-managed OpenShift cluster
        - managed: Managed service (OSD, ROSA, etc.)
    
    test_environment: Cloud provider/platform (default: "PSI")
        Options: PSI, AWS, GCP, ROSA, IBM, AZURE
    
    test_platform: Environment stage (default: "Stage")
        Options: Stage, Prod
        Note: Only applies to managed clusters (automatically unset for selfmanaged)
    
    cluster_architecture: CPU architecture (default: "amd64")
        Options: amd64, arm64
    
    team_name: RHOAI sub-team name (default: "devtestops")
        Used for resource tagging and organization
    
    deploy_rhods_operator: Install RHOAI/RHODS operator (default: True)
    
    enable_fips: Enable FIPS mode in cluster (default: False)
    
    install_gpu: Install GPU support (default: False; only supported on non-PSI clusters)
    
    deploy_nfs: Deploy NFS storage (default: False)
    
    deploy_external_dns: Deploy external-dns (default: auto-detected)
        Automatically enabled for RHOAI 3.x on PSI (required for 3.x)
        Can be explicitly set to True/False to override auto-detection
    
    cluster_action_post_execution: What to do after execution (default: "Retain Cluster Ready")
        Options: "Retain Cluster Ready", "Deprovision Cluster", "Hibernate Cluster"
    
    region: Cloud region (default: auto-selected based on test_environment)
        PSI: regionOne
        AWS: us-east-1, us-east-2
        GCP: us-central1
        IBM: us-south
        AZURE: eastus2
        If quota is exceeded on your default cloud provider location, you may specify a different region
        (e.g., for AWS use us-east-1 or us-east-2).
    
    ocp_version: OpenShift version (default: "4.19-latest")
        Format: "X.Y-latest" or "X.Y.Z"
        Examples: "4.19-latest", "4.18.0"
    
    psi_params: PSI cloud parameters (default: "rhos-d,,,")
        Format: cloud_name,param2,param3,param4
        Only used when test_environment is PSI
    
    ods_build_url: RHOAI build image URL (default: None)
        Example: "quay.io/rhoai/rhoai-fbc-fragment:rhoai-3.0"
        REQUIRED when deploy_rhods_operator=True and rhods_deployment_type="Cli"
    
    update_channel: RHOAI update channel (default: "stable")
        Example: "fast-3.x", "stable", "odh-nightlies"
    
    rhods_deployment_type: Deployment method (default: "Cli")
        Options: Cli, OperatorHub
    
    rhoai_namespaces: RHOAI installation namespaces (default: "redhat-ods-operator,redhat-ods-applications,rhods-notebooks")
        Comma-separated namespace list

Returns:
    str: Status message with job trigger information and build number
""")
async def provision_cluster(
    cluster_name: str,
    product: str = "RHODS",
    cluster_type: str = "selfmanaged",
    test_environment: str = "PSI",
    test_platform: str = "Stage",
    cluster_architecture: str = "amd64",
    team_name: str = "devtestops",
    deploy_rhods_operator: bool = True,
    enable_fips: bool = False,
    install_gpu: bool = False,
    deploy_nfs: bool = False,
    deploy_external_dns: bool = None,
    cluster_action_post_execution: str = "Retain Cluster Ready",
    region: str = None,
    ocp_version: str = "4.19-latest",
    psi_params: str = "rhos-d,,,",
    ods_build_url: str = None,
    update_channel: str = "stable",
    rhods_deployment_type: str = "Cli",
    rhoai_namespaces: str = "redhat-ods-operator,redhat-ods-applications,rhods-notebooks"
) -> str:
    """
    Provision a cluster using the rhoai-test-flow Jenkins job.
    """
    # Validate required parameters
    if deploy_rhods_operator and rhods_deployment_type == "Cli" and not ods_build_url:
        raise ValueError(
            "ERROR: ods_build_url is REQUIRED when deploy_rhods_operator=True and rhods_deployment_type='Cli'.\n\n"
            "To fix this error, provide an ods_build_url parameter with a valid RHOAI build image URL.\n"
            "Examples:\n"
            "  - 'quay.io/rhoai/rhoai-fbc-fragment:rhoai-3.0'\n"
            "  - 'quay.io/rhoai/rhoai-fbc-fragment:rhoai-2.17-nightly'\n"
            "  - 'brew.registry.redhat.io/rh-osbs/iib:RHODS_BUILD_NUMBER'\n\n"
            "Alternatively, you can:\n"
            "  - Set deploy_rhods_operator=False (to only provision cluster without RHOAI)\n"
            "  - Set rhods_deployment_type='OperatorHub' (to use OperatorHub instead of CLI deployment)"
        )
    
    # Validate ROSA is not used with selfmanaged
    if test_environment == "ROSA" and cluster_type == "selfmanaged":
        raise ValueError(
            "ERROR: ROSA is only supported with cluster_type='managed', not 'selfmanaged'.\n\n"
            "To fix this error:\n"
            "  - Change cluster_type to 'managed' for ROSA clusters\n"
            "  - Or use a different test_environment (PSI, AWS, GCP, IBM, AZURE)"
        )
    
    # Unset test_platform for selfmanaged clusters (only applies to managed)
    if cluster_type == "selfmanaged":
        test_platform = ""
    
    # Auto-detect deploy_external_dns if not explicitly set
    if deploy_external_dns is None:
        # Check if this is RHOAI 3.x on PSI
        is_rhoai_3x = False
        if ods_build_url and ('rhoai-3' in ods_build_url.lower() or ':3.' in ods_build_url):
            is_rhoai_3x = True
        elif update_channel and ('3.' in update_channel or '3.x' in update_channel.lower()):
            is_rhoai_3x = True
        
        # Enable external-dns for RHOAI 3.x on PSI (required)
        if test_environment == "PSI" and is_rhoai_3x:
            deploy_external_dns = True
        else:
            # Default to True for safety (can be disabled if needed)
            deploy_external_dns = True
    
    # Auto-select region based on test_environment if not provided
    if region is None:
        region_defaults = {
            "PSI": "regionOne",
            "AWS": "us-east-1",
            "GCP": "us-central1",
            "IBM": "us-south",
            "AZURE": "eastus2",
            "ROSA": "us-east-1"  # ROSA default, though it should be managed
        }
        region = region_defaults.get(test_environment, "regionOne")
    
    # Build TEST_CLUSTER_DETAILS based on test_environment
    # Format: region,master_nodes,worker_nodes,master_flavor,worker_flavor,ocp_version,channel_group,architecture
    cluster_configs = {
        "PSI": {
            "master_nodes": "3",
            "worker_nodes": "3",
            "master_flavor": "g.standard.xxl",
            "worker_flavor": "g.standard.xxl"
        },
        "AWS": {
            "master_nodes": "3",
            "worker_nodes": "3",
            "master_flavor": "m5.2xlarge",
            "worker_flavor": "m5.2xlarge"
        },
        "GCP": {
            "master_nodes": "3",
            "worker_nodes": "3",
            "master_flavor": "custom-8-32768",
            "worker_flavor": "n2-standard-8"
        },
        "IBM": {
            "master_nodes": "3",
            "worker_nodes": "3",
            "master_flavor": "bx2-4x16",
            "worker_flavor": "bx2-4x16"
        },
        "AZURE": {
            "master_nodes": "3",
            "worker_nodes": "3",
            "master_flavor": "Standard_D8s_v4",
            "worker_flavor": "Standard_D8s_v4"
        },
        "ROSA": {
            "master_nodes": "3",
            "worker_nodes": "3",
            "master_flavor": "m5.2xlarge",
            "worker_flavor": "m5.2xlarge"
        }
    }
    
    config = cluster_configs.get(test_environment, cluster_configs["PSI"])
    test_cluster_details = (
        f"{region},"
        f"{config['master_nodes']},"
        f"{config['worker_nodes']},"
        f"{config['master_flavor']},"
        f"{config['worker_flavor']},"
        f"{ocp_version},"
        f"stable,"
        f"{cluster_architecture}"
    )
    
    job_name = "devops/rhoai-test-flow"
    
    # Build parameters dictionary
    params = {
        "CLUSTER_NAME": cluster_name,
        "PRODUCT": product,
        "CLUSTER_TYPE": cluster_type,
        "CLUSTER_AUTH": "internal",  # Always internal as specified
        "TEST_ENVIRONMENT": test_environment,
        "TEST_PLATFORM": test_platform,
        "INSTALL_CLUSTER": True,  # Always true for provisioning
        "CLUSTER_ARCHITECTURE": cluster_architecture,
        "TEAM_NAME": team_name,
        "DEPLOY_RHODS_OPERATOR": deploy_rhods_operator,
        "ENABLE_FIPS_IN_CLUSTER": enable_fips,
        "INSTALL_GPU": str(install_gpu).lower(),
        "DEPLOY_NFS": deploy_nfs,
        "CLUSTER_ACTION_POST_EXECUTION": cluster_action_post_execution,
        # Cluster configuration parameters
        "TEST_CLUSTER_DETAILS": test_cluster_details,
        # PSI-specific parameters
        "PSI_PARAMS": psi_params,
        "SINGLE_NODE_OPENSHIFT": "false",
        # RHOAI deployment parameters
        "RHODS_DEPLOYMENT_TYPE": rhods_deployment_type,
        "RHOAI_NAMESPACES": rhoai_namespaces,
        # Test parameters - all disabled for provisioning
        "RUN_TESTS": False,
        "ODS_CI_RUN_SCRIPT_ARGS": "",
        "RUN_DASHBOARD_TESTS": "",
        "PARALLEL": False,
        "QUALITY_GATES": "-- None --",
        "UPDATE_POLARION": False,
        "UPDATE_REPORT_PORTAL": False,
        # Additional sensible defaults
        "DEPLOY_EXTERNAL_DNS": deploy_external_dns,
        "CREATE_IDP": True,
        "ARCHIVE_ARTIFACTS": True,
        "ADD_ICSP": True,
        "DEPROVISION_AFTER_INSTALL_FAILURE": True,
        "INSTALL_AUTHORINO_DEPENDENCY": True,
        "ENABLE_NEW_OBSERVABILITY_STACK": False,
        "KSERVE_RAW_DEPLOYMENT": False,
        # set UPDATE_CHANNEL to default "stable", can be overridden below
        "UPDATE_CHANNEL": update_channel 
    }
    
    # Add optional parameters if provided
    if ods_build_url:
        params["ODS_BUILD_URL"] = ods_build_url
    # Trigger the job
    build_info = jenkins_client.jenkins.build_job(job_name, parameters=params)
    
    # Wait briefly and get build number
    import time
    time.sleep(1)
    
    job_info = jenkins_client.jenkins.get_job_info(job_name)
    last_build = job_info.get('lastBuild')
    
    if last_build:
        build_number = last_build.get('number')
        build_url = f"{jenkins_client.url}/job/{job_name.replace('/', '/job/')}/{build_number}/"
        return f"Successfully triggered cluster provisioning for '{cluster_name}'\nJob: {job_name}\nBuild: #{build_number}\nURL: {build_url}\nQueue Item: {build_info}"
    else:
        return f"Triggered cluster provisioning for '{cluster_name}'\nJob: {job_name}\nQueue Item: {build_info}\n(Build number will be assigned when job starts)"
