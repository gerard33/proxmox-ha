"""
Support for monitoring the state of Proxmox VMs.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/sensor.proxmox/
"""
from datetime import timedelta
import logging

from homeassistant.const import ATTR_ATTRIBUTION
from custom_components.proxmox import DOMAIN as PROXMOX_DOMAIN ###
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = 'Data provided by Proxmox'
DEFAULT_NAME = 'Proxmox {}' ###
DEPENDENCIES = ['proxmox']

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=2)

SENSORS = {
    'cpu': ['mdi:chip', '%'],
    'mem': ['mdi:memory', '%'],
    'uptime': ['mdi:clock', 'days'],
    #'netin': ['mdi:download-network', 'Kbps'],
    #'netout': ['mdi:upload-network', 'Kbps'],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Proxmox sensors."""
    if discovery_info is None:
        return

    proxmox = hass.data[PROXMOX_DOMAIN]
    _LOGGER.debug('Proxmox setup sensor platform: %s', proxmox)

    vms = []
    for sensor in SENSORS:
        for vm in proxmox._api.cluster.resources.get(type='vm'):
            # No sensor when VM is off
            if vm['status'] == 'running':
                _LOGGER.debug('Proxmox sensor loaded the following VM: %s', vm)
                vms.append(ProxmoxSensor(proxmox, sensor, vm))
    _LOGGER.debug('Proxmox sensor has following vms: %s', vms)

    # if node not in proxmox.data:
    #     _LOGGER.debug("Node %s not found", node)
    #     return

    add_entities(vms, True)
    return True


class ProxmoxSensor(Entity):
    """Representation of a Proxmox VM sensor."""

    def __init__(self, proxmox, sensor, vm):
        """Initialize a new self._vmid binary sensor."""
        self._proxmox = proxmox
        self._sensor = sensor ### naam aanpassen naar attribute
        self._vmid = vm['vmid']
        self._vmname = vm['name']
        self._status = vm['status']
        self._cpu = vm['cpu']
        self._maxcpu = vm['maxcpu']
        self._uptime = vm['uptime']
        self._mem = vm['mem']
        self._maxmem = vm['maxmem']
        self._netin = vm['netin']
        self._netout = vm['netout']
        self._state = None
        self._name = '{} {} ({})'.format(self._vmname, self._sensor, self._vmid)
        self._unique_id = '{}_{}_{}'.format(PROXMOX_DOMAIN, self._name, int(self._vmid)*20) ###

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
        icon, _ = SENSORS.get(self._sensor, [None, None])
        return icon

    @property ##
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property ##
    def unit_of_measurement(self) -> str:
        """Get the unit of measurement."""
        _, unit = SENSORS.get(self._sensor, [None, None])
        return unit

    @property
    def _vm(self):
        """Return the VM."""
        return self._proxmox.get_vm(self._vmid)

    @property
    def device_state_attributes(self):
        """Return the state attributes of the Proxmox VM."""
        result = {
            'vmid': self._vmid,
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

        if self._sensor == 'cpu':
            result['max # cpu'] = self._maxcpu
        elif self._sensor == 'mem':
            result['memory used'] = '{} GiB of {} GiB'.format(round(self._mem/1073741824,2), round(self._maxmem/1073741824,2))

        return sorted(result.items())

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update state of binary sensor."""
        ## my_item = next((vm for vm in my_list if vm['vmid'] == self._vmid), None)
        # self.data = self._proxmox._api.cluster.resources.get(type='vm')
        ##_LOGGER.error('Proxmox sensor data loaded the following VMs: %s', self.data)
        # vm = next((vm for vm in self.data if vm['vmid'] == self._vmid), None)
        #_LOGGER.error('Proxmox sensor data loaded the following VM: %s', vm)
        #self.data = vm

        #self.data = self._proxmox.get_vm(self._vmid)
        self.data = self._proxmox._api.cluster.resources.get(type='vm')
        vm = next((vm for vm in self.data if vm['vmid'] == self._vmid), None)
        _LOGGER.error('Proxmox VM sensor: %s loaded: %s', self._vmid, vm)

        # No updates when VM is off
        if vm['status'] == 'running':
            if self._sensor == 'cpu':
                self._state = round(vm['cpu']*100,2)
            elif self._sensor == 'mem':
                self._state = round(vm['mem']/vm['maxmem']*100,2)
            elif self._sensor == 'uptime':
                self._state = round(vm['uptime']/86400, 2)
            elif self._sensor == 'netin':
                self._state = round(vm['netin']/1000,2)
            elif self._sensor == 'netout':
                self._state = round(vm['netout']/1000,2)
