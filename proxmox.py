"""
Support for Proxmox.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/proxmox/
"""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL)
from homeassistant.helpers import discovery
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['proxmoxer==1.0.2']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'proxmox'
UPDATE_TOPIC = DOMAIN
ERROR_TOPIC = DOMAIN + "_error"

NOTIFICATION_ID = 'proxmox_notification'
NOTIFICATION_TITLE = 'Proxmox Setup'

PROXMOX_COMPONENTS = ['binary_sensor', 'sensor']

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=2)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_VERIFY_SSL, default=False): cv.boolean,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the Proxmox component."""
    user = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    host = config[DOMAIN].get(CONF_HOST)
    verify_ssl = config[DOMAIN].get(CONF_VERIFY_SSL)

    proxmox = Proxmox(user, password, host, verify_ssl)
    _LOGGER.debug('Proxmox loaded in setup: %s', proxmox)

    try:
        proxmox.update()
    except Exception as ex:
        _LOGGER.debug("Failed to make update API request because: %s",
                      ex)
        hass.components.persistent_notification.create(
            'Error: {}'
            ''.format(ex),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)
        return False

    hass.data[DOMAIN] = proxmox
    _LOGGER.debug('Proxmox loaded in setup part 2: %s', hass.data[DOMAIN])

    for component in PROXMOX_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True


class Proxmox:
    """Handle all communication with the Proxmox API."""

    def __init__(self, user, password, host, verify_ssl):
        """Initialize the Proxmox connection."""
        from proxmoxer import ProxmoxAPI

        self.data = None # Gebruiken voor automatisch verversen

        try:
            self._api = ProxmoxAPI(host, user=user, password=password, verify_ssl=verify_ssl)
            _LOGGER.error('Proxmox init in class: %s', self._api)
        except: # noqa: E722 pylint: disable=bare-except
            _LOGGER.error("Error setting up connection with Proxmox server")
        # self._user = user
        # self._password = password
        # self._host = host
        # self._verify_ssl = verify_ssl

    # @property
    # def status(self):
    #     """Get latest update if throttle allows. Return status."""
    #     self.update()
    #     return self._status

    # def _get_status(self):
    #     """Get the status from APCUPSd and parse it into a dict."""
    #     return proxmox.nodes.proxmox_node()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update data from Proxmox API."""
        self.data = self._api.cluster.resources.get(type='vm')
        _LOGGER.error('Updating Proxmox data: %s', self.data)

    def get_vm(self, vmid):
        """Compatibility to work with one VM."""
        if self.data:
            # https://stackoverflow.com/questions/7079241/python-get-a-dict-from-a-list-based-on-something-inside-the-dict
            vm = next((vm for vm in self.data if vm['vmid'] == vmid), None)
            _LOGGER.error('Updating Proxmox VM: %s', vm)
            return vm
        return None
