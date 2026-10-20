import struct
import unittest

from shared.tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from shared.tools.xgfield import build_field, parse_field
from shared.tools.xgscript import AtelScript
from modules.rico.dialogue_portraits import present_field, PortraitCompileError, _decode


def field(code, text):
    script = bytearray(0xC4)
    struct.pack_into('<I', script, 0x80, 1)
    parts = [b'images', b'walkmesh', b'models', b'actors', b'sprites',
             bytes(script)+code, b'encounters',
             encode_dialogue([DialogueBlockSpec(0, 58, 7, text),
                              DialogueBlockSpec(1, 58, 7, 'SYSTEM\nUnchanged.<Close>')]),
             b'triggers']
    return build_field(bytes(0x180), parts)


def run(code, *, trigger_active=True):
    """Execute emitted CALL/RETURN and original continuation, capturing windows."""
    pc, stack, portrait, windows, unlocked, committed = 0, [], None, [], False, False
    for _ in range(1000):
        op=code[pc]
        if op == 0:
            return windows, unlocked, committed, stack
        if op == 0x05:
            stack.append(pc+3)
            pc=struct.unpack_from('<H',code,pc+1)[0]
        elif op == 0x0A:
            if trigger_active and len(stack) < 4:
                stack.append(pc+4)
                pc=struct.unpack_from('<H',code,pc+2)[0]
            else:
                pc+=4
        elif op == 0x0D:
            pc=stack.pop()
        elif op == 0xF5:
            windows.append((struct.unpack_from('<H',code,pc+1)[0],portrait,code[pc+3]))
            pc+=4
        elif op == 0x9C:
            pc+=1
        elif op == 0xF4:
            assert code[pc+1] == 1
            pc+=2
        elif op == 0x26:
            pc+=3
        elif op == 0x31:
            pc=struct.unpack_from('<H',code,pc+3)[0]
        elif op == 0x3A:
            committed=True
            pc+=6
        elif op == 0xFE and code[pc+1] == 0x0D:
            portrait=struct.unpack_from('<H',code,pc+2)[0]&0x7FFF
            pc+=4
        elif op == 0xFE and code[pc+1] == 0x53:
            unlocked=True
            pc+=2
        else:
            raise AssertionError(f'Unexpected opcode at {pc:#x}: {op:#x}')
    raise AssertionError('Presentation never returned')


class PortraitCompilerTests(unittest.TestCase):
    def test_speaker_switch_returns_to_original_progress_commit_and_unlock(self):
        code=bytes.fromhex('F5 00 00 00 9C 3A EC 03 01 00 40 FE 53 00')
        source=field(code,'Anne\nBe kind.<New><Rico>\nI promise.<Close>')
        result=present_field(source,{'Anne':33,'Rico':5},colorize=lambda s:'<Opcode:0B:FE>'+s)
        before,after=parse_field(source),parse_field(result.bundle)
        editor=AtelScript(after.parts[5].data)
        self.assertEqual(editor.bytecode[4:len(code)],code[4:])
        windows,unlock,commit,stack=run(editor.bytecode)
        self.assertEqual([p for _,p,_ in windows],[33,5])
        self.assertTrue(all(flags&1 for _,_,flags in windows))
        self.assertTrue(unlock and commit)
        self.assertEqual(stack,[])
        dialogue=parse_dialogue(after.parts[7].data)
        self.assertEqual(dialogue.blocks[1].payload,parse_dialogue(before.parts[7].data).blocks[1].payload)
        self.assertEqual(dialogue.blocks[0].text,'<Opcode:0B:FE>Anne\nBe kind.<Close>')
        self.assertEqual(dialogue.blocks[2].text,'<Opcode:0B:FE><Rico>\nI promise.<Close>')
        for index in (0,1,2,3,4,6,8):
            self.assertEqual(before.parts[index].data,after.parts[index].data)
        self.assertEqual(result.maximum_original_call_depth,0)
        self.assertEqual(result.windows,2)
        self.assertEqual(editor.bytecode.count(b'\xF4\x01\xFE\x0D'),2)
        self.assertEqual([dialogue.blocks[i].width for i in (0,2)],[41,41])

    def test_narration_inside_a_mixed_block_clears_portrait(self):
        source=field(bytes.fromhex('F5 00 00 01 9C 00'),
                     'A door opens.<New><Rico>\nStay close.<Close>')
        result=present_field(source,{'Rico':5})
        windows,*_=run(AtelScript(parse_field(result.bundle).parts[5].data).bytecode)
        self.assertEqual([p for _,p,_ in windows],[0xFC,5])

    def test_no_speaker_and_choices_remain_byte_identical(self):
        for text in ('SYSTEM\nRecord stored.<Close>',
                     '<Opcode:01:FF>RETURN\n     Yes\n     No<Close>'):
            source=field(bytes.fromhex('F5 00 00 01 9C 00'),text)
            self.assertEqual(present_field(source,{}).bundle,source)

    def test_opcode_like_operand_is_not_a_dialogue_callsite(self):
        source=field(bytes.fromhex('35 00 04 F5 00 40 00'),'<Rico>\nHello.<Close>')
        self.assertEqual(present_field(source,{'Rico':5}).calls,0)

    def test_unallocated_portrait_and_unknown_bytecode_fail(self):
        with self.assertRaisesRegex(PortraitCompileError,'No portrait allocated'):
            present_field(field(bytes.fromhex('F5 00 00 01 9C 00'),'Anne\nHello.<Close>'),{})
        with self.assertRaisesRegex(PortraitCompileError,'Unproven ATEL'):
            present_field(field(bytes.fromhex('FE FF 00'),'<Rico>\nHello.<Close>'),{'Rico':5})

    def test_native_call_stack_overflow_is_rejected_before_emission(self):
        # Four calls lead to the dialogue; the portrait helper would be fifth.
        code=bytes.fromhex('05 04 00 00 05 08 00 0D 05 0C 00 0D 05 10 00 0D F5 00 00 01 9C 0D')
        with self.assertRaisesRegex(PortraitCompileError,'overflow'):
            present_field(field(code,'<Rico>\nHello.<Close>'),{'Rico':5})

    def test_trigger_call_returns_to_its_four_byte_continuation(self):
        code=bytes.fromhex('0A 00 05 00 00 F5 00 00 01 9C 0D')
        result=present_field(field(code,'<Rico>\nHello.<Close>'),{'Rico':5})
        prepared=AtelScript(parse_field(result.bundle).parts[5].data).bytecode
        self.assertEqual(result.maximum_original_call_depth,1)
        windows,*_=run(prepared)
        self.assertEqual([portrait for _,portrait,_ in windows],[5])
        self.assertEqual(run(prepared,trigger_active=False)[0],[])

    def test_trigger_call_depth_is_counted_before_adding_portrait_helper(self):
        code=bytes.fromhex('05 04 00 00 05 08 00 0D 05 0C 00 0D 0A 00 11 00 0D F5 00 00 01 9C 0D')
        with self.assertRaisesRegex(PortraitCompileError,'overflow'):
            present_field(field(code,'<Rico>\nHello.<Close>'),{'Rico':5})

    def test_non_f5_consumers_of_the_same_record_are_rejected(self):
        for other in ('D2 00 00 01', 'D4 00 00 00 01', 'FC 00 00 00 01'):
            code=bytes.fromhex('F5 00 00 01 9C '+other+' 9C 00')
            with self.subTest(opcode=other):
                with self.assertRaisesRegex(PortraitCompileError,'shared with non-F5'):
                    present_field(field(code,'<Rico>\nHello.<Close>'),{'Rico':5})

    def test_async_dialogue_is_not_silently_made_blocking(self):
        code=bytes.fromhex('F5 00 00 01 26 01 80 9C 00')
        with self.assertRaisesRegex(PortraitCompileError,'not immediately awaited'):
            present_field(field(code,'<Rico>\nHello.<Close>'),{'Rico':5})


if __name__=='__main__':
    unittest.main()
