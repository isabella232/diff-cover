# -*- coding: utf-8 -*-
from diff_cover.diff_reporter import GitDiffReporter
from diff_cover.git_diff import GitDiffTool, GitDiffError
from diff_cover.tests.helpers import line_numbers, git_diff_output, unittest
class GitDiffReporterTest(unittest.TestCase):
        # Create a mock git diff wrapper
        self._git_diff = mock.MagicMock(GitDiffTool)
        self.diff = GitDiffReporter(git_diff=self._git_diff)
    def test_name(self):
        # Expect that diff report is named after its compare branch
        self.assertEqual(self.diff.name(),
                         'origin/master...HEAD, staged, and unstaged changes')

    def test_git_source_paths(self):
        self._set_git_diff_output(
            git_diff_output({'subdir/file1.py':
                             line_numbers(3, 10) + line_numbers(34, 47)}),
            git_diff_output({'subdir/file2.py': line_numbers(3, 10),
                             'file3.py': [0]}),
            git_diff_output(dict(), deleted_files=['README.md']))

        # Get the source paths in the diff
        source_paths = self.diff.src_paths_changed()

        # Validate the source paths
        # They should be in alphabetical order
        self.assertEqual(len(source_paths), 4)
        self.assertEqual('file3.py', source_paths[0])
        self.assertEqual('README.md', source_paths[1])
        self.assertEqual('subdir/file1.py', source_paths[2])
        self.assertEqual('subdir/file2.py', source_paths[3])

    def test_duplicate_source_paths(self):

        # Duplicate the output for committed, staged, and unstaged changes
        diff = git_diff_output({'subdir/file1.py':
                                line_numbers(3, 10) + line_numbers(34, 47)})
        self._set_git_diff_output(diff, diff, diff)
        # Get the source paths in the diff
        source_paths = self.diff.src_paths_changed()
        # Should see only one copy of source files
        self.assertEqual(len(source_paths), 1)
        self.assertEqual('subdir/file1.py', source_paths[0])
    def test_git_lines_changed(self):
        self._set_git_diff_output(
            git_diff_output({'subdir/file1.py':
                             line_numbers(3, 10) + line_numbers(34, 47)}),
            git_diff_output({'subdir/file2.py': line_numbers(3, 10),
                             'file3.py': [0]}),
            git_diff_output(dict(), deleted_files=['README.md']))
        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('subdir/file1.py')
        # Validate the lines changed
        self.assertEqual(lines_changed,
                         line_numbers(3, 10) + line_numbers(34, 47))
    def test_ignore_lines_outside_src(self):
        # Add some lines at the start of the diff, before any
        # source files are specified
        diff = git_diff_output({'subdir/file1.py': line_numbers(3, 10)})
        master_diff = "\n".join(['- deleted line', '+ added line', diff])
        self._set_git_diff_output(master_diff, "", "")
        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('subdir/file1.py')
        # Validate the lines changed
        self.assertEqual(lines_changed, line_numbers(3, 10))

    def test_one_line_file(self):
        # Files with only one line have a special format
        # in which the "length" part of the hunk is not specified
        diff_str = dedent("""
            diff --git a/diff_cover/one_line.txt b/diff_cover/one_line.txt
            index 0867e73..9daeafb 100644
            --- a/diff_cover/one_line.txt
            +++ b/diff_cover/one_line.txt
            @@ -1,3 +1 @@
            test
            -test
            -test
            """).strip()
        self._set_git_diff_output(diff_str, "", "")
        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('one_line.txt')
        # Expect that no lines are changed
        self.assertEqual(len(lines_changed), 0)
    def test_git_deleted_lines(self):
        self._set_git_diff_output(
            git_diff_output({'subdir/file1.py':
                             line_numbers(3, 10) + line_numbers(34, 47)}),
            git_diff_output({'subdir/file2.py': line_numbers(3, 10),
                             'file3.py': [0]}),
            git_diff_output(dict(), deleted_files=['README.md']))

        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('README.md')

        # Validate no lines changed
        self.assertEqual(len(lines_changed), 0)

    def test_git_unicode_filename(self):

        # Filenames with unicode characters have double quotes surrounding them
        # in the git diff output.
        diff_str = dedent("""
            diff --git "a/unic\303\270\342\210\202e\314\201.txt" "b/unic\303\270\342\210\202e\314\201.txt"
            new file mode 100644
            index 0000000..248ebea
            --- /dev/null
            +++ "b/unic\303\270\342\210\202e\314\201.txt"
            @@ -0,0 +1,13 @@
            +μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος
            +οὐλομένην, ἣ μυρί᾽ Ἀχαιοῖς ἄλγε᾽ ἔθηκε,
            +πολλὰς δ᾽ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν
            """).strip()

        self._set_git_diff_output(diff_str, "", "")
        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('unic\303\270\342\210\202e\314\201.txt')

        # Expect that three lines changed
        self.assertEqual(len(lines_changed), 3)


    def test_git_repeat_lines(self):

        # Same committed, staged, and unstaged lines
        diff = git_diff_output({'subdir/file1.py':
                                line_numbers(3, 10) + line_numbers(34, 47)})
        self._set_git_diff_output(diff, diff, diff)

        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('subdir/file1.py')

        # Validate the lines changed
        self.assertEqual(lines_changed,
                         line_numbers(3, 10) + line_numbers(34, 47))

    def test_git_overlapping_lines(self):
        master_diff = git_diff_output(
            {'subdir/file1.py': line_numbers(3, 10) + line_numbers(34, 47)})
        # Overlap, extending the end of the hunk (lines 3 to 10)
        overlap_1 = git_diff_output({'subdir/file1.py': line_numbers(5, 14)})

        # Overlap, extending the beginning of the hunk (lines 34 to 47)
        overlap_2 = git_diff_output({'subdir/file1.py': line_numbers(32, 37)})

        # Lines in staged / unstaged overlap with lines in master
        self._set_git_diff_output(master_diff, overlap_1, overlap_2)

        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('subdir/file1.py')

        # Validate the lines changed
        self.assertEqual(lines_changed,
                         line_numbers(3, 14) + line_numbers(32, 47))

    def test_git_line_within_hunk(self):

        master_diff = git_diff_output(
            {'subdir/file1.py': line_numbers(3, 10) + line_numbers(34, 47)})

        # Surround hunk in master (lines 3 to 10)
        surround = git_diff_output({'subdir/file1.py': line_numbers(2, 11)})

        # Within hunk in master (lines 34 to 47)
        within = git_diff_output({'subdir/file1.py': line_numbers(35, 46)})

        # Lines in staged / unstaged overlap with hunks in master
        self._set_git_diff_output(master_diff, surround, within)

        # Get the lines changed in the diff
        lines_changed = self.diff.lines_changed('subdir/file1.py')

        # Validate the lines changed
        self.assertEqual(lines_changed,
                         line_numbers(2, 11) + line_numbers(34, 47))

    def test_inter_diff_conflict(self):

        # Commit changes to lines 3 through 10
        added_diff = git_diff_output({'file.py': line_numbers(3, 10)})

        # Delete the lines we modified
        deleted_lines = []
        for line in added_diff.split('\n'):

            # Any added line becomes a deleted line
            if line.startswith('+'):
                deleted_lines.append(line.replace('+', '-'))

            # No need to include lines we already deleted
            elif line.startswith('-'):
                pass

            # Keep any other line
            else:
                deleted_lines.append(line)

        deleted_diff = "\n".join(deleted_lines)

        # Try all combinations of diff conflicts
        combinations = [(added_diff, deleted_diff, ''),
                        (added_diff, '', deleted_diff),
                        ('', added_diff, deleted_diff),
                        (added_diff, deleted_diff, deleted_diff)]

        for (master_diff, staged_diff, unstaged_diff) in combinations:

            # Set up so we add lines, then delete them
            self._set_git_diff_output(master_diff, staged_diff, unstaged_diff)

            # Should have no lines changed, since
            # we deleted all the lines we modified
            fail_msg = dedent("""
            master_diff = {0}
            staged_diff = {1}
            unstaged_diff = {2}
            """).format(master_diff, staged_diff, unstaged_diff)

            self.assertEqual(self.diff.lines_changed('file.py'), [],
                             msg=fail_msg)
        diff = git_diff_output({'subdir/file1.py': [1],
                                'subdir/file2.py': [2],
                                'file3.py': [3]})

        self._set_git_diff_output(diff, "", "")
        lines_changed = self.diff.lines_changed('no_such_file.txt')
        self.assertEqual(len(lines_changed), 0)
        # Configure the git diff output
        self._set_git_diff_output('', '', '')