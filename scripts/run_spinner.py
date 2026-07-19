
import csv
import sys
import os

# Add lib to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from text_spinner import TextParaphraser

def main():
    p = TextParaphraser()
    input_file = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts/guadalajara_iff_raw.csv'
    
    # Read rows into memory
    rows = []
    with open(input_file, 'r', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get('category'):
                row['category'] = p.replace_synonyms(row['category'])
            rows.append(row)
            
    # Overwrite the original file with paraphrased data
    with open(input_file, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == '__main__':
    main()
