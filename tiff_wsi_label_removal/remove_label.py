import sys
from tiffprocessor import copy_tiff_low_level

def main():
    if len(sys.argv) != 3:
        print("Usage: tiff_processor <input_file> <output_file>")
        print("Example: tiff_processor input.tiff output.tiff")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Processing {input_file}")
    result = copy_tiff_low_level(input_file, output_file)
    print(result)

if __name__ == "__main__":
    main()