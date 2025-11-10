# tapo_light_wrapper.py

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from iot_manager import IoTDevice
from config_manager import config

try:
    from tapo import ApiClient
    TAPO_AVAILABLE = True
except ImportError:
    TAPO_AVAILABLE = False
    print("[INFO] Tapo not available. Install tapo package for Tapo device support.")

class TapoLight(IoTDevice):
    """Tapo smart light device wrapper with proper async handling"""

    def __init__(self, device_id: str, name: str, username: str, password: str, ip: str, model: str = "L530", **kwargs):
        super().__init__(device_id, name, "light", "tapo", **kwargs)
        self.username = username
        self.password = password
        self.ip = ip
        self.model = model
        self.client = None
        self.device = None
        self._is_connected = False

        # Initialize connection
        if TAPO_AVAILABLE:
            try:
                self.client = ApiClient(username, password)
                self._is_connected = True
                print(f"[INFO] Tapo light '{name}' initialized successfully")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Tapo light '{name}': {e}")
        else:
            print(f"[WARN] Tapo not available for device '{name}'")

    async def _ensure_connection(self):
        """Ensure device connection is established"""
        if not self._is_connected or not self.device:
            try:
                if not self.client:
                    self.client = ApiClient(self.username, self.password)
                
                if self.model.upper() == "L530":
                    self.device = await self.client.l530(self.ip)
                elif self.model.upper() == "L510":
                    self.device = await self.client.l510(self.ip)
                elif self.model.upper() == "L900":
                    self.device = await self.client.l900(self.ip)
                else:
                    # Default to L530
                    self.device = await self.client.l530(self.ip)
                self._is_connected = True
                print(f"[DEBUG] Connected to Tapo device '{self.name}'")
            except Exception as e:
                print(f"[ERROR] Failed to connect to Tapo device '{self.name}': {e}")
                self._is_connected = False
                raise

    async def turn_on(self) -> bool:
        """Turn on the light"""
        try:
            await self._ensure_connection()
            # Use the correct method name for Tapo L530
            await self.device.on()
            self.last_state = {"on": True, "last_action": "turn_on"}
            self.last_updated = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to turn on Tapo light '{self.name}': {e}")
            return False

    async def turn_off(self) -> bool:
        """Turn off the light"""
        try:
            await self._ensure_connection()
            # Use the correct method name for Tapo L530
            await self.device.off()
            self.last_state = {"on": False, "last_action": "turn_off"}
            self.last_updated = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to turn off Tapo light '{self.name}': {e}")
            return False

    async def set_brightness(self, level: int) -> bool:
        """Set brightness level (0-100)"""
        try:
            if not 0 <= level <= 100:
                raise ValueError("Brightness must be between 0 and 100")

            await self._ensure_connection()
            # Use the correct method name for Tapo L530
            await self.device.set_brightness(level)
            self.last_state = {"brightness": level, "last_action": "set_brightness"}
            self.last_updated = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to set brightness for Tapo light '{self.name}': {e}")
            return False

    async def set_color(self, hue: int, saturation: int) -> bool:
        """Set color using hue and saturation (0-360, 0-100)"""
        try:
            if not 0 <= hue <= 360:
                raise ValueError("Hue must be between 0 and 360")
            if not 0 <= saturation <= 100:
                raise ValueError("Saturation must be between 0 and 100")

            await self._ensure_connection()
            # Use the correct method name for Tapo L530
            await self.device.set_color(hue, saturation)
            self.last_state = {"hue": hue, "saturation": saturation, "last_action": "set_color"}
            self.last_updated = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to set color for Tapo light '{self.name}': {e}")
            return False

    async def set_color_temperature(self, temperature: int) -> bool:
        """Set color temperature in Kelvin (2500-6500)"""
        try:
            if not 2500 <= temperature <= 6500:
                raise ValueError("Color temperature must be between 2500 and 6500 K")

            await self._ensure_connection()
            # Use the correct method name for Tapo L530
            await self.device.set_color_temperature(temperature)
            self.last_state = {"color_temperature": temperature, "last_action": "set_color_temperature"}
            self.last_updated = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to set color temperature for Tapo light '{self.name}': {e}")
            return False

    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        try:
            await self._ensure_connection()
            # Use the correct method name for Tapo L530
            info = await self.device.get_device_info()
            self.last_state.update(info)
            self.last_updated = asyncio.get_event_loop().time()
            return info
        except Exception as e:
            print(f"[ERROR] Failed to get device info for Tapo light '{self.name}': {e}")
            return {}

    async def get_device_usage(self) -> Dict[str, Any]:
        """Get device energy usage information"""
        try:
            await self._ensure_connection()
            # Use the correct method name for Tapo L530
            usage = await self.device.get_device_usage()
            self.last_state.update({"energy_usage": usage})
            return usage
        except Exception as e:
            print(f"[ERROR] Failed to get energy usage for Tapo light '{self.name}': {e}")
            return {}

class TapoManager:
    """Manager for Tapo devices with async support"""

    def __init__(self):
        self.devices = {}  # device_id -> TapoLight
        self.device_name_map = {}  # name -> device_id
        self._event_loop = None

    def add_device(self, device: TapoLight):
        """Add a Tapo device to the manager"""
        self.devices[device.device_id] = device
        self.device_name_map[device.name.lower()] = device.device_id
        print(f"[INFO] Added Tapo device: {device}")

    def get_device_by_name(self, name: str) -> Optional[TapoLight]:
        """Get Tapo device by name (case-insensitive)"""
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

    def list_devices(self) -> List[TapoLight]:
        """List all Tapo devices"""
        return list(self.devices.values())

    async def turn_on_light(self, device_name: str) -> str:
        """Turn on a Tapo light"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Tapo light '{device_name}' not found."

        success = await device.turn_on()
        if success:
            return f"Turned on Tapo light '{device.name}'."
        else:
            return f"Failed to turn on Tapo light '{device.name}'."

    async def turn_off_light(self, device_name: str) -> str:
        """Turn off a Tapo light"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Tapo light '{device_name}' not found."

        success = await device.turn_off()
        if success:
            return f"Turned off Tapo light '{device.name}'."
        else:
            return f"Failed to turn off Tapo light '{device.name}'."

    async def set_brightness(self, device_name: str, brightness: int) -> str:
        """Set Tapo light brightness"""
        if not 0 <= brightness <= 100:
            return "Brightness must be between 0 and 100."

        device = self.get_device_by_name(device_name)
        if not device:
            return f"Tapo light '{device_name}' not found."

        success = await device.set_brightness(brightness)
        if success:
            return f"Set '{device.name}' brightness to {brightness}%."
        else:
            return f"Failed to set brightness for '{device.name}'."

    async def set_color(self, device_name: str, hue: int, saturation: int) -> str:
        """Set Tapo light color"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Tapo light '{device_name}' not found."

        success = await device.set_color(hue, saturation)
        if success:
            return f"Set '{device.name}' color (hue: {hue}, saturation: {saturation})."
        else:
            return f"Failed to set color for '{device.name}'."

    async def set_color_temperature(self, device_name: str, temperature: int) -> str:
        """Set Tapo light color temperature"""
        device = self.get_device_by_name(device_name)
        if not device:
            return f"Tapo light '{device_name}' not found."

        success = await device.set_color_temperature(temperature)
        if success:
            return f"Set '{device.name}' color temperature to {temperature}K."
        else:
            return f"Failed to set color temperature for '{device.name}'."

    def get_event_loop(self):
        """Get or create event loop for async operations"""
        if self._event_loop is None or self._event_loop.is_closed():
            try:
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop

# Global Tapo manager instance
tapo_manager = TapoManager()

def create_tapo_device_from_config(device_config: Dict[str, Any]) -> Optional[TapoLight]:
    """Create a TapoLight device from configuration"""
    try:
        required_fields = ['id', 'name', 'username', 'password', 'ip']
        for field in required_fields:
            if field not in device_config:
                print(f"[ERROR] Missing required field '{field}' in Tapo device config")
                return None

        device = TapoLight(
            device_id=device_config['id'],
            name=device_config['name'],
            username=device_config['username'],
            password=device_config['password'],
            ip=device_config['ip'],
            model=device_config.get('model', 'L530'),
            **device_config.get('config', {})
        )

        return device

    except Exception as e:
        print(f"[ERROR] Failed to create Tapo device from config: {e}")
        return None

# Synchronous wrapper functions with proper async handling
def turn_on_tapo_light(device_name: str) -> str:
    """Synchronous wrapper for turning on Tapo light"""
    try:
        if not TAPO_AVAILABLE:
            return f"Tapo package not available. Please install with: pip install tapo"
        
        loop = tapo_manager.get_event_loop()
        
        if loop.is_running():
            # Create a new event loop in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, tapo_manager.turn_on_light(device_name))
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(tapo_manager.turn_on_light(device_name))
    except Exception as e:
        return f"Failed to turn on Tapo light '{device_name}': {str(e)}"

def turn_off_tapo_light(device_name: str) -> str:
    """Synchronous wrapper for turning off Tapo light"""
    try:
        if not TAPO_AVAILABLE:
            return f"Tapo package not available. Please install with: pip install tapo"
        
        loop = tapo_manager.get_event_loop()
        
        if loop.is_running():
            # Create a new event loop in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, tapo_manager.turn_off_light(device_name))
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(tapo_manager.turn_off_light(device_name))
    except Exception as e:
        return f"Failed to turn off Tapo light '{device_name}': {str(e)}"

def set_tapo_brightness(device_name: str, brightness: int) -> str:
    """Synchronous wrapper for setting Tapo light brightness"""
    try:
        if not TAPO_AVAILABLE:
            return f"Tapo package not available. Please install with: pip install tapo"
        
        loop = tapo_manager.get_event_loop()
        
        if loop.is_running():
            # Create a new event loop in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, tapo_manager.set_brightness(device_name, brightness))
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(tapo_manager.set_brightness(device_name, brightness))
    except Exception as e:
        return f"Failed to set brightness for Tapo light '{device_name}': {str(e)}"

def set_tapo_color(device_name: str, hue: int, saturation: int) -> str:
    """Synchronous wrapper for setting Tapo light color"""
    try:
        if not TAPO_AVAILABLE:
            return f"Tapo package not available. Please install with: pip install tapo"
        
        loop = tapo_manager.get_event_loop()
        
        if loop.is_running():
            # Create a new event loop in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, tapo_manager.set_color(device_name, hue, saturation))
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(tapo_manager.set_color(device_name, hue, saturation))
    except Exception as e:
        return f"Failed to set color for Tapo light '{device_name}': {str(e)}"

def set_tapo_color_temperature(device_name: str, temperature: int) -> str:
    """Synchronous wrapper for setting Tapo light color temperature"""
    try:
        if not TAPO_AVAILABLE:
            return f"Tapo package not available. Please install with: pip install tapo"
        
        loop = tapo_manager.get_event_loop()
        
        if loop.is_running():
            # Create a new event loop in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, tapo_manager.set_color_temperature(device_name, temperature))
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(tapo_manager.set_color_temperature(device_name, temperature))
    except Exception as e:
        return f"Failed to set color temperature for Tapo light '{device_name}': {str(e)}"