import argparse
import bz2
import tarfile
import zlib
import os
import sys
import time
from pathlib import Path


# --------------------- Вспомогательные функции ---------------------

def compress_zstd(data: bytes, level: int = 3) -> bytes:
    return zlib.compress(data, level)  # имитация zstd, т.к. стандартная библиотека не поддерживает zstd


def decompress_zstd(data: bytes) -> bytes:
    return zlib.decompress(data)


def compress_bz2(data: bytes, level: int = 9) -> bytes:
    return bz2.compress(data, compresslevel=level)


def decompress_bz2(data: bytes) -> bytes:
    return bz2.decompress(data)


def tar_directory(source_dir: Path, output_tar: Path):
    with tarfile.open(output_tar, "w") as tar:
        tar.add(source_dir, arcname=source_dir.name)


def untar_file(tar_path: Path, output_dir: Path):
    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(path=output_dir)


def print_progress_bar(progress, total, length=30):
    done = int(length * progress / total)
    bar = "█" * done + "-" * (length - done)
    print(f"\r[{bar}] {progress}/{total}", end='', flush=True)


# --------------------- Основные операции ---------------------

def compress(source: Path, target: Path, benchmark=False):
    start_time = time.perf_counter()

    temp_tar = None
    if source.is_dir():
        temp_tar = source.parent / f"{source.name}.tar"
        tar_directory(source, temp_tar)
        input_path = temp_tar
    else:
        input_path = source

    with open(input_path, "rb") as f:
        data = f.read()

    if target.suffix == ".bz2":
        compressed = compress_bz2(data)
    elif target.suffix == ".zst":
        compressed = compress_zstd(data)
    else:
        raise ValueError("Неподдерживаемое расширение файла. Используйте .bz2 или .zst")

    with open(target, "wb") as f:
        f.write(compressed)

    if temp_tar and temp_tar.exists():
        os.remove(temp_tar)

    if benchmark:
        print(f"\nВремя архивации: {time.perf_counter() - start_time:.2f} с")


def decompress(source: Path, target_dir: Path, benchmark=False):
    start_time = time.perf_counter()

    with open(source, "rb") as f:
        data = f.read()

    if source.suffix == ".bz2":
        decompressed = decompress_bz2(data)
    elif source.suffix == ".zst":
        decompressed = decompress_zstd(data)
    else:
        raise ValueError("Неподдерживаемое расширение файла. Используйте .bz2 или .zst")

    temp_tar = target_dir / "temp.tar"
    with open(temp_tar, "wb") as f:
        f.write(decompressed)

    try:
        untar_file(temp_tar, target_dir)
        os.remove(temp_tar)
    except tarfile.ReadError:
        os.replace(temp_tar, target_dir / source.stem)

    if benchmark:
        print(f"\nВремя распаковки: {time.perf_counter() - start_time:.2f} с")


# --------------------- CLI ---------------------

def main():
    parser = argparse.ArgumentParser(
        description="Утилита для архивации и распаковки файлов/папок (.bz2, .zst)"
    )
    parser.add_argument("source", type=Path, help="Источник (файл или директория)")
    parser.add_argument("target", type=Path, help="Целевой файл архива или директория распаковки")
    parser.add_argument(
        "--extract",
        "-x",
        action="store_true",
        help="Режим распаковки"
    )
    parser.add_argument(
        "--benchmark",
        "-b",
        action="store_true",
        help="Показать время выполнения"
    )
    args = parser.parse_args()

    if args.extract:
        decompress(args.source, args.target, benchmark=args.benchmark)
    else:
        compress(args.source, args.target, benchmark=args.benchmark)


if __name__ == "__main__":
    main()