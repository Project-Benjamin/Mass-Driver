#!/usr/bin/env python3
"""Structural tests for the defense archive's two native-textured doors."""

from __future__ import annotations

import hashlib
import struct
import unittest

from tools.xgdefense_bulkhead import (
    BULKHEAD_FRAME_MODEL_SHA256,
    BULKHEAD_FRAME_MODEL_SIZE,
    BULKHEAD_LEFT_MODEL_SHA256,
    BULKHEAD_LEFT_MODEL_SIZE,
    BULKHEAD_MODEL_SHA256,
    BULKHEAD_RIGHT_MODEL_SHA256,
    BULKHEAD_RIGHT_MODEL_SIZE,
    NORTH_LIFT_FRAME_MODEL_SHA256,
    NORTH_LIFT_FRAME_MODEL_SIZE,
    NORTH_LIFT_LEFT_MODEL_SHA256,
    NORTH_LIFT_LEFT_MODEL_SIZE,
    NORTH_LIFT_RIGHT_MODEL_SHA256,
    NORTH_LIFT_RIGHT_MODEL_SIZE,
    build_defense_archive_bulkhead,
    build_defense_archive_bulkhead_frame,
    build_defense_archive_bulkhead_left_leaf,
    build_defense_archive_bulkhead_right_leaf,
    build_defense_archive_north_lift_frame,
    build_defense_archive_north_lift_left_leaf,
    build_defense_archive_north_lift_right_leaf,
)


_TEXTURE_STATE = bytes.fromhex("87 00 00 C4 00 78 00 C8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _vertices(model: bytes) -> tuple[tuple[int, int, int, int], ...]:
    count = struct.unpack_from("<H", model, 0x12)[0]
    offset = struct.unpack_from("<I", model, 0x18)[0]
    return tuple(
        struct.unpack_from("<hhhh", model, offset + index * 8)
        for index in range(count)
    )


def _groups(
    model: bytes,
) -> tuple[tuple[int, int, tuple[tuple[int, int, int, int], ...]], ...]:
    group_count = struct.unpack_from("<H", model, 0x16)[0]
    cursor = struct.unpack_from("<I", model, 0x20)[0]
    display_offset = struct.unpack_from("<I", model, 0x24)[0]
    groups = []
    for _index in range(group_count):
        kind, unknown, count = struct.unpack_from("<BBH", model, cursor)
        cursor += 4
        indices = tuple(
            struct.unpack_from("<HHHH", model, cursor + primitive * 8)
            for primitive in range(count)
        )
        cursor += count * 8
        groups.append((kind, unknown, indices))
    if cursor != display_offset:
        raise AssertionError(
            f"mesh groups end at 0x{cursor:X}, display begins at "
            f"0x{display_offset:X}"
        )
    return tuple(groups)


def _textured_uvs(model: bytes) -> tuple[tuple[int, ...], ...]:
    groups = _groups(model)
    cursor = struct.unpack_from("<I", model, 0x24)[0]
    result = []
    for kind, _unknown, indices in groups:
        if kind == 0x04:
            cursor += len(indices) * 4
        elif kind == 0x0D:
            if model[cursor : cursor + 8] != _TEXTURE_STATE:
                raise AssertionError("FT4 group lost the native texture state")
            cursor += 8
            for _index in indices:
                record = model[cursor : cursor + 12]
                if record[:4] != bytes.fromhex("00 00 00 2D"):
                    raise AssertionError("FT4 display record is malformed")
                result.append(tuple(record[4:]))
                cursor += 12
        else:
            raise AssertionError(f"unexpected mesh group 0x{kind:02X}")
    if cursor != len(model):
        raise AssertionError("display records do not consume the model")
    return tuple(result)


class DefenseArchiveDoorModelTests(unittest.TestCase):
    def test_six_models_have_release_locked_sizes_and_hashes(self) -> None:
        models = (
            (
                build_defense_archive_bulkhead_left_leaf(),
                BULKHEAD_LEFT_MODEL_SIZE,
                BULKHEAD_LEFT_MODEL_SHA256,
            ),
            (
                build_defense_archive_bulkhead_right_leaf(),
                BULKHEAD_RIGHT_MODEL_SIZE,
                BULKHEAD_RIGHT_MODEL_SHA256,
            ),
            (
                build_defense_archive_bulkhead_frame(),
                BULKHEAD_FRAME_MODEL_SIZE,
                BULKHEAD_FRAME_MODEL_SHA256,
            ),
            (
                build_defense_archive_north_lift_left_leaf(),
                NORTH_LIFT_LEFT_MODEL_SIZE,
                NORTH_LIFT_LEFT_MODEL_SHA256,
            ),
            (
                build_defense_archive_north_lift_right_leaf(),
                NORTH_LIFT_RIGHT_MODEL_SIZE,
                NORTH_LIFT_RIGHT_MODEL_SHA256,
            ),
            (
                build_defense_archive_north_lift_frame(),
                NORTH_LIFT_FRAME_MODEL_SIZE,
                NORTH_LIFT_FRAME_MODEL_SHA256,
            ),
        )
        for model, expected_size, expected_hash in models:
            with self.subTest(expected_hash=expected_hash):
                self.assertEqual(len(model), expected_size)
                self.assertEqual(_sha256(model), expected_hash)

        self.assertEqual(BULKHEAD_MODEL_SHA256, BULKHEAD_LEFT_MODEL_SHA256)
        self.assertEqual(
            build_defense_archive_bulkhead(),
            build_defense_archive_bulkhead_left_leaf(),
        )

    def test_west_leaves_exactly_reconstruct_model_8_aperture(self) -> None:
        left = build_defense_archive_bulkhead_left_leaf()
        right = build_defense_archive_bulkhead_right_leaf()
        self.assertEqual(
            _vertices(left),
            (
                (-573, 0, 44, 0),
                (-573, 0, 0, 0),
                (-573, -132, 44, 0),
                (-573, -132, 0, 0),
            ),
        )
        self.assertEqual(
            _vertices(right),
            (
                (-573, 0, 0, 0),
                (-573, 0, -44, 0),
                (-573, -132, 0, 0),
                (-573, -132, -44, 0),
            ),
        )
        self.assertEqual(
            _textured_uvs(left),
            ((96, 115, 112, 115, 96, 66, 112, 66),),
        )
        self.assertEqual(
            _textured_uvs(right),
            ((112, 115, 128, 115, 112, 66, 128, 66),),
        )

        combined = _vertices(left) + _vertices(right)
        self.assertEqual({vertex[0] for vertex in combined}, {-573})
        self.assertEqual(
            (
                min(vertex[1] for vertex in combined),
                max(vertex[1] for vertex in combined),
            ),
            (-132, 0),
        )
        self.assertEqual(
            (
                min(vertex[2] for vertex in combined),
                max(vertex[2] for vertex in combined),
            ),
            (-44, 44),
        )

    def test_north_lift_leaves_exactly_reconstruct_model_13_panel(self) -> None:
        left = build_defense_archive_north_lift_left_leaf()
        right = build_defense_archive_north_lift_right_leaf()
        self.assertEqual(
            _vertices(left),
            (
                (0, 0, 308, 0),
                (-44, 0, 308, 0),
                (0, -85, 308, 0),
                (-44, -85, 308, 0),
            ),
        )
        self.assertEqual(
            _vertices(right),
            (
                (44, 0, 308, 0),
                (0, 0, 308, 0),
                (44, -85, 308, 0),
                (0, -85, 308, 0),
            ),
        )
        self.assertEqual(
            _textured_uvs(left),
            ((176, 115, 159, 115, 176, 84, 159, 84),),
        )
        self.assertEqual(
            _textured_uvs(right),
            ((192, 115, 176, 115, 192, 84, 176, 84),),
        )

        combined = _vertices(left) + _vertices(right)
        self.assertEqual({vertex[2] for vertex in combined}, {308})
        self.assertEqual(
            (
                min(vertex[0] for vertex in combined),
                max(vertex[0] for vertex in combined),
            ),
            (-44, 44),
        )
        self.assertEqual(
            (
                min(vertex[1] for vertex in combined),
                max(vertex[1] for vertex in combined),
            ),
            (-85, 0),
        )

    def test_moving_leaves_are_retail_scale_single_ft4_models(self) -> None:
        leaves = (
            build_defense_archive_bulkhead_left_leaf(),
            build_defense_archive_bulkhead_right_leaf(),
            build_defense_archive_north_lift_left_leaf(),
            build_defense_archive_north_lift_right_leaf(),
        )
        for leaf in leaves:
            with self.subTest(hash=_sha256(leaf)):
                self.assertEqual(struct.unpack_from("<I", leaf, 0)[0], 1)
                self.assertEqual(struct.unpack_from("<HHH", leaf, 0x12), (4, 1, 1))
                self.assertEqual(
                    tuple(
                        struct.unpack_from("<I", leaf, offset)[0]
                        for offset in (0x18, 0x1C, 0x20, 0x24, 0x44)
                    ),
                    (0x48, 0x48, 0x68, 0x74, 0x28),
                )
                self.assertEqual(
                    _groups(leaf),
                    ((0x0D, 119, ((0, 1, 2, 3),)),),
                )
                self.assertEqual(len(_textured_uvs(leaf)), 1)

    def test_west_frame_is_only_a_behind_wall_reveal(self) -> None:
        frame = build_defense_archive_bulkhead_frame()
        vertices = _vertices(frame)
        self.assertEqual(
            tuple(
                (
                    min(vertex[axis] for vertex in vertices),
                    max(vertex[axis] for vertex in vertices),
                )
                for axis in range(3)
            ),
            ((-580, -574), (-132, 0), (-44, 44)),
        )
        self.assertTrue(all(vertex[0] < -573 for vertex in vertices))
        self._assert_flat_reveal_model(frame)

    def test_north_frame_is_only_a_behind_wall_reveal(self) -> None:
        frame = build_defense_archive_north_lift_frame()
        vertices = _vertices(frame)
        self.assertEqual(
            tuple(
                (
                    min(vertex[axis] for vertex in vertices),
                    max(vertex[axis] for vertex in vertices),
                )
                for axis in range(3)
            ),
            ((-44, 44), (-85, 0), (309, 315)),
        )
        self.assertTrue(all(vertex[2] > 308 for vertex in vertices))
        self._assert_flat_reveal_model(frame)

    def _assert_flat_reveal_model(self, frame: bytes) -> None:
        self.assertEqual(struct.unpack_from("<I", frame, 0)[0], 1)
        self.assertEqual(struct.unpack_from("<HHH", frame, 0x12), (16, 16, 1))
        self.assertEqual(
            tuple(
                struct.unpack_from("<I", frame, offset)[0]
                for offset in (0x18, 0x1C, 0x20, 0x24, 0x44)
            ),
            (0x48, 0x48, 0xC8, 0x14C, 0x140),
        )
        groups = _groups(frame)
        self.assertEqual(len(groups), 1)
        self.assertEqual(
            (groups[0][0], groups[0][1], len(groups[0][2])),
            (0x04, 119, 16),
        )
        self.assertNotIn(_TEXTURE_STATE, frame)
        display = struct.unpack_from("<I", frame, 0x24)[0]
        self.assertEqual(
            {
                frame[display + index * 4 : display + index * 4 + 4]
                for index in range(16)
            },
            {bytes((30, 36, 35, 0x20))},
        )


if __name__ == "__main__":
    unittest.main()
