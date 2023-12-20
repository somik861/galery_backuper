from argparse import ArgumentParser
from pathlib import Path
import shutil
from PIL import Image
import py7zr
import os

shutil.register_archive_format(
    '7zip', py7zr.pack_7zarchive, description='7zip archive')


def create_archive(dir: Path, archive: Path) -> None:
    original = Path('.').absolute()
    orig_dir = dir.absolute()
    os.chdir(dir)
    with py7zr.SevenZipFile(original/archive.with_suffix('.7z'), 'w') as arch:
        for entry in orig_dir.iterdir():
            arch.writeall(entry.name)

    os.chdir(original)


def compress_jpeg(in_file: Path, out_file: Path) -> None:
    img = Image.open(in_file)
    exif = img.info['exif']

    img.save(out_file, "jpeg", quality=90, exif=exif)

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

    print("Compressing entries...", flush=True)
    process_entries(Path('tmp'), args.entry)
    print("Compressing archive...", flush=True)
    create_archive(Path('tmp'), args.destination)
    # shutil.rmtree(Path('tmp'))
    print("Done")


if __name__ == '__main__':
    main()
