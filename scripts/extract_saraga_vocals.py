"""
Extract vocal stems from Saraga 1.5 zip for target ragas.
Priority: Kamboji, Mohanam (fix weak ragas), then new ragas.

IMPORTANT: Only extract files we're confident about the raga.
- Sindhubhairavi, Salaga Bhairavi, Anandabhairavi are NOT Bhairavi
- Hameer Kalyani is NOT Kalyani
- Only extract true matches
"""
import zipfile, os, shutil

ZIP_PATH = r"H:\Swaragam\Datasets\Audio\saraga1.5_carnatic.zip"
SEED_DIR = r"D:\Swaragam\datasets\seed_carnatic"

# Exact files to extract, manually verified raga assignments
# Format: (zip_path_substring, raga_folder, output_filename)
EXTRACT_LIST = [
    # ============================================================
    # KAMBOJI (3 current -> 6 after, need more via Demucs later)
    # ============================================================
    ("Enadhu Manam Kavalai.multitrack-vocal.mp3",
     "Kamboji", "Enadhu Manam Kavalai.vocal.mp3"),
    ("Enadhu Manam Kavalai.multitrack-vocal-s.mp3",
     "Kamboji", "Enadhu Manam Kavalai.vocal-s.mp3"),
    ("Dinamani Vamsa.multitrack-vocal.mp3",
     "Kamboji", "Dinamani Vamsa.vocal.mp3"),

    # ============================================================
    # MOHANAM (6 current -> 11 after)
    # ============================================================
    ("Shloka Namaste Sarvalokaanam.multitrack-vocal.mp3",
     "Mohanam", "Shloka Namaste Sarvalokaanam.vocal.mp3"),
    ("Shloka Namaste Sarvalokaanam.multitrack-vocal-s.mp3",
     "Mohanam", "Shloka Namaste Sarvalokaanam.vocal-s.mp3"),
    ("Brochevarevarura.multitrack-vocal.mp3",
     "Mohanam", "Brochevarevarura.vocal.mp3"),
    ("Mati Matiki.multitrack-vocal.mp3",
     "Mohanam", "Mati Matiki.vocal.mp3"),
    ("Shloka Sri Ramachandra Shrita Parijata.multitrack-vocal.mp3",
     "Mohanam", "Shloka Sri Ramachandra.vocal.mp3"),

    # ============================================================
    # SAVERI (new raga, 4 vocal stems)
    # ============================================================
    ("Shankari Shankuru.multitrack-vocal.mp3",
     "Saveri", "Shankari Shankuru.vocal.mp3"),
    ("Shankari Shankuru.multitrack-vocal-s.mp3",
     "Saveri", "Shankari Shankuru.vocal-s.mp3"),
    ("Kari Kalabha Mukham.multitrack-vocal.mp3",
     "Saveri", "Kari Kalabha Mukham.vocal.mp3"),
    ("Sarasuda Ninne Kori.multitrack-vocal.mp3",
     "Saveri", "Sarasuda Ninne Kori.vocal.mp3"),

    # ============================================================
    # ABHOGI (new raga, 2 vocal stems)
    # ============================================================
    ("Nannu Brova Neeku.multitrack-vocal-s.mp3",
     "Abhogi", "Nannu Brova Neeku.vocal-s.mp3"),
    ("Nannu Brova Neeku.multitrack-vocal.mp3",
     "Abhogi", "Nannu Brova Neeku.vocal.mp3"),

    # ============================================================
    # MADHYAMAVATI (new raga, 2 vocal stems)
    # ============================================================
    ("Shlokam - Shivah Shaktyayukto.multitrack-vocal.mp3",
     "Madhyamavati", "Shlokam Shivah Shaktyayukto.vocal.mp3"),
    ("Rama Namam Bhajare.multitrack-vocal.mp3",
     "Madhyamavati", "Rama Namam Bhajare.vocal.mp3"),

    # ============================================================
    # HAMSADHVANI (new raga, 2 vocal stems — very short clips)
    # ============================================================
    # Note: Both are shloka-length (~1 min). May be too short.
    # Keeping for now, will need external sources.
]

# Also extract MIX files for Demucs processing (Kamboji + Mohanam priority)
DEMUCS_LIST = [
    # KAMBOJI mix files (need Demucs)
    ("Sanjay Subrahmanyan - Entara Nitana.mp3",
     "Kamboji", "Sanjay Subrahmanyan - Entara Nitana.mp3"),
    ("Dinamani Vamsa.mp3.mp3",
     "Kamboji", "Dinamani Vamsa.mix.mp3"),

    # MOHANAM mix files (need Demucs)
    ("Brochevarevarura.mp3.mp3",
     "Mohanam", "Brochevarevarura.mix.mp3"),
    ("Shloka Namaste Sarvalokaanam.mp3.mp3",
     "Mohanam", "Shloka Namaste Sarvalokaanam.mix.mp3"),

    # SAVERI mix files (need Demucs)
    ("Ashwath Narayanan - Samajavarada.mp3",
     "Saveri", "Ashwath Narayanan - Samajavarada.mp3"),
    ("Kari Kalabha Mukham.mp3.mp3",
     "Saveri", "Kari Kalabha Mukham.mix.mp3"),
    ("Sarasuda Ninne Kori.mp3.mp3",
     "Saveri", "Sarasuda Ninne Kori.mix.mp3"),

    # ABHOGI mix files (need Demucs)
    ("Vignesh Ishwar - Evvari Bodhana.mp3",
     "Abhogi", "Vignesh Ishwar - Evvari Bodhana.mp3"),
    ("Nannu Brova Neeku.mp3.mp3",
     "Abhogi", "Nannu Brova Neeku.mix.mp3"),

    # MADHYAMAVATI mix files (need Demucs)
    ("Shlokam - Shivah Shaktyayukto.mp3.mp3",
     "Madhyamavati", "Shlokam Shivah Shaktyayukto.mix.mp3"),
    ("Rama Namam Bhajare.mp3.mp3",
     "Madhyamavati", "Rama Namam Bhajare.mix.mp3"),

    # HAMSADHVANI mix files (need Demucs)
    ("Ashwath Narayanan - Sadabalarupapi Shlokam.mp3",
     "Hamsadhvani", "Ashwath Narayanan - Sadabalarupapi Shlokam.mp3"),
]


def extract_files(zip_path, file_list, dest_base, label):
    """Extract files from zip matching substrings."""
    print("Extracting {} files...".format(label))
    extracted = 0
    skipped = 0

    with zipfile.ZipFile(zip_path, 'r') as zf:
        all_entries = zf.namelist()

        for substring, raga, out_name in file_list:
            # Find matching entry
            matches = [e for e in all_entries
                       if substring in e
                       and not e.split('/')[-1].startswith('._')
                       and zf.getinfo(e).file_size > 1000]

            if not matches:
                print("  MISS: {} (not found in zip)".format(substring))
                continue

            # Take the best match (longest path = most specific)
            entry = sorted(matches, key=len)[-1]

            # Create raga folder if needed
            raga_dir = os.path.join(dest_base, raga)
            os.makedirs(raga_dir, exist_ok=True)

            out_path = os.path.join(raga_dir, out_name)
            if os.path.exists(out_path):
                print("  SKIP: {} (already exists)".format(out_name))
                skipped += 1
                continue

            # Extract
            with zf.open(entry) as src, open(out_path, 'wb') as dst:
                shutil.copyfileobj(src, dst)

            size_mb = round(os.path.getsize(out_path) / (1024*1024), 1)
            print("  OK: {} -> {}/{} ({:.1f}MB)".format(
                entry.split('/')[-1], raga, out_name, size_mb))
            extracted += 1

    print("  {} extracted, {} skipped".format(extracted, skipped))
    return extracted


print("=" * 80)
print("SARAGA VOCAL STEM + MIX EXTRACTION")
print("=" * 80)
print()

# Extract vocal stems (ready to use immediately)
n_vocal = extract_files(ZIP_PATH, EXTRACT_LIST, SEED_DIR, "vocal stems")

print()

# Extract mix files (need Demucs processing)
demucs_staging = r"D:\Swaragam\demucs_staging"
os.makedirs(demucs_staging, exist_ok=True)
n_mix = extract_files(ZIP_PATH, DEMUCS_LIST, demucs_staging, "mix files for Demucs")

# Summary
print()
print("=" * 80)
print("EXTRACTION SUMMARY")
print("=" * 80)
print()
print("  Vocal stems extracted to seed_carnatic/: {}".format(n_vocal))
print("  Mix files staged for Demucs:             {}".format(n_mix))
print()

# Show new folder contents
for raga in ['Kamboji', 'Mohanam', 'Saveri', 'Abhogi', 'Madhyamavati', 'Hamsadhvani']:
    raga_dir = os.path.join(SEED_DIR, raga)
    if os.path.exists(raga_dir):
        files = [f for f in os.listdir(raga_dir) if f.endswith('.mp3') or f.endswith('.wav')]
        print("  {}: {} clips".format(raga, len(files)))
        for f in sorted(files):
            print("    {}".format(f))
    else:
        print("  {}: (not created yet)".format(raga))
    print()

print("NEXT: Run Demucs on mix files in demucs_staging/")
print("Done.")
