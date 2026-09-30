# Siemens NX Automatic Layer Alignment Automation

This guide explains how to deploy and configure automatic layer alignment in Siemens NX (Unigraphics NX) for Sketches, Solid Bodies, Sheet Bodies, Datums, Curves, and Points.

---

## 1. Overview & Layer Standard Mapping

In Siemens NX CAD, designers frequently create sketches, datums, and features on whichever layer happens to be active. This script enforces your corporate CAD layer standard automatically by classifying each object by type and transferring it to its corresponding layer.

| Object Type | Default Target Layer | Description |
| :--- | :--- | :--- |
| **Solid Bodies** | **Layer 1** | Primary 3D solid geometry |
| **Sheet Bodies (Surfaces)**| **Layer 11** | Surface models, sheet geometry |
| **Sketches** | **Layer 21** | 2D Sketch curves & constraints |
| **Datums & CSYS** | **Layer 61** | Datum Planes, Datum Axes, Coordinate Systems |
| **Standalone Curves** | **Layer 81** | Wireframe lines, arcs, splines outside sketches |
| **Points** | **Layer 101** | Reference points |
| **Annotations / PMI** | **Layer 180** | Dimensions, notes, drafting annotations |

---

## 2. Quick Execution (Journal Play)

1. Open your model in **Siemens NX**.
2. Go to top menu: `Tools` > `Journal` > `Play...` (or press **Alt + F8**).
3. Browse and select [`nx_auto_layer_assigner.py`](file:///config/Desktop/Session1/examples/nx_auto_layer_assigner.py).
4. Click **Run**.
5. The **NX Information Window** will open showing a full summary report of all objects moved.

---

## 3. Adding a One-Click Toolbar Button in Siemens NX

To make this available as a 1-click button on the NX Ribbon interface:

1. Right-click anywhere on the Siemens NX Ribbon bar and select **Customize...** (or press **Ctrl + 1**).
2. Go to the **Commands** tab > scroll to **New Item**.
3. Drag **New Button** onto your preferred ribbon group (e.g., in the Home or Utilities tab).
4. Right-click the newly placed button > select **Edit Action...**
5. Change Type to **Journal File**, and browse to select `nx_auto_layer_assigner.py`.
6. Assign an icon and name like `Align Layers`.
7. Click **Close**. Now design engineers can click the button anytime to auto-organize their part layers!

---

## 4. Automatic Trigger on Part Save (NX Event Listener)

If you want NX to align layers automatically every time a user saves a part, you can register a Part Save callback in Python:

```python
import NXOpen

def on_part_save(part):
    # Call layer assignment routine here
    pass

theSession = NXOpen.Session.GetSession()
# Register callback
theSession.AddPartSaveHandler(NXOpen.Session.PartSaveHandler(on_part_save))
```
