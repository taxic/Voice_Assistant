# tapo_voice_commands.py

import re
from iot_manager import iot_manager
from response_variations import response_variations
from tapo_light_wrapper import tapo_manager

# Tapo Light Control Commands
def turn_on_tapo_light(device_name: str, brightness: int = None, color_temp: int = None) -> str:
    """Turn on a Tapo light with optional brightness and color temperature"""
    try:
        # Use the existing IoT manager which now supports Tapo
        response = iot_manager.turn_on_light(device_name, brightness=brightness)

        # Only provide feedback on failure, stay silent on success
        if "turned on" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            # Return error message if operation failed
            return f"Sorry, I couldn't turn on the Tapo light '{device_name}'."

    except Exception as e:
        return f"Sorry, I couldn't turn on the Tapo light '{device_name}': {str(e)}"

def turn_off_tapo_light(device_name: str) -> str:
    """Turn off a Tapo light"""
    try:
        response = iot_manager.turn_off_light(device_name)

        # Only provide feedback on failure, stay silent on success
        if "turned off" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            # Return error message if operation failed
            return f"Sorry, I couldn't turn off the Tapo light '{device_name}'."

    except Exception as e:
        return f"Sorry, I couldn't turn off the Tapo light '{device_name}': {str(e)}"

def set_tapo_brightness(device_name: str, brightness: int) -> str:
    """Set Tapo light brightness"""
    try:
        if not 0 <= brightness <= 100:
            return "Brightness must be between 0 and 100."

        response = iot_manager.set_brightness(device_name, brightness)

        # Only provide feedback on failure, stay silent on success
        if "brightness" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            return f"Sorry, I couldn't set the brightness for '{device_name}'."

    except Exception as e:
        return f"Sorry, I couldn't set the brightness for '{device_name}': {str(e)}"

def set_tapo_color_temperature(device_name: str, temperature: int) -> str:
    """Set Tapo light color temperature"""
    try:
        if not 2500 <= temperature <= 6500:
            return "Color temperature must be between 2500K (warm white) and 6500K (cool white)."

        # Use the sync wrapper function
        from tapo_light_wrapper import set_tapo_color_temperature
        response = set_tapo_color_temperature(device_name, temperature)

        # Only provide feedback on failure, stay silent on success
        if "color temperature" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            return f"Sorry, I couldn't set the color temperature for '{device_name}'."

    except Exception as e:
        return f"Sorry, I couldn't set the color temperature for '{device_name}': {str(e)}"

def set_tapo_warm_light(device_name: str) -> str:
    """Set Tapo light to warm white (2700K)"""
    return set_tapo_color_temperature(device_name, 2700)

def set_tapo_cool_light(device_name: str) -> str:
    """Set Tapo light to cool white (5000K)"""
    return set_tapo_color_temperature(device_name, 5000)

def set_tapo_reading_light(device_name: str) -> str:
    """Set Tapo light to reading mode (4000K, 80% brightness)"""
    try:
        # First set brightness to 80%
        brightness_response = set_tapo_brightness(device_name, 80)
        if "brightness" not in brightness_response.lower():
            return f"Failed to set reading brightness: {brightness_response}"

        # Then set color temperature to 4000K
        temp_response = set_tapo_color_temperature(device_name, 4000)
        if "color temperature" not in temp_response.lower():
            return f"Failed to set reading color temperature: {temp_response}"

        # Silent success for reading mode
        return ""

    except Exception as e:
        return f"Sorry, I couldn't set reading mode for '{device_name}': {str(e)}"

def set_tapo_relax_light(device_name: str) -> str:
    """Set Tapo light to relaxation mode (2200K, 30% brightness)"""
    try:
        # First set brightness to 30%
        brightness_response = set_tapo_brightness(device_name, 30)
        if "brightness" not in brightness_response.lower():
            return f"Failed to set relaxation brightness: {brightness_response}"

        # Then set color temperature to 2200K
        temp_response = set_tapo_color_temperature(device_name, 2200)
        if "color temperature" not in temp_response.lower():
            return f"Failed to set relaxation color temperature: {temp_response}"

        # Silent success for relax mode
        return ""

    except Exception as e:
        return f"Sorry, I couldn't set relaxation mode for '{device_name}': {str(e)}"

def get_tapo_device_info(device_name: str) -> str:
    """Get Tapo device information"""
    try:
        device = tapo_manager.get_device_by_name(device_name)
        if not device:
            return f"Tapo device '{device_name}' not found."

        # Get device info using the async method (simplified for sync context)
        return f"Tapo device '{device.name}' - Model: {device.model}, IP: {device.ip}"

    except Exception as e:
        return f"Sorry, I couldn't get info for '{device_name}': {str(e)}"

def list_tapo_devices() -> str:
    """List all Tapo devices"""
    try:
        devices = tapo_manager.list_devices()
        if not devices:
            return "No Tapo devices found."

        device_list = []
        for device in devices:
            device_list.append(f"• {device.name.title()} (IP: {device.ip}, Model: {device.model})")

        return f"Your Tapo devices:\n" + "\n".join(device_list)

    except Exception as e:
        return f"Sorry, I couldn't list Tapo devices: {str(e)}"

# Advanced Tapo Commands
def set_tapo_scene(device_name: str, scene: str) -> str:
    """Set Tapo light to a predefined scene"""
    try:
        scene_modes = {
            'reading': (4000, 80),
            'relax': (2200, 30),
            'movie': (3000, 40),
            'party': (2000, 90),
            'focus': (5000, 70),
            'romantic': (2400, 50)
        }

        if scene.lower() not in scene_modes:
            available_scenes = ", ".join(scene_modes.keys())
            return f"Unknown scene '{scene}'. Available scenes: {available_scenes}"

        temperature, brightness = scene_modes[scene.lower()]

        # Set brightness and color temperature
        brightness_response = set_tapo_brightness(device_name, brightness)
        if "brightness" not in brightness_response.lower():
            return f"Failed to set {scene} scene brightness: {brightness_response}"

        temp_response = set_tapo_color_temperature(device_name, temperature)
        if "color temperature" not in temp_response.lower():
            return f"Failed to set {scene} scene color temperature: {temp_response}"

        # Silent success for scenes
        return ""

    except Exception as e:
        return f"Sorry, I couldn't set the {scene} scene for '{device_name}': {str(e)}"

# Tapo Command Parsing Functions
def parse_tapo_light_command(command: str) -> dict:
    """Parse Tapo light control commands"""
    command = command.lower()
    result = {
        'action': None,
        'device_name': None,
        'brightness': None,
        'temperature': None,
        'scene': None
    }

    # Extract action
    if any(phrase in command for phrase in ['turn on', 'switch on', 'on']):
        result['action'] = 'turn_on'
    elif any(phrase in command for phrase in ['turn off', 'switch off', 'off']):
        result['action'] = 'turn_off'
    elif 'brightness' in command or 'bright' in command or 'dim' in command:
        result['action'] = 'brightness'
    elif 'temperature' in command or 'warm' in command or 'cool' in command:
        result['action'] = 'temperature'
    elif 'scene' in command or 'mode' in command:
        result['action'] = 'scene'
    elif 'reading' in command and 'mode' in command:
        result['action'] = 'reading_mode'
    elif 'relax' in command and 'mode' in command:
        result['action'] = 'relax_mode'

    # Extract brightness
    brightness_match = re.search(r'(\d+)\s*(?:percent|%|brightness)', command)
    if brightness_match:
        result['brightness'] = int(brightness_match.group(1))
    elif 'full' in command or 'maximum' in command:
        result['brightness'] = 100
    elif 'half' in command or 'medium' in command:
        result['brightness'] = 50
    elif 'low' in command or 'dim' in command:
        result['brightness'] = 20

    # Extract color temperature
    temp_match = re.search(r'(\d+)\s*(?:k|kelvin|degrees?)', command)
    if temp_match:
        result['temperature'] = int(temp_match.group(1))
    elif 'warm' in command:
        result['temperature'] = 2700
    elif 'cool' in command:
        result['temperature'] = 5000

    # Extract scene
    scenes = ['reading', 'relax', 'movie', 'party', 'focus', 'romantic']
    for scene in scenes:
        if scene in command:
            result['scene'] = scene
            break

    # Extract device name (look for common room names after "tapo")
    room_names = ['living room', 'bedroom', 'kitchen', 'bathroom', 'office', 'hallway', 'dining room', 'lounge']
    for room in room_names:
        if room in command:
            result['device_name'] = room
            break

    # If no specific room found, try to extract any word after "tapo" or "light"
    if not result['device_name']:
        tapo_pattern = r'(?:tapo\s+)?(?:light\s+)?(\w+(?:\s+\w+)?)'
        match = re.search(tapo_pattern, command)
        if match:
            result['device_name'] = match.group(1).strip()

    return result

# Main Tapo command dispatcher
def handle_tapo_command(command: str) -> str:
    """Main function to handle Tapo-specific commands"""
    command = command.lower()

    try:
        # Check if this is a Tapo command
        if 'tapo' not in command:
            return "This doesn't seem to be a Tapo command. Try saying 'turn on the living room Tapo light'."

        parsed = parse_tapo_light_command(command)

        if not parsed['device_name']:
            return "I need to know which Tapo light you want to control. Please specify the light name."

        if parsed['action'] == 'turn_on':
            return turn_on_tapo_light(parsed['device_name'], parsed['brightness'], parsed['temperature'])
        elif parsed['action'] == 'turn_off':
            return turn_off_tapo_light(parsed['device_name'])
        elif parsed['action'] == 'brightness' and parsed['brightness'] is not None:
            return set_tapo_brightness(parsed['device_name'], parsed['brightness'])
        elif parsed['action'] == 'temperature' and parsed['temperature'] is not None:
            return set_tapo_color_temperature(parsed['device_name'], parsed['temperature'])
        elif parsed['action'] == 'scene' and parsed['scene']:
            return set_tapo_scene(parsed['device_name'], parsed['scene'])
        elif parsed['action'] == 'reading_mode':
            return set_tapo_reading_light(parsed['device_name'])
        elif parsed['action'] == 'relax_mode':
            return set_tapo_relax_light(parsed['device_name'])
        elif 'warm' in command:
            return set_tapo_warm_light(parsed['device_name'])
        elif 'cool' in command:
            return set_tapo_cool_light(parsed['device_name'])
        elif any(phrase in command for phrase in ['list devices', 'show devices', 'what devices']):
            return list_tapo_devices()
        elif any(phrase in command for phrase in ['info', 'information', 'details']):
            return get_tapo_device_info(parsed['device_name'])
        else:
            return "I didn't understand that Tapo command. Try commands like 'turn on the living room Tapo light' or 'set bedroom Tapo to reading mode'."

    except Exception as e:
        error_response = response_variations.get_error_response()
        return f"{error_response} Tapo command failed: {str(e)}"

# Convenience functions for integration with existing command system
def handle_tapo_or_iot_command(command: str) -> str:
    """Handle command that might be either Tapo or general IoT"""
    if 'tapo' in command.lower():
        return handle_tapo_command(command)
    else:
        # Fall back to existing IoT command handler
        from iot_commands import handle_iot_command
        return handle_iot_command(command)