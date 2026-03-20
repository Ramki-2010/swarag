"""
Plan A: Scan Saraga 1.5 zip for target raga audio files.
Lists all audio files matching our target ragas (existing + new).
Identifies multitrack stems vs mix-only recordings.
"""
import zipfile
import os
import json

ZIP_PATH = r"H:\Swaragam\Datasets\Audio\saraga1.5_carnatic.zip"
SARAGA_META = r"D:\Swaragam\datasets\saraga-master\saraga-master\dataset\carnatic"

# Target ragas - using both ASCII and Unicode spellings
TARGET_KEYWORDS = [
    'kamboji', 'kambhoji',
    'mohanam', 'mohanal',
    'bhairavi',
    'hamsadhvani', 'hamsadwani',
    'saveri', 'saveri',
    'abhogi',
    'madhyamavati',
    'kalyani',
    'shankarabharanam', 'sankarabharanam',
    'thodi', 'todi',
]

print("=" * 80)
print("PLAN A: Saraga 1.5 Zip Audio Audit")
print("=" * 80)
print()

# Step 1: Build raga-to-folder mapping from metadata
print("Step 1: Building raga mapping from Saraga metadata...")
folder_raga_map = {}  # folder_name -> raga_name

for concert_dir in os.listdir(SARAGA_META):
    concert_path = os.path.join(SARAGA_META, concert_dir)
    if not os.path.isdir(concert_path):
        continue
    for item in os.listdir(concert_path):
        item_path = os.path.join(concert_path, item)
        if os.path.isdir(item_path):
            # Look for JSON metadata
            for f in os.listdir(item_path):
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(item_path, f), 'r', encoding='utf-8') as fh:
                            data = json.load(fh)
                        raagas = data.get('raaga', [])
                        for r in raagas:
                            rname = r.get('name', '')
                            if rname:
                                key = item.lower()
                                folder_raga_map[key] = rname
                    except:
                        pass

print("  Mapped {} songs to ragas".format(len(folder_raga_map)))
print()

# Step 2: Scan zip contents
print("Step 2: Scanning zip for audio files...")
target_files = {}
all_audio_count = 0

with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    for entry in zf.namelist():
        # Only care about audio files
        if not any(entry.lower().endswith(ext) for ext in ['.mp3', '.wav', '.flac', '.ogg']):
            continue
        all_audio_count += 1
        
        entry_lower = entry.lower()
        
        # Check if this matches a target raga
        matched_raga = None
        
        # First try: match via folder name in metadata
        parts = entry.replace('\\', '/').split('/')
        for part in parts:
            part_lower = part.lower()
            if part_lower in folder_raga_map:
                raga_name = folder_raga_map[part_lower]
                for kw in TARGET_KEYWORDS:
                    if kw in raga_name.lower():
                        matched_raga = raga_name
                        break
            if matched_raga:
                break
        
        # Second try: match by filename keywords
        if not matched_raga:
            for kw in TARGET_KEYWORDS:
                if kw in entry_lower:
                    matched_raga = kw.title()
                    break
        
        if matched_raga:
            is_vocal = 'vocal' in entry_lower
            is_multitrack = 'multitrack' in entry_lower
            is_mix = not is_multitrack
            
            target_files.setdefault(matched_raga, []).append({
                'path': entry,
                'is_vocal': is_vocal,
                'is_multitrack': is_multitrack,
                'size': zf.getinfo(entry).file_size,
            })

print("  Total audio files in zip: {}".format(all_audio_count))
print()

# Step 3: Report
print("=" * 80)
print("TARGET RAGA AUDIO IN SARAGA ZIP")
print("=" * 80)
print()

for raga in sorted(target_files.keys()):
    files = target_files[raga]
    vocals = [f for f in files if f['is_vocal']]
    multitracks = [f for f in files if f['is_multitrack']]
    mixes = [f for f in files if not f['is_multitrack']]
    
    print("{} ({} files, {} vocal stems, {} multitrack, {} mix):".format(
        raga, len(files), len(vocals), len(multitracks), len(mixes)))
    
    for f in sorted(files, key=lambda x: x['path']):
        size_mb = round(f['size'] / (1024 * 1024), 1)
        tags = []
        if f['is_vocal']:
            tags.append('VOCAL')
        if f['is_multitrack']:
            tags.append('MT')
        else:
            tags.append('MIX')
        short_path = '/'.join(f['path'].replace('\\', '/').split('/')[-3:])
        print("  [{:8}] {:5.1f}MB  {}".format(' '.join(tags), size_mb, short_path))
    print()

# Summary
print("=" * 80)
print("EXTRACTION PLAN")
print("=" * 80)
print()
existing_ragas = {'Bhairavi': 11, 'Kalyani': 14, 'Shankarabharanam': 9,
                  'Thodi': 10, 'Mohanam': 6, 'Kamboji': 3}

for raga in sorted(target_files.keys()):
    files = target_files[raga]
    vocals = [f for f in files if f['is_vocal']]
    current = existing_ragas.get(raga, 0)
    new_vocals = len(vocals)
    print("  {:25} Current: {:2d} clips, New vocal stems: {:2d}, Target: 10-15".format(
        raga, current, new_vocals))

# Check for new ragas not yet in our system
new_ragas = set()
for raga in target_files:
    raga_simple = raga.lower().replace(' ', '')
    is_new = True
    for existing in existing_ragas:
        if existing.lower() in raga_simple or raga_simple in existing.lower():
            is_new = False
            break
    if is_new:
        new_ragas.add(raga)

if new_ragas:
    print()
    print("  NEW RAGAS available: {}".format(', '.join(sorted(new_ragas))))

print()
print("Done.")
