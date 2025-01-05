import tifffile
import struct
import xml.etree.ElementTree as ET


TIFF_DATA_TYPES = {
    'uint8': 1,    
    'ascii': 2,    
    'uint16': 3,   
    'uint32': 4,   
    'uint64': 16,  
    'int8': 6,     
    'int16': 8,    
    'int32': 9,    
    'int64': 17,   
    'float32': 11, 
    'float64': 12, 
    'BYTE': 1,
    'ASCII': 2,
    'SHORT': 3,
    'LONG': 4,
    'RATIONAL': 5,
    'SBYTE': 6,
    'UNDEFINED': 7,
    'SSHORT': 8,
    'SLONG': 9,
    'SRATIONAL': 10,
    'FLOAT': 11,
    'DOUBLE': 12,
    'LONG8': 16,
    'SLONG8': 17,
    'IFD8': 18,
}

TIFF_DATA_SIZES = {
    1: 1,   # BYTE
    2: 1,   # ASCII
    3: 2,   # SHORT
    4: 4,   # LONG
    5: 8,   # RATIONAL
    6: 1,   # SBYTE
    7: 1,   # UNDEFINED
    8: 2,   # SSHORT
    9: 4,   # SLONG
    10: 8,  # SRATIONAL
    11: 4,  # FLOAT
    12: 8,  # DOUBLE
    16: 8,  # LONG8
    17: 8,  # SLONG8
    18: 8,  # IFD8
}

def verify_pages(tif: tifffile.TiffFile) -> dict:
    """
    Verify and identify important pages in TIFF file.
    
    Args:
        tif: TiffFile object to analyze
    
    Returns:
        dict: Dictionary containing page indices for label and macro
    """
    pages = {
        'label': None,
        'macro': None,
        'total': len(tif.pages)
    }
    
    for i, page in enumerate(tif.pages):
        if 'ImageDescription' in page.tags:
            desc = page.tags['ImageDescription'].value
            if isinstance(desc, bytes):
                desc = desc.decode('ascii', errors='replace')
            if desc.strip() == "Label":
                pages['label'] = i
            elif desc.startswith("Macro"):
                pages['macro'] = i
                
    return pages

def modify_xml_metadata(xml_content: str) -> str:
    """
    Process XML using proper parser to remove label section.
    
    Args:
        xml_content: Original XML metadata string
    
    Returns:
        str: Modified XML with label section removed
    """
    try:
        root = ET.fromstring(xml_content)
        scanned_images = root.find(".//Attribute[@Name='PIM_DP_SCANNED_IMAGES']/Array")
        if scanned_images is not None:
            for obj in scanned_images.findall("DataObject[@ObjectType='DPScannedImage']"):
                image_type = obj.find(".//Attribute[@Name='PIM_DP_IMAGE_TYPE']")
                if image_type is not None and 'LABELIMAGE' in image_type.text:
                    scanned_images.remove(obj)
                    break
        return ET.tostring(root, encoding='unicode')
    except ET.ParseError as e:
        raise ValueError(f"XML parsing error: {str(e)}")

def copy_tiff_low_level(input_filename: str, output_filename: str) -> str:
    """
    Copy TIFF file while removing Label page and modifying metadata.
    
    Args:
        input_filename: Path to input TIFF file
        output_filename: Path to output TIFF file
    
    Returns:
        str: Status message
    """
    try:
        with tifffile.TiffFile(input_filename) as in_tif, \
             open(input_filename, "rb") as in_f, \
             open(output_filename, "wb") as out_f:

            # Verify pages before processing
            pages_info = verify_pages(in_tif)
            if pages_info['macro'] is None:
                return "Error: No Macro page found"
            if pages_info['label'] is None:
                return "Error: No Label page found"

            # Get file parameters
            byte_order = '<' if in_tif.byteorder == '<' else '>'
            is_bigtiff = in_tif.is_bigtiff
            offset_size = 8 if is_bigtiff else 4
            header_size = 16 if is_bigtiff else 8
            pack_format = byte_order + ('Q' if is_bigtiff else 'I')

            # Copy header
            in_f.seek(0)
            header = in_f.read(header_size)
            out_f.write(header)

            # Write first IFD offset
            first_ifd_offset = in_tif.pages[0].offset
            out_f.write(struct.pack(pack_format, first_ifd_offset))

            # Process each page
            label_page_index = pages_info['label']
            for i, page in enumerate(in_tif.pages):
                if i == label_page_index:
                    continue

                # Calculate next page offset
                next_page_idx = i + 1
                if next_page_idx == label_page_index:
                    next_page_idx += 1
                next_offset = 0 if next_page_idx >= len(in_tif.pages) else in_tif.pages[next_page_idx].offset

                # Handle first page metadata
                if i == 0 and 'ImageDescription' in page.tags:
                    xml_content = page.tags['ImageDescription'].value
                    if isinstance(xml_content, bytes):
                        xml_content = xml_content.decode('ascii', errors='replace')
                    modified_xml = modify_xml_metadata(xml_content)
                    out_f.seek(page.tags['ImageDescription'].valueoffset)
                    out_f.write(modified_xml.encode('ascii') + b'\0')

                # Copy IFD structure
                current_offset = page.offset
                in_f.seek(current_offset)
                tag_count = struct.unpack(byte_order + ('Q' if is_bigtiff else 'H'), 
                    in_f.read(8 if is_bigtiff else 2))[0]
                ifd_size = (8 + tag_count * 20 + 8) if is_bigtiff else (2 + tag_count * 12 + 4)

                # Write IFD data
                in_f.seek(current_offset)
                ifd_data = in_f.read(ifd_size - offset_size)
                out_f.seek(current_offset)
                out_f.write(ifd_data)
                out_f.write(struct.pack(pack_format, next_offset))

                # Copy tag and image data
                for tag in page.tags.values():
                    if i == 0 and tag.name == 'ImageDescription':
                        continue
                    if hasattr(tag, 'valueoffset'):
                        data_size = tag.count * TIFF_DATA_SIZES.get(tag.dtype, 1)
                        if data_size > (8 if is_bigtiff else 4):
                            in_f.seek(tag.valueoffset)
                            out_f.seek(tag.valueoffset)
                            out_f.write(in_f.read(data_size))

                # Copy image data
                if 'TileOffsets' in page.tags:
                    for offset, bytecount in zip(page.tags['TileOffsets'].value, 
                                               page.tags['TileByteCounts'].value):
                        if offset > 0 and bytecount > 0:
                            in_f.seek(offset)
                            out_f.seek(offset)
                            out_f.write(in_f.read(bytecount))
                elif 'StripOffsets' in page.tags:  # Handle strip data (for Macro page)
                    for offset, bytecount in zip(page.tags['StripOffsets'].value, 
                                               page.tags['StripByteCounts'].value):
                        if offset > 0 and bytecount > 0:
                            in_f.seek(offset)
                            out_f.seek(offset)
                            out_f.write(in_f.read(bytecount))

            return "TIFF copied successfully (excluding Label page)"

    except Exception as e:
        raise
        return f"Error: {str(e)}"