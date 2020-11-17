#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


# ./mach run --app ../gecko-helpers/mach_run_remote.py --target hostname

import os
import subprocess
import sys

class RemoteTarget(object):
    def __init__(self, args):
        # Defaults
        self.remote_base = "/tmp/remote.mozrunner"
        self.app = 'firefox'

        # Remove this script.
        args.pop(0)

        self.app_args = []
        self.local_profile = None

        while args:
            arg = args.pop(0)
            if arg == "--target":
                self.remote_target = args.pop(0)
            elif arg == "--target-path":
                self.remote_base = args.pop(0)
            elif arg == "--target-app":
                self.app = args.pop(0)
            elif arg == "-profile":
                self.local_profile = args.pop(0)
            else:
                self.app_args.append(arg)

        if self.remote_target:
            print("Synchronizing with " + self.remote_target)
        else:
            print("No remote target to connect to: --target <REMOTE_TARGET>")

        if not self.local_profile:
            print("No profile detected, cannot deduce build folder")

        self.local_base = os.path.normpath(os.path.join(self.local_profile, "../.."))
        self.local_bin = os.path.join(self.local_base, "dist/bin")
        if not os.path.exists(self.local_bin):
            print("Cannot find dist at " + self.local_bin)

        self.remote_bin = os.path.join(self.remote_base, "bin")
        self.remote_profile = os.path.join(self.remote_base, "profile")

    def _rsync(self, src, dst):
        print("rsync " + src + " to " + dst)
        subprocess.check_call(
            [
                "rsync",
                "--info=progress2",
                "--copy-links",
                "-a",
                "-p",
                "-E",
                "-r",
                "-e",
                "ssh",
                src + "/",
                dst,
            ]
        )

    def _ssh_target(self, command):
        subprocess.check_call(
            ["ssh", self.remote_target, command]
        )

    def _rsync_remote_path(self, path):
        return self.remote_target + ":" + path

    def _rsync_remote(self, local_path, remote_path):
        self._ssh_target("mkdir -p " + remote_path)
        self._rsync(local_path, self._rsync_remote_path(remote_path))

    def _rsync_local(self, local_path, remote_path):
        self._rsync(self._rsync_remote_path(remote_path), local_path)

    def rsync_remote_bin(self):
        self._rsync_remote(self.local_bin, self.remote_bin)

    def rsync_remote_profile(self):
        self._rsync_remote(self.local_profile, self.remote_profile)

    def rsync_local_profile(self):
        self._rsync_local(self.local_profile, self.remote_profile)

    def execute_remote(self):
        app_args = ["DISPLAY=:0", os.path.join(self.remote_bin, self.app), "-profile", self.remote_profile]
        app_args.extend(self.app_args)
        app_command = " ".join(app_args)
        print("execute `" + app_command + "`")
        self._ssh_target(app_command)

remote = RemoteTarget(sys.argv)
remote.rsync_remote_bin()
remote.rsync_remote_profile()
remote.execute_remote()
remote.rsync_local_profile()
