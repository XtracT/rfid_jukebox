# 🎵 RFID Jukebox: A Home Assistant Music Assistant Controller

Disclaimer: Mostly vibe coded. 

This custom integration for Home Assistant turns any RFID reader into a seamless music jukebox powered by Music Assistant. The goal is to create a simple, robust, and kid-friendly way to play music using physical RFID tags.

This project is inspired by the desire for a less complex alternative to solutions like Phoniebox, leveraging the power and flexibility of Home Assistant, ESPHome or squeezelite-esp32, and Music Assistant. 

The intended hardware, at the moment of writing, is a loud-esp32 by sonocotta. This section will be expanded as the project advances. 

## 🎯 Core Features
 for 
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
- Test in the config flow is not in strings

## ESPHome Firmware

Below is a complete, working ESPHome configuration that you can use as a starting point for your own RFID jukebox. This firmware is designed to work with the `rfid_jukebox` custom integration and provides physical controls for playback.

### Features

*   **RFID Reader**: Uses a PN532 I2C RFID reader to scan tags.
*   **Physical Buttons**: Provides buttons for previous track, play/pause, and next track.
*   **Rotary Encoder**: Allows for volume control by turning the knob and toggles play/pause by pressing it.
*   **Direct Media Player Control**: Interacts directly with a specified Home Assistant `media_player` entity.
*   **Configurable**: The target `media_player` entity can be easily changed in one place.

## Out of scope  for the project

For now: 
-   **Control Tags**: Special tags for actions (Volume, skip, toggle). 
-   **Different RFID tag behavior**: Keeping the tag readable is the easiest, most intuitive and simplest to implement way of interacting with the jukebox. 
-   

