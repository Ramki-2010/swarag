"""
Comprehensive Saraga scan: map ALL songs to ragas, then find target audio.
Handles Unicode raga names properly.
"""
import zipfile, os, json

ZIP_PATH = r"H:\Swaragam\Datasets\Audio\saraga1.5_carnatic.zip"
SARAGA_META = r"D:\Swaragam\datasets\saraga-master\saraga-master\dataset\carnatic"

# Normalize raga names to ASCII for matching
RAGA_NORMALIZE = {
    'bhairavi': 'Bhairavi',
    'kalyani': 'Kalyani', 'kalyaṇi': 'Kalyani',
    'sankarabharanam': 'Shankarabharanam', 'sankarabharaṇaṁ': 'Shankarabharanam',
    'shankarabharanam': 'Shankarabharanam',
    'todi': 'Thodi', 'toḍi': 'Thodi',
    'mohanam': 'Mohanam', 'mohanaṁ': 'Mohanam',
    'kambhoji': 'Kamboji', 'kambhōji': 'Kamboji',
    'hamsadhvani': 'Hamsadhvani',
    'saveri': 'Saveri', 'savēri': 'Saveri',
    'abhogi': 'Abhogi', 'abhōgi': 'Abhogi',
    'madhyamavati': 'Madhyamavati', 'madhyamavāti': 'Madhyamavati',
    'hindolam': 'Hindolam', 'hindōlaṁ': 'Hindolam',
    'karaharapriya': 'Karaharapriya',
    'harikambhoji': 'Harikambhoji', 'harikambhōji': 'Harikambhoji',
    'begada': 'Begada', 'begaḍa': 'Begada',
}

def normalize_raga(name):
    """Normalize unicode raga name to simple ASCII."""
    name_lower = name.lower().strip()
    # Direct match
    for key, val in RAGA_NORMALIZE.items():
        if key in name_lower:
            return val
    # Strip diacritics manually
    import unicodedata
    stripped = ''.join(c for c in unicodedata.normalize('NFD', name_lower)
                       if unicodedata.category(c) != 'Mn')
    stripped = stripped.replace('ṁ', 'm').replace('ṇ', 'n').replace('ḍ', 'd')
    stripped = stripped.replace('ō', 'o').replace('ē', 'e').replace('ā', 'a')
    stripped = stripped.replace('ī', 'i').replace('ū', 'u')
    for key, val in RAGA_NORMALIZE.items():
        if key in stripped:
            return val
    return name  # Return original if no match

# Step 1: Map EVERY song folder to its raga
print("Step 1: Mapping all Saraga songs to ragas...")
song_folder_to_raga = {}  # (concert_folder, song_folder) -> normalized_raga
song_details = {}  # same key -> {title, artist, raga_orig}

for concert_dir in os.listdir(SARAGA_META):
    concert_path = os.path.join(SARAGA_META, concert_dir)
    if not os.path.isdir(concert_path):
        continue
    for song_dir in os.listdir(concert_path):
        song_path = os.path.join(concert_path, song_dir)
        if not os.path.isdir(song_path):
            continue
        for f in os.listdir(song_path):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(song_path, f), 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    raagas = data.get('raaga', [])
                    for r in raagas:
                        rname = r.get('name', '')
                        if rname:
                            norm = normalize_raga(rname)
                            key = (concert_dir.lower(), song_dir.lower())
                            song_folder_to_raga[key] = norm
                            song_details[key] = {
                                'title': data.get('title', song_dir),
                                'artist': data.get('album_artists', [{}])[0].get('name', ''),
                                'raga_orig': rname,
                            }
                except:
                    pass

print("  Mapped {} songs".format(len(song_folder_to_raga)))

# Step 2: Scan zip and match
print("Step 2: Scanning zip...")

target_ragas = ['Bhairavi', 'Kalyani', 'Shankarabharanam', 'Thodi', 
                'Mohanam', 'Kamboji', 'Hamsadhvani', 'Saveri', 
                'Abhogi', 'Madhyamavati']

raga_audio = {}  # raga -> list of audio entries

with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    for entry in zf.namelist():
        if not any(entry.lower().endswith(ext) for ext in ['.mp3', '.wav', '.flac']):
            continue
        # Skip macOS metadata files
        if '._' in entry.split('/')[-1]:
            continue
        if entry.endswith('/'):
            continue
        
        size = zf.getinfo(entry).file_size
        if size < 1000:  # Skip tiny/empty files
            continue
        
        parts = entry.replace('\\', '/').split('/')
        # Saraga structure: saraga1.5_carnatic/Concert/Song/file.mp3
        if len(parts) >= 3:
            concert = parts[-3].lower() if len(parts) >= 3 else ''
            song = parts[-2].lower() if len(parts) >= 2 else ''
            filename = parts[-1]
            
            # Try to match
            matched_raga = None
            for key, raga in song_folder_to_raga.items():
                if key[1] in song or song in key[1]:
                    if raga in target_ragas:
                        matched_raga = raga
                        break
            
            if matched_raga:
                is_vocal = 'vocal' in filename.lower()
                is_mt = 'multitrack' in filename.lower()
                
                raga_audio.setdefault(matched_raga, []).append({
                    'path': entry,
                    'filename': filename,
                    'is_vocal': is_vocal,
                    'is_multitrack': is_mt,
                    'size_mb': round(size / (1024*1024), 1),
                    'details': song_details.get(
                        (concert, song), 
                        song_details.get(
                            next((k for k in song_details if k[1] in song or song in k[1]), ('','')),
                            {'title': song, 'artist': '?', 'raga_orig': matched_raga}
                        )
                    ),
                })

# Step 3: Report
print()
print("=" * 80)
print("SARAGA AUDIO INVENTORY FOR TARGET RAGAS")
print("=" * 80)

existing = {'Bhairavi': 11, 'Kalyani': 14, 'Shankarabharanam': 9,
            'Thodi': 10, 'Mohanam': 6, 'Kamboji': 3}

for raga in target_ragas:
    files = raga_audio.get(raga, [])
    vocal_stems = [f for f in files if f['is_vocal'] and f['is_multitrack']]
    mix_only = [f for f in files if not f['is_multitrack']]
    mix_for_demucs = [f for f in mix_only if f['size_mb'] > 1]
    cur = existing.get(raga, 0)
    
    status = "EXISTING" if cur > 0 else "NEW"
    print()
    print("{} [{}] -- Current: {} clips, Vocal stems: {}, Mix (need Demucs): {}".format(
        raga, status, cur, len(vocal_stems), len(mix_for_demucs)))
    
    if vocal_stems:
        print("  VOCAL STEMS (ready to use):")
        for f in vocal_stems:
            print("    {:.1f}MB  {}".format(f['size_mb'], f['filename']))
    
    if mix_for_demucs:
        print("  MIX FILES (need Demucs):")
        for f in mix_for_demucs:
            d = f['details']
            print("    {:.1f}MB  {} ({})".format(f['size_mb'], f['filename'], d.get('artist', '?')[:30]))
    
    if not files:
        print("  ** NO AUDIO IN SARAGA -- need external sources **")

# Summary table
print()
print("=" * 80)
print("SUMMARY: Data Gap Analysis")
print("=" * 80)
print()
print("  {:20} {:>7} {:>8} {:>8} {:>8} {:>8}".format(
    "Raga", "Current", "Vocal", "Mix", "Total", "Gap"))
print("  " + "-" * 65)

total_new = 0
for raga in target_ragas:
    files = raga_audio.get(raga, [])
    vocals = len([f for f in files if f['is_vocal'] and f['is_multitrack']])
    mixes = len([f for f in files if not f['is_multitrack'] and f['size_mb'] > 1])
    cur = existing.get(raga, 0)
    new_total = vocals + mixes
    after = cur + new_total
    gap = max(0, 10 - after)
    total_new += new_total
    
    marker = " <-- NEED EXTERNAL" if gap > 5 else (" <-- LOW" if gap > 0 else " OK")
    print("  {:20} {:>7} {:>8} {:>8} {:>8} {:>8}{}".format(
        raga, cur, vocals, mixes, after, gap, marker))

print()
print("  Total new clips from Saraga: {}".format(total_new))
print()
print("Done.")
