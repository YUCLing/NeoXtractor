#no conversion needed (PyQT converts): bmp, gif, jpg, jpeg, png, pbm, pgm, ppm, xbm, xpm
import io
import struct
import math
from PIL import Image
from bitstring import ConstBitStream

#tga, ico, tiff, dds
def pillow_image_conversion(data, type):
    buf = io.BytesIO()
    return Image.open(io.BytesIO(data),"r", ["png", type])

def return_png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()

def get_astc_file_size(height, width, block_x, block_y):
    return math.ceil(width/block_y) * math.ceil(height/block_x) * 16

#this code was derived from TeaEffTeu's works and he slightly guided me, thank you very much for sharing!!
def compblks_convert(data):
    def int_to_bytes(number):
        return int.to_bytes(number, 4, "little")
    def get_pitch(width):
        return int.to_bytes(max(1, ((int.from_bytes(width, "little")+3)//4) ) * 16, 4, "little")
    width = data[16:18] + b"\0\0"
    height = data[18:20] + b"\0\0"
    
    nullbytes = b"\0\0\0\0"
    dds_header = b"DDS\x20\x7C\0\0\0\x07\x10\x08\0"
    dds_pixform_header = b"\x20\0\0\0\x04\0\0\0"
    
    dds_data = dds_header + height + width + get_pitch(width) + (nullbytes * 13) + dds_pixform_header + b"DXT5" + (nullbytes * 5) + b"\0\x10\0\0" + (nullbytes * 4) + data[28:]
    return pillow_image_conversion(dds_data, "dds")

def pvr_convert(data):
    def r_uintle32(data):
        return data.read('uintle:32')
    def r_uintle64(data):
        return data.read('uintle:64')
    def int_to_bytes(number):
        return int.to_bytes(number, 4, "little")
    def get_format_bits_per_pixel(form):
        match form:
            case 7:
                return (b"DXT1", 4)
            case 11:
                return (b"DXT5", 8)
            case 27:
                return ("ASTC", (4, 4))
            case 28:
                return ("ASTC", (5, 4))
            case 29:
                return ("ASTC", (5, 5))
            case 30:
                return ("ASTC", (6, 5))
            case 31:
                return ("ASTC", (6, 6))
            case 32:
                return ("ASTC", (8, 5))
            case 33:
                return ("ASTC", (8, 6))
            case 34:
                return ("ASTC", (8, 8))
            case 35:
                return ("ASTC", (10, 5))
            case 36:
                return ("ASTC", (10, 6))
            case 37:
                return ("ASTC", (10, 8))
            case 38:
                return ("ASTC", (10, 10))
            case 39:
                return ("ASTC", (12, 10))
            case 40:
                return ("ASTC", (12, 12))
    def get_pitch(width, block_size):
        return int.to_bytes(max(1, ((width+3)//4) ) * (2 * block_size), 4, "little")

    nullbytes = b"\0\0\0\0"
    dds_header = b"DDS\x20\x7C\0\0\0\x07\x10\0\0"
    dds_pixform_header = b"\x20\0\0\0\x04\0\0\0"


    f = ConstBitStream(io.BytesIO(data))
    version = f.read('hex:32')  # 50565203 (endianness does NOT match)
    flags = r_uintle32(f)  # 0 (no flag)
    pixel_format = r_uintle64(f)  # 34 (astc_8x8)
    colour_space = r_uintle32(f) # 0 (linear RGB)
    channel_type = r_uintle32(f) # 0 (unsigned byte normalised)
    height = r_uintle32(f) # 150
    width = r_uintle32(f) # 256
    depth = r_uintle32(f) # 1 (no depth)
    num_surfaces = r_uintle32(f) # 1
    num_faces = r_uintle32(f) # 1
    mip_map_count = r_uintle32(f) # 1
    meta_data_size = r_uintle32(f) # 15
    f.pos += meta_data_size * 8
    p_format, bpp = get_format_bits_per_pixel(pixel_format) # 4
    
    if p_format == "ASTC":
        x, y = bpp
        return Image.frombytes('RGBA', (width, height), f.read(f"bytes{get_astc_file_size(height, width, x, y)}"), 'astc', bpp)
    texture_data = f.read(f"bytes:{width*height*bpp // 8}")
    
    dds_data = dds_header + int_to_bytes(height) + int_to_bytes(width) + get_pitch(width, bpp) + nullbytes + int_to_bytes(mip_map_count) + (nullbytes * 11) + dds_pixform_header + p_format + (nullbytes * 10)

    return pillow_image_conversion(dds_data + texture_data, "dds")
    
    
#https://registry.khronos.org/KTX/specs/1.0/ktxspec.v1.html
#https://docs.vulkan.org/spec/latest/chapters/formats.html
def ktx_convert(data):
    def get_rest_to_multiple(num, target):
        buf = target
        while num < target:
            target = target + buf
        return num - target
    def get_glInternal_format(data):
        match data:
            case 37815:
                return "COMPRESSED_RGBA_ASTC_8x8_KHR"
    def r_uintle32(data):
        return data.read('uintle:32')
    def r_uintle64(data):
        return data.read('uintle:64')
    f = ConstBitStream(io.BytesIO(data))
    identifier = f.read("bytes:12")
    endianness = r_uintle32(f)
    glType = r_uintle32(f)
    glTypeSize = r_uintle32(f)
    glFormat = r_uintle32(f)
    glInternalFormat = get_glInternal_format(r_uintle32(f))
    glBaseInternalFormat = r_uintle32(f)
    pixelWidth = r_uintle32(f)
    pixelHeight = r_uintle32(f)
    pixelDepth = r_uintle32(f)
    numberOfArrayElements = r_uintle32(f)
    numberOfFaces = r_uintle32(f)
    numberOfMipmapLevels = r_uintle32(f)
    bytesOfKeyValueData  = r_uintle32(f)

    imageSize = r_uintle32(f)
    print(imageSize)
    image_data = f.read(f"bytes:{imageSize}")
    return Image.frombytes('RGBA', (pixelWidth, pixelHeight), image_data, 'astc', (8, 8))

def astc_convert(data):
    f = ConstBitStream(io.BytesIO(data))
    block_x, block_y = f.readlist("pad32, 2*uintle8 , pad8")
    size_x, size_y = f.readlist("2*uintle24, pad24")

    return Image.frombytes('RGBA', (size_x, size_y), f.read(f"bytes"), "astc", (block_x, block_y))

def convert_image(data, extension):
    if extension in ["tga", "ico", "tiff", "dds"]:
        return return_png(pillow_image_conversion(data, extension))
    elif extension == "pvr":
        return return_png(pvr_convert(data))
    elif extension == "ktx":
        return return_png(ktx_convert(data))
    elif extension == "astc":
        return return_png(astc_convert(data))
    elif extension == "cbk":
        return return_png(compblks_convert(data))
    return False
        

