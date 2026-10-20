"""Bounded visible choreography for The Champ.

The caller owns field assembly, actor initialization, story flags, and exits.
Install every returned ActorRoutine at its entity/script index, then append
SceneBuild.body at the exact base_pc supplied. Bodies retain the input lock;
commit progression before releasing it with FE53 or changing fields.

dialogue(scene_key, start, stop) must emit the requested authored block slice
(stop is exclusive, None means to the end). For example:
    lambda key, start, stop: core._dialogue_sequence(ids[key][start:stop])

Baptism uses field199 and the native Fei3/Rico33 special-animation pair.
Finals/crash use sanitized field225 with mounted *party sprites*, not mecha93
IDs. The world builder must load Rico's runtime Gear6 and Fei's Gear0 before
initializing those actors. Gear dialogue-name IDs17/11 are not those values.
The crash is a compressed visible charge, impact, and public aftermath; the
arena floor has no audited royal-box destruction model. No unrelated retail
Rankar/rescue scene is dispatched.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import struct
from typing import Callable

from modules.mass_driver import build as native


DialogueEmitter = Callable[[str, int, int | None], bytes]
CHOREOGRAPHY_SCENES = {
    "arrival_delivery": ("arrival_delivery",),
    "room_introduction": ("room_first", "hammer_report"),
    "baptism": ("baptism_before", "baptism_exchange", "baptism_after"),
    "bandage": ("bandage",),
    "finals": ("finals_exchange", "finals_after"),
    "crash": ("crash_before", "crash_public"),
    "flight": ("central_flight", "chapter_end"),
}

# Derived from directory4 local077A+n (special animation) and15+GearID
# (mounted party sprite). Every identity was compared on retail USA discs1/2.
CINEMATIC_RESOURCE_IDENTITIES = {
    443: (51732, "f3d792b9adeb63af0d72324da2bd496fe05e34ae58dd3c11fb9582b37de25241"),
    449: (67952, "2631f3fa52b3485492a8fd05f7925f9ee786173a744f90808c9f3a7d649345ef"),
    2339: (3112, "0bf4fa92a3ebda104fc327d548a2055f3613a5f879dfb5fe08af4f670f2bf5d8"),
    2369: (4752, "860df6544664be4adae6eba3c2c69ae0e2dac3546ed493edde32d2238f3031b4"),
    2455: (2500, "4fcba23f3ef636542a60e44c335c23ae59c8185e57c1f86446d160d977607f57"),
}
WALKMESH_IDENTITIES = {
    213: "8d46c1787156a7eb9745d60831c56cb74eb2c788c179d229e0dbe7bc5cf99d66",
    199: "0a848ad6775cecd4cfdd02958c55a0e5b9d2d14e8518632486b0f0e12ed2e7b3",
    218: "f8987e7178f18dfa4b6c2a1e361e8b8b542c319b6f2879862cc69d511ed4525b",
    231: "2e30d88b5789543c60cf073f95ca3db971b0350738895f259130cfbb3c0511fd",
    225: "deab0cf882fcfefe0f95b320949e4193a5f80c4344199263758c17ddc1af4c56",
}
ARENA_ENTRY = (-500, 0, 379)
ARENA_ANCHORS = {
    "rico": (-500, 0), "fei": (500, 0), "rico_close": (-150, 0),
    "fei_close": (150, 0), "rico_recoil": (-650, 0),
    "fei_recoil": (650, 0), "charge_midpoint": (0, -500),
    "impact": (0, -1400), "witness": (250, -1350),
}


@dataclass(frozen=True)
class ActorRoutine:
    entity: int
    script_index: int
    body: bytes
    label: str


@dataclass(frozen=True)
class MotionPath:
    points: tuple[tuple[int, int], ...]
    layer: int = 0


@dataclass(frozen=True)
class SceneBuild:
    body: bytes
    actor_routines: tuple[ActorRoutine, ...]
    required_resource_ids: tuple[int, ...]
    donor_field: int
    motion_paths: tuple[MotionPath, ...] = ()


def prepare_resources(read_canonical: Callable[[int], bytes]) -> dict[int, bytes]:
    """Return pinned retail resources for registration in any output profile."""
    result = {}
    for resource, identity in CINEMATIC_RESOURCE_IDENTITIES.items():
        data = read_canonical(resource)
        if (len(data), hashlib.sha256(data).hexdigest()) != identity:
            raise ValueError(f"Chapter2 cinematic resource{resource} changed")
        result[resource] = data
    return result


def scene_resources(disc1) -> dict[int, bytes]:
    """DiscReader adapter used by the Chapter2 replacement assembler."""
    return prepare_resources(disc1.canonical)


def arena_director_prefix() -> bytes:
    """Run in director INIT before any actor INIT, with party ordered(5,0).

    FE1E00 is the exact Gear-only field-loading form pinned in native263
    (mass_driver._install_goliath_defense_bay). Mode3 instead expects separate
    parked Gear actors and field-local on-foot banks, which arena225 lacks.
    OP16 subsequently initializes each actor from its loaded Gear buffer.
    """
    return (bytes.fromhex("FE A1 05 80 06 80 FE A1 00 80 00 80")
            + bytes.fromhex("FE 41 00 80 FE 41 01 80 FE 1E 00"))


def arena_actor_init(character: int, position: tuple[int, int]) -> bytes:
    """Initialize Stier/Rico5 or Weltall/Fei0 after arena_director_prefix."""
    if character not in (5, 0):
        raise ValueError("Arena cinematic supports only Rico and Fei")
    return (b"\x16" + _word(character) + b"\xFE\x0D" + _word(character)
            + b"\x19" + _position(position) + b"\x1A\x00\x00")


def unmount_before_travel() -> bytes:
    """Clear mounted flags before a normal field transition reloads humans."""
    return b"".join(b"\xFE\x42" + _word(slot) for slot in range(3))


def _word(value: int) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0x7FFF:
        raise ValueError("Immediate is outside0..32767")
    return struct.pack("<H", value | 0x8000)


def _position(point: tuple[int, int]) -> bytes:
    if len(point) != 2 or any(not -32768 <= v <= 32767 for v in point):
        raise ValueError("Actor position is outside signed16-bit range")
    return struct.pack("<hh", *point) + b"\xC0"


def _wait(frames: int) -> bytes:
    if frames < 1:
        raise ValueError("WAIT must be positive")
    return b"\x26" + _word(frames)


def _stage(point: tuple[int, int], direction: int) -> bytes:
    if not 0 <= direction < 8:
        raise ValueError("Actor direction must be0..7")
    return (b"\x20\x01\x80\x19" + _position(point)
            + b"\x1A\x00\x5F" + bytes((direction,)) + b"\x00")


def _walk(*points: tuple[int, int], max_steps: int = 120) -> bytes:
    if not points or not 1 <= max_steps <= 32767:
        raise ValueError("A route requires points and a finite positive bound")
    return b"".join(b"\x4B" + _position(p) + _word(max_steps)
                    + b"\x19" + _position(p) for p in points) + b"\x00"


def _run(entity: int, script: int) -> bytes:
    if not 0 <= entity <= 0xFC or not 0 <= script < 32:
        raise ValueError("Concrete actor/script slot is outside range")
    return bytes((0x09, entity, script | 0x20))


def _look(source: int, target: int) -> bytes:
    return bytes((0xFE, 0x17, source, target)) + _wait(4)


def _camera(target, eye, *, first=False, frames=18) -> bytes:
    return native._historical_camera_shot_body(
        native.HistoricalCameraShot(target, eye, 0 if first else frames, ()),
        enter_camera_mode=first, allow_silent=True)


def _shake() -> bytes:
    # Native arena224 PC0277..028B, including its explicit reset.
    return (b"\xF2" + _word(90) * 3 + _word(15) + _wait(60)
            + b"\xF2" + _word(0) * 3 + _word(15))


class _Scene:
    def __init__(self, base_pc, donor, actors, first_script, dialogue):
        if not 0 <= base_pc <= 0xFFFF:
            raise ValueError("Scene base PC is outside ATEL address range")
        if len(set(actors)) != len(actors) or any(not 0 <= e <= 0xFC for e in actors):
            raise ValueError("Scene actors must be distinct concrete entity IDs")
        if not 0 <= first_script <= 27:
            raise ValueError("Reserve at least five actor script slots")
        self.base_pc, self.donor = base_pc, donor
        self.actors = tuple(actors)
        self.dialogue, self.first_script = dialogue, first_script
        self.routines: list[ActorRoutine] = []
        self.paths: list[MotionPath] = []
        self.body = bytearray(b"\xF4\x01\xFE\x0D\xFC\x80\x33\xFE\x54")
        # Native release loop: repeated Cross must not skip the first beat.
        pc = base_pc + len(self.body)
        self.body.extend(b"\x31" + struct.pack("<H", native.PAD_MASK_CROSS)
                         + struct.pack("<H", pc + 11)
                         + _wait(1) + b"\x01" + struct.pack("<H", pc) + _wait(1))

    def actor(self, entity, offset, label, body):
        slot = self.first_script + offset
        _run(entity, slot)
        if any(r.entity == entity and r.script_index == slot for r in self.routines):
            raise ValueError("Actor routine slots overlap")
        self.routines.append(ActorRoutine(entity, slot, body, label))
        return _run(entity, slot)

    def say(self, key, start=0, stop=None):
        data = self.dialogue(key, start, stop)
        if not isinstance(data, bytes) or not data:
            raise ValueError(f"Missing emitted dialogue for {key}[{start}:{stop}]")
        self.body.extend(data)

    def open(self, stage_calls, target, eye, visible):
        fade = native._facility_video_screen_fade_body
        self.body.extend(fade(255, 8) + stage_calls
                         + b"".join(bytes((0x24, e)) for e in visible)
                         + _camera(target, eye, first=True) + fade(0, 12) + _wait(20))

    def finish(self, resources=()):
        # Staging temporarily bypasses actor collision. Restore the normal
        # on-foot flag contract before the caller returns free movement.
        for entity in self.actors:
            self.body.extend(self.actor(entity, 4, "Restore actor collision",
                                        bytes.fromhex("20 00 80 00")))
        self.body.extend(b"\xF4\x01\xFE\x0D\xFC\x80"
                         + native._historical_camera_release_body())
        if self.base_pc + len(self.body) > 0x10000:
            raise ValueError("Scene bytecode exceeds the ATEL address space")
        return SceneBuild(bytes(self.body), tuple(self.routines), tuple(resources),
                          self.donor, tuple(self.paths))


def build_arrival_delivery(base_pc: int, *, fei_entity: int, doctor_entity: int,
                           guard_entity: int,
                           dialogue: DialogueEmitter) -> SceneBuild:
    """One locked bedside reception in field213, ending under black.

    The caller initializes Fei, the attendant and the transplanted guard
    beneath a black hold. Native e1:s4 supplies special77/program0 (lying in
    bed), not the baptism collapse. Set the mattress position and pose before
    revealing anyone. Retain controls and camera ownership until the caller
    commits delivery and changes fields. Hammer enters the next scene.
    """
    from modules.rico import chapter_two_resources as resources

    s = _Scene(base_pc, 213, (fei_entity, doctor_entity, guard_entity), 24, dialogue)
    # Entry3's actor direction6 becomes native rotation0x800. OP5F uses a
    # different table: cardinal2 selects that same rotation, not cardinal6.
    staging = s.actor(fei_entity, 0, "Fei lies on the native infirmary mattress",
        _stage(resources.ARRIVAL_PATIENT[:2], 2)[:-1]
        + bytes.fromhex("FE 4A 77 80 FE 4B FE 4D 00") + _wait(2) + b"\x00")
    staging += s.actor(doctor_entity, 0, "Attendant at Fei's bedside",
                       _stage(resources.ARRIVAL_ATTENDANT[:2], 2))
    staging += s.actor(guard_entity, 0, "Guard beside the bed's foot",
                       _stage(resources.ARRIVAL_GUARD[:2], 2))
    staging += _look(doctor_entity, fei_entity) + _look(guard_entity, fei_entity)
    s.open(staging, resources.ARRIVAL_CAMERA_TARGET, resources.ARRIVAL_CAMERA_EYE,
           (fei_entity, doctor_entity, guard_entity))
    s.say("arrival_delivery")
    s.body.extend(native._facility_video_screen_fade_body(255, 8))
    for entity in s.actors:
        s.body.extend(s.actor(entity, 4, "Restore reception collision under black",
                              bytes.fromhex("20 00 80 00")))
    s.body.extend(b"\xF4\x01\xFE\x0D\xFC\x80")
    if base_pc + len(s.body) > 0x10000:
        raise ValueError("Scene bytecode exceeds the ATEL address space")
    return SceneBuild(bytes(s.body), tuple(s.routines), (2455,), 213)


def build_baptism(base_pc: int, rico_entity: int, fei_entity: int,
                  dialogue: DialogueEmitter, first_script: int = 24) -> SceneBuild:
    """Visible native Rico strike / Fei reaction in sanitized field199."""
    s = _Scene(base_pc, 199, (rico_entity, fei_entity), first_script, dialogue)
    rico_start, rico_hit = (-1800, -75), (-1799, -100)
    fei_start, fei_hit = (-1799, -334), (-1799, -315)
    staging = s.actor(rico_entity, 0, "Rico stage", _stage(rico_start, 1))
    staging += s.actor(fei_entity, 0, "Fei stage", _stage(fei_start, 5))
    approach = s.actor(rico_entity, 1, "Rico confronts Fei", _walk(rico_hit))
    strike = s.actor(rico_entity, 2, "Native Rico special33",
                     bytes.fromhex("FE 4A 21 80 FE 4B FE 4D 00 00"))
    # Native e1:s8; replace only the unbounded4A movement with the finite
    #4B+19 contract. Keep the actual special program, F6 envelope and45 wait.
    reaction = (bytes.fromhex("FE 4A 03 80 FE 4B F6 01")
                + _walk(fei_hit)[:-1] + bytes.fromhex("F6 00 FE 4D 00")
                + _wait(45) + b"\x00")
    react = s.actor(fei_entity, 1, "Native Fei special3", reaction)
    rico_idle = s.actor(rico_entity, 3, "Rico returns to idle", b"\x2C\xFF\x00")
    fei_idle = s.actor(fei_entity, 2, "Fei returns to idle", b"\x2C\xFF\x00")
    s.paths.extend((MotionPath((rico_start, rico_hit)), MotionPath((fei_start, fei_hit))))
    s.open(staging, (-1787, -167, -208), (-2053, 968, -806), (rico_entity, fei_entity))
    s.say("baptism_before")
    s.say("baptism_exchange", 0, 2)
    s.body.extend(approach + _look(rico_entity, fei_entity) + _look(fei_entity, rico_entity))
    s.say("baptism_exchange", 2)
    s.body.extend(strike + react + _wait(20))
    s.say("baptism_after", 0, 2)
    s.body.extend(rico_idle + _look(rico_entity, fei_entity) + _wait(20))
    s.say("baptism_after", 2)
    s.body.extend(fei_idle)
    return s.finish((2339, 2369))


def build_bandage(base_pc: int, rico_entity: int, hammer_entity: int,
                  dialogue: DialogueEmitter, first_script: int = 24) -> SceneBuild:
    """Visible approach and acceptance; no fabricated bandage animation."""
    from modules.rico import chapter_two_opening as opening

    s = _Scene(base_pc, 218, (rico_entity, hammer_entity), first_script, dialogue)
    # Remain on the same clear room floor as the introduction. The former
    # treatment positions put Hammer on the stair/rail and left him there.
    rp, hp, near = opening.MAIN_RICO[:2], opening.MAIN_HAMMER[:2], (55, -251)
    stage = s.actor(rico_entity, 0, "Rico arm treatment stage", _stage(rp, 2))
    stage += s.actor(hammer_entity, 0, "Hammer treatment stage", _stage(hp, 6))
    approach = s.actor(hammer_entity, 1, "Hammer tends the arm", _walk(near))
    withdraw = s.actor(hammer_entity, 2, "Hammer finishes the knot", _walk(hp))
    s.paths.append(MotionPath((hp, near, hp)))
    s.open(stage, opening.CONVERSATION_TARGET, opening.CONVERSATION_EYE,
           (rico_entity, hammer_entity))
    s.body.extend(_look(rico_entity, hammer_entity) + _look(hammer_entity, rico_entity))
    s.say("bandage", 0, 3)
    s.body.extend(approach + _wait(24))
    s.say("bandage", 3, 5)
    s.body.extend(_wait(30) + withdraw)
    s.say("bandage", 5)
    built = s.finish()
    # Keep Hammer at his authored interaction position without making the
    # post-treatment route to the stairs collide with him.
    return replace(built, actor_routines=tuple(
        replace(actor, body=opening.NPC_PASSABLE_FLAGS + b"\x00",
                label="Restore Hammer's passable stationary interaction flags")
        if (actor.entity, actor.script_index) == (hammer_entity, first_script + 4)
        else actor for actor in built.actor_routines))


def build_finals(base_pc: int, rico_entity: int, fei_entity: int,
                 dialogue: DialogueEmitter, first_script: int = 24) -> SceneBuild:
    """Visible mounted-sprite exchanges and Fei's decisive advance in225.

    `finals_before` belongs to the preparation room and is not repeated here.
    Normal movement supplies the actors' walk/idle programs. No 3D mecha
    animation index is applied to a party sprite.
    """
    s = _Scene(base_pc, 225, (rico_entity, fei_entity), first_script, dialogue)
    a = ARENA_ANCHORS
    stage = s.actor(rico_entity, 0, "Stier initial stance", _stage(a["rico"], 2))
    stage += s.actor(fei_entity, 0, "Weltall initial stance", _stage(a["fei"], 6))
    rico_advance = s.actor(rico_entity, 1, "Stier closes", _walk(a["rico_close"]))
    fei_advance = s.actor(fei_entity, 1, "Weltall closes", _walk(a["fei_close"]))
    rico_recoil = s.actor(rico_entity, 2, "Stier driven back", _walk(a["rico_recoil"]))
    fei_recoil = s.actor(fei_entity, 2, "Weltall yields ground", _walk(a["fei_recoil"]))
    fei_counter = s.actor(fei_entity, 3, "Weltall counter advances", _walk(a["fei_close"], (0, 0)))
    rico_hold = s.actor(rico_entity, 3, "Stier defeated stance", b"\x5F\x02\x00")
    s.paths.extend((MotionPath((a["rico"], a["rico_close"], a["rico_recoil"])),
                    MotionPath((a["fei"], a["fei_close"], a["fei_recoil"], a["fei_close"], (0, 0)))))
    s.open(stage, (-359, 617, -183), (-470, -1652, -1348), (rico_entity, fei_entity))
    s.body.extend(_look(rico_entity, fei_entity) + _look(fei_entity, rico_entity))
    s.say("finals_exchange", 0, 1)
    s.body.extend(fei_advance + rico_advance + _wait(12) + fei_recoil)
    s.say("finals_exchange", 1, 2)
    s.body.extend(fei_counter + rico_recoil + _wait(30) + rico_hold
                  + _look(fei_entity, rico_entity))
    s.say("finals_exchange", 2)
    s.body.extend(_wait(30))
    s.say("finals_after")
    return s.finish((443, 449))


def build_crash(base_pc: int, rico_entity: int, dialogue: DialogueEmitter,
                first_script: int = 16, witness_entity: int | None = None,
                fei_entity: int | None = None) -> SceneBuild:
    """Visible charge and impact, followed by a limited public report in225.

    If provided, witness_entity must already own an actual on-foot guard
    sprite. The world builder owns loading/scaling it beside mounted Stier.
    This helper does not assert a mechanical failure or depict new sabotage.
    Slots16–20 are separate from Finals slots24–28 in the same field.
    """
    actors = (rico_entity,) if witness_entity is None else (rico_entity, witness_entity)
    s = _Scene(base_pc, 225, actors, first_script, dialogue)
    a = ARENA_ANCHORS
    stage = s.actor(rico_entity, 0, "Stier returns to arena", _stage(a["rico"], 0))
    charge = s.actor(rico_entity, 1, "Stier charges the gallery side",
                     _walk(a["charge_midpoint"], a["impact"]))
    s.paths.append(MotionPath((a["rico"], a["charge_midpoint"], a["impact"])))
    witness_stage = b""
    if witness_entity is not None:
        witness_stage = s.actor(witness_entity, 0, "Public witness by impact",
                                _stage(a["witness"], 6))
    if fei_entity is not None:
        if fei_entity in actors or not 0 <= fei_entity <= 0xFC:
            raise ValueError("Unused Weltall entity must be distinct")
        stage += bytes((0x25, fei_entity))
    if witness_entity is not None:
        stage += bytes((0x25, witness_entity))
    s.open(stage, (-359, 617, -183), (-470, -1652, -1348), (rico_entity,))
    s.say("crash_before", 0, 1)
    s.say("crash_before", 1)
    s.body.extend(charge + _shake())
    # A short cut re-establishes the impact side, with an actual witness if
    #the caller supplies one. Most of the scene remains visibly on the field.
    fade = native._facility_video_screen_fade_body
    s.body.extend(fade(255, 6) + witness_stage
                  + (bytes((0x24, witness_entity)) if witness_entity is not None else b"")
                  + _camera((0, -1200, -200), (-470, -2852, -1348), frames=0)
                  + fade(0, 10) + _wait(15))
    if witness_entity is not None:
        s.body.extend(_look(witness_entity, rico_entity))
    s.say("crash_public")
    return s.finish((449,))


def build_flight(base_pc: int, rico_entity: int, dialogue: DialogueEmitter,
                 first_script: int = 24) -> SceneBuild:
    """Visible lower-floor escape through sanitized Central donor231.

    Owns central_flight and chapter_end dialogue. The caller must not emit
    those keys again. The donor's normal player-tracking camera supplies
    framing; no unrelated fixed camera vectors or upper-layer Chapter3 door
    are used. The duct climb is a short narrative cut, since this lower-floor
    route has no audited Rico climbing animation or traversable duct mesh.
    """
    s = _Scene(base_pc, 231, (rico_entity,), first_script, dialogue)
    concealment, checkpoint, gate = (-175, 32), (-84, 34), (397, 24)
    stage = s.actor(rico_entity, 0, "Rico concealed by the checkpoint",
                    _stage(concealment, 2))
    approach = s.actor(rico_entity, 1, "Rico approaches the checkpoint",
                       _walk(checkpoint))
    escape = s.actor(rico_entity, 2, "Rico slips toward the district gate",
                     _walk(gate))
    s.paths.append(MotionPath((concealment, checkpoint, gate)))
    fade = native._facility_video_screen_fade_body
    s.body.extend(fade(255, 6) + stage + bytes((0x24, rico_entity))
                  + native._historical_camera_release_body()
                  + fade(0, 10) + _wait(20))
    s.say("central_flight", 0, 1)
    s.body.extend(approach + _wait(20))
    s.say("central_flight", 1, 3)
    s.body.extend(escape + _wait(15) + fade(255, 6))
    s.say("central_flight", 3)
    s.say("chapter_end", 0, 1)
    s.body.extend(fade(0, 10) + _wait(15))
    s.say("chapter_end", 1)
    return s.finish()


def _segment_interval(start, end, triangle):
    """Clip an exact line segment against one convex walkmesh triangle."""
    vertices = [(v[0], v[2]) for v in triangle]
    area = sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(vertices, vertices[1:] + vertices[:1]))
    if area == 0:
        return None
    sign = 1 if area > 0 else -1
    lo, hi = 0.0, 1.0
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        def side(p):
            return sign * ((b[0] - a[0]) * (p[1] - a[1])
                           - (b[1] - a[1]) * (p[0] - a[0]))
        initial, final = side(start), side(end)
        if initial < 0 and final < 0:
            return None
        if initial < 0:
            lo = max(lo, -initial / (final - initial))
        elif final < 0:
            hi = min(hi, initial / (initial - final))
        if lo > hi:
            return None
    return lo, hi


def validate_geometry(scene: SceneBuild, walkmesh: bytes) -> dict[str, int]:
    """Check donor identity and full path coverage, not just endpoint samples."""
    from modules.soylent_system.base import _walkmesh_layer
    expected = WALKMESH_IDENTITIES.get(scene.donor_field)
    if expected is not None and hashlib.sha256(walkmesh).hexdigest() != expected:
        raise ValueError(f"Scene requires exact field{scene.donor_field} walkmesh")
    segments = 0
    for path in scene.motion_paths:
        triangles = _walkmesh_layer(walkmesh, path.layer)
        for start, end in zip(path.points, path.points[1:]):
            intervals = sorted(value for tri in triangles
                               if (value := _segment_interval(start, end, tri)) is not None)
            covered = 0.0
            for lo, hi in intervals:
                if lo > covered + 1e-9:
                    break
                covered = max(covered, hi)
            if covered < 1 - 1e-9:
                raise ValueError(f"Scene route leaves the donor floor: {start}->{end}")
            segments += 1
    return {"paths": len(scene.motion_paths), "segments": segments}
