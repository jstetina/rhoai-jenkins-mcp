# from jenkinsapi import jenkins
import os
import requests
from io import BytesIO

import jenkins

# Exclude GA rhoai versions
EXCLUDE_JOBS = ["rhoai/"]
class JenkinsClient:
    instance = None
    myattrib = ""


    def __new__(cls, url=None, username=None, password=None):
        if not cls.instance:
            cls.instance = super(JenkinsClient, cls).__new__(cls)
            cls.instance.url = url
            cls.instance.username = username
            cls.instance.password = password
            cls.instance.jenkins = jenkins.Jenkins(url, username, password)
            print(f"Jenkins Client created for {url}")
        else:
            print(f"Re-using existant Jenkins Client for {cls.instance.url}")
        return cls.instance

    def _extract_job_names(self, jobs: list, exclude: list = None) -> list:
        names = []
        for job in jobs:
            if isinstance(job, dict) and "jobs" in job and isinstance(job["jobs"], list):
                names.extend(self._extract_job_names(job["jobs"], exclude=exclude))
            elif isinstance(job, dict) and "fullname" in job:
                if exclude is not None and any(pattern in job['fullname'] for pattern in exclude):
                    continue
                names.append(job['fullname'])
        
        return names

    def get_job_full_paths(self):
        names = []
        print("Getting all jobs")
        jobs = self.jenkins.get_all_jobs()
        # get_all_jobs() returns a list, so we process it directly
        if isinstance(jobs, list):
            names.extend(self._extract_job_names(jobs, exclude=EXCLUDE_JOBS))
        # Dedupe before return
        return sorted(set(names))
    
    def get_job_info(self, job_name):
        return self.jenkins.get_job_info(job_name)

    def start_job(self, job_name):
        # Get the current last build number before triggering
        job_info = self.jenkins.get_job_info(job_name)
        last_build = job_info.get('lastBuild')
        previous_build_number = last_build.get('number') if last_build else 0
        
        # Trigger the job (this returns a queue item number, not the build number)
        queue_item = self.jenkins.build_job(job_name)
        
        # Wait a moment for Jenkins to assign the build number, then check
        import time
        time.sleep(1)  # Give Jenkins a moment to start the build
        
        # Get the updated job info to find the new build number
        job_info = self.jenkins.get_job_info(job_name)
        last_build = job_info.get('lastBuild')
        
        if last_build and last_build.get('number') > previous_build_number:
            build_number = last_build.get('number')
            return f"Triggered {job_name}. Build number: {build_number}"
        else:
            # If we can't get the build number yet, return the queue item
            return f"Triggered {job_name}. Queue item: {queue_item} (build number will be assigned when build starts)"

    def get_version(self):
        return self.jenkins.get_version()

    def get_build_logs(self, job_name: str, build_number: int = None) -> str:
        if build_number is None:
            # Get the last build number
            job_info = self.jenkins.get_job_info(job_name)
            last_build = job_info.get('lastBuild')
            if last_build is None:
                return f"No builds found for job {job_name}"
            build_number = last_build.get('number')
        
        return self.jenkins.get_build_console_output(job_name, build_number)

    def get_recent_build_numbers(self, job_name: str, limit: int = 10) -> list:
        job_info = self.jenkins.get_job_info(job_name)
        builds = job_info.get('builds', [])
        
        if not builds:
            return []
        
        # Extract build numbers from the builds list
        build_numbers = [build.get('number') for build in builds if build.get('number') is not None]
        
        # Return the most recent ones (they're already sorted by most recent first)
        return build_numbers[:limit]

    def get_build_info(self, job_name: str, build_number: int):
        return self.jenkins.get_build_info(job_name, build_number)

    def enable_job(self, job_name: str) -> str:
        self.jenkins.enable_job(job_name)
        return f"Successfully enabled job: {job_name}"

    def disable_job(self, job_name: str) -> str:
        self.jenkins.disable_job(job_name)
        return f"Successfully disabled job: {job_name}"

    def stop_build(self, job_name: str, build_number: int) -> str:
        self.jenkins.stop_build(job_name, build_number)
        return f"Successfully stopped build #{build_number} of job: {job_name}"

    def getJenkinsClient():
        return JenkinsClient()

    def run_job(self, job_name, params):
        queue_number = self.jenkins.build_job(job_name, parameters=params)
        queue_item = self.jenkins.get_queue_item(queue_number)
        if queue_item and queue_item.get('executable', {}).get('url', None):
            build_url = queue_item['executable']['url']
            msg = f"{job_name} triggered. Build URL: {build_url}"
        else:
            build_url = None
            msg = f"{job_name} waiting to be scheduled. Queue number: {queue_number}"
        return msg

    def run_job_with_file_param(self, job_name, params, file_param_name="EXTERNAL_KUBECONFIG_FILE"):
        """
        Trigger a Jenkins job that has a File Parameter.
        """
        # Build URL for the job
        build_url = f"{self.url}/job/{job_name.replace('/', '/job/')}/buildWithParameters"
        
        # Prepare multipart form data
        files = {}
        data = {}
        
        for key, value in params.items():
            data[key] = str(value)
        
        # Add empty file for the file parameter
        files[file_param_name] = ('', BytesIO(b''), 'application/octet-stream')
        
        # Make the request with auth
        response = requests.post(
            build_url,
            data=data,
            files=files,
            auth=(self.username, self.password)
        )
        
        if response.status_code == 201:
            # Job was queued successfully
            queue_url = response.headers.get('Location', '')
            if queue_url:
                # Extract queue number and get build info
                queue_number = int(queue_url.rstrip('/').split('/')[-1])
                queue_item = self.jenkins.get_queue_item(queue_number)
                if queue_item and queue_item.get('executable', {}).get('url', None):
                    build_url = queue_item['executable']['url']
                    msg = f"{job_name} triggered. Build URL: {build_url}"
                else:
                    msg = f"{job_name} waiting to be scheduled. Queue number: {queue_number}"
            else:
                msg = f"{job_name} triggered successfully."
            return msg
        else:
            raise Exception(f"Failed to trigger job: {response.status_code} - {response.text}")

