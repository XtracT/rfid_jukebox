# 🎵 RFID Jukebox: A Home Assistant + Music Assistant tag based jukebox! 

The goal is to create a simple, robust, and kid-friendly way to play music using physical RFID tags. This project is inspired by the desire for a less complex alternative to solutions like Phoniebox, leveraging the power and flexibility of Home Assistant, ESPHome or squeezelite-esp32, and Music Assistant. In order to achieve that, this repository provides: 

- A Bill of Materials and tutorial on how to make a toddler-targeted jukebox 
- An EspHome yaml file to add RFID reader, buttons and knob functionality. 
- A custom integration for Home Assistant that connects the ESP32 connected RFID reader to the required media player. 

Therefore, the main contribution is the integration. There are many different ways to achieve this setup though, so contributions are welcome! 

This is the list of used hardware:
- 1 [Louder-ESP32S3 by Sonocotta](https://www.tindie.com/products/sonocotta/louder-esp32s3/)
- 2 pcs [AIYIMA speakers](https://www.aliexpress.com/item/1005003690882286.html?spm=a2g0o.order_list.order_list_main.57.645a5c5fcSl91U)
- 1 PN532 
- 1 [keyes 040 knob](https://www.amazon.de/KEYESTUDIO-Encoder-Development-Arduino-Raspberry/dp/B085944A4G)
- 2 pcs cherry mx style switches, any style will do 
- any esp32 dev board
- an optional type Cpower bank
- The enclosure is 3D printed, you will be able to find the files and BOM [here](https://www.pending.com)


## Quick go through

1. Flash squeezelite-ESP32 to the Louder-ESP32S3
2. Connect it to Music Assistant (you need to point it to it's ip, do not add the port)
3. Connect the PN532 (or any other RFID reader supported by EspHome) to the ESP32 board, and the optional knob and buttons. 
4. Flash the ESP32 using EspHome and the provided yaml (modify as required). 
5. Add the integration to home assistant, that makes everything work together. 
6. Map tags to Music Assistant playlists, enjoy your toddler friendly jukebox! 

## 🎯 Core Features of the Home Assistant Integrations. 
 
*   **Tag-Based Playback**: Scan an RFID tag to instantly play the linked Music Assistant playlist.
*   **Seamless Control**: Play, pause, or resume music directly from tag presence.
*   **Simple Mapping UI**: A user-friendly interface within Home Assistant to map new RFID tags to playlists.
*   **Unknown Tag Alerts**: Get notified via TTS when an unmapped tag is scanned.
*   **Standalone & Integrated**: Works with any RFID reader that can publish tag IDs to an HA entity (e.g., via ESPHome or MQTT).

## ⚙️ Configuration

This integration is configured via the Home Assistant UI.

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration** and search for **RFID Jukebox**.
3.  Follow the on-screen instructions to configure the integration. You will need to provide:
    *   **Tag Sensor**: The `sensor` or `input_text` entity that provides the RFID tag ID.
    *   **Media Player**: The media player to control.
    *   **Unmapped Tag TTS Message** (Optional): The message to announce when an unmapped tag is scanned.
    *   **TTS Service** (Optional): The TTS service to use for announcements.

## 🎛️ Entities

This integration automatically creates the following entities to provide a simple UI for mapping tags:

-   **`sensor.rfid_jukebox_last_tag`**: Displays the ID of the last scanned RFID tag.
-   **`text.rfid_jukebox_playlist_to_map`**: A text field where you will type the exact name of the Music Assistant playlist you want to map.
-   **`button.rfid_jukebox_map_tag_button`**: A button that, when pressed, maps the last scanned tag to the playlist name you entered in the text field.

## 🏷️ How to Map a New Tag

Mapping a new tag is a simple, three-step process:

1.  **Scan the new RFID tag.** The `sensor.rfid_jukebox_last_tag` entity will update to show its ID.
2.  **Type the exact name** of the desired Music Assistant playlist into the `text.rfid_jukebox_playlist_to_map` field on your dashboard.
3.  **Press the `Map Scanned Tag` button.** The integration will save the mapping, and the tag is ready to use.

## 🔧 Services

The integration provides services for advanced control and automation:

-   **`rfid_jukebox.map_tag`**: (Advanced) Allows mapping a tag via an automation or script. Accepts `tag_id` and `playlist_name`. The UI button calls this service internally.
-   **`rfid_jukebox.reload_mappings`**: Manually reloads the tag-to-playlist mappings from the YAML file without restarting Home Assistant.

## TODO
- Automatically reload tag mapping
- Make sure that tags can be edited/remaped (removing is not relevant)
- Fix the TTS playback, does not seem to work
- Text in the config flow is not in strings

## ESPHome Firmware

Below is a complete, working ESPHome configuration that you can use as a starting point for your own RFID jukebox. This firmware is designed to work with the `rfid_jukebox` custom integration and provides physical controls for playback.

### Features

*   **RFID Reader**: Uses a PN532 I2C RFID reader to scan tags.
*   **Physical Buttons**: Provides buttons for previous track, play/pause, and next track.
*   **Rotary Encoder**: Allows for volume control by turning the knob and toggles play/pause by pressing it.
*   **Direct Media Player Control**: Interacts directly with a specified Home Assistant `media_player` entity.
*   **Configurable**: The target `media_player` entity can be easily changed in one place.
*   

### Alternative

It should be possible to flash the Louder-ESP32S3 with [the yaml provided by Sonocotta](https://github.com/sonocotta/esp32-audio-dock/blob/main/firmware/esphome/louder-esp32-s3-idf.yaml) , with the extra extra sensors / devices added by the configuraiton provided in this repository. However, take into account that: 
- The Louder-ESP32S3 is not designed to make it easy to add two switches, one knob and the I2C based PN532. Therefore you need to figure out the pinout and solder in the tespoints. 
- You lose some of the features provided by Squeezelite-ESP32. 

However, it could lead to a cleaner hardware setup and **maybe** a faster start-up time, although I have not tested how fast the esphome is available. In any case, let me know if you try this! 


## Out of scope  for the project

For now: 
-   **Control Tags**: Special tags for actions (Volume, skip, toggle). 
-   **Different RFID tag behavior**: Keeping the tag readable is the easiest, most intuitive and simplest to implement way of interacting with the jukebox. 
-   


Disclaimer: Mostly vibe coded. 

