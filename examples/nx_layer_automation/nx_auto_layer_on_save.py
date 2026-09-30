# ==============================================================================
# Siemens NX Open Python: Automatic On-Part-Save Layer Assignment Handler
# ==============================================================================
# File: nx_auto_layer_on_save.py
# Language: Python 3 (NX Open API)
#
# Description:
#   Registers an event callback in Siemens NX so that every time a user saves
#   a part file (Ctrl+S or File -> Save), the automatic layer alignment
#   process is triggered automatically in the background!
# ==============================================================================

import NXOpen
import nx_auto_layer_assigner

def part_save_callback(part):
    """
    Callback function invoked by Siemens NX engine whenever a Part file is saved.
    """
    try:
        theSession = NXOpen.Session.GetSession()
        lw = theSession.ListingWindow
        lw.Open()
        lw.WriteLine(f"[NX AUTO-LAYER] Part Save detected for: {part.Leaf}. Aligning layers...")
        
        # Trigger full layer alignment routine
        nx_auto_layer_assigner.main()
    except Exception as e:
        pass

def register_save_handler():
    """
    Registers the save handler into the active Siemens NX session.
    """
    theSession = NXOpen.Session.GetSession()
    theSession.AddPartSaveHandler(NXOpen.Session.PartSaveHandler(part_save_callback))
    
    lw = theSession.ListingWindow
    lw.Open()
    lw.WriteLine("[NX AUTO-LAYER] Automatic On-Save Layer Alignment Handler registered successfully!")

if __name__ == '__main__':
    register_save_handler()
