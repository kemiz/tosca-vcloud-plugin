import mock
import unittest

from cloudify import exceptions as cfy_exc
import test_mock_base
from network_plugin import security_group
from vcloud_plugin_common import TASK_STATUS_SUCCESS, TASK_STATUS_ERROR


class NetworkPluginSecurityGroupMockTestCase(test_mock_base.TestBase):
    pass


if __name__ == '__main__':
    unittest.main()