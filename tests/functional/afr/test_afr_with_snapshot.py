"""
 Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    Test cases related to afr snapshot.
"""

# disruptive;rep,dist-rep
# TODO: NFS, CIFS
from time import sleep
from tests.d_parent_test import DParentTest


class TestAFRSnapshot(DParentTest):

    def run_test(self, redant):
        """
        Test entry transaction crash consistency : create

        Description:
        - Create IO
        - Calculate arequal before creating snapshot
        - Create snapshot
        - Modify the data
        - Stop the volume
        - Restore snapshot
        - Start the volume
        - Get arequal after restoring snapshot
        - Compare arequals
        """
        script_file_path = "/usr/share/redant/file_dir_ops.py"
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Creating files on client side
        count = 1
        for mount_obj in self.mounts:
            cmd = (f"python3 {script_file_path} create_files -f 200 "
                   f"--base-file-name file_{count} {mount_obj['mountpath']}")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10

        # Wait for IO to complete
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed to complete on some of the clients")

        # Get arequal before creating snapshot
        result_before_snapshot = redant.collect_mounts_arequal(self.mounts)

        # Create snapshot
        snapshot_name = ("entry_transaction_crash_consistency_create-"
                         f"{self.vol_name}-fuse")
        redant.snap_create(self.vol_name, snapshot_name, self.server_list[0])

        # Modify the data
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            cmd = (f"python3 {script_file_path} append "
                   f"{mount_obj['mountpath']}")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Wait for IO to complete
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed to complete on some of the clients")

        # Restore snapshot
        ret = redant.snap_restore_complete(self.vol_name, snapshot_name,
                                           self.server_list[0])
        if not ret:
            raise Exception(f"Failed to restore snapshot {snapshot_name}")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception('Heal is not complete')

        # Wait for volume graph to get loaded.
        sleep(10)

        # Get arequal after restoring snapshot
        result_after_restoring = redant.collect_mounts_arequal(self.mounts)

        # Checking arequal before creating snapshot
        # and after restoring snapshot
        if result_before_snapshot != result_after_restoring:
            raise Exception('Checksums are not equal')
