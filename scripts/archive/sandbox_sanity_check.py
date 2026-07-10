"import numpy as np
from collections import defaultdict
import os

# Mock the key parts of recognize_raga_v12 to test the override impact
# Using current production logic
PER_RAGA_WEIGHTS_OVERRIDE = {'Bhairavi': (0.5, 0.5)}
BASE_PCD_W = 0.8
BASE_DYAD_W = 0.2

# (Dummy logic just to compare margins on the 70-clip set)
# I will run the actual evaluation logic from the previous sandbox
# to verify the Kalyani collapse.
print('Sanity check: Audit started.')
"