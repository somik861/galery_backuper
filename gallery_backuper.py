from argparse import ArgumentParser
from pathlib import Path
import shutil
from PIL import Image
import py7zr
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def create_archive(dir: Path, archive: Path) -> None:
    original = Path('.').absolute()
    orig_dir = dir.absolute()
    os.chdir(dir)
    with py7zr.SevenZipFile(archive, 'w') as arch:
        for entry in orig_dir.iterdir():
            arch.writeall(entry.name)

    os.chdir(original)


def upload_to_drive(file: Path) -> None:
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    drive_file = drive.CreateFile()
    drive_file.SetContentFile(file)
    drive_file.Upload()


def compress_jpeg(in_file: Path, out_file: Path) -> None:
    img = Image.open(in_file)
    exif = img.info.get('exif', None)

    if exif is not None:
        img.save(out_file, "jpeg", quality=90, exif=exif,
                 progressive=True, optimize=True)
    else:
        img.save(out_file, "jpeg", quality=90,
                 progressive=True, optimize=True)

    if in_file.stat().st_size <= out_file.stat().st_size:
        out_file.unlink()
        shutil.copy(in_file, out_file)


def _process_entry(tmp_dir: Path, entry: Path) -> None:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    if entry.is_dir():
        for dir_entry in entry.iterdir():
            _process_entry(tmp_dir/entry.name, dir_entry)
    elif entry.suffix.lower() in ['.jpg', '.jpeg', '.png', 'tiff', 'tif', 'gif']:
        compress_jpeg(entry, tmp_dir/entry.name)
    else:
        print(f'[WARNING] File ignored: {entry.absolute()}')


def process_entries(tmp_dir: Path, entries: list[Path]) -> None:
    for entry in entries:
        _process_entry(tmp_dir, entry)


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--destination', type=Path,
                        help='Destination file', required=True)
    parser.add_argument('entry', nargs='+', type=Path,
                        help='Files/Directories to archive')

    args = parser.parse_args()
    destination: Path = args.destination.with_suffix('.7z').absolute()

    try:
        print("Compressing entries...", flush=True)
        process_entries(Path('tmp'), args.entry)
        print("Compressing archive...", flush=True)
        create_archive(Path('tmp'), destination)
        #print("Uploading archive...", flush=True)
        #upload_to_drive(destination)
        print("Done")
    finally:
        shutil.rmtree(Path('tmp'))


if __name__ == '__main__':
    main()
