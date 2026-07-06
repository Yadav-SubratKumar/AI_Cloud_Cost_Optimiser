import subprocess
import json
import os
import shutil



AZ = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
class AzureCLIError(Exception):
    pass


def run_az_command(command):
    try:
        import shutil
        import os
        import sys

        result = subprocess.run(
            [AZ, "group", "list", "-o", "json"],
            capture_output=True,
            text=True,
            shell=True
        )
    except FileNotFoundError:
        raise AzureCLIError(
            "Azure CLI is not installed."
        )

    if result.returncode != 0:
        raise AzureCLIError(
            result.stderr.strip()
        )

    return json.loads(result.stdout)


def get_resource_groups():
    groups = run_az_command(
        [AZ, "group", "list", "-o", "json"]
    )

    return [
        g["name"]
        for g in groups
    ]


def scan_resource_group(resource_group):
    resources = run_az_command(
        [
            AZ,
            "resource",
            "list",
            "--resource-group",
            resource_group,
            "-o",
            "json"
        ]
    )

    data = []

    for r in resources:
        data.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "type": r.get("type"),
            "location": r.get("location"),
            "sku": r.get("sku"),
            "tags": r.get("tags", {})
        })

    return data