#!/usr/bin/env python3
"""Build the in-field four-card selector for the combined Disc 2 package.

The native title overlay is deliberately left as ``New Game / Continue /
Sound``.  New Game enters field 63, where an ordinary field script renders a
modern full-screen selector through the retail field-617 video plane already
installed in the finished Mass Driver field 376.

This module is a pure transformer.  It does not allocate CD files or write an
image: callers provide the *finished* field-376 bundle and graphics and receive
a sanitized field-63 bundle/graphics pair.  The small TIM is also returned as
a reproducibility artifact, but its pixels are embedded in graphics 733 as a
normal ``0x1200`` upload.  It must not replace global canonical file 2477,
which retail field 655 still uses.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Final, Mapping, Sequence

import modules.mass_driver.build as mass_driver
import modules.soylent_system.base as surface
import modules.soylent_system.tools.surface_soylent_campaign_title as surface_title
import shared.tools.xgcontent_menu as xgcontent_menu
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript, SCRIPTS_PER_ENTITY


class ContentMenuFieldError(RuntimeError):
    """A donor, layout, or generated field-menu contract changed."""


@dataclass(frozen=True)
class ContentCard:
    selection: int
    label: str
    rect: tuple[int, int, int, int]
    enabled: bool = True


CONTENT_MENU_FIELD: Final = 63
CONTENT_MENU_BUNDLE_CANONICAL_ID: Final = 732
CONTENT_MENU_GRAPHICS_CANONICAL_ID: Final = 733

MASS_DRIVER_SELECTION: Final = 0
SURFACE_SOYLENT_SELECTION: Final = 1
MAHANON_SELECTION: Final = 2
RICO_ARC_SELECTION: Final = 3
CONTENT_MENU_SELECTION_RING: Final = (
    MASS_DRIVER_SELECTION,
    SURFACE_SOYLENT_SELECTION,
    RICO_ARC_SELECTION,
)
CONTENT_MENU_SELECTION_VARIABLE: Final = 0x0014

MASS_DRIVER_PARTY: Final = (1, 6)  # Elly, Emeralda
SURFACE_SOYLENT_PARTY: Final = (0, 1, 2)  # Fei, Elly, Citan
RICO_ARC_PARTY: Final = (5,)
RICO_ARC_HUB_FIELD: Final = 229
RICO_PLAYABLE_STATE_VARIABLE: Final = 0x07D0

CONTENT_MENU_MUSIC_ID: Final = 0x41
CONTENT_MENU_SCREEN_ENTITY: Final = mass_driver.FACILITY_VIDEO_SCREEN_ENTITY
CONTENT_MENU_SCREEN_MODEL: Final = mass_driver.FACILITY_VIDEO_SCREEN_MODEL_INDEX
CONTENT_MENU_SCREEN_HEADER_RECORD: Final = bytes.fromhex(
    "B0 02 00 00 00 00 00 00 40 1F 50 00 40 1F 14 00"
)

CONTENT_MENU_LIVE_VRAM_ORIGIN: Final = mass_driver.NUKE_LIVE_VRAM_ORIGIN
CONTENT_MENU_LIVE_VRAM_RECT: Final = (
    *CONTENT_MENU_LIVE_VRAM_ORIGIN,
    320,
    224,
)
CONTENT_MENU_ATLAS_VRAM_RECT: Final = (
    xgcontent_menu.MENU_ATLAS_VRAM_X,
    xgcontent_menu.MENU_ATLAS_VRAM_Y,
    xgcontent_menu.MENU_ATLAS_WIDTH,
    xgcontent_menu.MENU_ATLAS_HEIGHT,
)

CONTENT_MENU_INPUT_MASK: Final = (
    mass_driver.PAD_MASK_UP
    | mass_driver.PAD_MASK_DOWN
    | mass_driver.PAD_MASK_CROSS
)
CONTENT_MENU_MOVE_MASK: Final = (
    mass_driver.PAD_MASK_UP | mass_driver.PAD_MASK_DOWN
)

CONTENT_MENU_TITLE: Final = "XENOGEARS REIMAGINED"
CONTENT_MENU_SUBTITLE: Final = "SELECT CONTENT"
CONTENT_MENU_FOOTER: Final = "D-PAD MOVE - CROSS SELECT"
CONTENT_MENU_CARDS: Final = (
    ContentCard(MASS_DRIVER_SELECTION, "MASS DRIVER", (24, 47, 272, 30)),
    ContentCard(SURFACE_SOYLENT_SELECTION, "SURFACE SOYLENT", (24, 84, 272, 30)),
    ContentCard(
        MAHANON_SELECTION,
        "MAHANON - COMING SOON",
        (24, 121, 272, 30),
        enabled=False,
    ),
    ContentCard(RICO_ARC_SELECTION, "RICO'S ARC", (24, 158, 272, 30)),
)
CONTENT_MENU_CARD_BY_SELECTION: Mapping[int, ContentCard] = {
    card.selection: card for card in CONTENT_MENU_CARDS
}

_STATIC_TITLE_Y: Final = 11
_STATIC_SUBTITLE_Y: Final = 26
_STATIC_FOOTER_Y: Final = 205
_ACTIVE_BORDER: Final = 2
_FIELD_BUNDLE_LIMIT: Final = 0x40000
_EXPECTED_SOURCE_ENTITY_COUNT: Final = 28
_EXPECTED_SOURCE_HEADER_RECORD_COUNT: Final = 44
_EXPECTED_SCREEN_MODEL_COUNT: Final = CONTENT_MENU_SCREEN_MODEL + 1


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def _rectangles_overlap(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> bool:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def _validate_screen_donor(bundle: bytes, graphics: bytes) -> tuple[object, list[bytes]]:
    """Validate only the stable post-transform field-376 screen contracts."""

    if not isinstance(bundle, bytes) or not isinstance(graphics, bytes):
        raise ContentMenuFieldError("Field-376 donor inputs must be immutable bytes")
    parsed = parse_field(bundle)
    components = [part.data for part in parsed.parts]
    if len(components) <= mass_driver.DIALOGUE_INDEX:
        raise ContentMenuFieldError("Field-376 donor lost required field components")
    if (
        len(parsed.header) < 0x190 + (CONTENT_MENU_SCREEN_ENTITY + 1) * 16
        or struct.unpack_from("<H", parsed.header, 0x18C)[0]
        != _EXPECTED_SOURCE_HEADER_RECORD_COUNT
    ):
        raise ContentMenuFieldError("Field-376 actor header changed")
    record_at = 0x190 + CONTENT_MENU_SCREEN_ENTITY * 16
    if parsed.header[record_at : record_at + 16] != CONTENT_MENU_SCREEN_HEADER_RECORD:
        raise ContentMenuFieldError("Field-376 full-screen plane record changed")

    models = mass_driver._indexed_bundle_entries(
        components[mass_driver.MODEL_INDEX]
    )
    if (
        len(models) != _EXPECTED_SCREEN_MODEL_COUNT
        or len(models[CONTENT_MENU_SCREEN_MODEL])
        != mass_driver.FACILITY_VIDEO_SCREEN_MODEL_SIZE
        or _sha256(models[CONTENT_MENU_SCREEN_MODEL])
        != mass_driver.FACILITY_VIDEO_SCREEN_MODEL_SHA256
    ):
        raise ContentMenuFieldError("Field-376 full-screen plane model changed")

    editor = AtelScript(components[mass_driver.SCRIPT_INDEX])
    if editor.entity_count != _EXPECTED_SOURCE_ENTITY_COUNT:
        raise ContentMenuFieldError("Field-376 ATEL entity layout changed")
    screen_init_pc = editor.get_script_pointer(CONTENT_MENU_SCREEN_ENTITY, 0)
    screen_init = mass_driver._facility_video_screen_init_body()
    if editor.bytecode[screen_init_pc : screen_init_pc + len(screen_init)] != screen_init:
        raise ContentMenuFieldError("Field-376 screen-plane initializer changed")

    try:
        _vram, rectangles = mass_driver._reconstruct_field_graphics_vram(
            graphics,
            label="finished Mass Driver field 376",
        )
    except mass_driver.DungeonBuildError as exc:
        raise ContentMenuFieldError(str(exc)) from exc
    for reserved_name, reserved in (
        ("live screen", CONTENT_MENU_LIVE_VRAM_RECT),
        ("menu atlas", CONTENT_MENU_ATLAS_VRAM_RECT),
    ):
        conflict = next(
            (rect for rect in rectangles if _rectangles_overlap(rect, reserved)),
            None,
        )
        if conflict is not None:
            raise ContentMenuFieldError(
                f"Field-376 graphics overlap the {reserved_name} VRAM: {conflict}"
            )
    return parsed, components


def _atlas_vram_rect(rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, width, height = rect
    return (
        xgcontent_menu.MENU_ATLAS_VRAM_X + x,
        xgcontent_menu.MENU_ATLAS_VRAM_Y + y,
        width,
        height,
    )


def _embed_menu_atlas(graphics: bytes, atlas: bytes) -> bytes:
    """Append the atlas pixels as one ordinary sector-aligned field upload."""

    if (
        len(atlas) != xgcontent_menu.MENU_ATLAS_TOTAL_SIZE
        or atlas[: len(xgcontent_menu.MENU_ATLAS_TIM_HEADER)]
        != xgcontent_menu.MENU_ATLAS_TIM_HEADER
    ):
        raise ContentMenuFieldError("Content-menu atlas TIM changed")
    rows = atlas[len(xgcontent_menu.MENU_ATLAS_TIM_HEADER) :]
    if len(rows) != xgcontent_menu.MENU_ATLAS_PIXEL_BYTES:
        raise ContentMenuFieldError("Content-menu atlas pixel extent changed")

    chunk_height = 16
    chunk_heights = (chunk_height,) * (
        xgcontent_menu.MENU_ATLAS_HEIGHT // chunk_height
    )
    if sum(chunk_heights) != xgcontent_menu.MENU_ATLAS_HEIGHT:
        raise ContentMenuFieldError("Content-menu atlas is not 16-row aligned")
    header = bytearray(0x800)
    struct.pack_into("<H", header, 0, 0x1200)
    struct.pack_into(
        "<8H",
        header,
        4,
        xgcontent_menu.MENU_ATLAS_VRAM_X,
        0,
        0,
        xgcontent_menu.MENU_ATLAS_VRAM_Y,
        xgcontent_menu.MENU_ATLAS_WIDTH,
        chunk_height,
        1,
        len(chunk_heights),
    )
    struct.pack_into(
        f"<{len(chunk_heights)}H",
        header,
        0x1C,
        *chunk_heights,
    )
    upload = bytearray(header)
    cursor = 0
    for height in chunk_heights:
        size = xgcontent_menu.MENU_ATLAS_WIDTH * height * 2
        chunk = rows[cursor : cursor + size]
        upload.extend(chunk)
        upload.extend(bytes((-len(chunk)) % 0x800))
        cursor += size
    if cursor != len(rows):
        raise ContentMenuFieldError("Embedded atlas upload lost pixel rows")

    result = graphics + bytes(upload)
    try:
        _vram, rectangles = mass_driver._reconstruct_field_graphics_vram(
            result,
            label="field 63 with embedded content-menu atlas",
        )
    except mass_driver.DungeonBuildError as exc:
        raise ContentMenuFieldError(str(exc)) from exc
    if rectangles[-1] != CONTENT_MENU_ATLAS_VRAM_RECT:
        raise ContentMenuFieldError(
            f"Embedded atlas upload has wrong VRAM extent: {rectangles[-1]}"
        )
    return result


def _menu_fill_screen_rect_body(
    rect: tuple[int, int, int, int],
    tile_name: str,
) -> bytes:
    """Fill a screen rectangle by geometrically growing one atlas pixel."""

    x, y, width, height = rect
    if (
        x < 0
        or y < 0
        or width <= 0
        or height <= 0
        or x + width > 320
        or y + height > 224
    ):
        raise ContentMenuFieldError(f"Menu fill rectangle is invalid: {rect}")
    if tile_name not in xgcontent_menu.MENU_TILE_RECTS:
        raise ContentMenuFieldError(f"Unknown menu fill tile: {tile_name!r}")
    tile_x, tile_y, tile_width, tile_height = _atlas_vram_rect(
        xgcontent_menu.MENU_TILE_RECTS[tile_name]
    )
    destination_x = CONTENT_MENU_LIVE_VRAM_ORIGIN[0] + x
    destination_y = CONTENT_MENU_LIVE_VRAM_ORIGIN[1] + y
    seeded_width = min(width, tile_width)
    seeded_height = min(height, tile_height)
    output = bytearray(
        mass_driver._vram_move(
            tile_x,
            tile_y,
            seeded_width,
            seeded_height,
            destination_x,
            destination_y,
        )
    )
    filled_width = seeded_width
    while filled_width < width:
        copy_width = min(filled_width, width - filled_width)
        output.extend(
            mass_driver._vram_move(
                destination_x,
                destination_y,
                copy_width,
                seeded_height,
                destination_x + filled_width,
                destination_y,
            )
        )
        filled_width += copy_width
    filled_height = seeded_height
    while filled_height < height:
        copy_height = min(filled_height, height - filled_height)
        output.extend(
            mass_driver._vram_move(
                destination_x,
                destination_y,
                width,
                copy_height,
                destination_x,
                destination_y + filled_height,
            )
        )
        filled_height += copy_height
    return bytes(output)


def _menu_text_body(text: str, x: int, y: int, style: str) -> bytes:
    """Draw one background-aware atlas string into the live screen page."""

    if not isinstance(text, str) or not text or "\n" in text:
        raise ContentMenuFieldError("Menu text must be one nonempty line")
    if style not in xgcontent_menu.MENU_STYLES:
        raise ContentMenuFieldError(f"Unknown menu text style: {style!r}")
    cursor_x = x
    output = bytearray()
    for character in text.upper():
        if character == " ":
            cursor_x += xgcontent_menu.MENU_FONT_CELL_WIDTH
            continue
        key = (style, character)
        if key not in xgcontent_menu.MENU_GLYPH_RECTS:
            raise ContentMenuFieldError(
                f"Content-menu atlas has no {style} glyph for {character!r}"
            )
        source_x, source_y, width, height = _atlas_vram_rect(
            xgcontent_menu.MENU_GLYPH_RECTS[key]
        )
        if (
            cursor_x < 0
            or y < 0
            or cursor_x + width > 320
            or y + height > 224
        ):
            raise ContentMenuFieldError(f"Menu text leaves the display: {text!r}")
        output.extend(
            mass_driver._vram_move(
                source_x,
                source_y,
                width,
                height,
                CONTENT_MENU_LIVE_VRAM_ORIGIN[0] + cursor_x,
                CONTENT_MENU_LIVE_VRAM_ORIGIN[1] + y,
            )
        )
        cursor_x += xgcontent_menu.MENU_FONT_CELL_WIDTH
    return bytes(output)


def _centered_text_body(text: str, y: int, style: str) -> bytes:
    width = len(text) * xgcontent_menu.MENU_FONT_CELL_WIDTH - 1
    if width > 320:
        raise ContentMenuFieldError(f"Centered menu text is too wide: {text!r}")
    return _menu_text_body(text, (320 - width) // 2, y, style)


def _card_body(card: ContentCard, selected: int) -> bytes:
    x, y, width, height = card.rect
    if card.enabled and card.selection == selected:
        interior = (
            x + _ACTIVE_BORDER,
            y + _ACTIVE_BORDER,
            width - _ACTIVE_BORDER * 2,
            height - _ACTIVE_BORDER * 2,
        )
        fill = _menu_fill_screen_rect_body(card.rect, "accent")
        fill += _menu_fill_screen_rect_body(interior, "highlight")
        style = xgcontent_menu.MENU_STYLE_ACTIVE
    elif card.enabled:
        fill = _menu_fill_screen_rect_body(card.rect, "panel")
        style = xgcontent_menu.MENU_STYLE_INACTIVE
    else:
        fill = _menu_fill_screen_rect_body(card.rect, "disabled")
        style = xgcontent_menu.MENU_STYLE_DISABLED
    text_width = len(card.label) * xgcontent_menu.MENU_FONT_CELL_WIDTH - 1
    text_x = x + (width - text_width) // 2
    text_y = y + (height - xgcontent_menu.MENU_FONT_GLYPH_HEIGHT) // 2
    return fill + _menu_text_body(card.label, text_x, text_y, style)


def _cards_body(selected: int) -> bytes:
    if selected not in CONTENT_MENU_SELECTION_RING:
        raise ContentMenuFieldError(f"Menu selection {selected} is not reachable")
    return b"".join(_card_body(card, selected) for card in CONTENT_MENU_CARDS) + b"\x0D"


def _static_menu_body() -> bytes:
    return (
        _menu_fill_screen_rect_body((0, 0, 320, 224), "background")
        + _centered_text_body(
            CONTENT_MENU_TITLE,
            _STATIC_TITLE_Y,
            xgcontent_menu.MENU_STYLE_BASE,
        )
        + _centered_text_body(
            CONTENT_MENU_SUBTITLE,
            _STATIC_SUBTITLE_Y,
            xgcontent_menu.MENU_STYLE_BASE,
        )
        + _centered_text_body(
            CONTENT_MENU_FOOTER,
            _STATIC_FOOTER_Y,
            xgcontent_menu.MENU_STYLE_BASE,
        )
        + b"\x0D"
    )


def _party_setup(party: Sequence[int]) -> bytes:
    """Install one exact party and battle frame from any live module state."""

    members = tuple(party)
    if (
        not members
        or len(members) != len(set(members))
        or any(not isinstance(member, int) or not 0 <= member <= 10 for member in members)
    ):
        raise ContentMenuFieldError(f"Invalid content-route party: {members}")
    result = bytearray()
    for character in range(11):
        result.extend(b"\xFE\x19" + bytes((character,)))
    for character in members:
        result.extend(b"\xFE\x18" + bytes((character,)) + b"\xFE\x1A")
    for character in range(11):
        result.extend(b"\xFE\x3B" + mass_driver._immediate(character))
    for character in members:
        result.extend(b"\xFE\x3A" + mass_driver._immediate(character))
    return bytes(result)


def _mass_driver_route_body() -> bytes:
    return (
        mass_driver._set_variable_s16(mass_driver.ANNEX_TREASURE_VARIABLE, 0)
        + mass_driver._set_variable_s16(mass_driver.LIFT_STATE_VARIABLE, 0)
        + mass_driver._set_variable_s16(mass_driver.INTERLOCK_VARIABLE, 0)
        + mass_driver._set_variable_s16(RICO_PLAYABLE_STATE_VARIABLE, 0)
        + _party_setup(MASS_DRIVER_PARTY)
        + b"\xFE\x42"
        + mass_driver._immediate(0)
        + b"\xFE\x42"
        + mass_driver._immediate(1)
        + b"\xFE\xA1"
        + mass_driver._immediate(1)
        + mass_driver._immediate(mass_driver.VIERGE_GEAR_ID)
        + b"\xFE\xA1"
        + mass_driver._immediate(6)
        + mass_driver._immediate(mass_driver.CRESCENS_GEAR_ID)
        + mass_driver._change_field(mass_driver.BOOTSTRAP_FIELD, 0)
        + b"\x5B"
    )


def _surface_soylent_route_body() -> bytes:
    direct_handoff = mass_driver._change_field(
        surface.SURFACE_ENTRY_FIELD,
        surface.SURFACE_ENTRY_PARAMETER,
    )
    if not surface.SURFACE_STATE_RESET_ROUTINE.endswith(direct_handoff):
        raise ContentMenuFieldError("Surface reset no longer ends at its entry field")
    state_reset = surface.SURFACE_STATE_RESET_ROUTINE[: -len(direct_handoff)]
    campaign_reset = surface_title.APPOINTMENT_STATE_CLEAR + b"".join(
        mass_driver._clear_var_bit(
            surface_title.CAMPAIGN_STATE_OPERAND,
            bit_index,
        )
        for bit_index in surface_title.CAMPAIGN_STATE_BIT_INDICES
    )
    return (
        state_reset
        + campaign_reset
        + mass_driver._set_variable_s16(RICO_PLAYABLE_STATE_VARIABLE, 0)
        + _party_setup(SURFACE_SOYLENT_PARTY)
        + direct_handoff
        + b"\x5B"
    )


def _rico_arc_route_body() -> bytes:
    return (
        _party_setup(RICO_ARC_PARTY)
        + mass_driver._set_variable_s16(RICO_PLAYABLE_STATE_VARIABLE, 0)
        + mass_driver._change_field(RICO_ARC_HUB_FIELD, 0)
        + b"\x5B"
    )


def _play_sound(sound_id: int) -> bytes:
    return b"\x74" + mass_driver._immediate(sound_id)


def _launch_prefix() -> bytes:
    """Fade out and restore global field controls before changing module."""

    frames = 15
    return (
        _play_sound(mass_driver.TITLE_MENU_CONFIRM_SOUND_ID)
        + b"\xB4"
        + mass_driver._immediate(frames)
        + mass_driver._wait(frames)
        + b"\x25"
        + bytes((CONTENT_MENU_SCREEN_ENTITY,))
        + b"\xFE\xE0\x00"
        # FE53 has no operand. A following 00 is STOP, which would end the
        # menu update before the appended party setup and field transition.
        + b"\xFE\x53"
    )


def _main_menu_body(
    base_pc: int,
    *,
    static_pc: int,
    render_pcs: Mapping[int, int],
) -> bytes:
    if tuple(render_pcs) != CONTENT_MENU_SELECTION_RING:
        raise ContentMenuFieldError("Menu render routines do not match selection ring")
    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(
        b"\xFE\xE0\x01"
        + b"\xFE\x54"
        + mass_driver._set_variable_s16(
            CONTENT_MENU_SELECTION_VARIABLE,
            MASS_DRIVER_SELECTION,
        )
        + b"\xB4"
        + mass_driver._immediate(1)
        + mass_driver._wait(1)
        + mass_driver._facility_video_screen_fade_body(0xFF, 1)
        + mass_driver._facility_video_screen_camera_body()
        + b"\x25"
        + bytes((CONTENT_MENU_SCREEN_ENTITY,))
        + mass_driver._call(static_pc)
        + mass_driver._call(render_pcs[MASS_DRIVER_SELECTION])
        + b"\x24"
        + bytes((CONTENT_MENU_SCREEN_ENTITY,))
        + mass_driver._facility_video_screen_fade_body(0, 1)
        + b"\xB3"
        + mass_driver._immediate(20)
        + mass_driver._wait(20)
    )
    release_pc = routine.pc
    routine.emit(mass_driver._wait_for_pad_release(CONTENT_MENU_INPUT_MASK, release_pc))

    routine.label("input_loop")
    routine.emit(mass_driver._yield_tick())
    routine.jump_if_pad_not_pressed(mass_driver.PAD_MASK_UP, "check_down")
    routine.jump_if_equal(
        CONTENT_MENU_SELECTION_VARIABLE,
        MASS_DRIVER_SELECTION,
        "select_rico",
    )
    routine.jump_if_equal(
        CONTENT_MENU_SELECTION_VARIABLE,
        SURFACE_SOYLENT_SELECTION,
        "select_mass",
    )
    routine.jump("select_surface")

    routine.label("check_down")
    routine.jump_if_pad_not_pressed(mass_driver.PAD_MASK_DOWN, "check_confirm")
    routine.jump_if_equal(
        CONTENT_MENU_SELECTION_VARIABLE,
        MASS_DRIVER_SELECTION,
        "select_surface",
    )
    routine.jump_if_equal(
        CONTENT_MENU_SELECTION_VARIABLE,
        SURFACE_SOYLENT_SELECTION,
        "select_rico",
    )
    routine.jump("select_mass")

    for selection, label in (
        (MASS_DRIVER_SELECTION, "select_mass"),
        (SURFACE_SOYLENT_SELECTION, "select_surface"),
        (RICO_ARC_SELECTION, "select_rico"),
    ):
        routine.label(label)
        routine.emit(
            mass_driver._set_variable_s16(
                CONTENT_MENU_SELECTION_VARIABLE,
                selection,
            )
            + _play_sound(mass_driver.TITLE_MENU_MOVE_SOUND_ID)
            + mass_driver._call(render_pcs[selection])
        )
        move_release_pc = routine.pc
        routine.emit(
            mass_driver._wait_for_pad_release(
                CONTENT_MENU_INPUT_MASK,
                move_release_pc,
            )
        )
        routine.jump("input_loop")

    routine.label("check_confirm")
    routine.jump_if_pad_not_pressed(mass_driver.PAD_MASK_CROSS, "input_loop")
    routine.jump_if_equal(
        CONTENT_MENU_SELECTION_VARIABLE,
        MASS_DRIVER_SELECTION,
        "launch_mass",
    )
    routine.jump_if_equal(
        CONTENT_MENU_SELECTION_VARIABLE,
        SURFACE_SOYLENT_SELECTION,
        "launch_surface",
    )
    routine.jump_if_equal(
        CONTENT_MENU_SELECTION_VARIABLE,
        RICO_ARC_SELECTION,
        "launch_rico",
    )
    # Value 2 is impossible through navigation.  Treat a corrupted or manually
    # injected value as the disabled Mahanon card, provide the native disabled
    # cue, and return to the first valid selection without changing field.
    routine.emit(
        _play_sound(mass_driver.TITLE_MENU_DISABLED_SOUND_ID)
        + mass_driver._set_variable_s16(
            CONTENT_MENU_SELECTION_VARIABLE,
            MASS_DRIVER_SELECTION,
        )
        + mass_driver._call(render_pcs[MASS_DRIVER_SELECTION])
    )
    disabled_release_pc = routine.pc
    routine.emit(
        mass_driver._wait_for_pad_release(
            CONTENT_MENU_INPUT_MASK,
            disabled_release_pc,
        )
    )
    routine.jump("input_loop")

    routine.label("launch_mass")
    routine.emit(_launch_prefix() + _mass_driver_route_body())
    routine.label("launch_surface")
    routine.emit(_launch_prefix() + _surface_soylent_route_body())
    routine.label("launch_rico")
    routine.emit(_launch_prefix() + _rico_arc_route_body())
    return routine.finish()


def _director_body() -> bytes:
    # BC/23 is the proven inert hidden field-director setup used by the Rico
    # hub sanitizer.  Lock control immediately; the resumable update owns the
    # bounded fades, rendering, and input loop.
    return (
        b"\xBC\x23\x2A"
        + mass_driver._play_music(CONTENT_MENU_MUSIC_ID)
        + b"\xFE\x54\x00"
    )


def build_content_menu_field(
    mass_field376_bundle: bytes,
    mass_field376_graphics: bytes,
) -> tuple[bytes, bytes, bytes]:
    """Return ``(field63 bundle, field63 graphics, atlas artifact TIM)``."""

    parsed, components = _validate_screen_donor(
        mass_field376_bundle,
        mass_field376_graphics,
    )
    # No retail Defense Archive routine is needed by the selector.  Rebuild a
    # minimal ATEL body instead of merely pointing around 47 KiB of dormant
    # doors, encounters, video clips, and arcade logic.  The fixed ATEL header
    # remains byte-for-byte intact; the entity table is zeroed onto one STOP.
    source_editor = AtelScript(components[mass_driver.SCRIPT_INDEX])
    clean_script = bytearray(
        components[mass_driver.SCRIPT_INDEX][: source_editor.bytecode_offset]
    )
    for entity in range(source_editor.entity_count):
        for script_index in range(SCRIPTS_PER_ENTITY):
            struct.pack_into(
                "<H",
                clean_script,
                0x84 + entity * SCRIPTS_PER_ENTITY * 2 + script_index * 2,
                0,
            )
    clean_script.append(0x00)
    editor = AtelScript(bytes(clean_script))

    static_pc = editor.append_raw_routine(_static_menu_body())
    render_pcs = {
        selection: editor.append_raw_routine(_cards_body(selection))
        for selection in CONTENT_MENU_SELECTION_RING
    }
    main_pc = editor.bytecode_size
    editor.append_and_repoint(
        0,
        1,
        _main_menu_body(
            main_pc,
            static_pc=static_pc,
            render_pcs=render_pcs,
        ),
    )
    editor.append_and_repoint(0, 0, _director_body())
    editor.append_and_repoint(
        CONTENT_MENU_SCREEN_ENTITY,
        0,
        mass_driver._facility_video_screen_init_body(),
    )
    components[mass_driver.SCRIPT_INDEX] = editor.to_bytes()
    result_bundle = build_field_preserving(
        mass_field376_bundle,
        components,
        (mass_driver.SCRIPT_INDEX,),
        compact_changed=True,
    )
    if len(result_bundle) >= _FIELD_BUNDLE_LIMIT:
        raise ContentMenuFieldError(
            f"Content-menu field exceeds loader budget: {len(result_bundle)} bytes"
        )
    reparsed = parse_field(result_bundle)
    if (
        len(reparsed.header) != len(parsed.header)
        or reparsed.header[0x18C:] != parsed.header[0x18C:]
        or tuple(part.data for part in reparsed.parts) != tuple(components)
    ):
        raise ContentMenuFieldError("Content-menu field failed packed round-trip")

    atlas = xgcontent_menu.build_content_menu_atlas_tim()
    result_graphics = _embed_menu_atlas(mass_field376_graphics, atlas)
    return result_bundle, result_graphics, atlas


def patch_title_field_for_content_menu(
    source_bundle: bytes,
    *,
    menu_field: int = CONTENT_MENU_FIELD,
) -> bytes:
    """Patch only field 490's checked New Game fallthrough to the selector."""

    if (
        not isinstance(source_bundle, bytes)
        or len(source_bundle) != mass_driver.TITLE_MENU_FIELD_SOURCE_SIZE
        or _sha256(source_bundle) != mass_driver.TITLE_MENU_FIELD_SOURCE_SHA256
    ):
        raise ContentMenuFieldError("Title field is not checked clean USA field 490")
    if (
        isinstance(menu_field, bool)
        or not isinstance(menu_field, int)
        or not 0 <= menu_field <= 999
    ):
        raise ContentMenuFieldError(f"Content-menu field is invalid: {menu_field!r}")

    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    editor = AtelScript(components[mass_driver.SCRIPT_INDEX])
    if (
        editor.bytecode[
            mass_driver.TITLE_MENU_FIELD_RESULT_BRANCH_PC :
            mass_driver.TITLE_MENU_FIELD_RESULT_BRANCH_PC
            + len(mass_driver.TITLE_MENU_FIELD_RESULT_BRANCH)
        ]
        != mass_driver.TITLE_MENU_FIELD_RESULT_BRANCH
    ):
        raise ContentMenuFieldError("Title menu-result branch changed")
    fallthrough_pc = mass_driver.TITLE_MENU_FIELD_MASS_DRIVER_FALLTHROUGH_PC
    source_fallthrough = mass_driver.TITLE_MENU_FIELD_MASS_DRIVER_FALLTHROUGH_SOURCE
    if editor.bytecode[fallthrough_pc : fallthrough_pc + len(source_fallthrough)] != source_fallthrough:
        raise ContentMenuFieldError("Title New Game fallthrough changed")

    route = mass_driver._change_field(menu_field, 0) + b"\x5B"
    route_pc = editor.append_raw_routine(route)
    script = bytearray(editor.to_bytes())
    absolute = editor.bytecode_offset + fallthrough_pc
    script[absolute : absolute + len(source_fallthrough)] = (
        b"\x01" + mass_driver._u16(route_pc) + bytes(5)
    )
    components[mass_driver.SCRIPT_INDEX] = bytes(script)
    result = build_field_preserving(
        source_bundle,
        components,
        (mass_driver.SCRIPT_INDEX,),
        compact_changed=True,
    )
    reparsed = parse_field(result)
    if (
        len(reparsed.header) != len(parsed.header)
        or reparsed.header[0x18C:] != parsed.header[0x18C:]
        or tuple(part.data for part in reparsed.parts) != tuple(components)
    ):
        raise ContentMenuFieldError("Title field route failed packed round-trip")
    return result


__all__ = [
    "CONTENT_MENU_BUNDLE_CANONICAL_ID",
    "CONTENT_MENU_CARDS",
    "CONTENT_MENU_FIELD",
    "CONTENT_MENU_GRAPHICS_CANONICAL_ID",
    "CONTENT_MENU_SELECTION_RING",
    "CONTENT_MENU_SELECTION_VARIABLE",
    "ContentCard",
    "ContentMenuFieldError",
    "MAHANON_SELECTION",
    "MASS_DRIVER_SELECTION",
    "RICO_ARC_SELECTION",
    "SURFACE_SOYLENT_SELECTION",
    "build_content_menu_field",
    "patch_title_field_for_content_menu",
]
