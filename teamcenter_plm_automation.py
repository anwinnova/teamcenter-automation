"""
Teamcenter Enterprise PLM Automation Framework in Python
========================================================
This complete Python automation suite covers the 5 key Teamcenter automation areas:
 1. Item & BOM Structure Management (Create Items, Revisions, BOM Windows & Children)
 2. CAD & Dataset Import/Export (Create Datasets, Upload Files via FMS Tickets, Download Attachments)
 3. Workflow & Approval Automation (Submit Objects to Workflows, Task Sign-offs)
 4. Data Synchronization & Export (Query Objects, Extract BOM, Export to CSV/JSON)
 5. Batch Processing & CLI Utilities (Mass CSV Batch Runner, Logging, Configuration)

Requires: Python 3.8+, requests
Install requirements: pip install requests
"""

import os
import sys
import json
import csv
import logging
import argparse
from typing import List, Dict, Any, Optional
import requests

# Configure logging for audit trails and batch execution monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("teamcenter_automation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TC_Automation")


class TeamcenterPLMSuite:
    """Master Python Suite for Teamcenter PLM Automation using SOA REST Endpoints."""

    def __init__(self, host_url: str, fms_url: Optional[str] = None):
        """
        :param host_url: Base Teamcenter REST URL, e.g. 'http://tcserver:8080/tc' or 'https://aw.company.com/tc'
        :param fms_url: Base FMS / FCC File Upload Server URL (default: derives from host_url)
        """
        self.host_url = host_url.rstrip('/')
        self.fms_url = fms_url.rstrip('/') if fms_url else f"{self.host_url}/fms"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.user_uid: Optional[str] = None
        self.is_authenticated: bool = False

    # =========================================================================
    # CORE AUTHENTICATION & SESSION MANAGEMENT
    # =========================================================================
    def login(self, username: str, password: str, group: str = "", role: str = "") -> bool:
        """Authenticate with Teamcenter Server and maintain active session."""
        url = f"{self.host_url}/rest/v1/Core-2011-06-Session/login"
        payload = {
            "header": {},
            "body": {
                "id": username,
                "password": password,
                "group": group,
                "role": role,
                "discriminator": "Python_PLM_Automation_Suite"
            }
        }
        try:
            response = self.session.post(url, json=payload, timeout=30)
            if response.status_code == 200 and "user" in response.text.lower():
                data = response.json()
                self.user_uid = data.get("body", {}).get("user", {}).get("uid", "")
                self.is_authenticated = True
                logger.info(f"Successfully authenticated to Teamcenter as user '{username}'.")
                return True
            else:
                logger.error(f"Login failed [{response.status_code}]: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Authentication exception: {str(e)}")
            return False

    def logout(self):
        """Gracefully terminate Teamcenter session."""
        if not self.is_authenticated:
            return
        url = f"{self.host_url}/rest/v1/Core-2006-03-Session/logout"
        try:
            self.session.post(url, json={"header": {}, "body": {}}, timeout=10)
            logger.info("Teamcenter session logged out successfully.")
        except Exception as e:
            logger.warning(f"Logout warning: {str(e)}")
        finally:
            self.is_authenticated = False

    # =========================================================================
    # MODULE 1: ITEM & BOM (STRUCTURE) MANAGEMENT
    # =========================================================================
    def create_item(self, item_id: str, name: str, item_type: str = "Item", 
                    description: str = "", rev_id: str = "A") -> Optional[Dict[str, Any]]:
        """
        Create a new Item and ItemRevision in Teamcenter.
        """
        url = f"{self.host_url}/rest/v1/Core-2008-06-DataManagement/createItems"
        payload = {
            "header": {},
            "body": {
                "properties": [{
                    "clientId": f"req_{item_id}",
                    "itemId": item_id,
                    "name": name,
                    "type": item_type,
                    "description": description,
                    "revId": rev_id
                }],
                "container": {},
                "relationType": ""
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            logger.info(f"[MODULE 1] Created Item '{item_id}' ({name}) [Type: {item_type}]")
            return data.get("body", {})
        else:
            logger.error(f"[MODULE 1] Failed to create item {item_id}: {res.text}")
            return None

    def update_properties(self, object_uid: str, object_type: str, properties: Dict[str, Any]) -> bool:
        """
        Update business object metadata attributes in Teamcenter.
        properties = {"object_name": "Updated Name", "d4_material": "Steel 316L"}
        """
        url = f"{self.host_url}/rest/v1/Core-2010-09-DataManagement/setProperties"
        vec_props = []
        for key, val in properties.items():
            vec_props.append({"name": key, "values": [str(val)]})

        payload = {
            "header": {},
            "body": {
                "info": [{
                    "object": {"uid": object_uid, "type": object_type},
                    "timestamp": "",
                    "vecNameVal": vec_props
                }]
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            logger.info(f"[MODULE 1] Updated properties for UID {object_uid}: {list(properties.keys())}")
            return True
        else:
            logger.error(f"[MODULE 1] Property update failed: {res.text}")
            return False

    def create_bom_structure(self, parent_rev_uid: str, child_rev_uids: List[str]) -> Optional[str]:
        """
        Build parent-child BOM assembly structure in Teamcenter.
        Creates a BOMWindow, opens parent, and adds children occurrences.
        """
        # 1. Create BOM Window
        url_win = f"{self.host_url}/rest/v1/Cad-2007-01-StructureManagement/createBOMWindows"
        payload_win = {
            "header": {},
            "body": {
                "info": [{"itemRev": {"uid": parent_rev_uid, "type": "ItemRevision"}}]
            }
        }
        res_win = self.session.post(url_win, json=payload_win)
        if res_win.status_code != 200:
            logger.error(f"[MODULE 1] BOM Window creation failed: {res_win.text}")
            return None

        bom_data = res_win.json()
        bom_window_uid = bom_data.get("body", {}).get("output", [{}])[0].get("bomWindow", {}).get("uid")
        parent_bom_line = bom_data.get("body", {}).get("output", [{}])[0].get("bomLine", {}).get("uid")

        # 2. Add Children to BOM Line
        url_add = f"{self.host_url}/rest/v1/Cad-2008-06-StructureManagement/addBOMChildren"
        child_inputs = [{"itemRev": {"uid": uid, "type": "ItemRevision"}} for uid in child_rev_uids]
        payload_add = {
            "header": {},
            "body": {
                "input": [{
                    "parentBOMLine": {"uid": parent_bom_line, "type": "BOMLine"},
                    "childItems": child_inputs
                }]
            }
        }
        res_add = self.session.post(url_add, json=payload_add)
        if res_add.status_code == 200:
            logger.info(f"[MODULE 1] Added {len(child_rev_uids)} children to parent BOM Revision {parent_rev_uid}")
            return bom_window_uid
        else:
            logger.error(f"[MODULE 1] Failed to add children to BOM: {res_add.text}")
            return None

    # =========================================================================
    # MODULE 2: CAD & DATASET IMPORT / EXPORT (FMS TICKET PROTOCOL)
    # =========================================================================
    def create_dataset_and_attach(self, parent_rev_uid: str, dataset_name: str, 
                                 dataset_type: str = "DirectModel", relation_type: str = "TC_Attaches") -> Optional[str]:
        """
        Create a Dataset object (JT, PDF, Text, UGMASTER) and relate it to an ItemRevision.
        """
        url = f"{self.host_url}/rest/v1/Core-2010-04-DataManagement/createDatasets"
        payload = {
            "header": {},
            "body": {
                "input": [{
                    "clientId": f"ds_{dataset_name}",
                    "name": dataset_name,
                    "type": dataset_type,
                    "datasetId": "",
                    "description": "Uploaded via Python Automation",
                    "container": {"uid": parent_rev_uid, "type": "ItemRevision"},
                    "relationType": relation_type
                }]
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            ds_uid = data.get("body", {}).get("datasetOutput", [{}])[0].get("dataset", {}).get("uid")
            logger.info(f"[MODULE 2] Created Dataset '{dataset_name}' [Type: {dataset_type}] UID: {ds_uid}")
            return ds_uid
        else:
            logger.error(f"[MODULE 2] Dataset creation failed: {res.text}")
            return None

    def upload_file_to_dataset(self, dataset_uid: str, local_file_path: str, named_ref: str = "JTSPEC") -> bool:
        """
        Upload local CAD/PDF file to Dataset using FMS Write Ticket protocol.
        """
        if not os.path.exists(local_file_path):
            logger.error(f"[MODULE 2] Local file not found: {local_file_path}")
            return False

        filename = os.path.basename(local_file_path)

        # 1. Request FMS Write PLMD Ticket
        ticket_url = f"{self.host_url}/rest/v1/Core-2006-03-FileManagement/getWritePLMDTickets"
        ticket_payload = {
            "header": {},
            "body": {
                "inputs": [{
                    "dataset": {"uid": dataset_uid, "type": "Dataset"},
                    "createNewVersion": True,
                    "fileInputs": [{
                        "fileName": filename,
                        "namedReferencedName": named_ref,
                        "isText": False
                    }]
                }]
            }
        }
        res_ticket = self.session.post(ticket_url, json=ticket_payload)
        if res_ticket.status_code != 200:
            logger.error(f"[MODULE 2] Failed to obtain FMS write ticket: {res_ticket.text}")
            return False

        ticket_data = res_ticket.json()
        ticket = ticket_data.get("body", {}).get("tickets", [{}])[0].get("ticket")

        # 2. Upload Binary File to FMS Server
        upload_url = f"{self.fms_url}/fcc/upload"
        with open(local_file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            headers = {'fmsTicket': ticket}
            res_upload = requests.post(upload_url, files=files, headers=headers)

        if res_upload.status_code in [200, 201]:
            logger.info(f"[MODULE 2] Uploaded file '{filename}' to Dataset UID {dataset_uid} via FMS.")
            return True
        else:
            logger.error(f"[MODULE 2] FMS file upload failed: {res_upload.text}")
            return False

    # =========================================================================
    # MODULE 3: WORKFLOW & APPROVAL AUTOMATION
    # =========================================================================
    def trigger_workflow(self, process_template: str, target_uids: List[str], process_name: str = "") -> bool:
        """
        Submit target objects (Items, Revisions, Datasets) to a Teamcenter Workflow Process.
        """
        url = f"{self.host_url}/rest/v1/Workflow-2008-06-Workflow/createInstance"
        targets = [{"uid": uid, "type": "WorkspaceObject"} for uid in target_uids]
        p_name = process_name if process_name else f"Auto_Release_{process_template}"

        payload = {
            "header": {},
            "body": {
                "startImmediately": True,
                "observerLocation": "",
                "processTemplate": process_template,
                "processName": p_name,
                "processDescription": "Automated workflow trigger via Python PLM Suite",
                "targetObjects": targets
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            logger.info(f"[MODULE 3] Triggered Workflow '{process_template}' for {len(target_uids)} targets.")
            return True
        else:
            logger.error(f"[MODULE 3] Workflow trigger failed: {res.text}")
            return False

    def perform_task_signoff(self, task_uid: str, action: str = "Approve", comments: str = "Approved via Python") -> bool:
        """
        Perform automated sign-off (Approve / Reject) on a Workflow Task.
        """
        url = f"{self.host_url}/rest/v1/Workflow-2014-06-Workflow/performAction3"
        payload = {
            "header": {},
            "body": {
                "input": [{
                    "task": {"uid": task_uid, "type": "EPMTask"},
                    "action": action,
                    "close": True,
                    "comments": comments,
                    "password": ""
                }]
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            logger.info(f"[MODULE 3] Task UID {task_uid} signed off with action '{action}'.")
            return True
        else:
            logger.error(f"[MODULE 3] Signoff failed: {res.text}")
            return False

    # =========================================================================
    # MODULE 4: DATA SYNCHRONIZATION & EXPORT
    # =========================================================================
    def execute_saved_query(self, query_name: str, entries: List[str], values: List[str]) -> List[Dict[str, Any]]:
        """
        Run a Teamcenter Saved Query and return matching objects.
        """
        url = f"{self.host_url}/rest/v1/Query-2010-04-SavedQuery/executeSavedQueries"
        payload = {
            "header": {},
            "body": {
                "input": [{
                    "query": {"queryName": query_name},
                    "entries": entries,
                    "values": values,
                    "maxNumToReturn": 100
                }]
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            objects = data.get("body", {}).get("arrayOfResults", [{}])[0].get("objectOfResults", [])
            logger.info(f"[MODULE 4] Query '{query_name}' returned {len(objects)} object results.")
            return objects
        else:
            logger.error(f"[MODULE 4] Query execution failed: {res.text}")
            return []

    def export_query_results_to_csv(self, query_name: str, entries: List[str], values: List[str], output_csv_path: str) -> bool:
        """
        Query Teamcenter objects and export metadata directly to a CSV spreadsheet.
        """
        results = self.execute_saved_query(query_name, entries, values)
        if not results:
            logger.warning("[MODULE 4] No data to export.")
            return False

        fieldnames = ["UID", "Type", "Name", "Query_Name"]
        try:
            with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for obj in results:
                    writer.writerow({
                        "UID": obj.get("uid"),
                        "Type": obj.get("type"),
                        "Name": obj.get("props", {}).get("object_name", {}).get("uiValue", "N/A"),
                        "Query_Name": query_name
                    })
            logger.info(f"[MODULE 4] Exported query results to CSV file: {output_csv_path}")
            return True
        except Exception as e:
            logger.error(f"[MODULE 4] CSV Export exception: {str(e)}")
            return False

    # =========================================================================
    # MODULE 5: BATCH PROCESSING & CLI RUNNER
    # =========================================================================
    def batch_process_items_from_csv(self, csv_file_path: str) -> Dict[str, int]:
        """
        Batch import/create multiple Items & Revisions from an input CSV file.
        CSV Columns expected: ItemID, Name, ItemType, Description
        """
        stats = {"success": 0, "failed": 0}
        if not os.path.exists(csv_file_path):
            logger.error(f"[MODULE 5] Batch CSV file not found: {csv_file_path}")
            return stats

        logger.info(f"[MODULE 5] Starting batch import from: {csv_file_path}")
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                item_id = row.get("ItemID")
                name = row.get("Name")
                itype = row.get("ItemType", "Item")
                desc = row.get("Description", "")

                res = self.create_item(item_id=item_id, name=name, item_type=itype, description=desc)
                if res:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

        logger.info(f"[MODULE 5] Batch Processing Completed. Success: {stats['success']}, Failed: {stats['failed']}")
        return stats

    # =========================================================================
    # MODULE 6: CAPP (MANUFACTURING) & EDN (ENGINEERING CHANGE) AUTOMATION
    # =========================================================================
    def update_capp_activity_ti_time(self, activity_uid: str, estimated_time_seconds: float, 
                                     frequency: float = 1.0, user_time: float = 0.0) -> bool:
        """
        Update CAPP (Computer-Aided Process Planning) Activity Time Instructions (TI).
        Updates properties on MEActivity / METask / MEProcess manufacturing objects.
        """
        properties = {
            "time_system_frequency": str(frequency),
            "user_time": str(user_time),
            "allocated_time": str(estimated_time_seconds),
            "estimated_time": str(estimated_time_seconds)
        }
        logger.info(f"[CAPP AUTOMATION] Updating TI Time to {estimated_time_seconds}s for CAPP Activity UID {activity_uid}")
        return self.update_properties(object_uid=activity_uid, object_type="MEActivity", properties=properties)

    def attach_edn_to_part(self, part_rev_uid: str, edn_uid: str, relation_type: str = "CMHasSolutionItem") -> bool:
        """
        Attach an EDN (Engineering Data Notice) or ECN (Change Notice) under a Part Revision.
        Relation Types: 'CMHasSolutionItem' (Solution Part), 'CMHasImpactedItem' (Impacted Part), 'CMHasProblemItem' (Problem Part)
        """
        url = f"{self.host_url}/rest/v1/Core-2006-03-DataManagement/createRelations"
        payload = {
            "header": {},
            "body": {
                "input": [{
                    "primaryObject": {"uid": edn_uid, "type": "EngineeringChange"},
                    "secondaryObject": {"uid": part_rev_uid, "type": "ItemRevision"},
                    "relationType": relation_type,
                    "userData": {}
                }]
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            logger.info(f"[EDN AUTOMATION] Successfully attached EDN UID {edn_uid} to Part Rev UID {part_rev_uid} via '{relation_type}'")
            return True
        else:
            logger.error(f"[EDN AUTOMATION] Failed to attach EDN: {res.text}")
            return False

    def remove_edn_from_part(self, part_rev_uid: str, edn_uid: str, relation_type: str = "CMHasSolutionItem") -> bool:
        """
        Remove/Detach an EDN or ECN relation from a Part Revision in Teamcenter.
        """
        url = f"{self.host_url}/rest/v1/Core-2006-03-DataManagement/deleteRelations"
        payload = {
            "header": {},
            "body": {
                "input": [{
                    "primaryObject": {"uid": edn_uid, "type": "EngineeringChange"},
                    "secondaryObject": {"uid": part_rev_uid, "type": "ItemRevision"},
                    "relationType": relation_type
                }]
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            logger.info(f"[EDN AUTOMATION] Successfully removed EDN UID {edn_uid} from Part Rev UID {part_rev_uid}")
            return True
        else:
            logger.error(f"[EDN AUTOMATION] Failed to remove EDN relation: {res.text}")
            return False

    def get_edns_under_part(self, part_rev_uid: str, relation_type: str = "CMHasSolutionItem") -> List[Dict[str, Any]]:
        """
        Find and expand all EDNs (Engineering Data Notices) attached under a given Part Revision.
        """
        url = f"{self.host_url}/rest/v1/Core-2007-09-DataManagement/expandGRMRelationsForPrimary"
        payload = {
            "header": {},
            "body": {
                "primaryObjects": [{"uid": part_rev_uid, "type": "ItemRevision"}],
                "pref": {
                    "expBy": "primary_object",
                    "info": [{
                        "relationTypeName": relation_type,
                        "otherSideObjectTypes": ["EngineeringChange", "Folder", "Dataset"]
                    }]
                }
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            edn_list = data.get("body", {}).get("output", [{}])[0].get("relationshipData", [{}])[0].get("relationshipObjects", [])
            logger.info(f"[EDN AUTOMATION] Found {len(edn_list)} EDNs under Part Rev UID {part_rev_uid}")
            return edn_list
        else:
            logger.error(f"[EDN AUTOMATION] Failed to get EDNs for Part: {res.text}")
            return []

    def delete_edn_permanently(self, edn_uid: str) -> bool:
        """
        Permanently delete an EDN object from Teamcenter database (POM Delete).
        """
        url = f"{self.host_url}/rest/v1/Core-2006-03-DataManagement/deleteObjects"
        payload = {
            "header": {},
            "body": {
                "objects": [{"uid": edn_uid, "type": "EngineeringChange"}]
            }
        }
        res = self.session.post(url, json=payload)
        if res.status_code == 200:
            logger.info(f"[EDN AUTOMATION] Permanently deleted EDN object UID {edn_uid} from Teamcenter.")
            return True
        else:
            logger.error(f"[EDN AUTOMATION] Permanent deletion failed: {res.text}")
            return False




# =============================================================================
# COMMAND LINE INTERFACE (CLI) & BATCH DRIVER
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Teamcenter Enterprise PLM Python Automation Suite")
    parser.add_argument("--host", default="http://localhost:8080/tc", help="Teamcenter Web Tier URL")
    parser.add_argument("--user", required=True, help="Teamcenter Username (e.g. infodba)")
    parser.add_argument("--password", required=True, help="Teamcenter Password")
    parser.add_argument("--action", choices=["create_item", "batch_csv", "export_query", "trigger_wf"], required=True)
    
    # Action specific args
    parser.add_argument("--item-id", help="Item ID for create_item action")
    parser.add_argument("--name", help="Name for item")
    parser.add_argument("--csv-file", help="CSV File path for batch processing or query export")
    parser.add_argument("--query-name", help="Teamcenter Saved Query name")
    parser.add_argument("--template", help="Workflow Process Template name")
    parser.add_argument("--target-uid", help="Target Object UID for workflow trigger")

    args = parser.parse_args()

    # Initialize Client Suite
    tc = TeamcenterPLMSuite(host_url=args.host)
    if not tc.login(username=args.user, password=args.password):
        sys.exit(1)

    try:
        if args.action == "create_item":
            if not args.item_id or not args.name:
                print("Error: --item-id and --name are required for create_item action.")
            else:
                tc.create_item(item_id=args.item_id, name=args.name)

        elif args.action == "batch_csv":
            if not args.csv_file:
                print("Error: --csv-file is required for batch_csv action.")
            else:
                tc.batch_process_items_from_csv(args.csv_file)

        elif args.action == "export_query":
            if not args.query_name or not args.csv_file:
                print("Error: --query-name and --csv-file are required for export_query.")
            else:
                tc.export_query_results_to_csv(
                    query_name=args.query_name,
                    entries=["Item ID"],
                    values=["*"],
                    output_csv_path=args.csv_file
                )

        elif args.action == "trigger_wf":
            if not args.template or not args.target_uid:
                print("Error: --template and --target-uid are required for trigger_wf.")
            else:
                tc.trigger_workflow(process_template=args.template, target_uids=[args.target_uid])

    finally:
        tc.logout()


if __name__ == "__main__":
    main()
