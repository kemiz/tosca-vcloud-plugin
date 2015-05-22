import mock
import unittest

from cloudify import exceptions as cfy_exc
from cloudify import mocks as cfy_mocks
from server_plugin import volume
import vcloud_plugin_common
import test_mock_base
import network_plugin


class ServerPluginServerMockTestCase(test_mock_base.TestBase):

    def test_creation_validation_external_resource(self):
        fake_client = self.generate_client()
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': True,
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        # use external without resorse_id
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with self.assertRaises(cfy_exc.NonRecoverableError):
                volume.creation_validation(ctx=fake_ctx)
        fake_client.get_disks.assert_called_with('vdc_name')
        # with resource id, but without disks(no disks for this client)
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': True,
                'resource_id': 'some',
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with self.assertRaises(cfy_exc.NonRecoverableError):
                volume.creation_validation(ctx=fake_ctx)
        # good case for external resource
        fake_client.get_disks = mock.MagicMock(return_value=[
            [
                self.generate_fake_client_disk('some'),
                self.generate_fake_vms_disk('some')
            ]
        ])
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            volume.creation_validation(ctx=fake_ctx)

    def test_creation_validation_internal(self):
        fake_client = self.generate_client()
        # internal resource without volume
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': False,
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with self.assertRaises(cfy_exc.NonRecoverableError):
                volume.creation_validation(ctx=fake_ctx)
        fake_client.get_disks.assert_called_with('vdc_name')
        # internal resourse wit volume and name,
        # but already exist such volume
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': False,
                'volume': {
                    'name': 'some'
                },
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        fake_client.get_disks = mock.MagicMock(return_value=[
            [
                self.generate_fake_client_disk('some'),
                self.generate_fake_vms_disk('some')
            ]
        ])
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with self.assertRaises(cfy_exc.NonRecoverableError):
                volume.creation_validation(ctx=fake_ctx)
        # correct name but without size
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': False,
                'volume': {
                    'name': 'some-other'
                },
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with self.assertRaises(cfy_exc.NonRecoverableError):
                volume.creation_validation(ctx=fake_ctx)
        # good case
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': False,
                'volume': {
                    'name': 'some-other',
                    'size': 11
                },
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            volume.creation_validation(ctx=fake_ctx)

    def test_delete_volume(self):
        fake_client = self.generate_client()
        # external resource
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': True,
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            volume.delete_volume(ctx=fake_ctx)
        # cant't add disk
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': False,
                'volume': {
                    'name': 'some-other',
                    'size': 11
                },
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with self.assertRaises(cfy_exc.NonRecoverableError):
                volume.delete_volume(ctx=fake_ctx)
        fake_client.delete_disk.assert_called_with(
            'vdc_name', 'some-other'
        )
        # positive case
        fake_client.delete_disk = mock.MagicMock(
            return_value=(True, self.generate_task(
                vcloud_plugin_common.TASK_STATUS_SUCCESS
            )
        ))
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            volume.delete_volume(ctx=fake_ctx)

    def test_create_volume(self):
        fake_client = self.generate_client()
        # external resource
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': True,
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            volume.create_volume(ctx=fake_ctx)
        #fail on create volume
        fake_ctx = cfy_mocks.MockCloudifyContext(
            node_id='test',
            node_name='test',
            properties={
                'use_external_resource': False,
                'volume': {
                    'name': 'some-other',
                    'size': 11
                },
                'vcloud_config': {
                    'vdc': 'vdc_name'
                }
            }
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with self.assertRaises(cfy_exc.NonRecoverableError):
                volume.create_volume(ctx=fake_ctx)
        fake_client.add_disk.assert_called_with(
            'vdc_name', 'some-other', 11534336
        )
        # positive case
        disk = mock.Mock()
        disk.get_Tasks = mock.MagicMock(
            return_value=[self.generate_task(
                vcloud_plugin_common.TASK_STATUS_SUCCESS
            )]
        )
        fake_client.add_disk = mock.MagicMock(
            return_value=(True, disk)
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            volume.create_volume(ctx=fake_ctx)

    def test_volume_operation_attach(self):
        fake_client = self.generate_client()
        fake_ctx = self.generate_relation_context()
        # use external resource, no disks
        fake_ctx._target.node.properties = {
            'volume': {
                'name': 'some'
            },
            'use_external_resource': True,
            'resource_id': 'some'
        }
        fake_ctx._source.node.properties = {
            'vcloud_config': {
                'vdc': 'vdc_name',
            }
        }
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with mock.patch(
                'vcloud_plugin_common.ctx', fake_ctx
            ):
                with mock.patch(
                    'server_plugin.volume.ctx', fake_ctx
                ):
                    volume._volume_operation(fake_client, 'ATTACH')
        fake_client.get_diskRefs.assert_called_with(
            fake_client._app_vdc
        )
        # disk exist, can't attach
        disk_ref = self.generate_fake_client_disk_ref('some')
        fake_client.get_diskRefs = mock.MagicMock(return_value=[
            disk_ref
        ])
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with mock.patch(
                'vcloud_plugin_common.ctx', fake_ctx
            ):
                with mock.patch(
                    'server_plugin.volume.ctx', fake_ctx
                ):
                    with self.assertRaises(cfy_exc.NonRecoverableError):
                        volume._volume_operation(fake_client, 'ATTACH')
        fake_client._vapp.attach_disk_to_vm.assert_called_with(
            'some', disk_ref
        )
        # disk exist, can't detach
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with mock.patch(
                'vcloud_plugin_common.ctx', fake_ctx
            ):
                with mock.patch(
                    'server_plugin.volume.ctx', fake_ctx
                ):
                    with self.assertRaises(cfy_exc.NonRecoverableError):
                        volume._volume_operation(fake_client, 'DETACH')
        fake_client._vapp.detach_disk_from_vm.assert_called_with(
            'some', disk_ref
        )
        # wrong operation
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with mock.patch(
                'vcloud_plugin_common.ctx', fake_ctx
            ):
                with mock.patch(
                    'server_plugin.volume.ctx', fake_ctx
                ):
                    with self.assertRaises(cfy_exc.NonRecoverableError):
                        volume._volume_operation(fake_client, 'Wrong')
        # disk exist, can attach
        fake_client._vapp.attach_disk_to_vm = mock.MagicMock(
            return_value=self.generate_task(
                vcloud_plugin_common.TASK_STATUS_SUCCESS
            )
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with mock.patch(
                'vcloud_plugin_common.ctx', fake_ctx
            ):
                with mock.patch(
                    'server_plugin.volume.ctx', fake_ctx
                ):
                    volume._volume_operation(fake_client, 'ATTACH')
        # disk exist, can detach
        fake_client._vapp.detach_disk_from_vm = mock.MagicMock(
            return_value=self.generate_task(
                vcloud_plugin_common.TASK_STATUS_SUCCESS
            )
        )
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with mock.patch(
                'vcloud_plugin_common.ctx', fake_ctx
            ):
                with mock.patch(
                    'server_plugin.volume.ctx', fake_ctx
                ):
                    volume._volume_operation(fake_client, 'DETACH')
        # disk exist, use internal resource
        fake_ctx._target.node.properties = {
            'volume': {
                'name': 'some'
            },
            'use_external_resource': False
        }
        fake_ctx._source.instance.runtime_properties = {
            network_plugin.VCLOUD_VAPP_NAME: "some_other"
        }
        with mock.patch(
            'vcloud_plugin_common.VcloudAirClient.get',
            mock.MagicMock(return_value=fake_client)
        ):
            with mock.patch(
                'vcloud_plugin_common.ctx', fake_ctx
            ):
                with mock.patch(
                    'server_plugin.volume.ctx', fake_ctx
                ):
                    volume._volume_operation(fake_client, 'DETACH')
        fake_client._vapp.detach_disk_from_vm.assert_called_with(
            'some_other', disk_ref
        )

if __name__ == '__main__':
    unittest.main()
