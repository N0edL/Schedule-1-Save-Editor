
from pathlib import Path

savefile_dir = next((x for x in (Path.home() / "AppData" / "LocalLow" / "TVGS" / "Schedule I" / "saves").iterdir() if x.is_dir()), None)

def load_save_folders():
    if savefile_dir is None:
        return
    for x in savefile_dir.iterdir():
        return {"name": x.name, "path": x}