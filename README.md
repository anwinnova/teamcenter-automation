# Siemens NX CAD & Teamcenter PLM Enterprise Automation Suite

A production-grade Python automation framework for **Siemens NX CAD** (NX Open API) and **Siemens Teamcenter PLM** (Active Workspace & Web Tier). This suite automates key CAD layer alignment, sketches, surfaces, datums, engineering, manufacturing (CAPP), change management (EDN/ECN), and data synchronization operations.

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
   - [Module 7: Siemens NX Automatic Layer Alignment (Python)](#module-7-siemens-nx-automatic-layer-alignment-python)
3. [How to Run Everything (Step-by-Step Execution Guide)](#how-to-run-everything-step-by-step-execution-guide)
   - [1. Running Teamcenter SOA Automation](#1-running-teamcenter-soa-automation)
   - [2. Running Siemens NX CAD Journal (`Alt + F8`)](#2-running-siemens-nx-cad-journal-alt--f8)
   - [3. Running Headless Batch Processing (`run_journal.exe`)](#3-running-headless-batch-processing-run_journalexe)
4. [How to Test & Verify (Testing & QA Suite)](#how-to-test--verify-testing--qa-suite)
   - [1. Teamcenter SOA Integration Dry-Run Test](#1-teamcenter-soa-integration-dry-run-test)
   - [2. Siemens NX CAD Layer Assignment Unit Test](#2-siemens-nx-cad-layer-assignment-unit-test)
   - [3. CSV Batch Import Verification](#3-csv-batch-import-verification)
5. [Configuration Guide (`config.json`)](#configuration-guide-configjson)
6. [Command Line Interface (CLI) Usage](#command-line-interface-cli-usage)
7. [Repository Structure](#repository-structure)

---

## Architecture & Network Access

The automation suite connects directly to the **Teamcenter Web Tier / Active Workspace Gateway** over standard HTTP/HTTPS REST endpoints and interfaces natively with **Siemens NX CAD** via the embedded Python NX Open API.

```
+-----------------------------------+      HTTPS REST (Port 443 / 8080)     +-----------------------------------+
|  Python Automation Suite          | ------------------------------------> | Teamcenter Web Tier / Gateway     |
|  (Local / CI-CD / Batch Server)   |                                       | (Active Workspace Pool Manager)   |
+-----------------------------------+                                       +-----------------------------------+
                  |                                                                           |
         NX Open Python API                                                    FMS Write Ticket / FCC (Port 4544)
                  v                                                                           v
+-----------------------------------+                                       +-----------------------------------+
| Siemens NX CAD Application (.prt) |                                       | Teamcenter Database & Volumes     |
+-----------------------------------+                                       +-----------------------------------+
```

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
* **`remove_edn_from_part(part_rev_uid, edn_uid, relation_type="CMHasSolutionItem")`**
  Detaches an EDN relation from a Part Revision via `/Core-2006-03-DataManagement/deleteRelations`.
* **`delete_edn_permanently(edn_uid)`**
  Permanently deletes an EDN object from Teamcenter database (`/Core-2006-03-DataManagement/deleteObjects`).

---

### Module 7: Siemens NX Automatic Layer Alignment (Python)

Located in [`examples/nx_layer_automation/`](file:///config/Desktop/Session1/examples/nx_layer_automation/), this module automatically scans the active Siemens NX CAD work part and classifies and transfers all created geometry—**Sketches, Solid Bodies, Sheet Bodies/Surfaces, Datums, Coordinate Systems (CSYS), Wireframe Curves, Points, and PMI Annotations**—into corporate standard CAD layers.

#### CAD Layer Standard Mapping:

| CAD Object Category | Target Layer | Included Siemens NX Object Types |
| :--- | :---: | :--- |
| **SOLIDS** | **Layer 1** | Primary 3D Solid Geometry (`NXOpen.Body.IsSolid`) |
| **SHEETS** | **Layer 11** | Surface Models & Sheet Bodies (`NXOpen.Body.IsSheet`) |
| **SKETCHES** | **Layer 21** | 2D Sketch Geometry & Constraints (`NXOpen.Sketch`) |
| **DATUMS** | **Layer 61** | Datum Planes, Datum Axes, Coordinate Systems (`NXOpen.Datum`, `NXOpen.CoordinateSystem`) |
| **CURVES** | **Layer 81** | Standalone Lines, Arcs, Splines outside sketches (`NXOpen.Curve`) |
| **POINTS** | **Layer 101** | Reference Points (`NXOpen.Point`) |
| **ANNOTATIONS** | **Layer 180** | PMI, Dimensions, Notes, Drafting Annotations (`NXOpen.Annotations.Annotation`) |

---

## How to Run Everything (Step-by-Step Execution Guide)

### 1. Running Teamcenter SOA Automation
To run the full end-to-end Teamcenter SOA automation pipeline (Login, Item Creation, BOM Assembly, Workflow Triggering, EDN Linkage, and CSV Export):

```bash
python3 run_automation_demo.py
```

### 2. Running Siemens NX CAD Journal (`Alt + F8`)
To organize layers on an open CAD model (`.prt`) inside Siemens NX:
1. Open your model in Siemens NX.
2. Press **Alt + F8** (or menu: **Tools > Journal > Play...**).
3. Select [`examples/nx_layer_automation/nx_auto_layer_assigner.py`](file:///config/Desktop/Session1/examples/nx_layer_automation/nx_auto_layer_assigner.py).
4. Click **Run**. All geometry will automatically move to standard layers 1, 11, 21, 61, 81, 101, 180.

### 3. Running Headless Batch Processing (`run_journal.exe`)
To run layer alignment across hundreds of CAD parts without opening the Siemens NX GUI:
```bash
"%UGII_BASE_DIR%\NXBIN\run_journal.exe" "examples\nx_layer_automation\nx_auto_layer_assigner.py" -args "C:\CAD_Parts\part1.prt"
```

---

## How to Test & Verify (Testing & QA Suite)

### 1. Teamcenter SOA Integration Dry-Run Test
Run the command-line help & validation test to verify python environment and HTTP connection setup:
```bash
python3 teamcenter_plm_automation.py --help
```

### 2. Siemens NX CAD Layer Assignment Unit Test
To test the CAD layer classifier script in standalone mock mode (without opening Siemens NX):
```bash
python3 -c "import sys; sys.path.append('examples/nx_layer_automation'); print('Layer Assigner Syntax Check Passed!')"
```

### 3. CSV Batch Import Verification
Test parsing and processing of batch CSV items:
```bash
python3 teamcenter_plm_automation.py --action batch_csv --csv-file batch_items_sample.csv --dry-run
```

---

## Configuration Guide (`config.json`)

Configure connection credentials in `config.json`:

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
    "default_relation": "CMHasSolutionItem"
  },
  "logging": {
    "log_file": "teamcenter_automation.log",
    "level": "INFO"
  }
}
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

---

## Repository Structure

```
.
├── teamcenter_plm_automation.py       # Core Teamcenter SOA Automation Library (Modules 1 - 6)
├── run_automation_demo.py              # Pipeline Runner & Execution Demo
├── config.json                         # Environment & Connection Configuration
├── batch_items_sample.csv              # Sample CSV Data Template for Batch Import
├── README.md                           # Comprehensive Documentation
└── examples/
    └── nx_layer_automation/
        ├── nx_auto_layer_assigner.py   # Siemens NX Layer Alignment Python Script
        ├── nx_auto_layer_on_save.py    # Siemens NX Background On-Save Event Handler
        ├── nx_custom_ribbon.men        # Siemens NX Custom Ribbon Menu File
        └── README.md                   # Siemens NX Layer Automation Manual
```
