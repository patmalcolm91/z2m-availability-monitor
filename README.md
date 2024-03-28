# Zigbee2MQTT Device Availability Monitor

A simple daemon that monitors the availability of Zigbee2MQTT devices and sends a list
of unavailable devices to an OpenHAB string item.

The configured OpenHAB string item will be populated with a list of device names separated
by commas and a space (e.g. "device1, device2, device3").

## Setup
* Enable the "availability" feature of Zigbee2MQTT
* Create a String-type OpenHAB item to which the offline device list will be sent
* Build and run this script once (either directly or with docker or docker-compose)
  to generate a default ``data/config.yaml`` file.
* Update the parameters in the config file to match your setup.
* Run the daemon (either directly or with docker or docker-compose)

## Docker-Compose Sample Config
```yaml
version: '3'
services:
  z2m-availability-monitor:
    container_name: z2m-availability-monitor
    build:
      context: https://github.com/patmalcolm91/z2m-availability-monitor.git
    volumes:
      - ./data:/data
    restart: always
    network_mode: host
    environment:
      - TZ=Europe/Amsterdam
```

## OpenHAB Sample Config
Items File:
```
String z2m_offline_devices_list "Zigbee2MQTT Offline Device List"
String z2m_offline_devices_ignore "Zigbee2MQTT Offline Device Ignore List" (restoreOnStartup)
Switch z2m_devices_online "Zigbee2MQTT Device Availability  [%s]" (devicesonline)
```
where `restoreOnStartup` is a group whose items are all restored when OpenHAB restarted and
`devicesonline` is a group of items that indicate the availability of various services and devices.

Rules File:
```
rule "Check Z2M Devices Online"
when
	Item z2m_offline_devices_list changed or
	Item z2m_offline_devices_ignore changed
then
	val offlineDevicesList = z2m_offline_devices_list.state.toString.split(", ")
    val offlineDevicesIgnore = z2m_offline_devices_ignore.state.toString.split(", ")

    val offlineDevicesNotIgnored = offlineDevicesList.filter[device | !offlineDevicesIgnore.contains(device)]

    if (offlineDevicesNotIgnored.size > 0) {
        z2m_devices_online.sendCommand(OFF)
    } else {
        z2m_devices_online.sendCommand(ON)
    }
end
```

Sitemap File:
```
Text item=z2m_devices_online icon="switch" {
    Text item=z2m_offline_devices_list label="Offline Devices  [%s]"
    Input item=z2m_offline_devices_ignore label="Ignore List  [%s]"
}
```