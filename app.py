from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

from datetime import datetime
alert_log= []

def log_event(message):

    timestamp = datetime.now().strftime("%I:%M:%S %p")
    
    log_entry = f"[{timestamp}] {message}"

    alert_log.insert(0,log_entry)

def get_time_of_day():

    current_hour = datetime.now().hour

    if 6 <= current_hour < 18:
        return "day"

    else:
        return "night"
    



panic_triggered= False
current_mode= None

manual_mode= None




supported_capabilities = {     #Dictionary to store commands on what devices allow

    #SMART CAMERAS

    "living_room_camera_1": [

        "ENABLE_VIDEO",
        "DISABLE_VIDEO",

        "ENABLE_AUDIO",
        "DISABLE_AUDIO",

        "ENABLE_MOTION_DETECTION",

        "ENABLE_FACIAL_RECOGNITION",

        "LIMIT_TRANSMISSION",

        "LOCAL_STORAGE_ONLY",

        "CLOUD_STREAMING"
    ],


    "bathroom_camera_1": [

        "DISABLE_VIDEO",

        "ENABLE_MOTION_DETECTION",

        "LIMIT_TRANSMISSION",

        "LOCAL_STORAGE_ONLY"
    ],

    "balcony_camera_1": [

        "DISABLE_VIDEO",

        "ENABLE_MOTION_DETECTION",

        "LIMIT_TRANSMISSION",

        "LOCAL_STORAGE_ONLY"
    ],


    "front_door_camera_1": [

        "ENABLE_VIDEO",

        "ENABLE_AUDIO",

        "ENABLE_FACIAL_RECOGNITION",

        "PERSON_DETECTION",

        "PACKAGE_DETECTION",

        "NIGHT_VISION",

        "CLOUD_STREAMING",

        "LIMIT_TRANSMISSION"
    ],

    "back_door_camera_1": [

        "ENABLE_VIDEO",

        "ENABLE_AUDIO",

        "ENABLE_FACIAL_RECOGNITION",

        "PERSON_DETECTION",

        "PACKAGE_DETECTION",

        "NIGHT_VISION",

        "CLOUD_STREAMING",

        "LIMIT_TRANSMISSION"
    ],


    # SMART SPEAKERS

    "living_room_speaker_1": [

        "ENABLE_MIC",

        "DISABLE_MIC",

        "WAKE_WORD_ONLY",

        "LIMIT_AUDIO_STORAGE",

        "VOICE_RECOGNITION",

        "CLOUD_VOICE_PROCESSING",

        "LOCAL_VOICE_PROCESSING"
    ],


    "bedroom_speaker_1": [

        "ENABLE_MIC",

        "DISABLE_MIC",

        "WAKE_WORD_ONLY",

        "LOCAL_VOICE_PROCESSING"
    ],


    # SMART LOCKS

    "front_door_lock_1": [

        "AUTO_LOCK_ON",

        "AUTO_LOCK_OFF",

        "REMOTE_UNLOCK",

        "PIN_ACCESS",

        "FINGERPRINT_ACCESS",

        "FACE_RECOGNITION_ACCESS",

        "ACCESS_LOGGING",

        "TAMPER_DETECTION"
    ],


    "back_door_lock_1": [

        "AUTO_LOCK_ON",

        "REMOTE_UNLOCK",

        "PIN_ACCESS",

        "ACCESS_LOGGING"
    ],


    # SMART THERMOSTATS

    "hallway_thermostat_1": [

        "TEMPERATURE_MONITORING",

        "HUMIDITY_MONITORING",

        "MOTION_SENSING",

        "OCCUPANCY_DETECTION",

        "REMOTE_CONTROL",

        "ENERGY_USAGE_TRACKING",

        "SCHEDULE_LEARNING"
    ],


    "bedroom_thermostat_1": [

        "TEMPERATURE_MONITORING",

        "MOTION_SENSING",

        "REMOTE_CONTROL"
    ]
}


device_sensitivity = {

    "living_room_camera_1": 4,
    "bathroom_camera_1": 5,
    "balcony_camera_1": 3,
    "front_door_camera_1": 4,
    "back_door_camera_1": 4,

    "living_room_speaker_1": 3,
    "bedroom_speaker_1": 4,

    "front_door_lock_1": 5,
    "back_door_lock_1": 4,

    "hallway_thermostat_1": 1,
    "bedroom_thermostat_1": 1
}   

data_sensitivity = {

    "ENABLE_VIDEO": 5,
    "ENABLE_AUDIO": 4,
    "ENABLE_MIC": 4,

    "ENABLE_FACIAL_RECOGNITION": 5,

    "PERSON_DETECTION": 3,
    "PACKAGE_DETECTION": 2,

    "ENABLE_MOTION_DETECTION": 2,

    "TEMPERATURE_MONITORING": 1,
    "HUMIDITY_MONITORING": 1,

    "AUTO_LOCK_ON": 2,
    "AUTO_LOCK_OFF": 2
}

def get_context_risk(mode, user_location):

    if mode == "emergency":
        return 4

    if user_location == "bathroom":
        return 5

    if user_location == "bedroom":
        return 4

    if mode == "away":
        return 2

    return 1

def calculate_risk(device, capability,
                   mode, user_location):

    ds = device_sensitivity.get(device, 1)

    dt = data_sensitivity.get(capability, 1)

    cx = get_context_risk(
        mode,
        user_location
    )

    return ds * dt * cx

def enforce_risk_policy(
    device,
    capability,
    mode,
    user_location
):

    risk = calculate_risk(
        device,
        capability,
        mode,
        user_location
    )

    if risk >= 80:
        return "BLOCK"

    elif risk >= 40:
        return "LIMIT"

    else:
        return "ALLOW"







def smart_home_mode_controller(                  #Context/Sensor layer

    #Shared context inputs             
    manual_mode=None,
    user_presence="home",  #home or away
    time_of_day=None,    #day or night
    user_location="living room", # user's location in the home based on motion sensor
    network_security="trusted",  #trust level of connection between smarthome system & external networks

    # Away-specific False by default(fallback assumption)
    user_absent=False,  #motion sensor doesn't decte user's presence
    door_locked=False,
    time_pattern_match=False,  #if it matches the user's usual routine

    # Emergency-specific  system state
    event_type=None,              # "panic"
    multiple_sensors=False,   #multiple sensors confirming events. bcus stated events can be uncertion or single-sourced. eg, door + camera agree
    user_responded=True,   #whether user interacts with/acknowlegde system after an alert 
    abnormal_behavior=False  #out of routine or unusual behavoiur detected
):
    
    #Manual Switching of modes
    global current_mode


    #Panic Override
    if event_type == "panic":  #a manual user triggered emergency alert
        
        return {
    "mode": "emergency",
    "event_type": event_type,
    "reason": "User panic activation",
    "score": 999
}

#Emergency mode
    emergency_score = 0  #to calculate how serious the situation is



    if manual_mode is not None:
        if current_mode!= manual_mode:
            log_event(f"{manual_mode.capitalize()} mode activated")

        current_mode=manual_mode
        return {
        "mode": manual_mode,
        "score": 0
    }

    if time_of_day is None:
        time_of_day = get_time_of_day()


    

        

   #Independent Events
    
    if event_type == "fire":
        emergency_score += 5

    if event_type == "tamper": #something is trying to break or disable a device/devices
        emergency_score += 4

    if event_type == "motion":  #motion confirmed in the house
        emergency_score += 2

    if multiple_sensors:   #sensors confirming events bcus stated events can be uncertion or single-sourced
        emergency_score += 2

    if time_of_day == "night":
        emergency_score += 1

    if user_presence == "away":
        emergency_score += 1

    if not user_responded:
        emergency_score += 2

    if abnormal_behavior:   
        emergency_score += 1


    # AWAY MODE
    away_score = 0

    if user_presence == "away":
        away_score += 3
    else:
        away_score -= 3

    if user_absent:
        away_score += 2

    if door_locked:
        away_score += 1

    if time_pattern_match:
        away_score += 1



    #  HOME MODE
    home_score = 0

    if user_presence == "home":
        home_score += 3
    else:
        home_score -= 3

    if time_of_day == "night":
        home_score += 1

    if user_location == "living room":
        home_score += 2
    elif user_location == "kitchen":
        home_score += 2
    elif user_location == "bathroom":
        home_score += 2
    elif user_location == "bedroom":
        home_score += 2
    elif user_location == "balcony":
        home_score += 2
    else:
        home_score = 0

    if network_security == "untrusted":
        home_score -= 1

    

    # FINAL DECISION
    if emergency_score >= 5:

        if current_mode != "emergency":
            log_event("Emergency mode activated")

        current_mode = "emergency"

        return {
            "mode": "emergency",
            "score": emergency_score
        }

    elif away_score >= 4 and away_score > home_score:

        if current_mode != "away":
            log_event("Away mode activated")

        current_mode = "away"

        return {
            "mode": "away",
            "score": away_score
        }

    else:

        if current_mode != "home":
            log_event("Home mode activated")

        current_mode = "home"

        return {
            "mode": "home",
            "score": home_score
        }



def device_capability_check(device, capability):  #Checks if a device supports a request command 


    return capability in supported_capabilities.get(device, [])   #Is the requested capability inside this device's supported list?


#This simulates network communication, API requests, IoT commands, and 6G transmission
def send_command(device_id, command):  #the controller sending command to devices
    print(f"Sending command to {device_id}: {command}") #which device & action to send
    log_event(f" {device_id} - {command}")





def apply_risk_based_permission(
    device,
    capability,
    mode,
    user_location,
    device_states
):

    decision = enforce_risk_policy(
        device,
        capability,
        mode,
        user_location
    )

    if decision == "ALLOW":

        send_command(
            device,
            capability
        )

        device_states[
            device
        ] = capability

    elif decision == "LIMIT":

        send_command(
            device,
            "LIMIT_TRANSMISSION"
        )

        device_states[
            device
        ] = "LIMIT_TRANSMISSION"

    else:

        send_command(
            device,
            "DISABLE_VIDEO"
        )

        device_states[
            device
        ] = "DISABLE_VIDEO"






def apply_audio_risk_permission(
    device,
    capability,
    mode,
    user_location,
    device_states
):

    decision = enforce_risk_policy(
        device,
        capability,
        mode,
        user_location
    )

    if decision == "ALLOW":

        send_command(
            device,
            capability
        )

        device_states[
            device
        ] = capability

    elif decision == "LIMIT":

        send_command(
            device,
            "WAKE_WORD_ONLY"
        )

        device_states[
            device
        ] = "WAKE_WORD_ONLY"

    else:

        send_command(
            device,
            "DISABLE_MIC"
        )

        device_states[
            device
        ] = "DISABLE_MIC"




default_device_states = {

    "living_room_camera_1": "DISABLE_VIDEO",

    "bathroom_camera_1": "DISABLE_VIDEO",

    "balcony_camera_1": "DISABLE_VIDEO",

    "front_door_camera_1": "ENABLE_VIDEO",

    "back_door_camera_1": "ENABLE_VIDEO",

    "living_room_speaker_1": "WAKE_WORD_ONLY",

    "bedroom_speaker_1": "WAKE_WORD_ONLY",

    "front_door_lock_1": "AUTO_LOCK_ON",

    "back_door_lock_1": "AUTO_LOCK_ON",

    "hallway_thermostat_1": "TEMPERATURE_MONITORING",

    "bedroom_thermostat_1": "TEMPERATURE_MONITORING"
}



def apply_device_permissions(mode_data, user_location):  #Policy Engine, what devices are allowed or restricted in each mode

    mode= mode_data["mode"]
    device_states = {}   #to store current device status & active permissions
    

#Make sure every device always has a state
    for device in supported_capabilities:
        device_states= default_device_states.copy()
        #device_states[device]= "STANDBY" #"NO ACTIVE STATE"


    # AWAY MODE
    if mode == "away":

    # Living Room Camera
     if device_capability_check(
        "living_room_camera_1",
        "ENABLE_VIDEO"
     ):

        apply_risk_based_permission(
        "living_room_camera_1",
        "ENABLE_VIDEO",
        mode,
        user_location,
        device_states
    )

    # Bathroom Camera
    if device_capability_check(
        "bathroom_camera_1",
        "DISABLE_VIDEO"
    ):

        apply_risk_based_permission(
        "bathroom_camera_1",
        "DISABLE_VIDEO",
        mode,
        user_location,
        device_states
    )

    # Front Door Camera
    if device_capability_check(
        "front_door_camera_1",
        "ENABLE_VIDEO"
    ):

        apply_risk_based_permission(
        "front_door_camera_1",
        "ENABLE_VIDEO",
        mode,
        user_location,
        device_states
    )

    # Living Room Speaker
    if device_capability_check(
        "living_room_speaker_1",
        "WAKE_WORD_ONLY"
    ):

        apply_audio_risk_permission(
        "living_room_speaker_1",
        "WAKE_WORD_ONLY",
        mode,
        user_location,
        device_states
    )

    # Front Door Lock
    if device_capability_check(
        "front_door_lock_1",
        "AUTO_LOCK_ON"
    ):

        send_command(
            "front_door_lock_1",
            "AUTO_LOCK_ON"
        )

        device_states[
            "front_door_lock_1"
        ] = "AUTO_LOCK_ON"


    # Thermostat
    if device_capability_check(
        "hallway_thermostat_1",
        "REMOTE_CONTROL"
    ):

        send_command(
            "hallway_thermostat_1",
            "REMOTE_CONTROL"
        )

        device_states[
            "hallway_thermostat_1"
        ] = "REMOTE_CONTROL"


# HOME MODE
    elif mode == "home":

    # Living Room Camera
     if device_capability_check(
        "living_room_camera_1",
        "DISABLE_VIDEO"
    ):

        apply_risk_based_permission(
        "living_room_camera_1",
        "DISABLE_VIDEO",
        mode,
        user_location,
        device_states
    )


    # Bathroom Camera
    if device_capability_check(
        "bathroom_camera_1",
        "DISABLE_VIDEO"
    ):

        apply_risk_based_permission(
        "bathroom_camera_1",
        "DISABLE_VIDEO",
        mode,
        user_location,
        device_states
    )

    # Living Room Speaker
    if device_capability_check(
        "living_room_speaker_1",
        "WAKE_WORD_ONLY"
    ):

        apply_audio_risk_permission(
        "living_room_speaker_1",
        "WAKE_WORD_ONLY",
        mode,
        user_location,
        device_states
    )

    # Front Door Lock
    if device_capability_check(
        "front_door_lock_1",
        "AUTO_LOCK_OFF"
    ):

        send_command(
            "front_door_lock_1",
            "AUTO_LOCK_OFF"
        )

        device_states[
            "front_door_lock_1"
        ] = "AUTO_LOCK_OFF"


# EMERGENCY MODE
    elif mode == "emergency":

    # Living Room Camera
     if device_capability_check(
        "living_room_camera_1",
        "ENABLE_VIDEO"
    ):

        apply_risk_based_permission(
        "living_room_camera_1",
        "ENABLE_VIDEO",
        mode,
        user_location,
        device_states
    )


    # Bathroom Camera
    if device_capability_check(
        "bathroom_camera_1",
        "ENABLE_VIDEO"
    ):

        apply_risk_based_permission(
        "bathroom_camera_1",
        "ENABLE_VIDEO",
        mode,
        user_location,
        device_states
    )


    # Front Door Camera
    if device_capability_check(
        "front_door_camera_1",
        "ENABLE_VIDEO"
    ):

        apply_risk_based_permission(
        "front_door_camera_1",
        "ENABLE_VIDEO",
        mode,
        user_location,
        device_states
    )

    # Living Room Speaker
    if device_capability_check(
        "living_room_speaker_1",
        "ENABLE_MIC"
    ):

        apply_audio_risk_permission(
        "living_room_speaker_1",
        "ENABLE_MIC",
        mode,
        user_location,
        device_states
    )

    # Front Door Lock
    if device_capability_check(
        "front_door_lock_1",
        "AUTO_LOCK_OFF"
    ):

        send_command(
            "front_door_lock_1",
            "AUTO_LOCK_OFF"
        )

        device_states[
            "front_door_lock_1"
        ] = "AUTO_LOCK_OFF"


    # Thermostat
    if device_capability_check(
        "hallway_thermostat_1",
        "TEMPERATURE_MONITORING"
    ):

        send_command(
            "hallway_thermostat_1",
            "TEMPERATURE_MONITORING"
        )

        device_states[
            "hallway_thermostat_1"
        ] = "TEMPERATURE_MONITORING"


    return device_states



@app.route("/")
def home():


    
    mode_data = smart_home_mode_controller(
        manual_mode=manual_mode,
        event_type="panic" if panic_triggered else None
    )

    event_type = "panic" if panic_triggered else mode_data.get("event_type", None)


    if mode_data["mode"] == "away":

        context_data = {

            "user_presence": "away",
            "time_of_day": get_time_of_day(),
            #"event_type" :"panic" if panic_triggered else None,
            "event_type" : event_type,
            "user_location": "outside home",
            "network_security": "trusted",
            "system_status": "Monitoring remotely"
        }

    elif mode_data["mode"] == "home":

        context_data = {

            "user_presence": "home",
            "time_of_day": get_time_of_day(),
            "event_type" :event_type,
            "user_location": "living room",
            "network_security": "trusted",
            "system_status": "Privacy optimized"
        }

    elif mode_data["mode"] == "emergency":

        context_data = {

            "user_presence": "unknown",
            "time_of_day": get_time_of_day(),
            "event_type" : "panic" if panic_triggered else mode_data.get ("reason", "emergency"),
            "user_location": "security breach detected",
            "network_security": "alert mode",
            "system_status": "Emergency response active"
        }
    

    risk_score = calculate_risk(
    "living_room_camera_1",
    "ENABLE_VIDEO",
    mode_data["mode"],
    context_data["user_location"]
)

    device_states = apply_device_permissions(mode_data, context_data["user_location"])



    return render_template (
        "index.html",
        mode=mode_data,
        devices=device_states, 
        capabilities=supported_capabilities,
        logs=alert_log,
        context=context_data,
        risk_score=risk_score
)

@app.route("/panic", methods=["POST"])
def panic():
    global panic_triggered
    panic_triggered= True
    log_event("PANIC BUTTON ACTIVATED")

#return redirect(url_for("home"))
    return{
       "status": "success"
    }

    

    

@app.route("/reset", methods=["POST"])
def reset():

    global panic_triggered

    panic_triggered = False

    log_event("Emergency mode cleared")

    return {
        "status": "success"
    }

#Manual Switch Mode Router

@app.route("/set_mode", methods=["POST"])
def set_mode():

    global manual_mode
    global panic_triggered

    data = request.json
    manual_mode = data["mode"]

#Clear panic state when manually switching modes
    panic_triggered = False
    log_event(f"{manual_mode.capitalize()} mode manually selected")

    return {"status": "ok"}
#log_event(f"Manual mode set to {mode}")



if __name__ == "__main__":

    app.run(debug=False)
