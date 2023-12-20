from argparse import ArgumentParser
from pathlib import Path
import shutil
from PIL import Image
import py7zr
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tqdm import tqdm
from dataclasses import dataclass


@dataclass
class ImageEntry:
    source: Path
    dest: Path


def create_archive(dir: Path, entries: list[ImageEntry], archive: Path) -> None:
    original = Path('.').absolute()
    os.chdir(dir)
    with py7zr.SevenZipFile(archive, 'w') as arch:
        for entry in tqdm(entries, desc="Archiving"):
            arch.write(entry.dest.relative_to(dir))

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
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if exif is not None:
        img.save(out_file, 'jpeg', quality=90, exif=exif,
                 progressive=True, optimize=True)
    else:
        img.save(out_file, 'jpeg', quality=90,
                 progressive=True, optimize=True)

    if in_file.stat().st_size <= out_file.stat().st_size:
        out_file.unlink()
        shutil.copy(in_file, out_file)


def _fetch_image_entries(tmp_dir: Path, entry: Path, entries: list[ImageEntry]) -> list[ImageEntry]:
    if entry.is_dir():
        for dir_entry in entry.iterdir():
            _fetch_image_entries(tmp_dir/entry.name, dir_entry, entries)
    elif entry.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.webp']:
        entries.append(ImageEntry(entry, tmp_dir/entry.name))
    else:
        print(f'[WARNING] File ignored: {entry.absolute()}')

    return entries


def fetch_image_entries(tmp_dir: Path, entries: list[Path]) -> list[ImageEntry]:
    out = []
    for entry in entries:
        _fetch_image_entries(tmp_dir, entry, out)
    return out


def process_entries(entries: list[ImageEntry]) -> None:
    for entry in tqdm(entries, desc="Compressing"):
        compress_jpeg(entry.source, entry.dest)


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--destination', type=Path,
                        help='Destination file', required=True)
    parser.add_argument('entry', nargs='+', type=Path,
                        help='Files/Directories to archive')

    args = parser.parse_args()
    destination: Path = args.destination.with_suffix('.7z').absolute()

    try:
        image_entries = fetch_image_entries(Path('tmp'), args.entry)
        print(f'Found: {len(image_entries)} entries')
        process_entries(image_entries)
        create_archive(Path('tmp'), image_entries, destination)
        # print("Uploading archive...", flush=True)
        # upload_to_drive(destination)
        print("Done")
    finally:
        shutil.rmtree(Path('tmp'), ignore_errors=True)


if __name__ == '__main__':
    main()
