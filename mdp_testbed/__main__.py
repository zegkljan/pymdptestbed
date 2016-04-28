import argparse

import mdp_testbed.ui as ui

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='MDP Testbed')
    grp = ap.add_mutually_exclusive_group(required=False)
    grp.add_argument('-e', '--editor', action='store_true', required=False,
                     help='If specified, the editor will be launched, '
                          'otherwise the solution viewer will be launched.')
    grp.add_argument('-s', '--solution', action='store', required=False,
                     nargs=1, metavar='filename', default=None,
                     help='If specified, the solution viewer will be launched '
                          'and will immediately load the  solution given in '
                          'the filename. Otherwise no solution will be loaded '
                          '(and can be loaded using the GUI).')
    ap.add_argument('-m', '--maze', action='store', required=False, nargs=1,
                    metavar='filename', default=None,
                    help='If specified, the solution viewer or the editor '
                         'will be started with the specified maze already '
                         'loaded. Otherwise no maze will be loaded (and can '
                         'be loaded using the GUI).')
    ns = ap.parse_args()
    if ns.editor:
        top, gui = ui.ResourceMazeEditor.create_editor()
    else:
        top, gui = ui.SolutionViewer.create_viewer()
        if ns.solution is not None:
            gui.after(1, gui.load_solution, ns.solution[0])
    if ns.maze is not None:
        gui.load_maze(ns.maze[0])
    # noinspection PyUnresolvedReferences
    top.mainloop()
