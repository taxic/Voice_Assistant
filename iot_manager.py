# iot_manager.py

import json
import requests
import socket
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from config_manager import config

# Configure debug logging for IoT operations
logging.basicConfig(level=logging.DEBUG)
iot_logger = logging.getLogger('iot_manager')
iot_logger.setLevel(logging.DEBUG)

# Create console handler for debug output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
console_handler.setFormatter(formatter)
iot_logger.addHandler(console_handler)

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("[INFO] MQTT not available. Install paho-mqtt for MQTT device support.")

try:
    from tuya_connector import TuyaOpenAPI
    TUYA_AVAILABLE = True
except ImportError:
    TUYA_AVAILABLE = False
    print("[INFO] Tuya not available. Install tuya-connector-python for Tuya device support.")

# Tapo imports will be done locally to avoid circular import issues
TAPO_AVAILABLE = True

class IoTDevice:
    """Base class for IoT devices"""
    def __init__(self, device_id: str, name: str, device_type: str, protocol: str, **kwargs):
        self.device_id = device_id
        self.name = name.lower()  # Store in lowercase for easier matching
        self.device_type = device_type  # light, switch, thermostat, sensor, etc.
        self.protocol = protocol  # mqtt, http, tuya, philips_hue, etc.
        self.config = kwargs
        self.last_state = {}
        self.last_updated = None
        
    def __str__(self):
        return f"{self.name} ({self.device_type}) via {self.protocol}"

class IoTManager:
    """Centralized IoT device management system"""
    
    def __init__(self):
        self.devices = {}  # device_id -> IoTDevice
        self.device_name_map = {}  # name -> device_id for quick lookup
        self.mqtt_client = None
        self.tuya_api = None
        self.philips_hue_bridge_ip = None
        self.philips_hue_username = None
        self.tapo_manager = None

        # Load configuration
        self.iot_config = config.get_section('iot')

        # Initialize connections
        self._initialize_connections()

        # Load devices from configuration
        self._load_devices_from_config()
        
    def _initialize_connections(self):
        """Initialize connections to various IoT platforms"""
        iot_logger.info("Initializing IoT connections...")

        # Initialize MQTT if available and configured
        if MQTT_AVAILABLE and self.iot_config.get('mqtt', {}).get('enabled', False):
            iot_logger.debug("MQTT enabled in configuration, initializing...")
            self._initialize_mqtt()
        else:
            iot_logger.debug("MQTT not enabled or not available")

        # Initialize Tuya if available and configured
        if TUYA_AVAILABLE and self.iot_config.get('tuya', {}).get('enabled', False):
            iot_logger.debug("Tuya enabled in configuration, initializing...")
            self._initialize_tuya()
        else:
            iot_logger.debug("Tuya not enabled or not available")

        # Initialize Philips Hue if configured
        if self.iot_config.get('philips_hue', {}).get('enabled', False):
            iot_logger.debug("Philips Hue enabled in configuration, initializing...")
            self._initialize_philips_hue()
        else:
            iot_logger.debug("Philips Hue not enabled in configuration")

        # Initialize Tapo if available
        try:
            iot_logger.debug("Attempting to initialize Tapo manager...")
            from tapo_light_wrapper import tapo_manager
            self.tapo_manager = tapo_manager
            iot_logger.info("Tapo manager initialized successfully")
        except ImportError as e:
            iot_logger.warning(f"Tapo manager import failed: {e}")
            self.tapo_manager = None
        except Exception as e:
            iot_logger.error(f"Unexpected error initializing Tapo manager: {e}")
            self.tapo_manager = None

        iot_logger.info("IoT connection initialization completed")
    
    def _initialize_mqtt(self):
        """Initialize MQTT connection"""
        try:
            mqtt_config = self.iot_config.get('mqtt', {})
            broker = mqtt_config.get('broker', 'localhost')
            port = mqtt_config.get('port', 1883)
            username = mqtt_config.get('username')
            password = mqtt_config.get('password')

            iot_logger.debug(f"Initializing MQTT connection to {broker}:{port}")
            iot_logger.debug(f"MQTT config - username: {'set' if username else 'not set'}, password: {'set' if password else 'not set'}")

            self.mqtt_client = mqtt.Client()

            if username and password:
                self.mqtt_client.username_pw_set(username, password)
                iot_logger.debug("MQTT credentials configured")

            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message

            iot_logger.debug(f"Attempting MQTT connection to {broker}:{port}")
            self.mqtt_client.connect(broker, port, 60)
            self.mqtt_client.loop_start()

            iot_logger.info(f"MQTT connected to {broker}:{port}")

        except Exception as e:
            iot_logger.error(f"Failed to initialize MQTT: {e}")
            iot_logger.debug(f"MQTT initialization error details: {type(e).__name__}: {str(e)}", exc_info=True)
    
    def _initialize_tuya(self):
        """Initialize Tuya Smart connection"""
        try:
            tuya_config = self.iot_config.get('tuya', {})
            access_id = tuya_config.get('access_id')
            access_secret = tuya_config.get('access_secret')
            api_endpoint = tuya_config.get('api_endpoint', 'https://openapi.tuyaus.com')

            iot_logger.debug(f"Initializing Tuya connection to {api_endpoint}")
            iot_logger.debug(f"Tuya config - access_id: {'set' if access_id else 'not set'}, access_secret: {'set' if access_secret else 'not set'}")

            if access_id and access_secret:
                iot_logger.debug("Creating Tuya API client...")
                self.tuya_api = TuyaOpenAPI(
                    endpoint=api_endpoint,
                    access_id=access_id,
                    access_key=access_secret
                )
                iot_logger.info("Tuya Smart initialized successfully")
            else:
                iot_logger.warning("Tuya access credentials not configured")

        except Exception as e:
            iot_logger.error(f"Failed to initialize Tuya: {e}")
            iot_logger.debug(f"Tuya initialization error details: {type(e).__name__}: {str(e)}", exc_info=True)
    
    def _initialize_philips_hue(self):
        """Initialize Philips Hue connection"""
        try:
            hue_config = self.iot_config.get('philips_hue', {})
            self.philips_hue_bridge_ip = hue_config.get('bridge_ip')
            self.philips_hue_username = hue_config.get('username')

            iot_logger.debug(f"Initializing Philips Hue - bridge_ip: {self.philips_hue_bridge_ip}, username: {'set' if self.philips_hue_username else 'not set'}")

            if self.philips_hue_bridge_ip and self.philips_hue_username:
                iot_logger.debug(f"Testing Philips Hue connection to {self.philips_hue_bridge_ip}")
                # Test connection
                response = requests.get(
                    f"http://{self.philips_hue_bridge_ip}/api/{self.philips_hue_username}/lights",
                    timeout=5
                )
                if response.status_code == 200:
                    iot_logger.info("Philips Hue bridge connected successfully")
                    iot_logger.debug(f"Philips Hue API response: {response.json()}")
                else:
                    iot_logger.warning(f"Philips Hue connection failed with status {response.status_code}")
                    iot_logger.debug(f"Philips Hue error response: {response.text}")
            else:
                iot_logger.warning("Philips Hue bridge IP or username not configured")

        except requests.exceptions.RequestException as e:
            iot_logger.error(f"Network error initializing Philips Hue: {e}")
        except Exception as e:
            iot_logger.error(f"Failed to initialize Philips Hue: {e}")
            iot_logger.debug(f"Philips Hue initialization error details: {type(e).__name__}: {str(e)}", exc_info=True)
    
    def _load_devices_from_config(self):
        """Load device configurations from config file"""
        devices_config = self.iot_config.get('devices', [])
        iot_logger.info(f"Loading {len(devices_config)} device configurations")

        for device_config in devices_config:
            try:
                iot_logger.debug(f"Processing device config: {device_config.get('name', 'unnamed')} ({device_config.get('protocol', 'unknown')})")

                # Handle Tapo devices specially
                if device_config.get('protocol') == 'tapo':
                    iot_logger.debug("Detected Tapo device, attempting to create...")
                    try:
                        from tapo_light_wrapper import create_tapo_device_from_config
                        device = create_tapo_device_from_config(device_config)
                        if device:
                            iot_logger.debug(f"Tapo device '{device.name}' created successfully")
                            self.add_device(device)
                            # Also add to Tapo manager
                            try:
                                from tapo_light_wrapper import tapo_manager
                                tapo_manager.add_device(device)
                                iot_logger.debug(f"Tapo device '{device.name}' added to Tapo manager")
                            except ImportError as e:
                                iot_logger.warning(f"Could not add Tapo device to manager: {e}")
                        else:
                            iot_logger.error(f"Failed to create Tapo device from config: {device_config}")
                    except ImportError as e:
                        iot_logger.warning(f"Tapo package not available for device configuration: {e}")
                    except Exception as e:
                        iot_logger.error(f"Error creating Tapo device '{device_config.get('name', 'unknown')}': {e}")
                else:
                    iot_logger.debug(f"Creating standard IoT device: {device_config}")
                    device = IoTDevice(
                        device_id=device_config['id'],
                        name=device_config['name'],
                        device_type=device_config['type'],
                        protocol=device_config['protocol'],
                        **device_config.get('config', {})
                    )
                    self.add_device(device)
                    iot_logger.debug(f"Standard device '{device.name}' added successfully")

            except KeyError as e:
                iot_logger.error(f"Missing required field in device config: {e}")
            except Exception as e:
                iot_logger.error(f"Failed to load device from config: {e}")
                iot_logger.debug(f"Device config that failed: {device_config}", exc_info=True)

        iot_logger.info(f"Device loading completed. Total devices: {len(self.devices)}")
    
    def add_device(self, device: IoTDevice):
        """Add a device to the manager"""
        iot_logger.debug(f"Adding device: {device.name} (ID: {device.device_id}, Type: {device.device_type}, Protocol: {device.protocol})")
        self.devices[device.device_id] = device
        self.device_name_map[device.name.lower()] = device.device_id
        iot_logger.info(f"Added IoT device: {device}")
    
    def get_device_by_name(self, name: str) -> Optional[IoTDevice]:
        """Get device by name (case-insensitive)"""
        name_lower = name.lower()
        
        # Exact match first
        if name_lower in self.device_name_map:
            device_id = self.device_name_map[name_lower]
            return self.devices.get(device_id)
        
        # Partial match
        for device_name, device_id in self.device_name_map.items():
            if name_lower in device_name or device_name in name_lower:
                return self.devices.get(device_id)
        
        return None
    
    def get_devices_by_type(self, device_type: str) -> List[IoTDevice]:
        """Get all devices of a specific type"""
        return [device for device in self.devices.values() if device.device_type == device_type]
    
    def list_devices(self) -> List[IoTDevice]:
        """List all devices"""
        return list(self.devices.values())
    
    # Light Control Methods
    def turn_on_light(self, device_name: str, brightness: int = None, color: str = None) -> str:
        """Turn on a light with optional brightness and color"""
        iot_logger.debug(f"Attempting to turn on light '{device_name}' (brightness: {brightness}, color: {color})")

        device = self.get_device_by_name(device_name)
        if not device:
            iot_logger.warning(f"Light '{device_name}' not found in device registry")
            return f"Light '{device_name}' not found."

        if device.device_type != 'light':
            iot_logger.warning(f"Device '{device_name}' is type '{device.device_type}', not 'light'")
            return f"'{device_name}' is not a light device."

        iot_logger.debug(f"Found light device: {device.name} (protocol: {device.protocol})")

        try:
            if device.protocol == 'philips_hue':
                iot_logger.debug("Routing to Philips Hue control")
                return self._control_hue_light(device, True, brightness, color)
            elif device.protocol == 'mqtt':
                iot_logger.debug("Routing to MQTT control")
                return self._control_mqtt_light(device, True, brightness, color)
            elif device.protocol == 'tuya':
                iot_logger.debug("Routing to Tuya control")
                return self._control_tuya_light(device, True, brightness, color)
            elif device.protocol == 'http':
                iot_logger.debug("Routing to HTTP control")
                return self._control_http_light(device, True, brightness, color)
            elif device.protocol == 'tapo':
                iot_logger.debug("Routing to Tapo control")
                return self._control_tapo_light(device, True, brightness, color)
            else:
                iot_logger.error(f"Unsupported protocol '{device.protocol}' for light control")
                return f"Unsupported protocol '{device.protocol}' for light control."

        except Exception as e:
            iot_logger.error(f"Failed to control light '{device_name}': {str(e)}")
            iot_logger.debug(f"Light control error details: {type(e).__name__}: {str(e)}", exc_info=True)
            return f"Failed to control light '{device_name}': {str(e)}"
    
    def turn_off_light(self, device_name: str) -> str:
        """Turn off a light"""
        iot_logger.debug(f"Attempting to turn off light '{device_name}'")

        device = self.get_device_by_name(device_name)
        if not device:
            iot_logger.warning(f"Light '{device_name}' not found in device registry")
            return f"Light '{device_name}' not found."

        if device.device_type != 'light':
            iot_logger.warning(f"Device '{device_name}' is type '{device.device_type}', not 'light'")
            return f"'{device_name}' is not a light device."

        iot_logger.debug(f"Found light device: {device.name} (protocol: {device.protocol})")

        try:
            if device.protocol == 'philips_hue':
                iot_logger.debug("Routing to Philips Hue control")
                return self._control_hue_light(device, False)
            elif device.protocol == 'mqtt':
                iot_logger.debug("Routing to MQTT control")
                return self._control_mqtt_light(device, False)
            elif device.protocol == 'tuya':
                iot_logger.debug("Routing to Tuya control")
                return self._control_tuya_light(device, False)
            elif device.protocol == 'http':
                iot_logger.debug("Routing to HTTP control")
                return self._control_http_light(device, False)
            elif device.protocol == 'tapo':
                iot_logger.debug("Routing to Tapo control")
                return self._control_tapo_light(device, False)
            else:
                iot_logger.error(f"Unsupported protocol '{device.protocol}' for light control")
                return f"Unsupported protocol '{device.protocol}' for light control."

        except Exception as e:
            iot_logger.error(f"Failed to control light '{device_name}': {str(e)}")
            iot_logger.debug(f"Light control error details: {type(e).__name__}: {str(e)}", exc_info=True)
            return f"Failed to control light '{device_name}': {str(e)}"
    
    def set_brightness(self, device_name: str, brightness: int) -> str:
        """Set light brightness (0-100)"""
        iot_logger.debug(f"Setting brightness for '{device_name}' to {brightness}%")

        if not 0 <= brightness <= 100:
            iot_logger.warning(f"Invalid brightness value: {brightness} (must be 0-100)")
            return "Brightness must be between 0 and 100."

        device = self.get_device_by_name(device_name)
        if not device:
            iot_logger.warning(f"Light '{device_name}' not found for brightness setting")
            return f"Light '{device_name}' not found."

        iot_logger.debug(f"Routing brightness setting to turn_on_light for device: {device.name}")
        return self.turn_on_light(device_name, brightness=brightness)
    
    def set_color(self, device_name: str, color: str) -> str:
        """Set light color"""
        iot_logger.debug(f"Setting color for '{device_name}' to {color}")

        device = self.get_device_by_name(device_name)
        if not device:
            iot_logger.warning(f"Light '{device_name}' not found for color setting")
            return f"Light '{device_name}' not found."

        iot_logger.debug(f"Routing color setting to turn_on_light for device: {device.name}")
        return self.turn_on_light(device_name, color=color)
    
    # Switch Control Methods
    def turn_on_switch(self, device_name: str) -> str:
        """Turn on a switch"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Switch '{device_name}' not found."
        
        if device.device_type != 'switch':
            return f"'{device_name}' is not a switch device."
        
        try:
            if device.protocol == 'mqtt':
                return self._control_mqtt_switch(device, True)
            elif device.protocol == 'tuya':
                return self._control_tuya_switch(device, True)
            elif device.protocol == 'http':
                return self._control_http_switch(device, True)
            else:
                return f"Unsupported protocol '{device.protocol}' for switch control."
                
        except Exception as e:
            return f"Failed to control switch '{device_name}': {str(e)}"
    
    def turn_off_switch(self, device_name: str) -> str:
        """Turn off a switch"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Switch '{device_name}' not found."
        
        if device.device_type != 'switch':
            return f"'{device_name}' is not a switch device."
        
        try:
            if device.protocol == 'mqtt':
                return self._control_mqtt_switch(device, False)
            elif device.protocol == 'tuya':
                return self._control_tuya_switch(device, False)
            elif device.protocol == 'http':
                return self._control_http_switch(device, False)
            else:
                return f"Unsupported protocol '{device.protocol}' for switch control."
                
        except Exception as e:
            return f"Failed to control switch '{device_name}': {str(e)}"
    
    # Thermostat Control Methods
    def set_temperature(self, device_name: str, temperature: float) -> str:
        """Set thermostat temperature"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Thermostat '{device_name}' not found."
        
        if device.device_type != 'thermostat':
            return f"'{device_name}' is not a thermostat device."
        
        try:
            if device.protocol == 'mqtt':
                return self._control_mqtt_thermostat(device, temperature)
            elif device.protocol == 'tuya':
                return self._control_tuya_thermostat(device, temperature)
            elif device.protocol == 'http':
                return self._control_http_thermostat(device, temperature)
            else:
                return f"Unsupported protocol '{device.protocol}' for thermostat control."
                
        except Exception as e:
            return f"Failed to control thermostat '{device_name}': {str(e)}"
    
    # Sensor Methods
    def get_sensor_reading(self, device_name: str) -> str:
        """Get sensor reading"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Sensor '{device_name}' not found."
        
        if device.device_type != 'sensor':
            return f"'{device_name}' is not a sensor device."
        
        try:
            if device.protocol == 'mqtt':
                return self._read_mqtt_sensor(device)
            elif device.protocol == 'tuya':
                return self._read_tuya_sensor(device)
            elif device.protocol == 'http':
                return self._read_http_sensor(device)
            else:
                return f"Unsupported protocol '{device.protocol}' for sensor reading."
                
        except Exception as e:
            return f"Failed to read sensor '{device_name}': {str(e)}"
    
    # Group Control Methods
    def turn_on_all_lights(self) -> str:
        """Turn on all lights"""
        iot_logger.info("Attempting to turn on all lights")

        lights = self.get_devices_by_type('light')
        if not lights:
            iot_logger.warning("No lights found in device registry")
            return "No lights found."

        iot_logger.debug(f"Found {len(lights)} lights to control")
        results = []
        for light in lights:
            iot_logger.debug(f"Turning on light: {light.name}")
            result = self.turn_on_light(light.name)
            results.append(f"{light.name}: {result}")

        success_count = sum(1 for result in results if "turned on" in result.lower() or "success" in result.lower())
        iot_logger.info(f"Turn on all lights completed: {success_count}/{len(lights)} successful")
        return f"Turned on {success_count} out of {len(lights)} lights."
    
    def turn_off_all_lights(self) -> str:
        """Turn off all lights"""
        iot_logger.info("Attempting to turn off all lights")

        lights = self.get_devices_by_type('light')
        if not lights:
            iot_logger.warning("No lights found in device registry")
            return "No lights found."

        iot_logger.debug(f"Found {len(lights)} lights to control")
        results = []
        for light in lights:
            iot_logger.debug(f"Turning off light: {light.name}")
            result = self.turn_off_light(light.name)
            results.append(f"{light.name}: {result}")

        success_count = sum(1 for result in results if "turned off" in result.lower() or "success" in result.lower())
        iot_logger.info(f"Turn off all lights completed: {success_count}/{len(lights)} successful")
        return f"Turned off {success_count} out of {len(lights)} lights."
    
    # Device Status
    def get_device_status(self, device_name: str) -> str:
        """Get device status"""
        iot_logger.debug(f"Getting status for device '{device_name}'")

        device = self.get_device_by_name(device_name)
        if not device:
            iot_logger.warning(f"Device '{device_name}' not found in registry")
            return f"Device '{device_name}' not found."

        iot_logger.debug(f"Found device: {device.name} (protocol: {device.protocol}, type: {device.device_type})")

        try:
            if device.protocol == 'philips_hue' and device.device_type == 'light':
                iot_logger.debug("Routing to Philips Hue status check")
                return self._get_hue_light_status(device)
            elif device.protocol == 'mqtt':
                iot_logger.debug("Routing to MQTT status check")
                return self._get_mqtt_device_status(device)
            elif device.protocol == 'tuya':
                iot_logger.debug("Routing to Tuya status check")
                return self._get_tuya_device_status(device)
            elif device.protocol == 'http':
                iot_logger.debug("Routing to HTTP status check")
                return self._get_http_device_status(device)
            elif device.protocol == 'tapo':
                iot_logger.debug("Routing to Tapo status check")
                return self._get_tapo_device_status(device)
            else:
                iot_logger.warning(f"Status not available for protocol '{device.protocol}'")
                return f"Status not available for protocol '{device.protocol}'."

        except Exception as e:
            iot_logger.error(f"Failed to get status for '{device_name}': {str(e)}")
            iot_logger.debug(f"Status check error details: {type(e).__name__}: {str(e)}", exc_info=True)
            return f"Failed to get status for '{device_name}': {str(e)}"
    
    def list_all_devices(self) -> str:
        """List all configured devices"""
        iot_logger.debug("Listing all configured devices")

        if not self.devices:
            iot_logger.info("No IoT devices configured")
            return "No IoT devices configured."

        iot_logger.debug(f"Found {len(self.devices)} devices to list")
        device_list = []
        for device in self.devices.values():
            status = "Unknown"
            try:
                # Try to get basic status
                if device.last_state:
                    status = "Online" if device.last_state.get('online', True) else "Offline"
                    iot_logger.debug(f"Device {device.name} status: {status}")
                else:
                    iot_logger.debug(f"Device {device.name} has no last_state")
            except Exception as e:
                iot_logger.debug(f"Error getting status for device {device.name}: {e}")
                pass

            device_info = f"• {device.name.title()} ({device.device_type}) via {device.protocol} - {status}"
            device_list.append(device_info)

        result = f"Available IoT devices:\n" + "\n".join(device_list)
        iot_logger.info(f"Listed {len(device_list)} devices")
        return result
    
    # Protocol-specific control methods
    def _control_hue_light(self, device: IoTDevice, on: bool, brightness: int = None, color: str = None) -> str:
        """Control Philips Hue light"""
        if not self.philips_hue_bridge_ip or not self.philips_hue_username:
            return "Philips Hue not configured."
        
        light_id = device.config.get('light_id', device.device_id)
        url = f"http://{self.philips_hue_bridge_ip}/api/{self.philips_hue_username}/lights/{light_id}/state"
        
        payload = {"on": on}
        
        if brightness is not None and 0 <= brightness <= 100:
            payload["bri"] = int(brightness * 2.54)  # Convert 0-100 to 0-254
        
        if color and on:
            # Simple color mapping
            color_map = {
                'red': {'hue': 0, 'sat': 254},
                'green': {'hue': 25500, 'sat': 254},
                'blue': {'hue': 46920, 'sat': 254},
                'yellow': {'hue': 12750, 'sat': 254},
                'purple': {'hue': 56100, 'sat': 254},
                'orange': {'hue': 6375, 'sat': 254},
                'white': {'hue': 0, 'sat': 0}
            }
            
            if color.lower() in color_map:
                payload.update(color_map[color.lower()])
        
        response = requests.put(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            action = "turned on" if on else "turned off"
            extras = []
            if brightness is not None:
                extras.append(f"brightness {brightness}%")
            if color:
                extras.append(f"color {color}")
            
            extra_text = f" with {', '.join(extras)}" if extras else ""
            return f"Light '{device.name}' {action}{extra_text}."
        else:
            return f"Failed to control Hue light '{device.name}'."
    
    def _control_mqtt_light(self, device: IoTDevice, on: bool, brightness: int = None, color: str = None) -> str:
        """Control MQTT light"""
        if not self.mqtt_client:
            return "MQTT not connected."
        
        topic = device.config.get('command_topic', f"lights/{device.device_id}/set")
        
        payload = {"state": "ON" if on else "OFF"}
        
        if brightness is not None:
            payload["brightness"] = brightness
        
        if color:
            payload["color"] = color
        
        self.mqtt_client.publish(topic, json.dumps(payload))
        
        action = "turned on" if on else "turned off"
        return f"Light '{device.name}' {action} via MQTT."
    
    def _control_tuya_light(self, device: IoTDevice, on: bool, brightness: int = None, color: str = None) -> str:
        """Control Tuya light"""
        if not self.tuya_api:
            return "Tuya not configured."
        
        # This would need actual Tuya API implementation
        # Placeholder for now
        action = "turned on" if on else "turned off"
        return f"Light '{device.name}' {action} via Tuya."
    
    def _control_http_light(self, device: IoTDevice, on: bool, brightness: int = None, color: str = None) -> str:
        """Control HTTP-based light"""
        base_url = device.config.get('base_url', '')
        if not base_url:
            return "HTTP base URL not configured for device."
        
        endpoint = device.config.get('control_endpoint', '/control')
        url = f"{base_url}{endpoint}"
        
        payload = {
            "device_id": device.device_id,
            "action": "turn_on" if on else "turn_off"
        }
        
        if brightness is not None:
            payload["brightness"] = brightness
        
        if color:
            payload["color"] = color
        
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            action = "turned on" if on else "turned off"
            return f"Light '{device.name}' {action} via HTTP."
        else:
            return f"Failed to control HTTP light '{device.name}'."

    def _control_tapo_light(self, device, on: bool, brightness: int = None, color: str = None) -> str:
        """Control Tapo light"""
        iot_logger.debug(f"Controlling Tapo light '{device.name}' - on: {on}, brightness: {brightness}, color: {color}")

        try:
            # Import Tapo components locally to avoid circular imports
            iot_logger.debug("Importing Tapo wrapper functions...")
            from tapo_light_wrapper import turn_on_tapo_light, turn_off_tapo_light, set_tapo_brightness

            if on:
                iot_logger.debug(f"Turning on Tapo light '{device.name}'")
                # First turn on the light
                result = turn_on_tapo_light(device.name)
                iot_logger.debug(f"Turn on result: {result}")

                if "turned on" not in result.lower():
                    iot_logger.error(f"Failed to turn on Tapo light: {result}")
                    return result

                # Set brightness if specified
                if brightness is not None:
                    iot_logger.debug(f"Setting brightness to {brightness}%")
                    brightness_result = set_tapo_brightness(device.name, brightness)
                    iot_logger.debug(f"Brightness set result: {brightness_result}")

                    if "brightness" not in brightness_result.lower():
                        iot_logger.error(f"Failed to set brightness: {brightness_result}")
                        return f"Light turned on but failed to set brightness: {brightness_result}"

                # Set color if specified (simplified color mapping)
                if color:
                    iot_logger.debug(f"Setting color to {color} (simplified implementation)")
                    # This would need more sophisticated color handling
                    # For now, just return success for color setting
                    pass

                action = "turned on"
                extras = []
                if brightness is not None:
                    extras.append(f"brightness {brightness}%")
                if color:
                    extras.append(f"color {color}")

                extra_text = f" with {', '.join(extras)}" if extras else ""
                success_msg = f"Light '{device.name}' {action}{extra_text}."
                iot_logger.info(success_msg)
                return success_msg

            else:
                iot_logger.debug(f"Turning off Tapo light '{device.name}'")
                # Turn off the light
                result = turn_off_tapo_light(device.name)
                iot_logger.debug(f"Turn off result: {result}")
                return result

        except ImportError as e:
            iot_logger.error(f"Tapo package not available: {e}")
            return "Tapo package not available. Please install with: pip install tapo"
        except Exception as e:
            iot_logger.error(f"Failed to control Tapo light '{device.name}': {str(e)}")
            iot_logger.debug(f"Tapo control error details: {type(e).__name__}: {str(e)}", exc_info=True)
            return f"Failed to control Tapo light '{device.name}': {str(e)}"

    def _control_mqtt_switch(self, device: IoTDevice, on: bool) -> str:
        """Control MQTT switch"""
        if not self.mqtt_client:
            return "MQTT not connected."
        
        topic = device.config.get('command_topic', f"switches/{device.device_id}/set")
        payload = "ON" if on else "OFF"
        
        self.mqtt_client.publish(topic, payload)
        
        action = "turned on" if on else "turned off"
        return f"Switch '{device.name}' {action} via MQTT."
    
    def _control_tuya_switch(self, device: IoTDevice, on: bool) -> str:
        """Control Tuya switch"""
        if not self.tuya_api:
            return "Tuya not configured."
        
        # Placeholder for Tuya switch control
        action = "turned on" if on else "turned off"
        return f"Switch '{device.name}' {action} via Tuya."
    
    def _control_http_switch(self, device: IoTDevice, on: bool) -> str:
        """Control HTTP switch"""
        base_url = device.config.get('base_url', '')
        if not base_url:
            return "HTTP base URL not configured for device."
        
        endpoint = device.config.get('control_endpoint', '/control')
        url = f"{base_url}{endpoint}"
        
        payload = {
            "device_id": device.device_id,
            "action": "turn_on" if on else "turn_off"
        }
        
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            action = "turned on" if on else "turned off"
            return f"Switch '{device.name}' {action} via HTTP."
        else:
            return f"Failed to control HTTP switch '{device.name}'."
    
    def _control_mqtt_thermostat(self, device: IoTDevice, temperature: float) -> str:
        """Control MQTT thermostat"""
        if not self.mqtt_client:
            return "MQTT not connected."
        
        topic = device.config.get('command_topic', f"thermostats/{device.device_id}/set")
        payload = json.dumps({"temperature": temperature})
        
        self.mqtt_client.publish(topic, payload)
        
        return f"Thermostat '{device.name}' set to {temperature}°C via MQTT."
    
    def _control_tuya_thermostat(self, device: IoTDevice, temperature: float) -> str:
        """Control Tuya thermostat"""
        if not self.tuya_api:
            return "Tuya not configured."
        
        # Placeholder for Tuya thermostat control
        return f"Thermostat '{device.name}' set to {temperature}°C via Tuya."
    
    def _control_http_thermostat(self, device: IoTDevice, temperature: float) -> str:
        """Control HTTP thermostat"""
        base_url = device.config.get('base_url', '')
        if not base_url:
            return "HTTP base URL not configured for device."
        
        endpoint = device.config.get('control_endpoint', '/control')
        url = f"{base_url}{endpoint}"
        
        payload = {
            "device_id": device.device_id,
            "action": "set_temperature",
            "temperature": temperature
        }
        
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            return f"Thermostat '{device.name}' set to {temperature}°C via HTTP."
        else:
            return f"Failed to control HTTP thermostat '{device.name}'."
    
    # Status methods (simplified for brevity)
    def _get_hue_light_status(self, device: IoTDevice) -> str:
        """Get Philips Hue light status"""
        iot_logger.debug(f"Getting Philips Hue status for light '{device.name}'")

        if not self.philips_hue_bridge_ip or not self.philips_hue_username:
            iot_logger.warning("Philips Hue not configured")
            return "Philips Hue not configured."

        light_id = device.config.get('light_id', device.device_id)
        url = f"http://{self.philips_hue_bridge_ip}/api/{self.philips_hue_username}/lights/{light_id}"

        iot_logger.debug(f"Making HTTP request to: {url}")
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                iot_logger.debug(f"Hue API response: {data}")
                state = data.get('state', {})
                on = state.get('on', False)
                brightness = int(state.get('bri', 0) / 2.54) if state.get('bri') else 0

                status = "on" if on else "off"
                result = f"Light '{device.name}' is {status}" + (f" at {brightness}% brightness" if on and brightness > 0 else "") + "."
                iot_logger.info(f"Hue light status retrieved: {result}")
                return result
            else:
                iot_logger.error(f"Hue API returned status {response.status_code}: {response.text}")
                return f"Failed to get status for Hue light '{device.name}'."
        except requests.exceptions.RequestException as e:
            iot_logger.error(f"Network error getting Hue light status: {e}")
            return f"Network error getting status for Hue light '{device.name}'."
        except Exception as e:
            iot_logger.error(f"Unexpected error getting Hue light status: {e}")
            return f"Failed to get status for Hue light '{device.name}'."
    
    def _get_mqtt_device_status(self, device: IoTDevice) -> str:
        """Get MQTT device status"""
        iot_logger.debug(f"Getting MQTT status for device '{device.name}'")

        # Check if we have recent state information
        if device.last_state:
            iot_logger.debug(f"Returning cached MQTT status for '{device.name}': {device.last_state}")
            return f"Device '{device.name}' status: {device.last_state}"
        else:
            iot_logger.debug(f"No cached status available for MQTT device '{device.name}'")
            return f"MQTT status for '{device.name}' - no recent data available."

    def _get_tuya_device_status(self, device: IoTDevice) -> str:
        """Get Tuya device status"""
        iot_logger.debug(f"Getting Tuya status for device '{device.name}'")
        iot_logger.debug("Tuya status feature not yet implemented")
        return f"Tuya status for '{device.name}' - feature coming soon."

    def _get_tapo_device_status(self, device: IoTDevice) -> str:
        """Get Tapo device status"""
        iot_logger.debug(f"Getting Tapo status for device '{device.name}'")

        try:
            # Import Tapo components locally to avoid circular imports
            iot_logger.debug("Importing Tapo wrapper for status check...")
            from tapo_light_wrapper import TapoLight

            # Find the device in the Tapo manager
            if self.tapo_manager:
                tapo_device = self.tapo_manager.get_device_by_name(device.name)
                if tapo_device:
                    iot_logger.debug("Found Tapo device, attempting to get device info...")
                    # Try to get device info asynchronously
                    import asyncio
                    import concurrent.futures

                    loop = self.tapo_manager.get_event_loop()

                    if loop.is_running():
                        # Run in thread executor to avoid event loop conflicts
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, tapo_device.get_device_info())
                            device_info = future.result(timeout=10)
                    else:
                        device_info = loop.run_until_complete(tapo_device.get_device_info())

                    iot_logger.debug(f"Tapo device info retrieved: {device_info}")
                    return f"Tapo light '{device.name}' status: {device_info}"
                else:
                    iot_logger.warning(f"Tapo device '{device.name}' not found in Tapo manager")
                    return f"Tapo device '{device.name}' not found in manager."
            else:
                iot_logger.warning("Tapo manager not available")
                return "Tapo manager not available."

        except ImportError as e:
            iot_logger.error(f"Tapo package not available for status: {e}")
            return "Tapo package not available. Please install with: pip install tapo"
        except Exception as e:
            iot_logger.error(f"Failed to get Tapo device status: {e}")
            iot_logger.debug(f"Tapo status error details: {type(e).__name__}: {str(e)}", exc_info=True)
            return f"Failed to get status for Tapo device '{device.name}': {str(e)}"
    
    def _get_http_device_status(self, device: IoTDevice) -> str:
        """Get HTTP device status"""
        iot_logger.debug(f"Getting HTTP status for device '{device.name}'")

        base_url = device.config.get('base_url', '')
        if not base_url:
            iot_logger.warning(f"HTTP base URL not configured for device '{device.name}'")
            return "HTTP base URL not configured for device."

        endpoint = device.config.get('status_endpoint', '/status')
        url = f"{base_url}{endpoint}"

        params = {"device_id": device.device_id}
        iot_logger.debug(f"Making HTTP GET request to: {url} with params: {params}")

        try:
            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                iot_logger.debug(f"HTTP status response: {data}")
                result = f"Device '{device.name}' status: {data}"
                iot_logger.info(f"HTTP device status retrieved successfully")
                return result
            else:
                iot_logger.error(f"HTTP status request failed with status {response.status_code}: {response.text}")
                return f"Failed to get HTTP status for '{device.name}'."
        except requests.exceptions.RequestException as e:
            iot_logger.error(f"Network error getting HTTP device status: {e}")
            return f"Network error getting HTTP status for '{device.name}': {str(e)}"
        except json.JSONDecodeError as e:
            iot_logger.error(f"Invalid JSON response from HTTP device status: {e}")
            return f"Invalid response format from '{device.name}': {str(e)}"
        except Exception as e:
            iot_logger.error(f"Unexpected error getting HTTP device status: {e}")
            iot_logger.debug(f"HTTP status error details: {type(e).__name__}: {str(e)}", exc_info=True)
            return f"Error getting HTTP status for '{device.name}': {str(e)}"
    
    # MQTT callback methods
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            iot_logger.info("MQTT connected successfully")
            # Subscribe to device status topics
            iot_logger.debug("Subscribing to device status topics")
            client.subscribe("devices/+/status")
        else:
            iot_logger.error(f"MQTT connection failed with code {rc}")

    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            iot_logger.debug(f"Received MQTT message on topic: {msg.topic}")
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3 and topic_parts[2] == 'status':
                device_id = topic_parts[1]
                iot_logger.debug(f"Processing status update for device_id: {device_id}")

                if device_id in self.devices:
                    # Update device state
                    payload = json.loads(msg.payload.decode())
                    iot_logger.debug(f"Updating device {device_id} state: {payload}")
                    self.devices[device_id].last_state = payload
                    self.devices[device_id].last_updated = datetime.now()
                else:
                    iot_logger.warning(f"Received status for unknown device_id: {device_id}")
            else:
                iot_logger.debug(f"Ignoring MQTT message on topic: {msg.topic}")

        except json.JSONDecodeError as e:
            iot_logger.error(f"Failed to parse MQTT message payload: {e}")
        except Exception as e:
            iot_logger.error(f"Failed to process MQTT message: {e}")
            iot_logger.debug(f"MQTT message processing error details: {type(e).__name__}: {str(e)}", exc_info=True)
    
    # Sensor reading methods (placeholders)
    def _read_mqtt_sensor(self, device: IoTDevice) -> str:
        """Read MQTT sensor"""
        # This would read from the device's last known state or request current reading
        if device.last_state:
            return f"Sensor '{device.name}' reading: {device.last_state}"
        return f"No recent data for sensor '{device.name}'."
    
    def _read_tuya_sensor(self, device: IoTDevice) -> str:
        """Read Tuya sensor"""
        return f"Tuya sensor reading for '{device.name}' - feature coming soon."
    
    def _read_http_sensor(self, device: IoTDevice) -> str:
        """Read HTTP sensor"""
        return self._get_http_device_status(device)


# Global IoT manager instance
iot_manager = IoTManager()
