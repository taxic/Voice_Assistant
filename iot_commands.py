# iot_commands.py

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
