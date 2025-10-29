# Muli Integration for Home Assistant

A Home Assistant integration for [Muli electric cargo bikes](https://muli-cycles.de/en), providing real-time monitoring and control of your bike's status, location, and security features.

## About Muli

Muli manufactures electric cargo bikes designed for urban transportation and family use. This integration connects to the Muli cloud API (powered by Velco) to provide monitoring and control capabilities within Home Assistant.

## Features

This integration provides the following platforms and entities:

### Sensors

- **Battery** - Main bike battery level (%)
- **Total Mileage** - Odometer reading in kilometers
- **Remaining Distance** - Estimated range in kilometers
- **Battery Cycles** - Total number of charge cycles
- **Assistance Level** - Current electric assistance level
- **Speed** - Current speed in km/h
- **Status** - Product status information
- **Firmware Version** (Diagnostic) - Bike firmware version
- **Hardware Version** (Diagnostic) - Bike hardware version
- **GPS Tracker Battery** (Diagnostic) - GPS tracker battery level (%)

### Switches

- **Armed** - Arm or disarm the bike's security alarm
- **Movement Alarm** - Enable or disable movement detection alarm

### Binary Sensors

- **Alarm** - Indicates if the security alarm has been triggered

### Device Tracker

- **Location** - Real-time GPS tracking of your bike with attributes:
  - GPS signal status
  - Last position timestamp
  - Last signal timestamp

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots menu (⋮) in the top right
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/jharting/home-assistant-muli`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Muli" in HACS and click "Download"
9. Restart Home Assistant
10. Go to **Settings** → **Devices & Services** → **Add Integration** → Search for "Muli"

### Manual Installation

1. Download the latest release from the [GitHub releases page](https://github.com/jharting/home-assistant-muli/releases)
2. Extract the `custom_components/mulibikes` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration** → Search for "Muli"

## Configuration

### Initial Setup

1. When adding the integration, you'll be prompted to enter:
   - **Email**: Your Muli account email address
   - **Password**: Your Muli account password

2. The integration will authenticate with the Muli cloud API and automatically discover your bike

### Reauthentication

If your authentication tokens expire, Home Assistant will prompt you to re-enter your credentials. Simply:

1. Click on the notification
2. Re-enter your email and password
3. The integration will refresh your tokens and resume normal operation

## Entities Reference

| Entity              | Type           | Unit | Description                            |
| ------------------- | -------------- | ---- | -------------------------------------- |
| Battery             | Sensor         | %    | Main bike battery level                |
| Total Mileage       | Sensor         | km   | Total distance traveled (odometer)     |
| Remaining Distance  | Sensor         | km   | Estimated remaining range              |
| Battery Cycles      | Sensor         | -    | Number of battery charge cycles        |
| Assistance Level    | Sensor         | -    | Current electric assistance level      |
| Speed               | Sensor         | km/h | Current speed                          |
| Status              | Sensor         | -    | Product status information             |
| Firmware Version    | Sensor         | -    | Bike firmware version (diagnostic)     |
| Hardware Version    | Sensor         | -    | Bike hardware version (diagnostic)     |
| GPS Tracker Battery | Sensor         | %    | GPS tracker battery level (diagnostic) |
| Armed               | Switch         | -    | Security alarm armed/disarmed          |
| Movement Alarm      | Switch         | -    | Movement detection enabled/disabled    |
| Alarm               | Binary Sensor  | -    | Alarm triggered state                  |
| Location            | Device Tracker | -    | Real-time GPS location                 |

## Update Intervals

- **Main Data**: Updated every 30 seconds (battery, speed, location, etc.)
- **Bike Details**: Updated every 30 minutes (firmware, hardware versions)

## Automation Examples

### Send notification when alarm is triggered

```yaml
automation:
  - alias: "Muli Alarm Triggered"
    trigger:
      - platform: state
        entity_id: binary_sensor.muli_bike_alarm
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Your Muli bike alarm has been triggered!"
          title: "Bike Alert"
```

### Notify when battery is low

```yaml
automation:
  - alias: "Muli Low Battery"
    trigger:
      - platform: numeric_state
        entity_id: sensor.muli_bike_battery
        below: 20
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Your Muli bike battery is below 20%"
          title: "Low Battery"
```

### Automatically arm alarm at night

```yaml
automation:
  - alias: "Arm Muli at Night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.muli_bike_armed
```

## API Information

This integration uses the Velco API (`vr-api.velco.bike`) which powers Muli bikes. The integration:

- Authenticates using JWT tokens
- Automatically refreshes access tokens when they expire
- Implements proper error handling and reauthentication flows
- Respects API rate limits with appropriate polling intervals

## Contributing

Contributions are welcome! Please see [DEVELOPERS.md](DEVELOPERS.md) for technical documentation and contribution guidelines.

## License

This integration is licensed under the [Apache License 2.0](LICENSE).

## Support

For issues, feature requests, or questions:

- **GitHub Issues**: [Report bugs or request features](https://github.com/jharting/home-assistant-muli/issues)
- **Documentation**: See this README and [DEVELOPERS.md](DEVELOPERS.md)

## Credits

Developed for the Home Assistant community.

- **API Provider**: Velco
- **Bike Manufacturer**: Muli
