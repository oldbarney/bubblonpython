"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
import tempfile
from subprocess import Popen, run

from PIL import Image, ImageTk
from .gutils import icon

thumbnail_map={
    'py':'python',
    'txt':'page',
    'xml':'page',
    'pdf':'page',
    'odt': 'page',
    'docx': 'page',
    'odx': 'tableupdate',
    'xlsx': 'tableupdate',
    'pbub':'create',
    'pas':'toolkit',
    'java':'toolkit',
    'c':'toolkit',
    'h':'toolkit',
    'cpp':'toolkit',
    'hpp':'toolkit',
    'js':'toolkit',
    'htm':'www',
    'html':'www',
    'mov':'playvideo',
    'mov':'playvideo',
    'mpg':'playvideo',
    'mpeg':'playvideo',
    'webm':'playvideo',
    'mov':'playvideo',
    'mkv': 'playvideo',
    'flv': 'playvideo',
    'vob': 'playvideo',
    'ogg': 'playvideo',
    'avi': 'playvideo',
    'wmv': 'playvideo',

    'wav':'playsound',
    'mp3':'playsound',
    'flac':'playsound',
    'aac':'playsound',
    'aiff': 'playsound',
    'au': 'playsound',
    'raw': 'playsound',
    'xz':'archive',
    'zip':'archive',
    '7z':'archive',
    'rar':'archive',
}

thumbnail_cache={}

class ThumbnailManager:
    def __init__(self,thumbnail_folder=None):
        if thumbnail_folder is None:
            thumbnail_folder=tempfile.gettempdir()+'/thumbnails'
        self.thumbnail_folder=thumbnail_folder
        if not os.path.isdir(thumbnail_folder):
            os.mkdir(thumbnail_folder)
        thumbnail_cache.clear()

    def clear_cache(self):
        thumbnail_cache.clear()

    def get_thumbnail(self,fn,size=32):
        tfn = f'{self.thumbnail_folder}/{fn.__hash__()}_{size}.png'
        try:
            return thumbnail_cache[tfn]
        except KeyError:
            pass

        if any (fn.lower().endswith(end)
            for end in (
                '.png','.gif','.jpg','.jpeg','.gif','.tiff','.bmp'
            )
        ):
            try:
                if not os.path.isfile(tfn):
                    im=Image.open(fn)
                    im.thumbnail((size,size))
                    im.save(tfn)
                else:
                    im=Image.open(tfn)
                    im.load()
                thumbnail_cache[tfn]=result=ImageTk.PhotoImage(im)
                #print('RETURNING IMAGE',result)
                return result

            except Exception as e:
                pass
                #print('FAILED TO GET THUMBNAIL',e)
                #return icon('question')
        elif any(fn.lower().endswith(end)
            for end in ('.wmv','.mpg','.mp4','.mpeg','.mov',
                '.webm','.mkv'
            )
        ):
            try:
               if not os.path.isfile(tfn):
                   try:
                       run(['ffmpeg', '-i', fn, '-frames:v', '1','-an', '-s', f'{size}x{size}',
                          tfn],check=True,capture_output=True)
                   except Exception as e:
                       #print('FFMPEG EXCEPTION',e)
                       return icon('playvideo')
                   im = Image.open(tfn)
                   im.load()
                   im.thumbnail((size, size))
               else:
                   im = Image.open(tfn)
                   im.load()

               thumbnail_cache[tfn] = result = ImageTk.PhotoImage(im)
               return result

            except Exception as e:
                pass #print('FAILED TO GET THUMBNAIL',e)
                #return icon('question')

        try:
            return icon(thumbnail_map[fn.lower().split('.')[-1]],icon_size=size)
        except KeyError:
            #print('NO ICON')
            return icon('blankpage',icon_size=size)