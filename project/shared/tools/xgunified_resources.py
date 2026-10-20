#!/usr/bin/env python3
"""Compose the shared resources used by every unified Disc 2 module.

Mass Driver, Surface Soylent, and Rico were originally authored as independent
patches.  Several canonical files are global rather than field-local, so the
unified image must merge their individual records instead of choosing one
whole-file replacement.  The helpers here operate on the already-prepared
Mass Driver resources and preserve every unrelated archive entry byte-for-byte.
"""

from __future__ import annotations

import struct
from typing import Sequence

import modules.mass_driver.build as mass_driver
import modules.rico.tools.xgrico_balance as rico_balance
import modules.rico.tools.xgrico_native_title as rico_title
from modules.rico.recruitment import apply_rico_recruitment_profile, RICO_RECRUITMENT_LEVEL
from shared.tools.xgdeathblows import grant_all_on_foot_deathblows
from shared.tools.xgdialog import PLAIN_ENCODE


class UnifiedResourceError(RuntimeError):
    """A prepared global resource no longer matches its merge contract."""


_PARTY_MEMBERSHIP_OFFSET = 0x1D30
_LIVE_PARTY_STATE_RANGE = (0x1D32, 0x1D37)
_RICO_REQUIRED_MEMBER_IDS = (
    0,  # Fei
    2,  # Citan
    3,  # Bart
    rico_balance.RICO_ID,
    rico_balance.YOUNG_RICO_ID,
)
_RICO_REQUIRED_MEMBERSHIP_MASK = sum(
    1 << character_id for character_id in _RICO_REQUIRED_MEMBER_IDS
)


def _archive_entries(
    source: bytes,
    *,
    expected_count: int,
) -> tuple[bytes, list[bytes], tuple[int, ...]]:
    if len(source) < 4:
        raise UnifiedResourceError("Archive is truncated")
    count = struct.unpack_from("<I", source, 0)[0]
    if count != expected_count:
        raise UnifiedResourceError(
            f"Archive contains {count} entries, expected {expected_count}"
        )
    table_end = 4 + count * 4
    if table_end > len(source):
        raise UnifiedResourceError("Archive pointer table is truncated")
    offsets = struct.unpack_from(f"<{count}I", source, 4)
    if (
        offsets[0] < table_end
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
        or offsets[-1] >= len(source)
    ):
        raise UnifiedResourceError("Archive offsets are invalid")
    entries = [
        source[start : offsets[index + 1] if index + 1 < count else len(source)]
        for index, start in enumerate(offsets)
    ]
    return source[: offsets[0]], entries, offsets


def _rebuild_unaligned_archive(header: bytes, entries: Sequence[bytes]) -> bytes:
    result = bytearray(header)
    offsets: list[int] = []
    for entry in entries:
        offsets.append(len(result))
        result.extend(entry)
    struct.pack_into(f"<{len(entries)}I", result, 4, *offsets)
    return bytes(result)


def _indexed_string(source: bytes, entry_id: int) -> tuple[bytes, bytes]:
    maximum = struct.unpack_from("<I", source, 0)[0]
    count = maximum + 1
    if not 0 <= entry_id < count:
        raise UnifiedResourceError(f"String ID {entry_id} is outside 0..{maximum}")
    pointer_end = 4 + count * 2
    dimensions_end = pointer_end + count * 2
    if dimensions_end > len(source):
        raise UnifiedResourceError("Indexed string table is truncated")
    pointers = struct.unpack_from(f"<{count}H", source, 4)
    if (
        pointers[0] != dimensions_end
        or any(left >= right for left, right in zip(pointers, pointers[1:]))
        or pointers[-1] >= len(source)
    ):
        raise UnifiedResourceError("Indexed string offsets are invalid")
    end = pointers[entry_id + 1] if entry_id + 1 < count else len(source)
    dimensions = source[
        pointer_end + entry_id * 2 : pointer_end + entry_id * 2 + 2
    ]
    return source[pointers[entry_id] : end], dimensions


def _encoded_text(value: str) -> bytes:
    try:
        return bytes(PLAIN_ENCODE[character] for character in value) + b"\x00"
    except KeyError as exc:  # pragma: no cover - constants are import-time stable
        raise UnifiedResourceError(f"Unsupported menu character {exc.args[0]!r}") from exc


def merge_system_names(mass_names: bytes) -> bytes:
    """Add young Rico's three keepsake names to Mass Driver's Video Disk data."""

    decoded, consumed = rico_balance.decode_lzss_complete_groups(
        mass_names + bytes(16)
    )
    if consumed > len(mass_names) + 16:
        raise UnifiedResourceError("System-name stream exceeds its allocation")
    header, entries, _offsets = _archive_entries(
        decoded,
        expected_count=rico_balance.SYSTEM_NAMES_ARCHIVE_COUNT,
    )
    names_index = rico_balance.EQUIPMENT_NAMES_ARCHIVE_ENTRY
    names = entries[names_index]
    for item_id, value in rico_balance.YOUNG_RICO_EQUIPMENT_NAMES.items():
        names = rico_balance._replace_indexed_string(
            names,
            entry_id=item_id,
            expected_text=b"\x01\x00",
            expected_dimensions=b"\x00\x02",
            replacement_text=_encoded_text(value),
            replacement_dimensions=bytes((len(value) * 2, 1)),
        )
    if len(names) & 1:
        raise UnifiedResourceError("Young-Rico equipment-name entry lost alignment")
    entries[names_index] = names
    rebuilt = _rebuild_unaligned_archive(header, entries)
    result = rico_balance.compress_lzss_exact_complete_groups(rebuilt)
    round_trip, round_trip_consumed = rico_balance.decode_lzss_complete_groups(result)
    if round_trip != rebuilt or round_trip_consumed > len(result):
        raise UnifiedResourceError("Unified system names failed LZSS round-trip")

    # The two projects own different indexed tables.  Assert both payloads in
    # the final result so a future archive reordering cannot silently drop one.
    _, final_entries, _ = _archive_entries(
        round_trip,
        expected_count=rico_balance.SYSTEM_NAMES_ARCHIVE_COUNT,
    )
    video_name, _ = _indexed_string(
        final_entries[mass_driver.FACILITY_VIDEO_ITEM_NAME_ARCHIVE_ENTRY],
        mass_driver.FACILITY_VIDEO_ITEM_ID,
    )
    if video_name != _encoded_text(mass_driver.FACILITY_VIDEO_ITEM_NAME):
        raise UnifiedResourceError("Video Disk name was lost during Rico merge")
    for item_id, value in rico_balance.YOUNG_RICO_EQUIPMENT_NAMES.items():
        actual, _ = _indexed_string(final_entries[names_index], item_id)
        if actual != _encoded_text(value):
            raise UnifiedResourceError(f"Young-Rico item {item_id:#x} name was lost")
    return result


def merge_system_data(mass_data: bytes) -> bytes:
    """Merge Memento/keepsake data with Mass Driver's Video Disk description."""

    header, entries, offsets = _archive_entries(
        mass_data,
        expected_count=rico_balance.SYSTEM_DATA_ARCHIVE_COUNT,
    )

    item_index = rico_balance.MEMENTO_ITEM_ARCHIVE_ENTRY
    item_decoded, item_consumed = rico_balance.decode_lzss_complete_groups(
        entries[item_index] + bytes(16)
    )
    if item_consumed > len(entries[item_index]) + 16:
        raise UnifiedResourceError("Memento item stream exceeds its allocation")
    start = rico_balance.MEMENTO_ITEM_RECORD_OFFSET
    end = start + rico_balance.MEMENTO_ITEM_RECORD_SIZE
    if item_decoded[start:end] != rico_balance.MEMENTO_ITEM_RETAIL_RECORD:
        raise UnifiedResourceError("Disc 2 Memento record changed")
    patched_item = bytearray(item_decoded)
    struct.pack_into(
        "<H",
        patched_item,
        start + 0x0A,
        rico_balance.MEMENTO_ITEM_EFFECT_FLAGS,
    )
    entries[item_index] = rico_balance.compress_lzss_exact_complete_groups(
        bytes(patched_item)
    )

    descriptions_index = rico_balance.MEMENTO_DESCRIPTION_ARCHIVE_ENTRY
    descriptions, description_consumed = rico_balance.decode_lzss_complete_groups(
        mass_data[offsets[descriptions_index] :] + bytes(16)
    )
    if description_consumed > len(entries[descriptions_index]) + 16:
        raise UnifiedResourceError("Equipment-description stream exceeds allocation")
    descriptions = rico_balance._replace_indexed_string(
        descriptions,
        entry_id=rico_balance.MEMENTO_ITEM_ID,
        expected_text=b"\x01\x00",
        expected_dimensions=b"\x00\x02",
        replacement_text=_encoded_text(rico_balance.MEMENTO_DESCRIPTION),
        replacement_dimensions=rico_balance.MEMENTO_DESCRIPTION_DIMENSIONS,
    )
    for item_id, value in rico_balance.YOUNG_RICO_EQUIPMENT_DESCRIPTIONS.items():
        descriptions = rico_balance._replace_indexed_string(
            descriptions,
            entry_id=item_id,
            expected_text=b"\x01\x00",
            expected_dimensions=b"\x00\x02",
            replacement_text=_encoded_text(value),
            replacement_dimensions=bytes((len(value) * 2, 1)),
        )
    entries[descriptions_index] = rico_balance.compress_lzss_exact_complete_groups(
        descriptions
    )

    result = rico_balance._rebuild_archive(entries, header_size=len(header))
    _, final_entries, final_offsets = _archive_entries(
        result,
        expected_count=rico_balance.SYSTEM_DATA_ARCHIVE_COUNT,
    )
    video_descriptions, _ = rico_balance.decode_lzss_complete_groups(
        result[
            final_offsets[mass_driver.FACILITY_VIDEO_ITEM_DESCRIPTION_ARCHIVE_ENTRY] :
        ]
        + bytes(16)
    )
    video_text, _ = _indexed_string(
        video_descriptions,
        mass_driver.FACILITY_VIDEO_ITEM_ID,
    )
    if video_text != _encoded_text(mass_driver.FACILITY_VIDEO_ITEM_DESCRIPTION):
        raise UnifiedResourceError("Video Disk description was lost during Rico merge")
    final_descriptions, _ = rico_balance.decode_lzss_complete_groups(
        result[final_offsets[descriptions_index] :] + bytes(16)
    )
    expected = {
        rico_balance.MEMENTO_ITEM_ID: rico_balance.MEMENTO_DESCRIPTION,
        **rico_balance.YOUNG_RICO_EQUIPMENT_DESCRIPTIONS,
    }
    for item_id, value in expected.items():
        actual, _ = _indexed_string(final_descriptions, item_id)
        if actual != _encoded_text(value):
            raise UnifiedResourceError(f"Unified item {item_id:#x} description was lost")
    # Keep the local variable referenced: it documents that all entries, not
    # only the modified ones, survived the rebuild and makes static linters
    # catch a future accidental unpacking change.
    if len(final_entries) != len(entries):  # pragma: no cover - guarded above
        raise UnifiedResourceError("System-data entry count changed")
    return result


def merge_menu_archive_with_young_rico(
    retail_menu: bytes,
    mass_menu: bytes,
    young_rico_portrait: bytes,
) -> bytes:
    """Compose native title labels, Mass shops, and young Rico's portrait."""

    header, retail_entries, _retail_offsets = _archive_entries(
        retail_menu,
        expected_count=rico_title.ARCHIVE_ENTRY_COUNT,
    )
    _mass_header, mass_entries, _mass_offsets = _archive_entries(
        mass_menu,
        expected_count=rico_title.ARCHIVE_ENTRY_COUNT,
    )
    entries = list(retail_entries)
    # Mass Driver's Repair Bots own only these two catalog streams.  In
    # particular, do not carry its former three-row title glyphs in entry 2:
    # the unified title must retain native New Game / Continue / Sound.
    for index in (
        mass_driver.ITEM_SHOP_ARCHIVE_ENTRY,
        mass_driver.GEAR_SHOP_ARCHIVE_ENTRY,
    ):
        entries[index] = mass_entries[index]

    # Recompress the byte-identical native font.  This is a storage-only
    # transform and frees room in the single-sector archive for the portrait
    # and expanded shop tables without changing one title glyph record.
    font_index = mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY
    retail_font, font_consumed = rico_title._decode_complete_groups(
        entries[font_index] + bytes(16)
    )
    if font_consumed > len(entries[font_index]) + 16:
        raise UnifiedResourceError("Retail title-font stream exceeds allocation")
    entries[font_index] = rico_title._compress_exact_complete_groups(retail_font)

    portrait_index = rico_title.MENU_PORTRAIT_ENTRY
    portrait_entry = entries[portrait_index]
    rico_title._validate_young_rico_portrait_tim(young_rico_portrait)
    decoded, consumed = rico_title._decode_complete_groups(
        portrait_entry + bytes(16)
    )
    if consumed > len(portrait_entry) + 16:
        raise UnifiedResourceError("Mass menu portrait stream exceeds allocation")
    start = rico_title.YOUNG_RICO_PORTRAIT_OFFSET
    end = start + rico_title.MENU_PORTRAIT_TIM_SIZE
    if end > len(decoded) or rico_title._sha256(decoded[start:end]) != (
        rico_title.YOUNG_RICO_PORTRAIT_SOURCE_SHA256
    ):
        raise UnifiedResourceError("Mass menu portrait slot 10 changed")
    patched_decoded = bytearray(decoded)
    patched_decoded[start:end] = young_rico_portrait
    packed_portraits = rico_title._compress_exact_complete_groups(
        bytes(patched_decoded)
    )
    entries[portrait_index] = packed_portraits
    round_trip, round_trip_consumed = rico_title._decode_complete_groups(
        entries[portrait_index]
    )
    if (
        round_trip != bytes(patched_decoded)
        or round_trip_consumed > len(packed_portraits)
    ):
        raise UnifiedResourceError("Young-Rico portrait failed menu round-trip")
    result, _ = rico_title._rebuild_archive(header, tuple(entries))
    if len(result) > rico_title.TITLE_MENU_SECTOR_BUDGET:
        raise UnifiedResourceError(
            f"Unified menu archive is {len(result)} bytes, beyond one sector window"
        )
    _, after, _ = _archive_entries(
        result,
        expected_count=rico_title.ARCHIVE_ENTRY_COUNT,
    )
    decoded_final_font, _ = rico_title._decode_complete_groups(
        after[font_index] + bytes(16)
    )
    if decoded_final_font != retail_font:
        raise UnifiedResourceError("Unified title font differs from retail")
    for index in (
        mass_driver.ITEM_SHOP_ARCHIVE_ENTRY,
        mass_driver.GEAR_SHOP_ARCHIVE_ENTRY,
    ):
        if after[index] != mass_entries[index]:
            raise UnifiedResourceError(f"Mass shop archive entry {index} was lost")
    mutable = {
        font_index,
        portrait_index,
        mass_driver.ITEM_SHOP_ARCHIVE_ENTRY,
        mass_driver.GEAR_SHOP_ARCHIVE_ENTRY,
    }
    for index, (old, new) in enumerate(zip(retail_entries, after, strict=True)):
        if index not in mutable and old != new:
            raise UnifiedResourceError(f"Unified menu changed unrelated entry {index}")
    return result


def merge_initial_gamestate(mass_state: bytes) -> bytes:
    """Retain module starts while adding abilities and both Rico profiles."""

    if len(mass_state) != rico_balance.GAMESTATE_SIZE:
        raise UnifiedResourceError(
            f"Initial GameState is {len(mass_state)} bytes, expected "
            f"{rico_balance.GAMESTATE_SIZE}"
        )
    original_elly_gear = mass_state[mass_driver.INITIAL_GAMESTATE_ELLY_GEAR_OFFSET]
    live_start, live_end = _LIVE_PARTY_STATE_RANGE
    original_live_party = mass_state[live_start:live_end]
    result = grant_all_on_foot_deathblows(mass_state)
    result = rico_balance.apply_initial_character_balance(result)
    result = rico_balance.apply_young_rico_anthology_profile(result)
    result = apply_rico_recruitment_profile(result)

    # The selector routes own the current party and battle-frame mask, so keep
    # Mass Driver's neutral title state there.  Persistent roster membership is
    # different: Chapter 1 must be able to install young Rico's carrier and
    # Chapter 3 must be able to install Citan.  OR the anthology's required
    # members instead of replacing the source roster used by the other modules.
    mutable = bytearray(result)
    membership = struct.unpack_from("<H", mutable, _PARTY_MEMBERSHIP_OFFSET)[0]
    struct.pack_into(
        "<H",
        mutable,
        _PARTY_MEMBERSHIP_OFFSET,
        membership | _RICO_REQUIRED_MEMBERSHIP_MASK,
    )
    result = bytes(mutable)

    if (
        original_elly_gear != mass_driver.VIERGE_GEAR_ID
        or result[mass_driver.INITIAL_GAMESTATE_ELLY_GEAR_OFFSET]
        != mass_driver.VIERGE_GEAR_ID
    ):
        raise UnifiedResourceError("Unified GameState did not preserve Elly's Vierge")
    if result[live_start:live_end] != original_live_party:
        raise UnifiedResourceError("Unified GameState changed the module-neutral party")
    final_membership = struct.unpack_from(
        "<H", result, _PARTY_MEMBERSHIP_OFFSET
    )[0]
    if final_membership & _RICO_REQUIRED_MEMBERSHIP_MASK != (
        _RICO_REQUIRED_MEMBERSHIP_MASK
    ):
        raise UnifiedResourceError("Unified GameState omitted a Rico party member")
    for character_id in range(rico_balance.YOUNG_RICO_ID):
        record = (
            rico_balance.PARTY_RECORD_BASE
            + character_id * rico_balance.PARTY_RECORD_SIZE
        )
        levels = slice(record + 0x62, record + 0x64)
        expected_levels = (bytes((RICO_RECRUITMENT_LEVEL,) * 2)
                           if character_id == rico_balance.RICO_ID else mass_state[levels])
        if result[levels] != expected_levels:
            raise UnifiedResourceError(
                f"Unified GameState changed character {character_id}'s source level"
            )
    return result


__all__ = [
    "UnifiedResourceError",
    "merge_initial_gamestate",
    "merge_menu_archive_with_young_rico",
    "merge_system_data",
    "merge_system_names",
]
