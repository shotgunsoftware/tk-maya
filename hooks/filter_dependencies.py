# Copyright 2017 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

import sgtk


class FilterDependenciesHook(sgtk.get_hook_baseclass()):
    """
    Hook to filter file dependencies gathered from a
    session. Use this hook to add or remove custom file
    dependencies for specialized requirements.
    """

    def filter_dependencies(self, dependencies):
        """
        Performs filtering of file dependency data and
        returns the filtered list. It extends
        `Engine.get_session_dependencies()` to perform any
        post-processing on dependency data.

        :param dependencies: A list of file dependencies
                    gathered from a session. The data is
                    of the form:
                    [
                     { "path": "/foo/bar/hello.jpeg",
                       "engine": "tk-maya",
                       "type": "reference"
                     },
                     { "path": "/foo/bar/hello.obj",
                       "engine": "tk-maya",
                       "type": "file"
                     },
                   ]
        :returns: A new list containing filtered file
                  dependency data.
        """
        # Generate and return a new list with modified
        # file dependency data. For now, simply return a copy
        # of the existing dependency list back to the caller.
        return dependencies[:]
