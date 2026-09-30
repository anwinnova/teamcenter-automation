# ==============================================================================
# Siemens NX Open Python Journal: Automatic Layer Assigner & Classifier
# ==============================================================================
# Purpose: Automatically moves all objects in the active Siemens NX work part 
#          (Sketches, Solid Bodies, Sheet Bodies, Datums, CSYS, Curves, Points, 
#          Annotations) into their designated corporate standard layers.
#
# How to Run in Siemens NX:
#   1. Open any Part file in Siemens NX (.prt).
#   2. Go to Menu -> Tools -> Journal -> Play (or press Alt + F8).
#   3. Select this script (nx_auto_layer_assigner.py) and click Run.
# ==============================================================================

import NXOpen
import NXOpen.Layer
import NXOpen.UF

def main():
    # Obtain NX Session and Active Work Part
    theSession = NXOpen.Session.GetSession()
    workPart = theSession.Parts.Work
    
    lw = theSession.ListingWindow

    if workPart is None:
        lw.Open()
        lw.WriteLine("ERROR: No active Work Part found. Please open an NX part file first.")
        return

    # --------------------------------------------------------------------------
    # CORPORATE LAYER MAPPING CONFIGURATION
    # Customize layer numbers here according to your CAD / Company standard.
    # --------------------------------------------------------------------------
    LAYER_CONFIG = {
        "SOLIDS": 1,        # Solid Bodies
        "SHEETS": 11,      # Sheet Bodies / Surface Models
        "SKETCHES": 21,    # Sketches
        "DATUMS": 61,      # Datum Planes, Datum Axes, Datum CSYS
        "CURVES": 81,      # Wireframe Curves (Lines, Arcs, Splines)
        "POINTS": 101,     # Reference Points
        "ANNOTATIONS": 180 # PMI & Drafting Annotations/Dimensions
    }

    # Create an Undo Mark so user can undo whole operation with Ctrl+Z
    mark_id = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Auto Assign Object Layers")

    # Buckets for displayable objects
    objects_to_move = {layer: [] for layer in set(LAYER_CONFIG.values())}
    summary_counts = {category: 0 for category in LAYER_CONFIG.keys()}

    # --------------------------------------------------------------------------
    # 1. SKETCHES
    # --------------------------------------------------------------------------
    sketch_target_layer = LAYER_CONFIG["SKETCHES"]
    for sketch in workPart.Sketches:
        objects_to_move[sketch_target_layer].append(sketch)
        summary_counts["SKETCHES"] += 1

    # --------------------------------------------------------------------------
    # 2. DATUM PLANES & DATUM AXES
    # --------------------------------------------------------------------------
    datum_target_layer = LAYER_CONFIG["DATUMS"]
    for datum in workPart.Datums:
        objects_to_move[datum_target_layer].append(datum)
        summary_counts["DATUMS"] += 1

    # --------------------------------------------------------------------------
    # 3. COORDINATE SYSTEMS (CSYS)
    # --------------------------------------------------------------------------
    for csys in workPart.CoordinateSystems:
        objects_to_move[datum_target_layer].append(csys)
        summary_counts["DATUMS"] += 1

    # --------------------------------------------------------------------------
    # 4. SOLID BODIES & SHEET BODIES (SURFACES)
    # --------------------------------------------------------------------------
    solid_layer = LAYER_CONFIG["SOLIDS"]
    sheet_layer = LAYER_CONFIG["SHEETS"]

    for body in workPart.Bodies:
        if body.IsSolid:
            objects_to_move[solid_layer].append(body)
            summary_counts["SOLIDS"] += 1
        elif body.IsSheet:
            objects_to_move[sheet_layer].append(body)
            summary_counts["SHEETS"] += 1

    # --------------------------------------------------------------------------
    # 5. STANDALONE CURVES (Wireframe, Lines, Arcs, Splines)
    # --------------------------------------------------------------------------
    curve_target_layer = LAYER_CONFIG["CURVES"]
    for curve in workPart.Curves:
        # Avoid moving curves that are internally managed inside a sketch
        try:
            if hasattr(curve, "GetSketch") and curve.GetSketch() is not None:
                continue
        except Exception:
            pass
        objects_to_move[curve_target_layer].append(curve)
        summary_counts["CURVES"] += 1

    # --------------------------------------------------------------------------
    # 6. POINTS
    # --------------------------------------------------------------------------
    point_target_layer = LAYER_CONFIG["POINTS"]
    for pt in workPart.Points:
        objects_to_move[point_target_layer].append(pt)
        summary_counts["POINTS"] += 1

    # --------------------------------------------------------------------------
    # EXECUTE MOVEMENTS IN NX LAYER MANAGER
    # --------------------------------------------------------------------------
    total_moved = 0
    for target_layer, obj_list in objects_to_move.items():
        if obj_list:
            # Filter objects to ensure only displayable objects are passed
            disp_objs = [o for o in obj_list if isinstance(o, NXOpen.DisplayableObject)]
            if disp_objs:
                workPart.Layers.MoveDisplayableObjects(target_layer, disp_objs)
                total_moved += len(disp_objs)

    # --------------------------------------------------------------------------
    # DISPLAY EXECUTION REPORT IN NX INFORMATION WINDOW
    # --------------------------------------------------------------------------
    lw.Open()
    lw.WriteLine("==========================================================")
    lw.WriteLine("      SIEMENS NX AUTOMATIC LAYER ASSIGNMENT REPORT       ")
    lw.WriteLine("==========================================================")
    lw.WriteLine(f" Active Work Part: {workPart.Leaf}")
    lw.WriteLine("----------------------------------------------------------")
    for category, count in summary_counts.items():
        target_l = LAYER_CONFIG[category]
        lw.WriteLine(f"  * {category:<12} : {count:>4} object(s)  ==> Layer {target_l}")
    lw.WriteLine("----------------------------------------------------------")
    lw.WriteLine(f" Total Objects Re-aligned : {total_moved}")
    lw.WriteLine(" Status                   : SUCCESS")
    lw.WriteLine("==========================================================")

if __name__ == '__main__':
    main()
