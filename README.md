# Siemens Teamcenter PLM Enterprise Automation Suite

A production-grade Python automation framework for Siemens Teamcenter PLM (Active Workspace & Rich Client / Web Tier). This suite automates key engineering, manufacturing (CAPP), change management (EDN/ECN), and data synchronization operations using native Teamcenter SOA REST APIs.

---

## Table of Contents
1. [Architecture & Network Access](#architecture--network-access)
2. [Module Guide & API Capabilities](#module-guide--api-capabilities)
   - [Module 1: Item & BOM Structure Management](#module-1-item--bom-structure-management)
   - [Module 2: CAD & Dataset Import/Export (FMS Tickets)](#module-2-cad--dataset-importexport-fms-tickets)
   - [Module 3: Workflow & Approval Automation](#module-3-workflow--approval-automation)
   - [Module 4: Data Synchronization & CSV Export](#module-4-data-synchronization--csv-export)
   - [Module 5: Batch Processing Engine](#module-5-batch-processing-engine)
   - [Module 6: CAPP (Manufacturing) & EDN Management](#module-6-capp-manufacturing--edn-management)
3. [Configuration Guide (`config.json`)](#configuration-guide-configjson)
4. [Installation & Quick Start](#installation--quick-start)
5. [Command Line Interface (CLI) Usage](#command-line-interface-cli-usage)
6. [Git & Deployment Setup](#git--deployment-setup)

---

## Architecture & Network Access

The automation suite connects directly to the **Teamcenter Web Tier / Active Workspace Gateway** over standard HTTP/HTTPS REST endpoints.

```
+-----------------------------------+      HTTPS REST (Port 443 / 8080)     +-----------------------------------+
|  Python Automation Suite          | ------------------------------------> | Teamcenter Web Tier / Gateway     |
|  (Local / CI-CD / Batch Server)   |                                       | (Active Workspace Pool Manager)   |
+-----------------------------------+                                       +-----------------------------------+
                                                                                              |
                                                                       FMS Write Ticket / FCC (Port 4544)
                                                                                              v
                                                                            +-----------------------------------+
                                                                            | Teamcenter Database & Volumes     |
                                                                            +-----------------------------------+
```

### Network Requirements:
* **Network Access**: Needs HTTPS connectivity to your Teamcenter server (e.g., `https://tcweb.company.com/tc` or `http://tcserver:8080/tc`) via corporate LAN or VPN.
* **Authentication**: Supports standard password authentication, Active Directory / LDAP, and SAML/OAuth2 Single Sign-On (SSO) session headers.
* **FMS Ticket Transfer**: File uploads (JT, CAD, PDF) use Teamcenter's official FMS Write Ticket protocol to stream binary data straight into TC volume storage.

---

## Module Guide & API Capabilities

### Module 1: Item & BOM Structure Management
Automates the lifecycle creation of Items, ItemRevisions, attribute updates, and parent-child BOM structures.

* **`create_item(item_id, name, item_type="Item", description="", rev_id="A")`**
  Creates an Item and revision in Teamcenter via `/Core-2008-06-DataManagement/createItems`.
* **`update_properties(object_uid, object_type, properties)`**
  Updates BMIDE metadata attributes on any object via `/Core-2010-09-DataManagement/setProperties`.
* **`create_bom_structure(parent_rev_uid, child_rev_uids)`**
  Instantiates a `BOMWindow`, opens the parent revision, and appends child `BOMLine` occurrences via Structure Management SOA.

---

### Module 2: CAD & Dataset Import/Export (FMS Tickets)
Manages file attachments (PDFs, JT 3D models, NX UGMASTER) linked to ItemRevisions.

* **`create_dataset_and_attach(parent_rev_uid, dataset_name, dataset_type="DirectModel", relation_type="TC_Attaches")`**
  Creates a Dataset object and attaches it to an ItemRevision.
* **`upload_file_to_dataset(dataset_uid, local_file_path, named_ref="JTSPEC")`**
  Obtains an FMS PLMD Write Ticket from Teamcenter (`/Core-2006-03-FileManagement/getWritePLMDTickets`) and uploads the local file directly to Teamcenter Volume storage.

---

### Module 3: Workflow & Approval Automation
Submits engineering objects to Teamcenter Workflow Process Templates and automates task sign-offs.

* **`trigger_workflow(process_template, target_uids, process_name="")`**
  Initiates a workflow process (e.g. *Fast Track Release*, *ECN Process*) for target UIDs via `/Workflow-2008-06-Workflow/createInstance`.
* **`perform_task_signoff(task_uid, action="Approve", comments="")`**
  Signs off workflow tasks programmatically via `/Workflow-2014-06-Workflow/performAction3`.

---

### Module 4: Data Synchronization & CSV Export
Queries Teamcenter objects and extracts metadata reports.

* **`execute_saved_query(query_name, entries, values)`**
  Runs Teamcenter Saved Queries (e.g., `Item ID...`, `Item Name...`) via `/Query-2010-04-SavedQuery/executeSavedQueries`.
* **`export_query_results_to_csv(query_name, entries, values, output_csv_path)`**
  Exports query results and metadata attributes directly into a structured CSV file.

---

### Module 5: Batch Processing Engine
Performs mass creation of Parts/Revisions from CSV data sources.

* **`batch_process_items_from_csv(csv_file_path)`**
  Parses a CSV file (`ItemID`, `Name`, `ItemType`, `Description`) and batch-imports items with error logging and success statistics.

---

### Module 6: CAPP (Manufacturing) & EDN Management

#### Computer-Aided Process Planning (CAPP) & TI Updates:
* **`update_capp_activity_ti_time(activity_uid, estimated_time_seconds, frequency=1.0, user_time=0.0)`**
  Updates Time Instruction (TI) time standards (`allocated_time`, `estimated_time`, `user_time`, `time_system_frequency`) on CAPP manufacturing activities (`MEActivity`, `METask`, `MEProcess`).

#### EDN (Engineering Data Notice) & Change Notice Management:
* **`get_edns_under_part(part_rev_uid, relation_type="CMHasSolutionItem")`**
  Expands GRM relations (`Core-2007-09-DataManagement/expandGRMRelationsForPrimary`) under any Part Revision to list all linked EDNs.
* **`attach_edn_to_part(part_rev_uid, edn_uid, relation_type="CMHasSolutionItem")`**
  Links an EDN under a Part Revision via `/Core-2006-03-DataManagement/createRelations`.
  *Relation types*: `CMHasSolutionItem` (Solution Part), `CMHasImpactedItem` (Impacted Part), `CMHasProblemItem` (Problem Part).
* **`remove_edn_from_part(part_rev_uid, edn_uid, relation_type="CMHasSolutionItem")`**
  Detaches an EDN relation from a Part Revision via `/Core-2006-03-DataManagement/deleteRelations` while retaining the EDN record in Teamcenter.
* **`delete_edn_permanently(edn_uid)`**
  Permanently deletes an EDN object from Teamcenter database (`/Core-2006-03-DataManagement/deleteObjects`).

---

## Configuration Guide (`config.json`)

Configure your connection settings in `config.json`:

```json
{
  "teamcenter": {
    "host_url": "http://your-tc-server:8080/tc",
    "fms_url": "http://your-tc-server:8080/fms",
    "default_user": "infodba",
    "group": "",
    "role": ""
  },
  "edn_settings": {
    "default_relation": "CMHasSolutionItem",
    "impacted_relation": "CMHasImpactedItem",
    "problem_relation": "CMHasProblemItem"
  },
  "capp_settings": {
    "default_time_unit": "sec",
    "default_frequency": 1.0
  },
  "logging": {
    "log_file": "teamcenter_automation.log",
    "level": "INFO"
  }
}
```

---

## Installation & Quick Start

1. **Prerequisites**: Python 3.8+ and `requests` library.
   ```bash
   pip install requests
   ```

2. **Run Demo Pipeline**:
   ```bash
   python3 run_automation_demo.py
   ```

---

## Command Line Interface (CLI) Usage

### 1. Batch Import Items from CSV:
```bash
python3 teamcenter_plm_automation.py \
  --host "http://your-tc-server:8080/tc" \
  --user "infodba" \
  --password "your_password" \
  --action batch_csv \
  --csv-file "batch_items_sample.csv"
```

### 2. Create Single Item:
```bash
python3 teamcenter_plm_automation.py \
  --host "http://your-tc-server:8080/tc" \
  --user "infodba" \
  --password "your_password" \
  --action create_item \
  --item-id "PART-9001" \
  --name "Compressor Valve"
```

### 3. Export Query Results to CSV:
```bash
python3 teamcenter_plm_automation.py \
  --host "http://your-tc-server:8080/tc" \
  --user "infodba" \
  --password "your_password" \
  --action export_query \
  --query-name "Item ID..." \
  --csv-file "export_output.csv"
```

---

## Repository Structure

```
.
├── teamcenter_plm_automation.py   # Core Teamcenter SOA Automation Library (Modules 1 - 6)
├── run_automation_demo.py          # Pipeline Runner & Execution Demo
├── config.json                     # Environment & Connection Configuration
├── batch_items_sample.csv          # Sample CSV Data Template for Batch Import
├── README.md                       # Comprehensive Documentation
└── .gitignore                      # Git Ignore Configuration
```
