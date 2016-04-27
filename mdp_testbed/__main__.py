import sys
import textwrap
from importlib.machinery import SourceFileLoader

import mdp_testbed.ui as ui

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(textwrap.dedent('''
        Wrong number of arguments.

        Usage: {} (editor | classname)

        The program takes a single argument which is either "editor"
        or a name of a class.

        If the argument is "editor" (case insensitive) a maze editor is
        launched. Otherwise a class with the specified name will be loaded
        and used for learning.
        ''').strip().format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    arg = sys.argv[1]

    if arg.lower() == 'editor':
        editor = ui.ResourceMazeEditor()
        editor.mainloop()
    else:
        print('TODO run VI algorithm')
        foo = SourceFileLoader('module', arg).load_module()
        viewer = ui.SolutionViewer(foo.Solver())
        viewer.mainloop()
