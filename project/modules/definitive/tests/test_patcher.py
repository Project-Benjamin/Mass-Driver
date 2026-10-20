from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch
from modules.definitive.options import Options
from modules.definitive.patcher import Patcher, save_selection


class SelectionTests(unittest.TestCase):
    def test_independent_patcher_choices_keep_distinct_immutable_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = save_selection(Options(yellow_names=True), root)
            second = save_selection(Options(double_xp=True), root)
            self.assertNotEqual(first, second)
            self.assertTrue(Options.load(root / first).yellow_names)
            self.assertFalse(Options.load(root / first).double_xp)
            self.assertTrue(Options.load(root / second).double_xp)
            self.assertEqual(first, save_selection(Options(yellow_names=True), root))
            (root / first).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'identity'):
                save_selection(Options(yellow_names=True), root)


class PatcherInteractionTests(unittest.TestCase):
    """Exercise the form without a visible window or any build/config writes."""

    def setUp(self):
        try:
            self.window = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'Tk display unavailable: {exc}')
        self.window.withdraw()
        self.app = Patcher(self.window)

    def tearDown(self):
        if hasattr(self, 'app'):
            self.window.after_cancel(self.app.poll_id)
            self.window.destroy()

    def drain(self):
        self.window.after_cancel(self.app.poll_id)
        self.app.poll()

    def test_missing_disc_is_reported_before_any_worker_starts(self):
        self.app.paths[1].set('')
        with patch('modules.definitive.patcher.threading.Thread') as thread:
            self.app.start()
            self.app.start_portraits()
        thread.assert_not_called()
        self.assertFalse(self.app.busy)
        self.assertEqual(self.app.status.get(), 'Choose a BIN image for Disc 1.')

    def test_work_locks_selection_and_prevents_a_second_operation(self):
        self.app.begin('Checking disc images…')
        self.assertTrue(all(w.instate(['disabled']) for w in self.app.controls))
        self.assertTrue(self.app.build_button.instate(['disabled']))
        with patch('modules.definitive.patcher.threading.Thread') as thread:
            self.app.start()
            self.app.start_portraits()
        thread.assert_not_called()
        destination = Path('builds') / 'example-output'
        self.app.events.put(('stage', 'Creating patched discs…'))
        self.app.events.put(('success', ('Patched discs created.', destination)))
        self.app.events.put(('done', ''))
        self.drain()
        self.assertFalse(self.app.busy)
        self.assertTrue(all(not w.instate(['disabled']) for w in self.app.controls))
        self.assertEqual(self.app.output, destination)
        self.assertEqual(self.app.status.get(), 'Patched discs created.')
        self.assertEqual(self.app.output_button.winfo_manager(), 'pack')

    def test_error_exposes_the_log_and_restores_controls(self):
        self.app.begin('Checking disc images…')
        self.app.events.put(('log', 'ERROR: Disc checksum did not match.\n'))
        self.app.events.put(('error', 'Could not create patched discs. See the log.'))
        self.app.events.put(('done', ''))
        with patch.object(self.app, 'show_details') as details:
            self.drain()
        details.assert_called_once()
        self.assertIn('Disc checksum did not match.', ''.join(self.app.log_lines))
        self.assertFalse(self.app.busy)
        self.assertFalse(self.app.build_button.instate(['disabled']))
        self.assertIsNone(self.app.output)


class SinglePageLayoutTests(unittest.TestCase):
    def test_form_fits_without_scrolling_at_common_display_scales(self):
        for dpi in (96, 144, 192):
            with self.subTest(dpi=dpi):
                try:
                    window = tk.Tk()
                except tk.TclError as exc:
                    self.skipTest(f'Tk display unavailable: {exc}')
                window.withdraw()
                window.tk.call('tk', 'scaling', dpi / 72)
                app = Patcher(window)
                try:
                    window.update_idletasks()
                    width, height = window.minsize()
                    self.assertLessEqual(height, 410 * dpi / 96)
                    self.assertLessEqual(window.winfo_reqheight(), height)
                    self.assertLessEqual(window.winfo_reqwidth(), width)
                    self.assertEqual(window.resizable(), (1, 0))
                    pending = [app.page]
                    while pending:
                        widget = pending.pop()
                        self.assertNotIn(widget.winfo_class(), ('Canvas', 'TScrollbar', 'Scrollbar'))
                        pending.extend(widget.winfo_children())
                    # Completion must not push the build action onto another page.
                    app.output_button.pack(side='left', padx=(app.px(16), 0))
                    app.status.set('Portraits exported. See the included setup notes.')
                    window.update_idletasks()
                    self.assertLessEqual(window.winfo_reqheight(), height)
                    self.assertLessEqual(window.winfo_reqwidth(), width)
                finally:
                    app.close()


if __name__ == '__main__':
    unittest.main()
