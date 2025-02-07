"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
   TC to check split brain in glusterd with quorum set
"""

from tests.d_parent_test import DParentTest

# disruptive;


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        - On a 6 node cluster
        - Create a volume using first four nodes
        - Set the volumes options
        - Stop two gluster nodes
        - Perform gluster vol reset
        - Start the glusterd on the nodes where it stopped
        - Check the peer status, all the nodes should be in connected state

        """
        # Check server requirements
        self.redant.check_hardware_requirements(self.server_list, 6)

        # Create a dist-rep volume using first 4 nodes
        conf_hash = {
            "dist_count": 2,
            "replica_count": 3,
            "transport": "tcp"
        }
        self.volname = f"{self.test_name}-{self.volume_type}"
        redant.setup_volume(self.volname, self.server_list[0],
                            conf_hash, self.server_list[-2:],
                            self.brick_roots)

        # Volume options to set on the volume
        volume_options = {
            'nfs.disable': 'off',
            'auth.allow': '1.1.1.1',
            'nfs.rpc-auth-allow': '1.1.1.1',
            'nfs.addr-namelookup': 'on',
            'cluster.server-quorum-type': 'server',
            'network.ping-timeout': '20',
            'nfs.port': '2049',
            'performance.nfs.write-behind': 'on',
        }

        # Set the volume options
        redant.set_volume_options(self.volname, volume_options,
                                  self.server_list[0])

        # Stop glusterd on two gluster nodes where bricks aren't present
        redant.stop_glusterd(self.server_list[-2:])

        # Check glusterd is stopped
        if not redant.wait_for_glusterd_to_stop(self.server_list[-2:]):
            raise Exception("Glusterd is still running on nodes: "
                            f"{self.server_list[-2:]}")

        # Performing volume reset on the volume to remove all the volume
        # options set earlier
        redant.volume_reset(self.volname, self.server_list[0])

        # Bring back glusterd online on the nodes where it stopped earlier
        redant.start_glusterd(self.server_list[-2:])

        # Check peer status whether all peer are in connected state none of the
        # nodes should be in peer rejected state
        if not redant.wait_till_all_peers_connected(self.server_list):
            raise Exception("Peers are not connected state after "
                            "bringing back glusterd online on the "
                            "nodes in which previously glusterd "
                            "had been stopped")
