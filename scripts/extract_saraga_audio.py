import os
import json
import zipfile
import shutil
from collections import defaultdict

ZIP_PATH    = r'H:\Swaragam\Datasets\Audio\saraga1.5_carnatic.zip'
METADATA    = r'D:\Swaragam\datasets\saraga-master\saraga-master\dataset\carnatic'
SEED_DIR    = r'D:\Swaragam\datasets\seed_carnatic'

TARGET_RAGAS = {
    'kalyani':          'Kalyani',
    'bhairavi':         'Bhairavi',
    'sankarabharanam':  'Shankarabharanam',
    'mohanam':          'Mohanam',
    'thodi':            'Thodi',
    'kamboji':          'Kamboji',
}

def build_song_map():
    song_map = {}
    for root, dirs, files in os.walk(METADATA):
        for f in files:
            if not f.endswith('.json'):
                continue
            path = os.path.join(root, f)
            try:
                data = json.load(open(path, encoding='utf-8'))
                raaga = data.get('raaga', [])
                if not raaga:
                    continue
                rname = raaga[0].get('common_name', '').lower()
                if rname not in TARGET_RAGAS:
                    continue
                rel = os.path.relpath(root, METADATA)
                title = data.get('title', f.replace('.json', ''))
                song_map[rel] = (TARGET_RAGAS[rname], title)
            except Exception:
                pass
    return song_map

def find_audio_in_zip(zf, song_map):
    extractions = []
    for entry in zf.namelist():
        if not entry.lower().endswith('.mp3'):
            continue
        lower = entry.lower()
        if any(x in lower for x in ['multitrack', 'violin', 'mridangam',
                                     'ghatam', 'secondary']):
            continue
        for rel_path, (raga_folder, title) in song_map.items():
            rel_n = rel_path.replace(chr(92), '/')
            entry_n = entry.replace(chr(92), '/')
            if rel_n in entry_n:
                fname = os.path.basename(entry)
                dest = os.path.join(SEED_DIR, raga_folder, fname)
                extractions.append((entry, dest, raga_folder, title))
                break
    return extractions

def extract_files(zf, extractions):
    raga_counts = defaultdict(int)
    for entry, dest, raga_folder, title in extractions:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest):
            print('  SKIP (exists): ' + os.path.basename(dest))
            raga_counts[raga_folder] += 1
            continue
        with zf.open(entry) as src, open(dest, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print('  >> {:20s} {:40s} {:.1f} MB'.format(raga_folder, title, size_mb))
        raga_counts[raga_folder] += 1
    return raga_counts

def main():
    print('Saraga Audio Extractor for Swarag')
    print('=' * 50)

    if not os.path.exists(ZIP_PATH):
        print('\nX Zip not found: ' + ZIP_PATH)
        print('  Download from: https://zenodo.org/records/4301737/files/saraga1.5_carnatic.zip')
        return

    zip_size_gb = os.path.getsize(ZIP_PATH) / (1024**3)
    print('\nZip found: {} ({:.1f} GB)'.format(ZIP_PATH, zip_size_gb))

    print('\nStep 1: Building song -> raga mapping from metadata...')
    song_map = build_song_map()
    print('  Found {} target songs across {} ragas'.format(len(song_map), len(TARGET_RAGAS)))
    for rel, (raga, title) in sorted(song_map.items(), key=lambda x: x[1][0]):
        print('    {:20s} {}'.format(raga, title))

    print('\nStep 2: Scanning zip for matching audio files...')
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        extractions = find_audio_in_zip(zf, song_map)
        print('  Found {} audio files to extract'.format(len(extractions)))

        if not extractions:
            print('\n  No matches found. Sample zip entries:')
            for e in list(zf.namelist())[:30]:
                print('    ' + e)
            return

        print('\nStep 3: Extracting to ' + SEED_DIR)
        raga_counts = extract_files(zf, extractions)

    print('\n' + '=' * 50)
    print('Extraction Summary:')
    for raga in sorted(TARGET_RAGAS.values()):
        raga_dir = os.path.join(SEED_DIR, raga)
        existing = 0
        if os.path.exists(raga_dir):
            existing = len([f for f in os.listdir(raga_dir)
                           if f.lower().endswith(('.mp3', '.wav', '.flac'))])
        extracted = raga_counts.get(raga, 0)
        print('  {:20s} : {} extracted, {} total in folder'.format(raga, extracted, existing))

    print('\nDone. Run aggregate_all_v12.py to rebuild models.')

if __name__ == '__main__':
    main()