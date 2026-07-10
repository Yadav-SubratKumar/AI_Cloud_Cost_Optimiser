import subprocess
import json
import os
import shutil

Az = " Path to az cmd"

class AzureCLIError(Exception):
    pass


def run_az_command(command_list):
    """
    Executes an Azure CLI command array securely.
    """
    try:
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            shell=True
        )
    except FileNotFoundError:
        raise AzureCLIError("Azure CLI is not installed.")

    if result.returncode != 0:
        raise AzureCLIError(result.stderr.strip())

    return json.loads(result.stdout) if result.stdout.strip() else {}


def get_resource_groups():
    groups = run_az_command([AZ, "group", "list", "-o", "json"])
    return [g["name"] for g in groups]

def get_vm_optimization_details(resource_group, vm_name):
    """
    Fetches runtime power state, configurations, and auto-shutdown schedules 
    for cost optimization analysis without using Monitor/Advisor.
    """
    vm_data = {
        "power_state": "Unknown",
        "priority": "Regular",
        "os_type": "Unknown",
        "auto_shutdown_enabled": False
    }
    
    # 1. Fetch Instance View for PowerState (Allocated vs Deallocated)
    try:
        instance_view = run_az_command([
            AZ, "vm", "get-instance-view",
            "--resource-group", resource_group,
            "--name", vm_name,
            "-o", "json"
        ])
        instance = instance_view.get("instanceView", [])
        statuses = instance.get("statuses", [])
        # print(statuses)
        for status in statuses:
            if "PowerState" in status.get("code", ""):
                vm_data["power_state"] = status.get("displayStatus", "VM deallocated")
                # print(vm_data["power_state"])
    except Exception:
        pass

    # 2. Fetch specific VM properties (Spot priority and OS disk licensing type)
    try:
        vm_details = run_az_command([
            AZ, "vm", "show",
            "--resource-group", resource_group,
            "--name", vm_name,
            "-o", "json"
        ])
        vm_data["priority"] = vm_details.get("priority", "Regular")
        
        storage_profile = vm_details.get("storageProfile", {})
        os_disk = storage_profile.get("osDisk", {})
        vm_data["os_type"] = os_disk.get("osType", "Unknown")
    except Exception:
        pass

    # 3. Check for Auto-Shutdown Schedule Resource associated with the VM
    try:
        schedule_name = f"shutdown-computevm-{vm_name}"
        schedule_details = run_az_command([
            AZ, "resource", "show",
            "--resource-group", resource_group,
            "--name", schedule_name,
            "--resource-type", "Microsoft.DevTestLab/schedules",
            "-o", "json"
        ])
        if schedule_details.get("properties", {}).get("status") == "Enabled":
            vm_data["auto_shutdown_enabled"] = True
    except Exception:
        vm_data["auto_shutdown_enabled"] = False
    return vm_data


# ==========================================
# STORAGE (DISKS & ACCOUNTS) OPTIMIZATION CHECKS
# ==========================================
def get_disk_optimization_details(resource_group, disk_name):
    """
    Checks if a managed disk is attached to any VM. Orphaned disks cost 100% of their SKU rate.
    """
    disk_data = {"is_attached": False, "sku_tier": "Standard"}
    try:
        disk_details = run_az_command([
            AZ, "disk", "show",
            "--resource-group", resource_group,
            "--name", disk_name,
            "-o", "json"
        ])
        if disk_details.get("managedBy"):
            disk_data["is_attached"] = True
        
        if disk_details.get("sku"):
            disk_data["sku_tier"] = disk_details["sku"].get("name", "Standard")
    except Exception:
        pass
    return disk_data


def get_storage_optimization_details(resource_group, account_name):
    """
    Evaluates storage account configurations like redundancy and lifecycle policies.
    """
    storage_data = {
        "redundancy": "Unknown",
        "has_lifecycle_policy": False,
        "blob_access_tier": "Hot"
    }
    try:
        acc_details = run_az_command([
            AZ, "storage account", "show",
            "--resource-group", resource_group,
            "--name", account_name,
            "-o", "json"
        ])
        storage_data["redundancy"] = acc_details.get("sku", {}).get("name", "Unknown")
        storage_data["blob_access_tier"] = acc_details.get("accessTier", "Hot")
    except Exception:
        pass

    try:
        policy = run_az_command([
            AZ, "storage account", "management-policy", "show",
            "--resource-group", resource_group,
            "--account-name", account_name,
            "-o", "json"
        ])
        if policy.get("policy", {}).get("rules"):
            storage_data["has_lifecycle_policy"] = True
    except Exception:
        storage_data["has_lifecycle_policy"] = False

    return storage_data


# ==========================================
# MAIN SCANNER PIPELINE
# ==========================================
def scan_resource_group(resource_group):
    resources = run_az_command([
        AZ, "resource", "list",
        "--resource-group", resource_group,
        "-o", "json"
    ])

    data = []

    for r in resources:
        res_type = r.get("type")
        res_name = r.get("name")
        
        base_info = {
            "id": r.get("id"),
            "name": res_name,
            "type": res_type,
            "location": r.get("location"),
            "sku": r.get("sku"),
            "tags": r.get("tags", {}),
            "optimization_metrics": {}
        }

        # 1. Virtual Machines Handling
        if res_type == "Microsoft.Compute/virtualMachines":
            opt_data = get_vm_optimization_details(resource_group, res_name)
            cost_flags = []
            
            if opt_data["power_state"] == "VM running":
                cost_flags.append("Resource running 24/7. Check utilization rules.")
            if not opt_data["auto_shutdown_enabled"] and opt_data["priority"] != "Spot":
                cost_flags.append("Missing auto-shutdown configuration for non-prod environment.")
            if opt_data["os_type"] == "Windows":
                cost_flags.append("Windows licensing applied. Verify Hybrid Benefit eligibility.")
            if opt_data["priority"] == "Spot":
                cost_flags.append("Already cost-optimized using Azure Spot capacity.")

            base_info["optimization_metrics"] = {
                "power_state": opt_data["power_state"],
                "allocation_priority": opt_data["priority"],
                "os_platform": opt_data["os_type"],
                "auto_shutdown_active": opt_data["auto_shutdown_enabled"],
                "cost_saving_opportunities": cost_flags if cost_flags else ["Optimized"]
            }

        # 2. Managed Disks Handling
        elif res_type == "Microsoft.Compute/disks":
            disk_opt = get_disk_optimization_details(resource_group, res_name)
            cost_flags = []
            
            if not disk_opt["is_attached"]:
                cost_flags.append("CRITICAL: Disk is unattached/orphaned. Incurring unnecessary costs.")
            if "Premium" in disk_opt["sku_tier"] and not disk_opt["is_attached"]:
                cost_flags.append("High cost premium disk sitting idle.")

            base_info["optimization_metrics"] = {
                "is_attached_to_vm": disk_opt["is_attached"],
                "disk_tier": disk_opt["sku_tier"],
                "cost_saving_opportunities": cost_flags if cost_flags else ["Optimized"]
            }

        # 3. Storage Accounts Handling
        elif res_type == "Microsoft.Storage/storageAccounts":
            storage_opt = get_storage_optimization_details(resource_group, res_name)
            cost_flags = []
            
            if "GRS" in storage_opt["redundancy"] or "GZRS" in storage_opt["redundancy"]:
                cost_flags.append(f"Geo-redundancy active ({storage_opt['redundancy']}). Verify if Local Redundancy (LRS) suffices for dev/test.")
            if not storage_opt["has_lifecycle_policy"] and storage_opt["blob_access_tier"] == "Hot":
                cost_flags.append("Missing Lifecycle Management Policy. Data never auto-transitions to Cool/Archive tiers.")

            base_info["optimization_metrics"] = {
                "redundancy_type": storage_opt["redundancy"],
                "default_tier": storage_opt["blob_access_tier"],
                "lifecycle_policy_configured": storage_opt["has_lifecycle_policy"],
                "cost_saving_opportunities": cost_flags if cost_flags else ["Optimized"]
            }
            
        data.append(base_info)
    return data
# get_vm_optimization_details("azure", "azure")