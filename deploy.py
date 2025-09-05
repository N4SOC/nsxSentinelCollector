#!/usr/bin/python3
import os
import subprocess
import sys

import config


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


if os.geteuid() != 0:
    print("Script must be run as root, try using sudo...")
    sys.exit()


def runcmd(cmd):  # Wrapper to make running commands quicker
    runcmd = subprocess.run(cmd.split(" "))
    return runcmd.returncode


def installUpdater():
    cwd = os.getcwd()
    cronScript = f"""
    #!/usr/bin/env bash
    cd "{cwd}"
    /usr/bin/git pull
    /usr/local/bin/docker compose build
    /usr/local/bin/docker compose up -d --force-recreate
    """
    with open("/etc/cron.daily/sentinel_docker_refresh.sh", "w") as f:
        f.write(cronScript)
    runcmd("chmod +x /etc/cron.daily/sentinel_docker_refresh.sh")


pipelinesOutput = """
- pipeline.id: ingest
  queue.type: persisted
  path.config: /usr/share/logstash/pipeline/ingest.conf
"""

pipelinesTemplate = """
- pipeline.id: sentinel-{0}
  queue.type: persisted
  path.config: /usr/share/logstash/pipeline/sentinel-{0}.conf
"""

ingestPipelineOutput = """
input {
  tcp {
    port => 514
    type => syslog
  }
  udp {
    port => 514
    type => syslog
  }
}
filter { }
output {
    if [message] == "" { drop {} }
"""

ingestPipelineTemplate = """
else if [message] !~ "{0}"  {{
          pipeline {{ send_to => sentinel-{1} }}
}}
"""

for client in config.clients:
    pipelinesSection = pipelinesTemplate.format(client["name"])
    pipelinesOutput += "\n" + pipelinesSection
    sentinelPipelineOutput = (
        """
    input {
        pipeline {
            address => "sentinel-"""
        + client["name"]
        + """"}
        }
    filter {
    mutate {
        add_tag => [ """
        " + config.collectorTag + "
        """ ]
        }
    }
    output {
    microsoft-logstash-output-azure-loganalytics {
        workspace_id => " """
        + client["workspaceID"]
        + """"
        workspace_key => " """
        + client["workspaceKey"]
        + """"
        custom_log_table_name => "vmwarensx"
        }
    }
    """
    )
    with open("vmware-aria/pipeline/sentinel-" + client["name"] + ".conf", "w") as f:
        f.write(sentinelPipelineOutput)

    sentinelPipelineSectionOut = ""
    for label in client["nsxLabels"]:
        ingestPipelineSection = ingestPipelineTemplate.format(label, client["name"])
        sentinelPipelineSectionOut += ingestPipelineSection
    ingestPipelineOutput += "\n" + sentinelPipelineSectionOut
ingestPipelineOutput += "\n}"


with open("vmware-aria/config/pipelines.yml", "w") as ff:
    ff.write(pipelinesOutput)

with open("vmware-aria/pipeline/ingest.conf", "w") as fff:
    fff.write(ingestPipelineOutput)


if runcmd("docker compose down --remove-orphans") == 0:
    print(f"Stopped existing containers")
else:
    print("Stop Failed")

if runcmd("docker compose build") == 0:
    print(f"Build Successful - {len(config.clients)} client pipelines built")
else:
    print("Build Failed")

if runcmd("docker compose up -d") == 0:
    print(f"Execution Successful - {len(config.clients)} client pipelines running")
else:
    print("Execution Failed")
