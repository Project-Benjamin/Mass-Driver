#!/usr/bin/env python3
"""Authoritative active topology and progression contract for Surface Soylent.

This module intentionally contains no disc or ATEL editing code.  It gives the
campaign builder, manifest writer, and tests one data-only description of the
facility's full topology.  ``DoorClass.INTERNAL`` means an internal
circulation connection; its endpoints may bridge two field resources or two
distinct entry parameters within one large field.  The twenty pairs and forty
endpoints form the active reciprocal X-button route. Progression checks each
award against its registered interaction and prerequisites; compiled-script
tests and emulator playthroughs must independently verify those contracts.
The old Quarantine content boundary is retained only as historical evidence.

The facility is the Ignas/worldwide Surface Soylent installation presented in
the Disc 2 narration.  It is not the playable Etrenank Soylent System from
Disc 1.  The reconstruction uses retail fields 620--626 as its narrative
spine and Solaris/Ethos donor rooms as specialist annexes.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, AbstractSet, Iterable, Mapping


ENTRY_FIELD = 623
FINAL_FIELD = 622
STATE_OPERAND = 0x03FA
PLANNED_TOPOLOGY_SCOPE = "planned_future_topology_foundation"
PLANNED_PROGRESSION_SCOPE = "planned_future_back_half"
ACTIVE_TOPOLOGY_SCOPE = "active_current_release"
ACTIVE_PROGRESSION_SCOPE = "active_campaign_progression"
CURRENT_RELEASE_VERSION = 240
QUARANTINE_REQUIRED_RELAYS = ("Genome", "Limiter", "Nanomachines")
QUARANTINE_EXCLUDED_RELAY = "Caste"
QUARANTINE_SELECTION_MASK = 0x00F0
QUARANTINE_VALID_SELECTION = 0x0070


class BlueprintError(ValueError):
    """Raised when the static campaign contract is internally inconsistent."""


class RoomOrigin(str, Enum):
    NATIVE_SURFACE = "native_surface"
    DONOR_SOLARIS = "donor_solaris"
    DONOR_ETHOS = "donor_ethos"


class DoorClass(str, Enum):
    MAIN = "main"
    ANNEX = "annex"
    INTERNAL = "internal"
    SHORTCUT = "shortcut"


@dataclass(frozen=True)
class Room:
    field: int
    slug: str
    name: str
    origin: RoomOrigin
    function: str
    lore_beat: str


@dataclass(frozen=True)
class CampaignFlag:
    key: str
    name: str
    operand: int
    mask: int
    bit_index: int
    awarded_in_field: int | None
    allocation: str
    meaning: str
    reset_on_surface_start: bool = True
    active: bool = True


@dataclass(frozen=True)
class Gate:
    key: str
    name: str
    requirements: tuple[str, ...]
    denial_text: str


@dataclass(frozen=True)
class DoorEndpoint:
    """One side of a physical, reciprocal X-button doorway.

    ``local_entry_parameter`` is where the other endpoint returns the player.
    ``destination_entry_parameter`` is the parameter used by this endpoint's
    CHANGE_FIELD operation.  Keeping both values explicit makes reciprocity
    mechanically testable even where a field has many doors.
    """

    id: str
    field: int
    local_entry_parameter: int
    destination_field: int
    destination_entry_parameter: int
    sign: str
    interaction: str = "x"

    @property
    def link(self) -> tuple[int, int, int]:
        return (
            self.field,
            self.destination_field,
            self.destination_entry_parameter,
        )


@dataclass(frozen=True)
class DoorPair:
    id: str
    classification: DoorClass
    description: str
    a: DoorEndpoint
    b: DoorEndpoint
    gate: str | None = None

    @property
    def endpoints(self) -> tuple[DoorEndpoint, DoorEndpoint]:
        return self.a, self.b

    @property
    def fields(self) -> tuple[int, int]:
        return self.a.field, self.b.field


@dataclass(frozen=True)
class ProgressionStage:
    """One recommended story beat in an otherwise explorable facility."""

    key: str
    name: str
    interaction_field: int | None
    awards: tuple[str, ...]
    expected_new_rooms: tuple[int, ...]
    expected_new_doors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProgressionSnapshot:
    stage: str
    flags: frozenset[str]
    reachable_rooms: frozenset[int]
    newly_reachable_rooms: frozenset[int]
    newly_unlocked_doors: frozenset[str]


@dataclass(frozen=True)
class AwardWriter:
    """A live interaction that can earn one permanent progression award.

    Prerequisites include access credentials, not merely checks inside the
    action body. ``condition`` records the local gameplay operation that the
    data-only room graph cannot execute.
    """

    flag: str
    field: int
    entities: tuple[int, ...]
    script_index: int
    prerequisites: tuple[str, ...]
    condition: str
    endpoint_id: str | None = None


@dataclass(frozen=True)
class CurrentContentBoundary:
    """One release's override of a reciprocal door endpoint."""

    version: int
    endpoint_id: str
    field: int
    controller_entity: int
    action_script_index: int
    action_pc: int
    side: str
    dialogue_id: int
    dialogue: str
    dialogue_width: int
    dialogue_height: int
    repeatable: bool
    cross_release_drains: int
    plays_sound: bool
    animates_leaf: bool
    opens: bool
    transitions: bool
    writes_state: bool
    planned_destination: tuple[int, int]
    preserved_return_endpoint_id: str
    preserved_return_controller_entity: int
    preserved_return_destination: tuple[int, int]


FACILITY_IDENTITY: Mapping[str, str] = {
    "facility": "Ignas Surface Soylent System",
    "continuity": "Disc 2 surface installation during the Verus crisis",
    "not_the_same_location_as": "Disc 1 Etrenank Soylent System",
    "scope": "One node in the worldwide surface network, not the entire crisis",
    "outcome": (
        "The party secures this node, preserves the Meld and Sufal Mass beats, "
        "and continues the canonical effort against the remaining installations."
    ),
}


ROOMS = (
    Room(
        623,
        "tissue_transfer_vestibule",
        "Tissue Transfer Vestibule",
        RoomOrigin.NATIVE_SURFACE,
        "Facility threshold and post-finale return loop",
        (
            "The blood-filled tubes establish molecular disintegration and "
            "fusion as a physical process already operating inside this surface node."
        ),
    ),
    Room(
        621,
        "intake_triage_reception",
        "Intake and Triage Reception",
        RoomOrigin.NATIVE_SURFACE,
        "Primary hub, survivor space, and ten-door circulation spine",
        (
            "People drawn from across the surface are sorted as material; the "
            "haves-and-have-nots theme begins without conflating this site with Etrenank."
        ),
    ),
    Room(
        549,
        "classification_archive",
        "Classification Systems Archive",
        RoomOrigin.DONOR_SOLARIS,
        "Mandatory intake registration with optional classification records",
        (
            "Solaris records expose unequal intake categories and administrative "
            "language that erases the patients' identities."
        ),
    ),
    Room(
        550,
        "intake_examination_office",
        "Intake Examination Office",
        RoomOrigin.DONOR_ETHOS,
        "Timed clinic appointment, security confrontation, and keycard recovery",
        (
            "An Ethos infirmary room hosts the physician's bloodwork and injection "
            "briefing. Defeating the responding security team yields the keycard "
            "needed to enter the facility's service network."
        ),
    ),
    Room(
        620,
        "quarantine_diagnostics",
        "Quarantine Diagnostics",
        RoomOrigin.NATIVE_SURFACE,
        "Four-relay diagnostic chamber",
        (
            "The Verus transformations leave suffering human identities behind. "
            "They follow the limiter's collapse and Krelian's virus, before the Gaetia Key."
        ),
    ),
    Room(
        565,
        "service_distribution_manifold",
        "Service Distribution Manifold",
        RoomOrigin.DONOR_SOLARIS,
        "Maintenance crossroads, scanner annex access, and production circulation",
        (
            "The patient and staff corridors feed the maintenance network. A restored "
            "service threshold reaches the isolated clinical interface scanner."
        ),
    ),
    Room(
        567,
        "unassigned_medical_examination_room",
        "Unassigned Medical Examination Room",
        RoomOrigin.DONOR_ETHOS,
        "Optional empty medical annex with one bed and a read-only workstation",
        (
            "An unassigned Ethos examination room retains one clinical bed and "
            "reports that no patient is loaded. It has no NPC, combat, gate, or "
            "progression logic."
        ),
    ),
    Room(
        591,
        "intake_examination_room_a",
        "Intake Examination Room A",
        RoomOrigin.DONOR_ETHOS,
        "Bright examination room with a Solaris hematology terminal",
        (
            "A clean clinical bay records blood-cell counts and intake sample status "
            "through a repurposed Solaris terminal without adding a progression award."
        ),
    ),
    Room(
        592,
        "intake_examination_room_b",
        "Intake Examination Room B",
        RoomOrigin.DONOR_ETHOS,
        "Bright examination room with a Solaris nanomachine assay terminal",
        (
            "A second examination bay presents routine nanomachine compatibility "
            "results while retaining the facility's bright medical visual language."
        ),
    ),
    Room(
        593,
        "intake_examination_room_c",
        "Intake Examination Room C",
        RoomOrigin.DONOR_ETHOS,
        "Bright examination room whose Solaris terminal holds the Quarantine keycard",
        (
            "A Quarantine keycard remains visibly inserted in the terminal's "
            "authorization slot until Fei removes it for use in the service network."
        ),
    ),
    Room(
        594,
        "treatment_preparation_room",
        "Treatment Preparation Room",
        RoomOrigin.DONOR_ETHOS,
        "Bright self-contained preoperative treatment room with a read-only Solaris terminal",
        (
            "The clean preparation bay stages metabolic conditioning and injections "
            "before patient transfer. Its terminal reports equipment status without "
            "awarding a credential or advancing progression."
        ),
    ),
    Room(
        589,
        "organic_resonance_annex",
        "Organic Resonance Annex",
        RoomOrigin.DONOR_SOLARIS,
        "Tone-interlock specialist annex",
        (
            "An acoustic maintenance interlock monitors living tissue handling; "
            "the mechanism adds no new supernatural cause to the crisis."
        ),
    ),
    Room(
        588,
        "clinical_interface_scanner_annex",
        "Clinical Interface Scanner Annex",
        RoomOrigin.DONOR_SOLARIS,
        "Required bright clinical scanner annex that arms the interface cutoff",
        (
            "The bright Disc 1 field-550 clinical shell retains its obvious four-bit "
            "diagnostic scanner and reciprocal animated entrance. All unrelated "
            "donor story and event behavior is retired. Its scanner arms only the "
            "living-subject interface cutoff; it neither stores nor issues a keycard."
        ),
    ),
    Room(
        590,
        "clinical_stabilization_ward",
        "Clinical Stabilization Ward",
        RoomOrigin.DONOR_SOLARIS,
        "Recovered three-door clinical bridge between service circulation and production",
        (
            "A preserved Krelian Lab stabilization ward supplies the clinical "
            "handling step between intake processing and molecular sorting without "
            "reviving its retired surgery event."
        ),
    ),
    Room(
        624,
        "molecular_sorting_floor",
        "Molecular Sorting Floor",
        RoomOrigin.NATIVE_SURFACE,
        "Three-feed diversion puzzle",
        (
            "The production line sorts disintegrated material for reconfiguration "
            "into a single weapon-lifeform."
        ),
    ),
    Room(
        626,
        "m_project_ring_core",
        "M-Project Ring Core",
        RoomOrigin.NATIVE_SURFACE,
        "Fusion, pattern, and containment calibration",
        (
            "The machinery exposes the Gazel Ministry's M Project. Krelian's plan "
            "overlaps it, but the two are not presented as identical schemes."
        ),
    ),
    Room(
        625,
        "meld_containment",
        "Meld Containment",
        RoomOrigin.NATIVE_SURFACE,
        "Irreversible story turn",
        (
            "Meld is an amalgamation of people, not one former person; its wordless "
            "plea drives the party toward the generation hall."
        ),
    ),
    Room(
        622,
        "sufal_generation_hall",
        "Sufal Generation Hall",
        RoomOrigin.NATIVE_SURFACE,
        "Canonical climax, boss, shutdown, and save point",
        (
            "The social barrier collapses, Elly answers the people within Meld, and "
            "the Sufal Mass confrontation secures this installation without ending the global crisis."
        ),
    ),
)
ROOM_BY_FIELD = {room.field: room for room in ROOMS}


FLAGS = (
    CampaignFlag(
        "intake_checkin_complete",
        "Intake registration complete",
        STATE_OPERAND,
        0x0080,
        7,
        549,
        "surface_campaign",
        (
            "Fei registered under an intake alias at the Classification "
            "Systems Archive terminal."
        ),
    ),
    CampaignFlag(
        "security_keycard",
        "Security keycard obtained",
        0x021A,
        0x0001,
        0,
        550,
        "retail_reused",
        "Recovered from the Solaris security team after victory in the physician's office.",
    ),
    CampaignFlag(
        "quarantine_keycard",
        "Quarantine keycard obtained",
        0x021A,
        0x0100,
        8,
        593,
        "retail_reused",
        (
            "Removed from the authorization slot of the Solaris terminal in Intake "
            "Examination Room C; no other terminal or scanner issues this credential."
        ),
    ),
    CampaignFlag(
        "tone_authorized",
        "Organic resonance tone authorized",
        0x021E,
        0x0200,
        9,
        565,
        "retail_reused",
        "The native service input panel accepted the five-tone directional code.",
    ),
    CampaignFlag(
        "quarantine_complete",
        "Quarantine diagnostics complete",
        STATE_OPERAND,
        0x0100,
        8,
        620,
        "surface_v173",
        "Genome, Limiter, and Nanomachines are on; Caste is off. The east-door receipt confirms human identity.",
    ),
    CampaignFlag(
        "finale_epilogue_pending",
        "Transient finale epilogue pending",
        STATE_OPERAND,
        0x0400,
        10,
        None,
        "surface_v173_repurposed",
        (
            "Transient handoff reserved for the one-time post-Sufal epilogue; "
            "it does not unlock topology and is not a progression-stage award."
        ),
        active=False,
    ),
    CampaignFlag(
        "interface_cutoff_armed",
        "Living-subject interface cutoff armed",
        STATE_OPERAND,
        0x0800,
        11,
        588,
        "surface_campaign",
        (
            "The required clinical diagnostic scanner arms only the living-subject "
            "interface cutoff and never stores or issues the Quarantine keycard."
        ),
    ),
    CampaignFlag(
        "sorter_complete",
        "Molecular feed diversion complete",
        STATE_OPERAND,
        0x1000,
        12,
        624,
        "surface_campaign",
        "The three molecular feeds have been diverted to non-production destinations.",
    ),
    CampaignFlag(
        "m_core_safe",
        "M-Project core calibrated safe",
        STATE_OPERAND,
        0x2000,
        13,
        626,
        "surface_campaign",
        "Fusion and pattern alignment are off while containment remains on.",
    ),
    CampaignFlag(
        "meld_witnessed",
        "Meld witnessed",
        STATE_OPERAND,
        0x4000,
        14,
        625,
        "surface_campaign",
        "The party has heard the people within Meld and committed to stopping the line.",
    ),
    CampaignFlag(
        "facility_secured",
        "Surface node secured",
        STATE_OPERAND,
        0x8000,
        15,
        622,
        "surface_campaign",
        "The Sufal Mass encounter and this node's shutdown sequence are complete.",
    ),
)
FLAG_BY_KEY = {flag.key: flag for flag in FLAGS}
ACTIVE_FLAG_KEYS = frozenset(flag.key for flag in FLAGS if flag.active)
NEW_CAMPAIGN_FLAG_KEYS = (
    "interface_cutoff_armed",
    "sorter_complete",
    "m_core_safe",
    "meld_witnessed",
    "facility_secured",
)
NEW_CAMPAIGN_BIT_INDICES = tuple(FLAG_BY_KEY[key].bit_index for key in NEW_CAMPAIGN_FLAG_KEYS)
SURFACE_RESET_FLAG_KEYS = tuple(flag.key for flag in FLAGS if flag.reset_on_surface_start)


GATES = (
    Gate(
        "clinic_appointment",
        "Physician appointment access",
        ("intake_checkin_complete",),
        "EXAMINATION ROOM // COMPLETE REGISTRATION AND WAIT FOR THE PHYSICIAN",
    ),
    Gate(
        "security_keycard_access",
        "Restricted clinical and service access",
        ("security_keycard",),
        "RESTRICTED ACCESS LOCKED // SECURITY KEYCARD REQUIRED",
    ),
    Gate(
        "quarantine_keycard_access",
        "Quarantine keycard access",
        ("quarantine_keycard",),
        "QUARANTINE ACCESS LOCKED // QUARANTINE KEYCARD REQUIRED",
    ),
    Gate(
        "quarantine_clearance",
        "Quarantine biological clearance",
        ("quarantine_complete",),
        "QUARANTINE ROUTE DENIED // ENABLE GENOME, LIMITER, NANOMACHINES; EXCLUDE CASTE",
    ),
    Gate(
        "production_clearance",
        "Production bulkhead consensus",
        (
            "security_keycard",
            "tone_authorized",
            "quarantine_complete",
            "interface_cutoff_armed",
        ),
        "PRODUCTION ROUTE DENIED // FOUR CLEARANCES REQUIRED",
    ),
    Gate(
        "sorting_clearance",
        "Molecular sorter clearance",
        ("sorter_complete",),
        "M-PROJECT ROUTE DENIED // DIVERT ALL THREE MOLECULAR FEEDS",
    ),
    Gate(
        "m_core_clearance",
        "M-Project safe-state clearance",
        ("m_core_safe",),
        "MELD ROUTE DENIED // CALIBRATE THE RING CORE TO SAFE STATE",
    ),
    Gate(
        "meld_clearance",
        "Meld chamber narrative clearance",
        ("meld_witnessed",),
        "GENERATION ROUTE DENIED // THE VOICES WITHIN MELD HAVE NOT BEEN HEARD",
    ),
    Gate(
        "facility_secured_clearance",
        "Post-finale emergency return",
        ("facility_secured",),
        "EMERGENCY RETURN SEALED // GENERATION HALL REMAINS ACTIVE",
    ),
)
GATE_BY_KEY = {gate.key: gate for gate in GATES}


def _endpoint(
    id: str,
    field: int,
    local_entry: int,
    destination_field: int,
    destination_entry: int,
    sign: str,
) -> DoorEndpoint:
    return DoorEndpoint(
        id,
        field,
        local_entry,
        destination_field,
        destination_entry,
        sign,
    )


DOOR_PAIRS = (
    DoorPair(
        "transfer_intake",
        DoorClass.MAIN,
        "Blood-transfer threshold into the public intake spine.",
        _endpoint("transfer_intake.transfer", 623, 1, 621, 6, "INTAKE / TRIAGE"),
        _endpoint("transfer_intake.intake", 621, 6, 623, 1, "TISSUE TRANSFER"),
    ),
    DoorPair(
        "intake_quarantine",
        DoorClass.MAIN,
        (
            "Quarantine-keycard entrance at the live-audited west-side "
            "Intake threshold."
        ),
        _endpoint("intake_quarantine.intake", 621, 2, 620, 0, "QUARANTINE"),
        _endpoint("intake_quarantine.quarantine", 620, 0, 621, 2, "INTAKE"),
        gate="quarantine_keycard_access",
    ),
    DoorPair(
        "intake_archive",
        DoorClass.ANNEX,
        "Mandatory registration terminal with optional classification records.",
        _endpoint("intake_archive.intake", 621, 0, 549, 0, "CLASSIFICATION ARCHIVE"),
        _endpoint("intake_archive.archive", 549, 0, 621, 0, "INTAKE"),
    ),
    DoorPair(
        "intake_scanner",
        DoorClass.ANNEX,
        "Physician-controlled examination room that supplies production clearance.",
        _endpoint("intake_scanner.intake", 621, 3, 550, 0, "EXAMINATION ROOM"),
        _endpoint("intake_scanner.scanner", 550, 0, 621, 3, "INTAKE"),
        gate="clinic_appointment",
    ),
    DoorPair(
        "intake_service_patient",
        DoorClass.INTERNAL,
        (
            "Keycard-controlled patient-transfer corridor restored to its "
            "original intake threshold."
        ),
        _endpoint("intake_service_patient.intake", 621, 1, 565, 0, "PATIENT TRANSFER"),
        _endpoint("intake_service_patient.service", 565, 0, 621, 1, "INTAKE / PATIENT"),
        gate="security_keycard_access",
    ),
    DoorPair(
        "intake_medical_examination",
        DoorClass.ANNEX,
        "Optional empty examination annex with a read-only patient terminal.",
        _endpoint(
            "intake_medical_examination.intake",
            621,
            4,
            567,
            0,
            "UNASSIGNED EXAM ROOM",
        ),
        _endpoint(
            "intake_medical_examination.examination",
            567,
            0,
            621,
            4,
            "INTAKE / TRIAGE",
        ),
    ),
    DoorPair(
        "intake_treatment_preparation",
        DoorClass.ANNEX,
        (
            "Security-keycard-controlled Intake annex for preoperative treatment "
            "preparation; it does not expose the deeper laboratory corridor."
        ),
        _endpoint(
            "intake_treatment_preparation.intake",
            621,
            5,
            594,
            0,
            "TREATMENT PREPARATION",
        ),
        _endpoint(
            "intake_treatment_preparation.treatment",
            594,
            0,
            621,
            5,
            "INTAKE / TRIAGE",
        ),
        gate="security_keycard_access",
    ),
    DoorPair(
        "intake_exam_a",
        DoorClass.ANNEX,
        "Security-keycard-controlled bright examination room with hematology terminal.",
        _endpoint(
            "intake_exam_a.intake",
            621,
            7,
            591,
            0,
            "EXAMINATION ROOM A",
        ),
        _endpoint(
            "intake_exam_a.examination",
            591,
            0,
            621,
            7,
            "INTAKE / TRIAGE",
        ),
        gate="security_keycard_access",
    ),
    DoorPair(
        "intake_exam_b",
        DoorClass.ANNEX,
        "Security-keycard-controlled bright examination room with assay terminal.",
        _endpoint(
            "intake_exam_b.intake",
            621,
            8,
            592,
            0,
            "EXAMINATION ROOM B",
        ),
        _endpoint(
            "intake_exam_b.examination",
            592,
            0,
            621,
            8,
            "INTAKE / TRIAGE",
        ),
        gate="security_keycard_access",
    ),
    DoorPair(
        "intake_exam_c",
        DoorClass.ANNEX,
        (
            "Security-keycard-controlled bright examination room whose terminal "
            "holds the removable Quarantine keycard."
        ),
        _endpoint(
            "intake_exam_c.intake",
            621,
            9,
            593,
            0,
            "EXAMINATION ROOM C",
        ),
        _endpoint(
            "intake_exam_c.examination",
            593,
            0,
            621,
            9,
            "INTAKE / TRIAGE",
        ),
        gate="security_keycard_access",
    ),
    DoorPair(
        "quarantine_service",
        DoorClass.MAIN,
        (
            "Quarantine-keycard-controlled diagnostics access from maintenance; field "
            "620's native service exit still requires the local relay solve."
        ),
        _endpoint("quarantine_service.quarantine", 620, 1, 565, 6, "SERVICE / CLEARED"),
        _endpoint("quarantine_service.service", 565, 6, 620, 1, "QUARANTINE"),
        gate="quarantine_keycard_access",
    ),
    DoorPair(
        "service_resonance",
        DoorClass.ANNEX,
        "Acoustic maintenance interlock branch.",
        _endpoint("service_resonance.service", 565, 4, 589, 0, "ORGANIC RESONANCE"),
        _endpoint("service_resonance.resonance", 589, 0, 565, 4, "SERVICE MANIFOLD"),
    ),
    DoorPair(
        "service_interface_annex",
        DoorClass.ANNEX,
        "Reciprocal service threshold into the required clinical interface scanner.",
        _endpoint(
            "service_interface_annex.service",
            565,
            5,
            588,
            0,
            "CLINICAL INTERFACE SCANNER",
        ),
        _endpoint(
            "service_interface_annex.interface",
            588,
            0,
            565,
            5,
            "SERVICE MANIFOLD",
        ),
    ),
    DoorPair(
        "service_stabilization_production",
        DoorClass.INTERNAL,
        "Primary service-manifold circulation route into the stabilization ward.",
        _endpoint(
            "service_stabilization_production.service",
            565,
            1,
            590,
            0,
            "CLINICAL STABILIZATION",
        ),
        _endpoint(
            "service_stabilization_production.stabilization",
            590,
            0,
            565,
            1,
            "SERVICE MANIFOLD / BULKHEAD",
        ),
    ),
    DoorPair(
        "service_stabilization_staff",
        DoorClass.INTERNAL,
        "Parallel staff circulation route into the stabilization ward.",
        _endpoint(
            "service_stabilization_staff.service",
            565,
            2,
            590,
            1,
            "CLINICAL STABILIZATION / STAFF",
        ),
        _endpoint(
            "service_stabilization_staff.stabilization",
            590,
            1,
            565,
            2,
            "SERVICE MANIFOLD / STAFF",
        ),
    ),
    DoorPair(
        "stabilization_sorting",
        DoorClass.MAIN,
        "Four-clearance ward production bulkhead into molecular sorting.",
        _endpoint(
            "stabilization_sorting.stabilization",
            590,
            2,
            624,
            0,
            "MOLECULAR SORTING",
        ),
        _endpoint(
            "stabilization_sorting.sorting",
            624,
            0,
            590,
            2,
            "CLINICAL STABILIZATION",
        ),
        gate="production_clearance",
    ),
    DoorPair(
        "sorting_m_core",
        DoorClass.MAIN,
        "Sorting-line output into the M-Project ring core.",
        _endpoint("sorting_m_core.sorting", 624, 1, 626, 0, "M-PROJECT CORE"),
        _endpoint("sorting_m_core.m_core", 626, 0, 624, 1, "MOLECULAR SORTING"),
        gate="sorting_clearance",
    ),
    DoorPair(
        "m_core_meld",
        DoorClass.MAIN,
        "Core containment route into the Meld chamber.",
        _endpoint("m_core_meld.m_core", 626, 1, 625, 0, "MELD CONTAINMENT"),
        _endpoint("m_core_meld.meld", 625, 0, 626, 1, "M-PROJECT CORE"),
        gate="m_core_clearance",
    ),
    DoorPair(
        "meld_generation",
        DoorClass.MAIN,
        "Final production route into the Sufal generation hall.",
        _endpoint("meld_generation.meld", 625, 1, 622, 0, "GENERATION HALL"),
        _endpoint("meld_generation.generation", 622, 0, 625, 1, "MELD CONTAINMENT"),
        gate="meld_clearance",
    ),
    DoorPair(
        "generation_transfer_shortcut",
        DoorClass.SHORTCUT,
        "Post-finale emergency return closes the dungeon into one physical loop.",
        _endpoint("generation_transfer_shortcut.generation", 622, 1, 623, 0, "EMERGENCY RETURN"),
        _endpoint("generation_transfer_shortcut.transfer", 623, 0, 622, 1, "GENERATION HALL"),
        gate="facility_secured_clearance",
    ),
)
DOOR_PAIR_BY_ID = {pair.id: pair for pair in DOOR_PAIRS}
ENDPOINTS = tuple(endpoint for pair in DOOR_PAIRS for endpoint in pair.endpoints)
ENDPOINT_BY_ID = {endpoint.id: endpoint for endpoint in ENDPOINTS}


# Historical V232 boundary, retained for migration tools and old receipts.
# V237 restores this endpoint's relay completion and reciprocal transition.
CURRENT_CONTENT_BOUNDARY = CurrentContentBoundary(
    version=232,
    endpoint_id="quarantine_service.quarantine",
    field=620,
    controller_entity=24,
    action_script_index=2,
    action_pc=0x0C42,
    side="east continuation threshold",
    dialogue_id=24,
    dialogue=(
        "This is the end for now.\n"
        "The rest is coming soon...<Close>"
    ),
    dialogue_width=58,
    dialogue_height=4,
    repeatable=True,
    cross_release_drains=2,
    plays_sound=False,
    animates_leaf=False,
    opens=False,
    transitions=False,
    writes_state=False,
    planned_destination=(565, 6),
    preserved_return_endpoint_id="intake_quarantine.quarantine",
    preserved_return_controller_entity=23,
    preserved_return_destination=(621, 2),
)
HISTORICAL_CONTENT_BOUNDARIES = (CURRENT_CONTENT_BOUNDARY,)
ACTIVE_CONTENT_BOUNDARIES: tuple[CurrentContentBoundary, ...] = ()


AWARD_WRITERS = (
    AwardWriter(
        "intake_checkin_complete", 549, (4,), 2, (),
        "Choose an intake alias and close the registration receipt.",
    ),
    AwardWriter(
        "security_keycard", 550, (16,), 1, ("intake_checkin_complete",),
        "Attend the timed appointment, refuse bloodwork, defeat clinic security, and close the keycard receipt.",
    ),
    AwardWriter(
        "quarantine_keycard", 593, (19, 4, 5), 2, ("security_keycard",),
        "Remove the Quarantine keycard from the examination terminal.",
    ),
    AwardWriter(
        "tone_authorized", 565, (12,), 2, ("security_keycard",),
        "Enter the five-direction organic resonance code at the service panel.",
    ),
    AwardWriter(
        "interface_cutoff_armed", 588, (4,), 2, ("security_keycard",),
        "Use the clinical scanner and close its interface cutoff receipt.",
    ),
    AwardWriter(
        "quarantine_complete", 620, (24,), 2, ("quarantine_keycard",),
        "Enable Genome, Limiter, and Nanomachines; leave Caste off; confirm the east door and close its receipt.",
        "quarantine_service.quarantine",
    ),
    AwardWriter(
        "sorter_complete", 624, (1,), 2,
        ("security_keycard", "tone_authorized", "quarantine_complete", "interface_cutoff_armed"),
        "Divert all three feeds, then close the onward-door completion receipt.",
        "sorting_m_core.sorting",
    ),
    AwardWriter(
        "m_core_safe", 626, (1,), 2, ("sorter_complete",),
        "Discharge fusion, uncouple pattern, retain containment, and close the onward-door receipt.",
        "m_core_meld.m_core",
    ),
    AwardWriter(
        "meld_witnessed", 625, (33,), 2, ("m_core_safe",),
        "Interact with Meld and hear the people in containment.",
    ),
    AwardWriter(
        "facility_secured", 622, (29,), 2, ("meld_witnessed",),
        "Defeat Sufal Mass and close the shutdown epilogue; a pending epilogue resumes without replaying the battle.",
    ),
)
AWARD_WRITER_BY_FLAG = {writer.flag: writer for writer in AWARD_WRITERS}


PROGRESSION_STAGES = (
    ProgressionStage(
        "entry",
        "Enter the Surface Soylent node",
        None,
        (),
        (549, 567, 621, 623),
        (
            "transfer_intake",
            "intake_archive",
            "intake_medical_examination",
            "service_resonance",
            "service_interface_annex",
            "service_stabilization_production",
            "service_stabilization_staff",
        ),
    ),
    ProgressionStage(
        "checkin",
        "Register an intake alias at the archive terminal",
        549,
        ("intake_checkin_complete",),
        (550,),
        ("intake_scanner",),
    ),
    ProgressionStage(
        "security_keycard",
        "Defeat clinic security and recover their keycard",
        550,
        ("security_keycard",),
        (565, 588, 589, 590, 591, 592, 593, 594),
        (
            "intake_service_patient",
            "intake_treatment_preparation",
            "intake_exam_a",
            "intake_exam_b",
            "intake_exam_c",
        ),
    ),
    ProgressionStage(
        "quarantine_keycard",
        "Remove the Quarantine keycard from Examination Room C's terminal",
        593,
        ("quarantine_keycard",),
        (620,),
        ("intake_quarantine", "quarantine_service"),
    ),
    ProgressionStage(
        "resonance",
        "Solve the native five-tone service panel",
        565,
        ("tone_authorized",),
        (),
    ),
    ProgressionStage(
        "interface_cutoff",
        "Use the required clinical scanner to arm the interface cutoff",
        588,
        ("interface_cutoff_armed",),
        (),
    ),
    ProgressionStage(
        "quarantine",
        "Enable Genome, Limiter, and Nanomachines; exclude Caste; confirm the east door",
        620,
        ("quarantine_complete",),
        (624,),
        ("stabilization_sorting",),
    ),
    ProgressionStage(
        "sorting",
        "Divert all three molecular feeds",
        624,
        ("sorter_complete",),
        (626,),
        ("sorting_m_core",),
    ),
    ProgressionStage(
        "m_core",
        "Calibrate the M-Project ring to safe state",
        626,
        ("m_core_safe",),
        (625,),
        ("m_core_meld",),
    ),
    ProgressionStage(
        "meld",
        "Witness the people within Meld",
        625,
        ("meld_witnessed",),
        (622,),
        ("meld_generation",),
    ),
    ProgressionStage(
        "generation",
        "Defeat the Sufal Mass and secure this node",
        622,
        ("facility_secured",),
        (),
        ("generation_transfer_shortcut",),
    ),
)


def normalize_flag_keys(flags: Iterable[str | CampaignFlag]) -> frozenset[str]:
    keys = frozenset(flag.key if isinstance(flag, CampaignFlag) else flag for flag in flags)
    unknown = keys - set(FLAG_BY_KEY)
    if unknown:
        raise BlueprintError(f"Unknown campaign flags: {sorted(unknown)!r}")
    return keys


def gate_is_open(gate: str | Gate | None, flags: Iterable[str | CampaignFlag]) -> bool:
    if gate is None:
        return True
    gate_spec = GATE_BY_KEY[gate] if isinstance(gate, str) else gate
    keys = normalize_flag_keys(flags)
    return set(gate_spec.requirements) <= keys


def unlocked_door_pairs(flags: Iterable[str | CampaignFlag]) -> frozenset[str]:
    """Return door pairs whose room-access credentials are satisfied."""

    keys = normalize_flag_keys(flags)
    return frozenset(pair.id for pair in DOOR_PAIRS if gate_is_open(pair.gate, keys))


def reachable_rooms(
    flags: Iterable[str | CampaignFlag] = (),
    *,
    start_field: int = ENTRY_FIELD,
) -> frozenset[int]:
    """Return room-level access through the active reciprocal door graph.

    Local puzzles and the timed clinic sequence are modeled by award writers,
    not by pretending every credential immediately completes its interaction.
    Any active content boundary removes only its overridden direction.
    """

    if start_field not in ROOM_BY_FIELD:
        raise BlueprintError(f"Unknown start field: {start_field}")
    keys = normalize_flag_keys(flags)
    neighbors: dict[int, set[int]] = {field: set() for field in ROOM_BY_FIELD}
    blocked_endpoints = {
        boundary.endpoint_id for boundary in ACTIVE_CONTENT_BOUNDARIES
        if not boundary.transitions
    }
    for pair in DOOR_PAIRS:
        if gate_is_open(pair.gate, keys):
            for endpoint in pair.endpoints:
                if endpoint.id not in blocked_endpoints:
                    neighbors[endpoint.field].add(endpoint.destination_field)
    reached = {start_field}
    queue = deque((start_field,))
    while queue:
        field = queue.popleft()
        for neighbor in neighbors[field] - reached:
            reached.add(neighbor)
            queue.append(neighbor)
    return frozenset(reached)


def simulate_progression(
    stages: Iterable[ProgressionStage] = PROGRESSION_STAGES,
) -> tuple[ProgressionSnapshot, ...]:
    """Check the active route's award locations and prerequisites in order.

    This is a static contract check, not ATEL execution or runtime proof.
    Every award needs a reachable registered writer; a historical boundary
    accidentally reactivated at that writer makes the simulation fail.
    """

    flags: set[str] = set()
    previous_rooms: frozenset[int] = frozenset()
    previous_doors: frozenset[str] = frozenset()
    snapshots: list[ProgressionSnapshot] = []
    seen_stages: set[str] = set()
    for stage in stages:
        if stage.key in seen_stages:
            raise BlueprintError(f"Progression stage is repeated: {stage.key!r}")
        seen_stages.add(stage.key)
        before = reachable_rooms(flags)
        if stage.interaction_field is not None and stage.interaction_field not in before:
            raise BlueprintError(
                f"Stage {stage.key!r} is awarded in unreachable field "
                f"{stage.interaction_field}"
            )
        for key in stage.awards:
            if key not in ACTIVE_FLAG_KEYS or key not in AWARD_WRITER_BY_FLAG:
                raise BlueprintError(f"Stage {stage.key!r} has no active writer for {key!r}")
            writer = AWARD_WRITER_BY_FLAG[key]
            if writer.field != stage.interaction_field or writer.field not in before:
                raise BlueprintError(
                    f"Stage {stage.key!r} must use {key!r}'s reachable writer in field {writer.field}"
                )
            if writer.field != FLAG_BY_KEY[key].awarded_in_field:
                raise BlueprintError(f"Writer for {key!r} disagrees with its flag's award field")
            missing = set(writer.prerequisites) - flags
            if missing:
                raise BlueprintError(f"Writer for {key!r} lacks prerequisites: {sorted(missing)!r}")
            if key in flags:
                raise BlueprintError(f"Progression award is repeated: {key!r}")
            if any(
                boundary.field == writer.field
                and boundary.controller_entity in writer.entities
                and boundary.action_script_index == writer.script_index
                and not boundary.writes_state
                for boundary in ACTIVE_CONTENT_BOUNDARIES
            ):
                raise BlueprintError(f"Active content boundary disables writer for {key!r}")
        flags.update(stage.awards)
        rooms = reachable_rooms(flags)
        doors = unlocked_door_pairs(flags)
        new_rooms = rooms - previous_rooms
        new_doors = doors - previous_doors
        if new_rooms != frozenset(stage.expected_new_rooms):
            raise BlueprintError(
                f"Stage {stage.key!r} reaches {sorted(new_rooms)!r}; expected "
                f"{sorted(stage.expected_new_rooms)!r}"
            )
        if new_doors != frozenset(stage.expected_new_doors):
            raise BlueprintError(
                f"Stage {stage.key!r} unlocks {sorted(new_doors)!r}; expected "
                f"{sorted(stage.expected_new_doors)!r}"
            )
        snapshots.append(
            ProgressionSnapshot(
                stage.key,
                frozenset(flags),
                rooms,
                new_rooms,
                new_doors,
            )
        )
        previous_rooms = rooms
        previous_doors = doors
    return tuple(snapshots)


def reset_masks_by_operand() -> dict[int, int]:
    """Return persistent bits that a fresh Surface campaign must clear."""

    masks: dict[int, int] = {}
    for key in SURFACE_RESET_FLAG_KEYS:
        flag = FLAG_BY_KEY[key]
        masks[flag.operand] = masks.get(flag.operand, 0) | flag.mask
    return masks


def physical_links() -> frozenset[tuple[int, int, int]]:
    """Return source/destination/entry triples for the authored door route."""

    return frozenset(endpoint.link for endpoint in ENDPOINTS)


def validate_blueprint() -> None:
    """Validate the active complete route and preserve historical evidence."""

    if len(ROOM_BY_FIELD) != len(ROOMS):
        raise BlueprintError("Room fields are not unique")
    if set(ROOM_BY_FIELD) != {
        549,
        550,
        565,
        567,
        588,
        589,
        590,
        591,
        592,
        593,
        594,
        620,
        621,
        622,
        623,
        624,
        625,
        626,
    }:
        raise BlueprintError("The Surface campaign must contain its exact eighteen fields")
    if len(DOOR_PAIR_BY_ID) != len(DOOR_PAIRS):
        raise BlueprintError("Door-pair IDs are not unique")
    if len(ENDPOINT_BY_ID) != len(ENDPOINTS):
        raise BlueprintError("Door-endpoint IDs are not unique")
    if len(DOOR_PAIRS) != 20 or len(ENDPOINTS) != 40:
        raise BlueprintError("The Surface campaign requires 20 pairs / 40 endpoints")
    if ACTIVE_CONTENT_BOUNDARIES:
        raise BlueprintError("The completed V237 route must not have a content boundary")
    boundary = CURRENT_CONTENT_BOUNDARY
    if boundary.endpoint_id not in ENDPOINT_BY_ID:
        raise BlueprintError("Current-content boundary targets an unknown endpoint")
    endpoint = ENDPOINT_BY_ID[boundary.endpoint_id]
    if (
        boundary.version != 232
        or boundary.field != endpoint.field
        or boundary.planned_destination
        != (endpoint.destination_field, endpoint.destination_entry_parameter)
        or boundary.controller_entity != 24
        or boundary.action_script_index != 2
        or boundary.action_pc != 0x0C42
        or boundary.dialogue_id != 24
        or boundary.dialogue
        != "This is the end for now.\nThe rest is coming soon...<Close>"
        or (boundary.dialogue_width, boundary.dialogue_height) != (58, 4)
        or not boundary.repeatable
        or boundary.cross_release_drains != 2
        or boundary.plays_sound
        or boundary.animates_leaf
        or boundary.opens
        or boundary.transitions
        or boundary.writes_state
    ):
        raise BlueprintError("Historical V232 field-620 content boundary contract changed")
    if boundary.preserved_return_endpoint_id not in ENDPOINT_BY_ID:
        raise BlueprintError("Current-content boundary return targets an unknown endpoint")
    preserved_return = ENDPOINT_BY_ID[boundary.preserved_return_endpoint_id]
    if (
        preserved_return.field != boundary.field
        or boundary.preserved_return_controller_entity != 23
        or boundary.preserved_return_destination
        != (
            preserved_return.destination_field,
            preserved_return.destination_entry_parameter,
        )
    ):
        raise BlueprintError("Field-620 current-content boundary lost its west return")
    if len(GATE_BY_KEY) != len(GATES):
        raise BlueprintError("Gate keys are not unique")
    if len(FLAG_BY_KEY) != len(FLAGS):
        raise BlueprintError("Campaign flag keys are not unique")

    local_entries: set[tuple[int, int]] = set()
    for pair in DOOR_PAIRS:
        if pair.gate is not None and pair.gate not in GATE_BY_KEY:
            raise BlueprintError(f"Door {pair.id!r} uses unknown gate {pair.gate!r}")
        a, b = pair.endpoints
        if a.field not in ROOM_BY_FIELD or b.field not in ROOM_BY_FIELD:
            raise BlueprintError(f"Door {pair.id!r} references an unknown field")
        if a.destination_field != b.field or b.destination_field != a.field:
            raise BlueprintError(f"Door {pair.id!r} is not field-reciprocal")
        if a.destination_entry_parameter != b.local_entry_parameter:
            raise BlueprintError(f"Door {pair.id!r} A does not target B's entry")
        if b.destination_entry_parameter != a.local_entry_parameter:
            raise BlueprintError(f"Door {pair.id!r} B does not target A's entry")
        for endpoint in pair.endpoints:
            if endpoint.interaction != "x":
                raise BlueprintError(f"Door endpoint {endpoint.id!r} is not X-gated")
            local = (endpoint.field, endpoint.local_entry_parameter)
            if local in local_entries:
                raise BlueprintError(f"Entry parameter is reused: {local!r}")
            local_entries.add(local)

    used_allocations: set[tuple[int, int]] = set()
    for flag in FLAGS:
        if flag.mask != 1 << flag.bit_index:
            raise BlueprintError(f"Flag {flag.key!r} mask and bit index disagree")
        allocation = (flag.operand, flag.mask)
        if allocation in used_allocations:
            raise BlueprintError(f"Persistent allocation is reused: {allocation!r}")
        used_allocations.add(allocation)
        if flag.awarded_in_field is not None and flag.awarded_in_field not in ROOM_BY_FIELD:
            raise BlueprintError(f"Flag {flag.key!r} is awarded in an unknown room")
    for gate in GATES:
        unknown = set(gate.requirements) - ACTIVE_FLAG_KEYS
        if unknown:
            raise BlueprintError(f"Gate {gate.key!r} uses inactive/unknown flags: {unknown!r}")
    if FLAG_BY_KEY["intake_checkin_complete"].bit_index != 7:
        raise BlueprintError("Intake registration must remain on Surface bit 7")
    if FLAG_BY_KEY["quarantine_keycard"].awarded_in_field != 593:
        raise BlueprintError("Only Examination Room C may award the Quarantine keycard")
    if NEW_CAMPAIGN_BIT_INDICES != (11, 12, 13, 14, 15):
        raise BlueprintError("New Surface campaign bits must remain contiguous at 11..15")
    if len(AWARD_WRITER_BY_FLAG) != len(AWARD_WRITERS):
        raise BlueprintError("Progression award writers are not unique")
    if set(AWARD_WRITER_BY_FLAG) != ACTIVE_FLAG_KEYS:
        raise BlueprintError("Every active progression flag requires exactly one writer contract")
    for writer in AWARD_WRITERS:
        if writer.field != FLAG_BY_KEY[writer.flag].awarded_in_field:
            raise BlueprintError(f"Writer for {writer.flag!r} disagrees with its award field")
        if not writer.entities or not 0 <= writer.script_index < 32 or not writer.condition:
            raise BlueprintError(f"Writer for {writer.flag!r} has no usable action contract")
        if set(writer.prerequisites) - ACTIVE_FLAG_KEYS or writer.flag in writer.prerequisites:
            raise BlueprintError(f"Writer for {writer.flag!r} has invalid prerequisites")
        if writer.endpoint_id is not None:
            endpoint = ENDPOINT_BY_ID.get(writer.endpoint_id)
            if endpoint is None or endpoint.field != writer.field:
                raise BlueprintError(f"Writer for {writer.flag!r} references an invalid endpoint")

    snapshots = simulate_progression()
    if snapshots[-1].reachable_rooms != frozenset(ROOM_BY_FIELD):
        raise BlueprintError("Ordered progression does not reach all eighteen rooms")
    if snapshots[-1].newly_unlocked_doors != frozenset(
        ("generation_transfer_shortcut",)
    ):
        raise BlueprintError("The final beat must close the post-finale loop")


def to_manifest() -> dict[str, Any]:
    """Return a JSON-ready representation for the build manifest."""

    return {
        "format": "xenogears-surface-soylent-campaign-blueprint-v1",
        "topology_scope": {
            "door_graph": ACTIVE_TOPOLOGY_SCOPE,
            "progression": ACTIVE_PROGRESSION_SCOPE,
            "current_release_version": CURRENT_RELEASE_VERSION,
            "policy": (
                "the complete route is active; each progression award requires "
                "a reachable registered writer and its prerequisites; static "
                "contracts require independent compiled-script and runtime verification"
            ),
        },
        "identity": dict(FACILITY_IDENTITY),
        "entry_field": ENTRY_FIELD,
        "final_field": FINAL_FIELD,
        "current_content_boundary": None,
        "active_content_boundaries": [],
        "historical_content_boundaries": [{
            "version": CURRENT_CONTENT_BOUNDARY.version,
            "endpoint_id": CURRENT_CONTENT_BOUNDARY.endpoint_id,
            "field": CURRENT_CONTENT_BOUNDARY.field,
            "entity": CURRENT_CONTENT_BOUNDARY.controller_entity,
            "action_script_index": (
                CURRENT_CONTENT_BOUNDARY.action_script_index
            ),
            "action_pc": CURRENT_CONTENT_BOUNDARY.action_pc,
            "side": CURRENT_CONTENT_BOUNDARY.side,
            "dialogue_id": CURRENT_CONTENT_BOUNDARY.dialogue_id,
            "dialogue": CURRENT_CONTENT_BOUNDARY.dialogue.removesuffix(
                "<Close>"
            ),
            "window": [
                CURRENT_CONTENT_BOUNDARY.dialogue_width,
                CURRENT_CONTENT_BOUNDARY.dialogue_height,
            ],
            "underlying_future_destination": list(
                CURRENT_CONTENT_BOUNDARY.planned_destination
            ),
            "historical_behavior": {
                "repeatable": CURRENT_CONTENT_BOUNDARY.repeatable,
                "cross_release_drains": (
                    CURRENT_CONTENT_BOUNDARY.cross_release_drains
                ),
                "plays_sound": CURRENT_CONTENT_BOUNDARY.plays_sound,
                "animates_leaf": CURRENT_CONTENT_BOUNDARY.animates_leaf,
                "opens": CURRENT_CONTENT_BOUNDARY.opens,
                "transitions": CURRENT_CONTENT_BOUNDARY.transitions,
                "writes_state": CURRENT_CONTENT_BOUNDARY.writes_state,
            },
            "preserved_return": {
                "endpoint_id": (
                    CURRENT_CONTENT_BOUNDARY.preserved_return_endpoint_id
                ),
                "entity": (
                    CURRENT_CONTENT_BOUNDARY.preserved_return_controller_entity
                ),
                "destination": list(
                    CURRENT_CONTENT_BOUNDARY.preserved_return_destination
                ),
            },
        }],
        "quarantine_solution": {
            "enabled_relays": list(QUARANTINE_REQUIRED_RELAYS),
            "disabled_relay": QUARANTINE_EXCLUDED_RELAY,
            "selection_mask": QUARANTINE_SELECTION_MASK,
            "valid_selection": QUARANTINE_VALID_SELECTION,
            "completion_endpoint": "quarantine_service.quarantine",
            "commit": "after the east-door success receipt closes",
        },
        "award_writers": [
            {
                "flag": writer.flag,
                "field": writer.field,
                "entities": list(writer.entities),
                "script_index": writer.script_index,
                "prerequisites": list(writer.prerequisites),
                "condition": writer.condition,
                "endpoint_id": writer.endpoint_id,
            }
            for writer in AWARD_WRITERS
        ],
        "rooms": [
            {
                "field": room.field,
                "slug": room.slug,
                "name": room.name,
                "origin": room.origin.value,
                "function": room.function,
                "lore_beat": room.lore_beat,
            }
            for room in ROOMS
        ],
        "state": [
            {
                "key": flag.key,
                "name": flag.name,
                "operand": flag.operand,
                "mask": flag.mask,
                "bit_index": flag.bit_index,
                "awarded_in_field": flag.awarded_in_field,
                "allocation": flag.allocation,
                "meaning": flag.meaning,
                "reset_on_surface_start": flag.reset_on_surface_start,
                "active": flag.active,
            }
            for flag in FLAGS
        ],
        "gates": [
            {
                "key": gate.key,
                "name": gate.name,
                "requirements": list(gate.requirements),
                "denial_text": gate.denial_text,
            }
            for gate in GATES
        ],
        "doors": [
            {
                "id": pair.id,
                "classification": pair.classification.value,
                "description": pair.description,
                "gate": pair.gate,
                "endpoints": [
                    {
                        "id": endpoint.id,
                        "field": endpoint.field,
                        "local_entry_parameter": endpoint.local_entry_parameter,
                        "destination_field": endpoint.destination_field,
                        "destination_entry_parameter": endpoint.destination_entry_parameter,
                        "sign": endpoint.sign,
                        "interaction": endpoint.interaction,
                    }
                    for endpoint in pair.endpoints
                ],
            }
            for pair in DOOR_PAIRS
        ],
        "progression": [
            {
                "key": stage.key,
                "name": stage.name,
                "interaction_field": stage.interaction_field,
                "awards": list(stage.awards),
                "expected_new_rooms": list(stage.expected_new_rooms),
                "expected_new_doors": list(stage.expected_new_doors),
            }
            for stage in PROGRESSION_STAGES
        ],
    }


validate_blueprint()
