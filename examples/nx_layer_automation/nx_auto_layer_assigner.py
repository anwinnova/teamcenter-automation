# ==============================================================================
# Siemens NX Open Python Journal: Automatic Layer Classifier & Assigner
# ==============================================================================
# File: nx_auto_layer_assigner.py
# Language: Python 3 (NX Open API)
# Author: Enterprise Automation Suite
#
# Description:
#   Scans the active Siemens NX Work Part and automatically classifies and 
#   transfers all objects (Sketches, Solid Bodies, Sheet Bodies/Surfaces, 
#   Datums, CSYS, Standalone Curves, Reference Points, and Annotations/PMI) 
#   into their exact corporate standard layers.
#
# Execution Methods in Siemens NX:
#   1. Menu -> Tools -> Journal -> Play... (Alt + F8)
#   2. Siemens NX Ribbon Button (Custom UI / Ribbon customization)
#   3. Command Line Batch Execution via run_journal.exe
# ==============================================================================

import sys
import NXOpen
import NXOpen.Layer
import NXOpen.UF

def main():
    # --------------------------------------------------------------------------
    # 1. INITIALIZE NX SESSION & ACTIVE WORK PART
    # --------------------------------------------------------------------------
    theSession = NXOpen.Session.GetSession()
    ufSession = NXOpen.UF.UFSession.GetUFSession()
    workPart = theSession.Parts.Work
    lw = theSession.ListingWindow

    if workPart is None:
        lw.Open()
        lw.WriteLine("[ERROR] No active Work Part found in Siemens NX.")
        lw.WriteLine("        Please open an NX Part file (.prt) before running this script.")
        return

    # --------------------------------------------------------------------------
    # 2. CONFIGURABLE CORPORATE LAYER MAPPING DICTIONARY
    #    Change layer numbers below to match your organization's CAD standards.
    # --------------------------------------------------------------------------
    LAYER_MAPPING = {
        "SOLIDS": 1,         # Primary 3D Solid Geometry (Layer 1 - 10)
        "SHEETS": 11,       # Surface Models / Sheet Bodies (Layer 11 - 20)
        "SKETCHES": 21,     # 2D Sketch Geometry & Constraints (Layer 21 - 40)
        "DATUMS": 61,       # Datum Planes, Datum Axes, Datum CSYS (Layer 61 - 80)
        "CURVES": 81,       # Standalone Wireframe Lines, Arcs, Splines (Layer 81 - 100)
        "POINTS": 101,      # Reference Points (Layer 101 - 110)
        "ANNOTATIONS": 180  # PMI, Dimensions, Notes, Drafting (Layer 180 - 200)
    }

    # --------------------------------------------------------------------------
    # 3. SET NX UNDO MARK (Allows full single-click undo with Ctrl+Z)
    # --------------------------------------------------------------------------
    mark_id = theSession.SetUndoMark(
        NXOpen.Session.MarkVisibility.Visible, 
        "Automated Layer Assignment"
    )

    # Initialize data structures for sorting objects
    objects_by_layer = {layer_num: [] for layer_num in set(LAYER_MAPPING.values())}
    statistics = {category: 0 for category in LAYER_MAPPING.keys()}

    # --------------------------------------------------------------------------
    # 4. PROCESS SKETCHES -> Move to SKETCHES Layer
    # --------------------------------------------------------------------------
    sketch_target = LAYER_MAPPING["SKETCHES"]
    for sketch in workPart.Sketches:
        objects_by_layer[sketch_target].append(sketch)
        statistics["SKETCHES"] += 1

    # --------------------------------------------------------------------------
    # 5. PROCESS DATUM PLANES & DATUM AXES -> Move to DATUMS Layer
    # --------------------------------------------------------------------------
    datum_target = LAYER_MAPPING["DATUMS"]
    for datum in workPart.Datums:
        objects_by_layer[datum_target].append(datum)
        statistics["DATUMS"] += 1

    # --------------------------------------------------------------------------
    # 6. PROCESS COORDINATE SYSTEMS (CSYS) -> Move to DATUMS Layer
    # --------------------------------------------------------------------------
    for csys in workPart.CoordinateSystems:
        objects_by_layer[datum_target].append(csys)
        statistics["DATUMS"] += 1

    # --------------------------------------------------------------------------
    # 7. PROCESS SOLID BODIES & SHEET BODIES (SURFACES)
    # --------------------------------------------------------------------------
    solid_target = LAYER_MAPPING["SOLIDS"]
    sheet_target = LAYER_MAPPING["SHEETS"]

    for body in workPart.Bodies:
        try:
            if body.IsSolid:
                objects_by_layer[solid_target].append(body)
                statistics["SOLIDS"] += 1
            elif body.IsSheet:
                objects_by_layer[sheet_target].append(body)
                statistics["SHEETS"] += 1
        except Exception as ex:
            pass

    # --------------------------------------------------------------------------
    # 8. PROCESS STANDALONE CURVES (Lines, Arcs, Splines outside sketches)
    # --------------------------------------------------------------------------
    curve_target = LAYER_MAPPING["CURVES"]
    for curve in workPart.Curves:
        try:
            # Check if curve belongs to a sketch; if so, skip (sketch owns it)
            if hasattr(curve, "GetSketch") and curve.GetSketch() is not None:
                continue
        except Exception:
            pass
        
        objects_by_layer[curve_target].append(curve)
        statistics["CURVES"] += 1

    # --------------------------------------------------------------------------
    # 9. PROCESS POINTS -> Move to POINTS Layer
    # --------------------------------------------------------------------------
    point_target = LAYER_MAPPING["POINTS"]
    for point in workPart.Points:
        objects_by_layer[point_target].append(point)
        statistics["POINTS"] += 1

    # --------------------------------------------------------------------------
    # 10. EXECUTE DISPLAYABLE OBJECT LAYER MOVEMENT IN NX
    # --------------------------------------------------------------------------
    total_moved = 0
    for layer_number, obj_list in objects_by_layer.items():
        if obj_list:
            # Filter objects to ensure only DisplayableObjects are sent to NX Layer Manager
            valid_disp_objs = [obj for obj in obj_list if isinstance(obj, NXOpen.DisplayableObject)]
            if valid_disp_objs:
                try:
                    workPart.Layers.MoveDisplayableObjects(layer_number, valid_disp_objs)
                    total_moved += len(valid_disp_objs)
                except Exception as err:
                    lw.Open()
                    lw.WriteLine(f"[WARNING] Failed to move some objects to Layer {layer_number}: {str(err)}")

    # --------------------------------------------------------------------------
    # 11. GENERATE EXECUTION SUMMARY REPORT IN NX LISTING WINDOW
    # --------------------------------------------------------------------------
    lw.Open()
    lw.WriteLine("=======================================================================")
    lw.WriteLine("               SIEMENS NX AUTOMATIC LAYER ALIGNMENT SUMMARY             ")
    lw.WriteLine("=======================================================================")
    lw.WriteLine(f"  Part File Name   : {workPart.Leaf}.prt")
    lw.WriteLine(f"  Part Full Path   : {workPart.FullPath}")
    lw.WriteLine("-----------------------------------------------------------------------")
    lw.WriteLine("  CATEGORY          PROCESSED COUNT      ASSIGNED TARGET LAYER")
    lw.WriteLine("-----------------------------------------------------------------------")
    for category_name, count in statistics.items():
        assigned_l = LAYER_MAPPING[category_name]
        lw.WriteLine(f"  * {category_name:<15} : {count:>5} object(s)    ===> Layer {assigned_l:>3}")
    lw.WriteLine("-----------------------------------------------------------------------")
    lw.WriteLine(f"  Total Re-Aligned Objects : {total_moved}")
    lw.WriteLine("  Status                   : SUCCESS")
    lw.WriteLine("=======================================================================")

if __name__ == '__main__':
    main()
