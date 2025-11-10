# iot_commands.py

import re
from iot_manager import iot_manager
from response_variations import response_variations

# Light Control Commands
def turn_on_light(device_name: str, brightness: int = None, color: str = None) -> str:
    """Turn on a light with optional brightness and color"""
    try:
        response = iot_manager.turn_on_light(device_name, brightness, color)
        
        # Only provide feedback on failure, stay silent on success
        if "turned on" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            # Return error message if operation failed
            return f"Sorry, I couldn't turn on the light '{device_name}'."
        
    except Exception as e:
        return f"Sorry, I couldn't control the light '{device_name}': {str(e)}"

def turn_off_light(device_name: str) -> str:
    """Turn off a light"""
    try:
        response = iot_manager.turn_off_light(device_name)
        
        # Only provide feedback on failure, stay silent on success
        if "turned off" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            # Return error message if operation failed
            return f"Sorry, I couldn't turn off the light '{device_name}'."
        
    except Exception as e:
        return f"Sorry, I couldn't control the light '{device_name}': {str(e)}"

def set_light_brightness(device_name: str, brightness: int) -> str:
    """Set light brightness"""
    try:
        response = iot_manager.set_brightness(device_name, brightness)
        
        # Only provide feedback on failure, stay silent on success
        if "brightness" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            return f"Sorry, I couldn't set the brightness for '{device_name}'."
    except Exception as e:
        return f"Sorry, I couldn't set the brightness for '{device_name}': {str(e)}"

def set_light_color(device_name: str, color: str) -> str:
    """Set light color"""
    try:
        response = iot_manager.set_color(device_name, color)
        
        # Only provide feedback on failure, stay silent on success
        if "color" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            return f"Sorry, I couldn't change the color of '{device_name}'."
    except Exception as e:
        return f"Sorry, I couldn't change the color of '{device_name}': {str(e)}"

def turn_on_all_lights() -> str:
    """Turn on all lights"""
    try:
        response = iot_manager.turn_on_all_lights()
        
        # Only provide feedback on failure, stay silent on success
        if "turned on" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            return f"Sorry, I couldn't turn on all the lights."
        
    except Exception as e:
        return f"Sorry, I couldn't turn on all the lights: {str(e)}"

def turn_off_all_lights() -> str:
    """Turn off all lights"""
    try:
        response = iot_manager.turn_off_all_lights()
        
        # Only provide feedback on failure, stay silent on success
        if "turned off" in response.lower() or "success" in response.lower():
            return ""  # Silent success
        else:
            return f"Sorry, I couldn't turn off all the lights."
        
    except Exception as e:
        return f"Sorry, I couldn't turn off all the lights: {str(e)}"

# Switch Control Commands
def turn_on_switch(device_name: str) -> str:
    """Turn on a switch"""
    try:
        response = iot_manager.turn_on_switch(device_name)
        
        # Add personality to successful responses
        if "turned on" in response.lower():
            success_phrase = response_variations.get_success_response()
            response = f"{response} {success_phrase}"
        
        return response
        
    except Exception as e:
        return f"Sorry, I couldn't turn on the switch '{device_name}': {str(e)}"

def turn_off_switch(device_name: str) -> str:
    """Turn off a switch"""
    try:
        response = iot_manager.turn_off_switch(device_name)
        
        # Add personality to successful responses
        if "turned off" in response.lower():
            success_phrase = response_variations.get_success_response()
            response = f"{response} {success_phrase}"
        
        return response
        
    except Exception as e:
        return f"Sorry, I couldn't turn off the switch '{device_name}': {str(e)}"

# Thermostat Control Commands
def set_temperature(device_name: str, temperature: float) -> str:
    """Set thermostat temperature"""
    try:
        response = iot_manager.set_temperature(device_name, temperature)
        
        # Add confirmation for temperature changes
        if "set to" in response.lower():
            acknowledgment = response_variations.get_acknowledgment_response()
            response = f"{response} {acknowledgment}"
        
        return response
        
    except Exception as e:
        return f"Sorry, I couldn't set the temperature for '{device_name}': {str(e)}"

# Sensor Reading Commands
def get_sensor_reading(device_name: str) -> str:
    """Get sensor reading"""
    try:
        return iot_manager.get_sensor_reading(device_name)
    except Exception as e:
        return f"Sorry, I couldn't read the sensor '{device_name}': {str(e)}"

# Device Status Commands
def get_device_status(device_name: str) -> str:
    """Get device status"""
    try:
        return iot_manager.get_device_status(device_name)
    except Exception as e:
        return f"Sorry, I couldn't get the status for '{device_name}': {str(e)}"

def list_all_devices() -> str:
    """List all IoT devices"""
    try:
        return iot_manager.list_all_devices()
    except Exception as e:
        return f"Sorry, I couldn't list the devices: {str(e)}"

# Smart Command Parsing Functions
def parse_light_command(command: str) -> dict:
    """Parse light control commands"""
    command = command.lower()
    result = {
        'action': None,
        'device_name': None,
        'brightness': None,
        'color': None,
        'all_lights': False
    }
    
    # Check for all lights commands
    if any(phrase in command for phrase in ['all lights', 'every light', 'all the lights','the lights']):
        result['all_lights'] = True
        if any(word in command for word in ['turn on', 'switch on', 'on']):
            result['action'] = 'turn_on'
        elif any(word in command for word in ['turn off', 'switch off', 'off']):
            result['action'] = 'turn_off'
        return result
    
    # Extract action
    if any(phrase in command for phrase in ['turn on', 'switch on', 'on']):
        result['action'] = 'turn_on'
    elif any(phrase in command for phrase in ['turn off', 'switch off', 'off']):
        result['action'] = 'turn_off'
    elif 'brightness' in command or 'bright' in command or 'dim' in command:
        result['action'] = 'brightness'
    elif 'color' in command or any(color in command for color in ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'white']):
        result['action'] = 'color'
    
    # Extract brightness
    brightness_match = re.search(r'(\d+)\s*(?:percent|%)', command)
    if brightness_match:
        result['brightness'] = int(brightness_match.group(1))
    elif 'bright' in command or 'full' in command:
        result['brightness'] = 100
    elif 'dim' in command or 'low' in command:
        result['brightness'] = 20
    
    # Extract color
    colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'white']
    for color in colors:
        if color in command:
            result['color'] = color
            break
    
    # Extract device name (simple approach - look for common light names)
    common_light_names = ['living room', 'bedroom', 'kitchen', 'bathroom', 'office', 'hallway', 'dining room','lounge']
    for light_name in common_light_names:
        if light_name in command:
            result['device_name'] = light_name
            break
    
    # If no specific room found, try to extract any word after "light" or "lamp"
    if not result['device_name']:
        light_pattern = r'(?:turn\s+(?:on|off)\s+(?:the\s+)?|brightness\s+(?:of\s+)?(?:the\s+)?|color\s+(?:of\s+)?(?:the\s+)?)?(\w+(?:\s+\w+)?)\s*(?:light|lamp)'
        match = re.search(light_pattern, command)
        if match:
            result['device_name'] = match.group(1).strip()
    
    return result

def parse_switch_command(command: str) -> dict:
    """Parse switch control commands"""
    command = command.lower()
    result = {
        'action': None,
        'device_name': None
    }
    
    # Extract action
    if any(phrase in command for phrase in ['turn on', 'switch on', 'on']):
        result['action'] = 'turn_on'
    elif any(phrase in command for phrase in ['turn off', 'switch off', 'off']):
        result['action'] = 'turn_off'
    
    # Extract device name
    switch_pattern = r'(?:turn\s+(?:on|off)\s+(?:the\s+)?)?(\w+(?:\s+\w+)?)\s*switch'
    match = re.search(switch_pattern, command)
    if match:
        result['device_name'] = match.group(1).strip()
    
    return result

def parse_temperature_command(command: str) -> dict:
    """Parse thermostat commands"""
    command = command.lower()
    result = {
        'action': 'set_temperature',
        'device_name': None,
        'temperature': None
    }
    
    # Extract temperature
    temp_patterns = [
        r'(\d+)\s*(?:degrees?|°)',
        r'to\s+(\d+)',
        r'set.*?(\d+)'
    ]
    
    for pattern in temp_patterns:
        match = re.search(pattern, command)
        if match:
            result['temperature'] = float(match.group(1))
            break
    
    # Extract device name (default to "thermostat" if not specified)
    thermostat_names = ['thermostat', 'temperature', 'heating', 'cooling']
    for name in thermostat_names:
        if name in command:
            result['device_name'] = name
            break
    
    if not result['device_name']:
        result['device_name'] = 'thermostat'  # Default
    
    return result

def parse_sensor_command(command: str) -> dict:
    """Parse sensor reading commands"""
    command = command.lower()
    result = {
        'action': 'read_sensor',
        'device_name': None
    }
    
    # Common sensor names
    sensor_names = ['temperature sensor', 'humidity sensor', 'motion sensor', 'door sensor', 'window sensor']
    
    for sensor in sensor_names:
        if sensor in command:
            result['device_name'] = sensor
            break
    
    # If no specific sensor found, try to extract general sensor name
    if not result['device_name']:
        sensor_pattern = r'(?:read|check|get)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s*sensor'
        match = re.search(sensor_pattern, command)
        if match:
            result['device_name'] = match.group(1).strip() + ' sensor'
    
    return result

# Main IoT command dispatcher
def handle_iot_command(command: str) -> str:
    """Main function to handle IoT commands"""
    command = command.lower()

    try:
        # Check for Tapo commands first
        if 'tapo' in command:
            from tapo_voice_commands import handle_tapo_command
            return handle_tapo_command(command)
        # Light commands
        if any(word in command for word in ['light', 'lights', 'lamp', 'bulb']):
            parsed = parse_light_command(command)
            
            if parsed['all_lights']:
                if parsed['action'] == 'turn_on':
                    return turn_on_all_lights()
                elif parsed['action'] == 'turn_off':
                    return turn_off_all_lights()
            
            if not parsed['device_name']:
                return "I need to know which light you want to control. Please specify the light name."
            
            if parsed['action'] == 'turn_on':
                return turn_on_light(parsed['device_name'], parsed['brightness'], parsed['color'])
            elif parsed['action'] == 'turn_off':
                return turn_off_light(parsed['device_name'])
            elif parsed['action'] == 'brightness' and parsed['brightness'] is not None:
                return set_light_brightness(parsed['device_name'], parsed['brightness'])
            elif parsed['action'] == 'color' and parsed['color']:
                return set_light_color(parsed['device_name'], parsed['color'])
        
        # Switch commands
        elif 'switch' in command:
            parsed = parse_switch_command(command)
            
            if not parsed['device_name']:
                return "I need to know which switch you want to control. Please specify the switch name."
            
            if parsed['action'] == 'turn_on':
                return turn_on_switch(parsed['device_name'])
            elif parsed['action'] == 'turn_off':
                return turn_off_switch(parsed['device_name'])
        
        # Temperature/Thermostat commands
        elif any(word in command for word in ['temperature', 'thermostat', 'heating', 'cooling']):
            if 'set' in command or 'change' in command:
                parsed = parse_temperature_command(command)
                
                if parsed['temperature'] is None:
                    return "I need to know what temperature to set. Please specify the temperature in degrees."
                
                return set_temperature(parsed['device_name'], parsed['temperature'])
            else:
                # Assume they want to read temperature
                return get_sensor_reading('temperature sensor')
        
        # Sensor reading commands
        elif any(word in command for word in ['sensor', 'reading', 'check']):
            parsed = parse_sensor_command(command)
            
            if not parsed['device_name']:
                return "I need to know which sensor you want to read. Please specify the sensor name."
            
            return get_sensor_reading(parsed['device_name'])
        
        # Device status commands
        elif any(phrase in command for phrase in ['status', 'state', 'how is', 'what is']):
            # Try to extract device name from the command
            device_name = None
            words = command.split()
            
            # Simple approach: look for device type words
            device_types = ['light', 'switch', 'thermostat', 'sensor']
            for i, word in enumerate(words):
                if word in device_types and i > 0:
                    device_name = words[i-1] + ' ' + word
                    break
            
            if device_name:
                return get_device_status(device_name)
            else:
                return "I need to know which device you want to check. Please specify the device name."
        
        # List devices command
        elif any(phrase in command for phrase in ['list devices', 'show devices', 'what devices', 'available devices']):
            return list_all_devices()
        
        # If we get here, the command wasn't recognized as IoT
        return "I didn't understand that IoT command. Try commands like 'turn on the living room light' or 'set thermostat to 22 degrees'."
        
    except Exception as e:
        error_response = response_variations.get_error_response()
        return f"{error_response} IoT command failed: {str(e)}"
