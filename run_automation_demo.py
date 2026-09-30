"""
Teamcenter PLM Automation End-to-End Execution Script
=====================================================
Demonstrates full automated workflow across:
 - Session Authentication
 - Item Creation & Property Updating
 - CAPP TI Time Updates
 - EDN (Engineering Data Notice) Search, Attach, and Detach
 - Workflow Submissions
 - Data Export to CSV
"""

import sys
import json
import logging
from teamcenter_plm_automation import TeamcenterPLMSuite

def run_pipeline():
    # Load configuration
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return

    tc_conf = config.get("teamcenter", {})
    host_url = tc_conf.get("host_url")
    username = tc_conf.get("default_user")

    print("===============================================================")
    print("      TEAMCENTER PLM COMPLETE AUTOMATION PIPELINE RUNNER       ")
    print("===============================================================")
    print(f"Connecting to Teamcenter Server: {host_url}")

    # Initialize Automation Suite
    tc = TeamcenterPLMSuite(host_url=host_url)

    # Prompt or use configured credentials
    password = "your_password"  # Replace with actual password or secure prompt

    # 1. Login
    print("\n[STEP 1] Authenticating with Teamcenter...")
    login_success = tc.login(username=username, password=password)
    if not login_success:
        print("Note: Login failed because server URL is a placeholder. Update 'config.json' with your actual Teamcenter server URL and credentials.")
        print("\nDemonstrating script structure and available functions successfully loaded!")
        return

    try:
        # 2. Item & BOM Creation
        print("\n[STEP 2] Creating Part Item & Revision...")
        item_data = tc.create_item(
            item_id="PART-2026-X1",
            name="Turbine Housing Assembly",
            item_type="Design",
            description="Automated High-Temp Turbine Housing"
        )

        # 3. CAPP TI Time Updates
        print("\n[STEP 3] Updating CAPP Process Planning TI Times...")
        tc.update_capp_activity_ti_time(
            activity_uid="capp_activity_uid_sample",
            estimated_time_seconds=240.0,
            frequency=1.0
        )

        # 4. EDN Attachment & Removal
        print("\n[STEP 4] Managing EDNs under Part Revision...")
        part_rev_uid = "sample_part_rev_uid"
        edn_uid = "sample_edn_uid"

        print("-> Attaching EDN under Part Number...")
        tc.attach_edn_to_part(part_rev_uid=part_rev_uid, edn_uid=edn_uid)

        print("-> Querying EDNs under Part Number...")
        edns = tc.get_edns_under_part(part_rev_uid=part_rev_uid)

        print("-> Detaching EDN from Part Number...")
        tc.remove_edn_from_part(part_rev_uid=part_rev_uid, edn_uid=edn_uid)

        # 5. Workflow Submission
        print("\n[STEP 5] Triggering Release Workflow...")
        tc.trigger_workflow(
            process_template="TCM Release Process",
            target_uids=[part_rev_uid]
        )

        # 6. Batch CSV Export
        print("\n[STEP 6] Exporting Query Results to CSV...")
        tc.export_query_results_to_csv(
            query_name="Item ID...",
            entries=["Item ID"],
            values=["PART-2026*"],
            output_csv_path="output_parts_export.csv"
        )

        print("\n[SUCCESS] Pipeline executed successfully!")

    finally:
        # 7. Logout
        print("\n[STEP 7] Logging out from Teamcenter...")
        tc.logout()

if __name__ == "__main__":
    run_pipeline()
