"""
Support for monitoring the state of Proxmox VMs.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.proxmox/
"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA)
from custom_components.proxmox import DOMAIN as PROXMOX_DOMAIN ###

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = 'Data provided by Proxmox'
DEFAULT_DEVICE_CLASS = 'power'
DEFAULT_NAME = 'Proxmox {}' ###
DEPENDENCIES = ['proxmox']


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Proxmox binary sensors."""
    if discovery_info is None:
        return

    proxmox = hass.data[PROXMOX_DOMAIN]
    _LOGGER.debug('Proxmox setup platform: %s', proxmox)

    vms = []
    for vm in proxmox._api.cluster.resources.get(type='vm'):
        _LOGGER.debug('Proxmox loaded the following VM: %s', vm)
        vms.append(ProxmoxBinarySensor(proxmox, vm))
    _LOGGER.debug('Proxmox has following vms: %s', vms)

    # if node not in proxmox.data:
    #     _LOGGER.debug("Node %s not found", node)
    #     return

    add_entities(vms, True)
    return True


class ProxmoxBinarySensor(BinarySensorDevice):
    """Representation of a Proxmox VM binary sensor."""

    def __init__(self, proxmox, vm):
        """Initialize a new self._vmid binary sensor."""
        self._proxmox = proxmox
        self._vmid = vm['vmid']
        self._vmname = vm['name']
        self._status = vm['status']
        self._maxdisk = vm['maxdisk']
        self._template = vm['template']
        self._type = vm['type']
        self._name = '{} ({})'.format(self._vmname, self._vmid)
        self._unique_id = '{}_{}_{}'.format(PROXMOX_DOMAIN, self._name, int(self._vmid)*10) ###

        self.data = None

    @property
    def unique_id(self):
        """Return the unique ID of the binary sensor."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon of this VM."""
        return 'mdi:server-network' if self.is_on else 'mdi:server-network-off'

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._status == 'running'

    @property
    def _vm(self):
        """Return the VM."""
        return self._proxmox.get_vm(self._vmid)
    
    @property
    def device_class(self):
        """Return the class of this sensor."""
        return DEFAULT_DEVICE_CLASS

    @property
    def device_state_attributes(self):
        """Return the state attributes of the Proxmox VM."""
        return {
            'vmid': self._vmid,
            'type': self._type,
            'disk size': '{} {}'.format(round(self._maxdisk/1073741824,2), 'GB'),
            'template': True if self._template == 1 else False,
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    def update(self):
        """Update state of binary sensor."""
        # my_item = next((vm for vm in my_list if vm['vmid'] == self._vmid), None)
        self.data = self._proxmox._api.cluster.resources.get(type='vm')
        #_LOGGER.error('Proxmox sensor data loaded the following VMs: %s', self.data)
        vm = next((vm for vm in self.data if vm['vmid'] == self._vmid), None)
        _LOGGER.error('Proxmox binary sensor data loaded the following VM: %s', vm)
        self.data = vm

