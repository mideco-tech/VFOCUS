#!/usr/bin/env bash
# VFOCUS release build, based on the F4HWN Labs preset. Apache-2.0.
set -euo pipefail

if (( $# > 1 )); then
    echo "Usage: $0 [directory-containing-arm-none-eabi-gcc]" >&2
    exit 2
fi
if (( $# == 1 )); then
    toolchain_dir=$(cd "$1" && pwd)
    export PATH="$toolchain_dir:$PATH"
fi
cd "$(dirname "${BASH_SOURCE[0]}")/.."

version=$(tr -d '\r\n' < VERSION)
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "VERSION must contain a numeric major.minor.patch version" >&2
    exit 2
fi
edition="VF${version}-Labs"
# Multiboot stores a 16-byte edition name, including its terminating zero.
if (( ${#edition} > 15 )); then
    echo "Release edition does not fit the Multiboot name field: $edition" >&2
    exit 2
fi

arm-none-eabi-gcc --version | head -1
if [[ -z "${SOURCE_DATE_EPOCH:-}" ]]; then
    if ! SOURCE_DATE_EPOCH=$(git log -1 --format=%ct 2>/dev/null); then
        echo "Set SOURCE_DATE_EPOCH to the release manifest value when building a source archive." >&2
        exit 2
    fi
fi
if [[ ! "$SOURCE_DATE_EPOCH" =~ ^[0-9]+$ ]]; then
    echo "SOURCE_DATE_EPOCH must be a nonnegative Unix timestamp." >&2
    exit 2
fi
export SOURCE_DATE_EPOCH
build_dir=build/VFOCUS-Labs
target="vfocus.labs.v${version}"
cmake --fresh --preset Labs -B "$build_dir" \
    -DTARGET="$target" -DEDITION_STRING="$edition"
cmake --build "$build_dir" --parallel "${BUILD_JOBS:-4}"
arm-none-eabi-size "$build_dir/$target.elf"
sha256sum "$build_dir/$target.bin"
