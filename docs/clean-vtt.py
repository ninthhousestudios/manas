import sys

def clean_vtt(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in lines:
            # Skip timestamps, VTT headers, and empty lines
            if '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or line.strip() == '':
                continue
            # Write the clean spoken text
            f.write(line)

# Usage: python clean_subs.py input.vtt output.txt
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python clean_subs.py <input.vtt> <output.txt>")
    else:
        clean_vtt(sys.argv[1], sys.argv[2])
        print(f"Successfully cleaned {sys.argv[1]} into {sys.argv[2]}")
