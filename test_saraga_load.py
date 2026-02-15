import mirdata

# Load dataset
dataset = mirdata.initialize("saraga_carnatic")

# Download index + metadata (audio optional for now)
dataset.download()

print("Download complete!")
print("Number of tracks:", len(dataset.track_ids))
