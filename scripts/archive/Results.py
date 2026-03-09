# =============================================================================
# DIAGNOSTIC SCRATCH SCRIPT -- not part of any pipeline
# Inspects keys inside a dyad_stats .npz file from the v1.2 aggregation output.
# Hardcoded to a specific run path -- update path before running.
# =============================================================================

import numpy as np

path = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260215_113720\dyad_stats\Kalyani_dyad_stats.npz"

data = np.load(path, allow_pickle=True)

print("Keys inside file:")
print(data.files)
