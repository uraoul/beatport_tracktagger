import json
import re

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from pathlib import Path
from track import Track

beatport_id_pattern = re.compile('^[0-9]+[_]')

def scrapeFileTags(path):
  if Path(path).suffix == ".flac":
    f = FLAC(path)  
  elif Path(path).suffix == ".mp3":
    f = EasyID3(path)  

  tr = Track(0)
  tr.file_name = Path(path).name
  tr.file_path = Path(path)
  # extract artist and title
  try:
    tr.artists = f['ARTIST']
    tr.title = f['TITLE'].pop().split(' (')[0]
  except:
    print("** error cannot match file without artist or title")
    print("** skipping")
    return

  # try to extract remixer
  try:
    tr.remixer = f['TITLE'][0].split('(')[1].split(')')[0]
  except:
    # assume it's original mix, when no remixer is supplied
    tr.remixer = "Original Mix"
  return tr

# return valid filetypes only
def scanFiletype(src, recursive):
  filetypes = '.flac', '.mp3'
  if Path(src).is_file():           # single file
    files = [Path(src)]
  elif recursive:                   # recursive 
    files = Path(src).glob('**/*')
  else:                             # input folder
    files = Path(src).glob('*')     

  # match filetype
  out = []
  for f in files:
    if Path(f).suffix in filetypes: 
      out.append(f)
  return out

# *** database ***

class Database:
  def __init__(self):
    # from file scan
    self.track_count = 0
    self.db = dict()

  # get path of scanned files with beatport id in filename
  def scanBeatportID(self, files):
    outputFiles = []
    for f in files:
      # match beatport id in Track.db
      if beatport_id_pattern.match(Path(f).name):
        beatport_id = beatport_id_pattern.match(Path(f).name).group()[:-1]
        if beatport_id in self.db.keys():
          # assing scanned path to db
          self.db[beatport_id].file_path = Path(f)
        outputFiles.append(Path(f))
    self.track_count = len(outputFiles)
    return outputFiles

  def trackInDB(self, beatport_id):
    if beatport_id in self.db:
      return True
    return False
    
  def loadJSON(self, src):
    json_db = []
    with open(src, 'r') as f:
      json_db = f.readlines()
    for track in json_db:
      track_object = Track()
      track_object.__dict__ = json.loads(track)
      self.db[track_object.beatport_id] = track_object

  def saveJSON(self, src):
    with open(src, 'w') as f:
      for k, v in self.db.items():
        import copy                      # raw object copy, to make true duplicate
        vv = copy.copy(v) 
        if "file_path" in vv.__dict__:
          del vv.__dict__["file_path"]   # we won't store file_path
        track_json = json.dumps(vv.__dict__)
        f.write(track_json + '\n')

