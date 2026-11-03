"""Create a small complete ALTO-only test project, using only Python stdlib.

Images are synthetic horizontal strokes, not reproductions of manuscripts.
Run: python creer_demo.py
"""
from pathlib import Path
import struct
import zlib

from varians_synchro.core import new_project, create_witness, add_image_source, add_alto_source, save_project
from varians_synchro.imaging import create_pages, bind_alto


def write_png(path, shift=0):
    width, height = 580, 440
    pixels = []
    for y in range(height):
        line=bytearray()
        for x in range(width):
            ink = any(y in range(top+shift,top+shift+12) and 65 < x < end
                      for top,end in ((70,490),(155,535),(245,450)))
            line.extend((60,52,44) if ink else (248,246,237))
        pixels.append(b'\0'+bytes(line))
    raw=zlib.compress(b''.join(pixels),9)
    def chunk(tag, data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+
                     chunk(b'IDAT',raw)+chunk(b'IEND',b''))


def write_alto(path, texts):
    content = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">',
               '<Layout><Page ID="page1" WIDTH="580" HEIGHT="440"><PrintSpace>']
    for i,text in enumerate(texts,1):
        from xml.sax.saxutils import escape
        top=70+(i-1)*85
        content.append(f'<TextLine ID="line{i}" HPOS="60" VPOS="{top}" WIDTH="480" HEIGHT="16">'
                       f'<String CONTENT="{escape(text, {chr(34): "&quot;"})}"/></TextLine>')
    content+=['</PrintSpace></Page></Layout></alto>']
    path.write_text('\n'.join(content),encoding='utf-8')


def main():
    folder=Path(__file__).resolve().parent/'demo_local_ALTO'
    folder.mkdir(exist_ok=True)
    p=new_project('Exemple de deux témoins ALTO sans TEI')
    for witness_id, texts, shift in (
        ('A',['Beatus Germanus in hac vita','multis miraculis claruit','et populum docuit'],0),
        ('B',['Beatus Germanus in','hac vita multis miraculis','claruit et populum docuit'],10)):
        w=create_witness(p,witness_id)
        img=folder/f'{witness_id}.png';alto=folder/f'{witness_id}.xml'
        write_png(img,shift)
        write_alto(alto,texts)
        add_image_source(w,'local',img)
        create_pages(w)
        data=add_alto_source(w,alto)
        bind_alto(w,w['pages'][0]['id'],data['id'])
    output=folder/'exemple.vsynch'
    save_project(p,output)
    print('Projet de démonstration créé :',output)


if __name__=='__main__':
    main()
