#!/usr/bin/env python3
"""Checked Disc-1 field-mecha compatibility data for Weltall-2.

Three-dimensional field and cutscene mecha do not use the mounted field
sprites.  Model zero loads directory-4 files 0x06BA/0x06BB (canonical
2144/2145), while native Weltall-2 model 0x2A loads 0x070E/0x070F
(canonical 2228/2229).

Weltall-2's geometry has a different skeleton, so its geometry cannot safely
be driven by Weltall's controller.  Conversely, the native Weltall-2
controller exposes only animations 0..8, while Disc-1 model-zero scripts can
request higher IDs.  ``build_compat_controller`` retains Weltall-2's complete
keyframe bank and bytecode tail, then creates a 23-entry compatibility table
whose entries are byte-for-byte copies of native Weltall-2 programs.

The table is memory- and skeleton-safe, but several Weltall-only story motions
have no native Weltall-2 equivalent.  Their conservative substitutions still
require emulator validation for scene choreography and camera composition.
"""

from __future__ import annotations

import hashlib
import struct
from typing import Final


# Directory-4 selector pairs used by the field mecha loader.
FIELD_WELTALL_CONTROLLER_ID: Final = 2144       # local 0x06BA
FIELD_WELTALL_GEOMETRY_ID: Final = 2145         # local 0x06BB
# Model 7 is a second scripted/cinematic Weltall variant used in five Disc-1
# scenes, including Citan's Rankar-sequence transformation choreography.
FIELD_TRANSFORM_WELTALL_CONTROLLER_ID: Final = 2158  # local 0x06C8
FIELD_TRANSFORM_WELTALL_GEOMETRY_ID: Final = 2159    # local 0x06C9
FIELD_WELTALL2_CONTROLLER_ID: Final = 2228      # local 0x070E
FIELD_WELTALL2_GEOMETRY_ID: Final = 2229        # local 0x070F

# The same geometry payloads are reused by the normal-battle directory.
BATTLE_WELTALL_GEOMETRY_ID: Final = 2926
BATTLE_WELTALL2_GEOMETRY_ID: Final = 2928


# Exact USA retail Disc-1 identities.  The equality of the respective field
# and battle hashes is intentional and proves that each geometry is shared
# byte-for-byte between those two engines.
RETAIL_RESOURCE_IDENTITIES: Final = {
    FIELD_WELTALL_CONTROLLER_ID: (
        20_892,
        "ace45304ce982e61931b3db177938c271ac6e3f95e7eb542a590c56f1308d0fe",
    ),
    FIELD_WELTALL_GEOMETRY_ID: (
        49_840,
        "2584a9f52d50a6be4518a582474ce3a9523d99fb9eaa71e420f56dfb8b1086a1",
    ),
    FIELD_TRANSFORM_WELTALL_CONTROLLER_ID: (
        8_188,
        "ca59d8d9914b63e005aee6252d631d1047bf90ffdd24b86a44af79d12201a928",
    ),
    FIELD_TRANSFORM_WELTALL_GEOMETRY_ID: (
        52_060,
        "b00a8cc8c0f72487f6d1f78307a6c4c3e56bc3f7a211d83b0c265e65f48ac9e5",
    ),
    FIELD_WELTALL2_CONTROLLER_ID: (
        9_564,
        "c29cdec622f480170005e37e3785f2fba6bbc0d3415c38612bdb6b701293adf8",
    ),
    FIELD_WELTALL2_GEOMETRY_ID: (
        52_280,
        "b3576c385efba096fa45895b2141888f68c4e2c7c0258485849d9ab61d5e0afe",
    ),
    BATTLE_WELTALL_GEOMETRY_ID: (
        49_840,
        "2584a9f52d50a6be4518a582474ce3a9523d99fb9eaa71e420f56dfb8b1086a1",
    ),
    BATTLE_WELTALL2_GEOMETRY_ID: (
        52_280,
        "b3576c385efba096fa45895b2141888f68c4e2c7c0258485849d9ab61d5e0afe",
    ),
}


# Regular-Weltall target animation ID -> native Weltall-2 donor animation ID.
# IDs 0..3 retain the closest like-for-like base/single-pose/interpolated
# programs.  Repeated neutral, multi-pose, and finite native clips provide
# safe substitutes for the remaining story-only motions.
REGULAR_TO_WELTALL2_ANIMATION: Final = (
    0, 1, 2, 3, 2, 1, 3, 4, 3, 3, 5, 5,
    4, 4, 6, 7, 5, 8, 8, 8, 8, 5, 5,
)

# The Rankar event embeds model 7 with one keyframe bank plus exactly 32
# animation programs.  Only animation 1 is explicitly selected in the event,
# but retaining the complete table width makes every possible lookup safe.
RANKAR_TRANSFORM_TO_WELTALL2_ANIMATION: Final = (
    REGULAR_TO_WELTALL2_ANIMATION + (1,) * 9
)

WELTALL2_SOURCE_ROOTS: Final = (2, 0x10, 0x253C, 0x255C)
WELTALL2_SOURCE_POINTERS: Final = (
    0x0030,
    0x23D4,
    0x2414,
    0x2434,
    0x2454,
    0x2478,
    0x2494,
    0x24C4,
    0x24E4,
    0x2508,
    0x252C,
)
WELTALL2_KEYFRAME_SHA256: Final = (
    "84535aea3475814142622f989148950f74c4a877c26f49ccedea3f35b8233b1f"
)
WELTALL2_PROGRAM_SHA256: Final = (
    "5062e2029dc2d92eeede601602306293e350ba88da7e9ba159fbadcfc0aa7583",
    "4f53903309fc7dd16c05fc6e8262829f10dda522e34316119c0bcb0ec101fbae",
    "dc0873c28a7b4d01c61e252839605dc8ab05d7a9954b7d3dd5b4065d0aa80841",
    "8c168d34ca4267deeafc439fea2e588d67653cc289dd0f830d47aad283237887",
    "405c5b2a884890a9d437b73f18275976289644771e683ce6de19e5442cea0cba",
    "76aaf12697b4c765af256c5a4d18a975794ec4fa3da30744caa0807fb28568fc",
    "363a8e4fc812252b8312a54d67d4e1cac2fd1cc8671af2b4b5d47803762a2cdc",
    "fe24f676632875cf1ad6588d7454d8665855c82a2bf57d63447cceb8b18190f3",
    "ade53171b88c018bb7b588ba931f0c60f3752de2054f0a2a85bf7c1aaef72263",
)
WELTALL2_TAIL_SHA256: Final = (
    "e13f50e0c01760ce1f735a67473841d641a402c356f429771e5b67b461ec5e9f"
)

COMPAT_CONTROLLER_ROOTS: Final = (2, 0x10, 0x2784, 0x27A4)
COMPAT_CONTROLLER_SIZE: Final = 10_148
COMPAT_CONTROLLER_SHA256: Final = (
    "e8c8519f888e3d2ddd6316667948588809f7405abc8b60053ff4b5809f0c0728"
)
RANKAR_TRANSFORM_COMPAT_CONTROLLER_ROOTS: Final = (2, 0x10, 0x28C8, 0x28E8)
RANKAR_TRANSFORM_COMPAT_CONTROLLER_SIZE: Final = 10_472
RANKAR_TRANSFORM_COMPAT_CONTROLLER_SHA256: Final = (
    "53d4bc74dd64b90cc9eaf4e849869576ad468d1af5dab975985330b70cac6654"
)


class Weltall2Field3DError(RuntimeError):
    """Raised when audited field-mecha data or structure changes."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_retail_resource(canonical_id: int, data: bytes) -> None:
    """Validate one audited controller or geometry payload."""

    try:
        expected_size, expected_hash = RETAIL_RESOURCE_IDENTITIES[canonical_id]
    except KeyError as exc:
        raise Weltall2Field3DError(
            f"Canonical {canonical_id} is not an audited field-mecha resource"
        ) from exc
    actual_hash = _sha256(data)
    if len(data) != expected_size or actual_hash != expected_hash:
        raise Weltall2Field3DError(
            f"Canonical {canonical_id} identity changed: {len(data)} bytes, "
            f"SHA-256 {actual_hash}; expected {expected_size}, {expected_hash}"
        )


def _controller_entries(
    controller: bytes,
) -> tuple[tuple[int, int, int, int], tuple[bytes, ...], bytes]:
    """Parse the complete two-part field-mecha controller archive."""

    if len(controller) < 16:
        raise Weltall2Field3DError("Field-mecha controller is truncated")
    roots = struct.unpack_from("<4I", controller, 0)
    count, main_start, tail_start, archive_end = roots
    if (
        count != 2
        or main_start != 16
        or not main_start < tail_start < archive_end
        or archive_end != len(controller)
    ):
        raise Weltall2Field3DError(
            f"Field-mecha outer archive is invalid: {roots}"
        )

    entry_count = struct.unpack_from("<I", controller, main_start)[0]
    pointer_count = entry_count + 1
    table_start = main_start + 4
    table_end = table_start + pointer_count * 4
    if entry_count == 0 or table_end > tail_start:
        raise Weltall2Field3DError("Field-mecha nested table is truncated")
    pointers = struct.unpack_from(
        f"<{pointer_count}I", controller, table_start
    )
    table_size = 4 + pointer_count * 4
    if (
        pointers[0] != table_size
        or pointers[-1] != tail_start - main_start
        or any(pointer % 4 for pointer in pointers)
        or any(left >= right for left, right in zip(pointers, pointers[1:]))
    ):
        raise Weltall2Field3DError(
            f"Field-mecha nested pointers are invalid: {pointers}"
        )

    entries = tuple(
        controller[main_start + pointers[index] : main_start + pointers[index + 1]]
        for index in range(entry_count)
    )
    return roots, entries, controller[tail_start:archive_end]


def _build_mapped_controller(
    w2_controller: bytes,
    animation_map: tuple[int, ...],
    *,
    expected_roots: tuple[int, int, int, int],
    expected_size: int,
    expected_hash: str,
    role: str,
) -> bytes:
    """Build one checked controller entirely from native Weltall-2 data."""

    validate_retail_resource(FIELD_WELTALL2_CONTROLLER_ID, w2_controller)
    roots, source_entries, source_tail = _controller_entries(w2_controller)
    if roots != WELTALL2_SOURCE_ROOTS:
        raise Weltall2Field3DError(
            f"Weltall-2 controller roots changed: {roots}"
        )
    if len(source_entries) != 10:
        raise Weltall2Field3DError(
            "Weltall-2 controller no longer contains one keyframe bank and "
            "nine animation programs"
        )

    main_start = roots[1]
    entry_count = len(source_entries)
    pointers = struct.unpack_from(
        f"<{entry_count + 1}I", w2_controller, main_start + 4
    )
    if pointers != WELTALL2_SOURCE_POINTERS:
        raise Weltall2Field3DError(
            f"Weltall-2 nested pointers changed: {pointers}"
        )
    keyframes, *source_programs = source_entries
    if _sha256(keyframes) != WELTALL2_KEYFRAME_SHA256:
        raise Weltall2Field3DError("Weltall-2 keyframe bank identity changed")
    program_hashes = tuple(_sha256(program) for program in source_programs)
    if program_hashes != WELTALL2_PROGRAM_SHA256:
        raise Weltall2Field3DError(
            "One or more Weltall-2 animation program identities changed"
        )
    if _sha256(source_tail) != WELTALL2_TAIL_SHA256:
        raise Weltall2Field3DError("Weltall-2 controller tail identity changed")
    if not animation_map or any(
        not 0 <= donor < len(source_programs) for donor in animation_map
    ):
        raise Weltall2Field3DError(f"{role} animation map is invalid")

    output_entries = (
        keyframes,
        *(source_programs[donor] for donor in animation_map),
    )
    nested_header_size = 4 + 4 * (len(output_entries) + 1)
    output_pointers: list[int] = []
    cursor = nested_header_size
    for entry in output_entries:
        output_pointers.append(cursor)
        cursor += len(entry)
    output_pointers.append(cursor)
    main = (
        struct.pack(
            f"<I{len(output_pointers)}I",
            len(output_entries),
            *output_pointers,
        )
        + b"".join(output_entries)
    )
    output_roots = (
        2,
        16,
        16 + len(main),
        16 + len(main) + len(source_tail),
    )
    result = struct.pack("<4I", *output_roots) + main + source_tail

    # Reparse the result and prove every model-local record is an exact native
    # Weltall-2 record selected by the declared compatibility map.
    checked_roots, checked_entries, checked_tail = _controller_entries(result)
    if checked_roots != expected_roots:
        raise Weltall2Field3DError(
            f"{role} controller roots changed: {checked_roots}"
        )
    if (
        len(checked_entries) != len(animation_map) + 1
        or checked_entries[0] != keyframes
    ):
        raise Weltall2Field3DError(
            f"{role} controller did not preserve its keyframe bank"
        )
    for target_id, donor_id in enumerate(animation_map):
        if checked_entries[target_id + 1] != source_programs[donor_id]:
            raise Weltall2Field3DError(
                f"{role} animation {target_id} differs from native "
                f"Weltall-2 donor {donor_id}"
            )
    if checked_tail != source_tail:
        raise Weltall2Field3DError(
            f"{role} controller did not preserve its bytecode tail"
        )
    actual_hash = _sha256(result)
    if len(result) != expected_size or actual_hash != expected_hash:
        raise Weltall2Field3DError(
            f"{role} result changed: {len(result)} bytes, SHA-256 "
            f"{actual_hash}; expected {expected_size}, {expected_hash}"
        )
    return result


def build_compat_controller(w2_controller: bytes) -> bytes:
    """Build the checked 23-animation controller for regular Weltall."""

    if len(REGULAR_TO_WELTALL2_ANIMATION) != 23:
        raise Weltall2Field3DError("Compatibility animation map is invalid")
    return _build_mapped_controller(
        w2_controller,
        REGULAR_TO_WELTALL2_ANIMATION,
        expected_roots=COMPAT_CONTROLLER_ROOTS,
        expected_size=COMPAT_CONTROLLER_SIZE,
        expected_hash=COMPAT_CONTROLLER_SHA256,
        role="regular-Weltall compatibility",
    )


def build_rankar_transform_compat_controller(w2_controller: bytes) -> bytes:
    """Build the 32-program controller for the Rankar model-7 actor."""

    if len(RANKAR_TRANSFORM_TO_WELTALL2_ANIMATION) != 32:
        raise Weltall2Field3DError("Rankar transform animation map is invalid")
    return _build_mapped_controller(
        w2_controller,
        RANKAR_TRANSFORM_TO_WELTALL2_ANIMATION,
        expected_roots=RANKAR_TRANSFORM_COMPAT_CONTROLLER_ROOTS,
        expected_size=RANKAR_TRANSFORM_COMPAT_CONTROLLER_SIZE,
        expected_hash=RANKAR_TRANSFORM_COMPAT_CONTROLLER_SHA256,
        role="Rankar transform Weltall compatibility",
    )


__all__ = [
    "BATTLE_WELTALL2_GEOMETRY_ID",
    "BATTLE_WELTALL_GEOMETRY_ID",
    "COMPAT_CONTROLLER_ROOTS",
    "COMPAT_CONTROLLER_SHA256",
    "COMPAT_CONTROLLER_SIZE",
    "FIELD_TRANSFORM_WELTALL_CONTROLLER_ID",
    "FIELD_TRANSFORM_WELTALL_GEOMETRY_ID",
    "FIELD_WELTALL2_CONTROLLER_ID",
    "FIELD_WELTALL2_GEOMETRY_ID",
    "FIELD_WELTALL_CONTROLLER_ID",
    "FIELD_WELTALL_GEOMETRY_ID",
    "RANKAR_TRANSFORM_COMPAT_CONTROLLER_ROOTS",
    "RANKAR_TRANSFORM_COMPAT_CONTROLLER_SHA256",
    "RANKAR_TRANSFORM_COMPAT_CONTROLLER_SIZE",
    "RANKAR_TRANSFORM_TO_WELTALL2_ANIMATION",
    "REGULAR_TO_WELTALL2_ANIMATION",
    "RETAIL_RESOURCE_IDENTITIES",
    "Weltall2Field3DError",
    "build_compat_controller",
    "build_rankar_transform_compat_controller",
    "validate_retail_resource",
]
