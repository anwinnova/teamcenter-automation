# Siemens NX Automatic Layer Alignment & Classification (Python)

A production-grade Python automation suite for **Siemens NX** (formerly Unigraphics NX) that automatically classifies and transfers CAD objects—**Sketches, Solid Bodies, Sheet Bodies / Surfaces, Datums, CSYS, Standalone Curves, Points, and Annotations**—into their designated corporate standard layers.

---

## 1. Corporate CAD Layer Standard Matrix

By default, the Python script uses the following industry-standard CAD layer classification:

| Object Category | Target Layer | Included NX Object Types |
| :--- | :---: | :--- |
| **SOLIDS** | **Layer 1** | Primary 3D Solid Bodies (`NXOpen.Body.IsSolid`) |
| **SHEETS** | **Layer 11** | Surface Models & Sheet Bodies (`NXOpen.Body.IsSheet`) |
| **SKETCHES** | **Layer 21** | 2D Sketch Geometry & Constraints (`NXOpen.Sketch`) |
| **DATUMS** | **Layer 61** | Datum Planes, Datum Axes, Coordinate Systems (`NXOpen.Datum`, `NXOpen.CoordinateSystem`) |
| **CURVES** | **Layer 81** | Standalone Lines, Arcs, Splines, Wireframe (`NXOpen.Curve`) |
| **POINTS** | **Layer 101** | Reference Points (`NXOpen.Point`) |
| **ANNOTATIONS** | **Layer 180** | PMI, Dimensions, Notes, Drafting Annotations (`NXOpen.Annotations.Annotation`) |

---

## 2. File Architecture

```
examples/nx_layer_automation/
├── nx_auto_layer_assigner.py    # Main Python script for Siemens NX layer alignment
├── nx_auto_layer_on_save.py     # Background handler that auto-aligns layers on Part Save (Ctrl+S)
├── nx_custom_ribbon.men         # Siemens NX custom Menu/Ribbon integration file
└── README.md                    # Detailed deployment & configuration manual
```

---

## 3. How to Configure Layer Rules (Python)

To change layer target numbers to match your company's specific CAD standard, open [`nx_auto_layer_assigner.py`](file:///config/Desktop/Session1/examples/nx_layer_automation/nx_auto_layer_assigner.py) in any text editor and update the `LAYER_MAPPING` dictionary:

```python
# Customize layer numbers here:
LAYER_MAPPING = {
    "SOLIDS": 1,        # Target layer for 3D Solid Bodies
    "SHEETS": 11,      # Target layer for Sheet Bodies / Surfaces
    "SKETCHES": 21,    # Target layer for Sketches
    "DATUMS": 61,      # Target layer for Datum Planes / Axes / CSYS
    "CURVES": 81,      # Target layer for Standalone Wireframe Curves
    "POINTS": 101,     # Target layer for Points
    "ANNOTATIONS": 180 # Target layer for PMI & Dimensions
}
```

---

## 4. How to Execute & Configure in Siemens NX

### Method 1: Run On-Demand via NX Journal Play (Keyboard Shortcut)
1. Open any part file (`.prt`) in Siemens NX.
2. Go to top menu: **Menu** > **Tools** > **Journal** > **Play...** (or press **Alt + F8**).
3. Browse and select [`nx_auto_layer_assigner.py`](file:///config/Desktop/Session1/examples/nx_layer_automation/nx_auto_layer_assigner.py).
4. Click **Run**.
5. The **NX Information Window** will pop up displaying a detailed execution summary showing how many objects were moved to each layer.

---

### Method 2: Configure a 1-Click Button on the NX Ribbon Bar
To give your engineering team a simple 1-click button on the Siemens NX top ribbon:

1. In Siemens NX, right-click anywhere on the top Ribbon bar and select **Customize...** (or press **Ctrl + 1**).
2. Click on the **Commands** tab and scroll down to **New Item**.
3. Drag **New Button** onto your preferred ribbon tab (e.g., *Home*, *Utilities*, or *Curve* tab).
4. Right-click the newly placed button on the ribbon > select **Edit Action...**
5. Set **Type** to `Journal File`.
6. Click **Browse** and select `nx_auto_layer_assigner.py`.
7. (Optional) Right-click the button > **Change Button Image** to pick a custom icon, and rename the text label to **"Auto-Align Layers"**.
8. Click **Close**. The button is now permanently saved in your Siemens NX profile!

---

### Method 3: Deploy via Siemens NX Custom Menu File (`.men`)
For company-wide enterprise deployment across all CAD workstations:

1. Copy `nx_custom_ribbon.men` and `nx_auto_layer_assigner.py` into your company's NX startup folder (e.g., `%UGII_SITE_DIR%\startup\` or `%UGII_USER_DIR%\startup\`).
2. Launch Siemens NX.
3. A new top-level menu item called **Automation Tools** > **Auto-Align CAD Layers** will automatically appear in every user's Siemens NX interface!

---

### Method 4: Automatic Execution on Every Part Save (Background Hook)
To ensure layers are automatically organized without engineers needing to click anything:

1. Open Siemens NX.
2. Run [`nx_auto_layer_on_save.py`](file:///config/Desktop/Session1/examples/nx_layer_automation/nx_auto_layer_on_save.py) via **Alt + F8**.
3. Whenever an engineer presses **Ctrl + S** or clicks **File > Save**, Siemens NX will automatically execute the layer alignment routine in the background before saving the part!

---

### Method 5: Run Batch Layer Alignment across Multiple `.prt` Files
To process hundreds of existing NX part files in batch mode without opening the NX GUI:

Open Command Prompt / Terminal and run Siemens NX `run_journal.exe`:

```bash
# Windows Command Prompt / PowerShell
"%UGII_BASE_DIR%\NXBIN\run_journal.exe" "C:\path\to\nx_auto_layer_assigner.py" -args "C:\CAD_Parts\part1.prt"
```

---

## 5. Features & Safety Mechanisms

* **Full Undo Support (`Ctrl + Z`)**: The script creates a single visible NX Undo Mark (`theSession.SetUndoMark`). If a user wants to revert the layer assignment, pressing `Ctrl + Z` instantly restores all objects to their original layers.
* **Internal Sketch Curve Exclusion**: Standalone curves inside a sketch are automatically identified and excluded so internal sketch constraints are never broken.
* **Displayable Object Filtering**: Only displayable objects (`NXOpen.DisplayableObject`) are passed to `workPart.Layers.MoveDisplayableObjects` to prevent NX Open runtime type errors.
* **Execution Logging**: Outputs a clean report into the Siemens NX Information Window (`ListingWindow`).

---

## 6. Troubleshooting

* **Q: Error "No active Work Part found"**
  * *Solution*: Make sure an active `.prt` file is loaded in Siemens NX before running the script.
* **Q: How do I change Python version used by Siemens NX?**
  * *Solution*: Siemens NX comes bundled with its own embedded Python environment located at `%UGII_BASE_DIR%\NXBIN\python\python.exe`.
