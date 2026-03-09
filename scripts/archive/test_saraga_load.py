# =============================================================================
# DEPRECATED -- early test phase script
# Used during initial project setup to explore the Saraga Carnatic dataset
# via mirdata as a potential data source. The project moved to its own
# seed_carnatic dataset instead. mirdata is not in requirements.txt.
#
# Do not use.
# =============================================================================

import mirdata

# Load dataset
dataset = mirdata.initialize("saraga_carnatic")

# Download index + metadata (audio optional for now)
dataset.download()

print("Download complete!")
print("Number of tracks:", len(dataset.track_ids))
