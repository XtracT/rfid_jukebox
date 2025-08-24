# 🎵 RFID Jukebox: A DIY Jukebox for Home Assistant

Welcome! This project provides everything you need to build a simple, robust, and kid-friendly jukebox using RFID tags, an ESP32, and the power of Home Assistant.

The goal is to create a standalone music player that's easy for anyone to use—just place a card on the box, and music starts playing. It's a modern take on the classic jukebox, built with modern, open-source tools.

This repository contains:
-   A complete **Bill of Materials (BOM)** and guide for building the hardware.
-   A pre-configured **ESPHome firmware** for a dedicated "controller" ESP32 that handles the RFID reader, buttons, and volume knob.
-   A **Home Assistant custom integration** that ties everything together, managing the RFID tags and controlling the ESPHome media player.

## 🎯 Core Features

*   **Standalone Operation**: No need for external services like Music Assistant or LMS. Your music plays directly from a local folder.
*   **Tag-Based Playback**: Scan an RFID tag to instantly play the corresponding folder of music.
*   **Seamless Control**: Removing the tag pauses the music; placing it back resumes playback.
*   **Physical Controls**: Use physical buttons and a knob for play/pause, next/previous track, and volume control.
*   **Simple Mapping UI**: A user-friendly interface within Home Assistant to map new RFID tags to music folders.
*   **Automatic Advancement**: When a song finishes, the next track in the folder plays automatically.
*   **"Now Playing" Context**: The integration provides a virtual media player that shows the current track, artist, and album in the Home Assistant UI.

---

## �️ The Build: Hardware & Assembly

This build uses a two-board ESP32 design for simplicity: one board acts as the audio player, and a second board acts as the physical controller.

### Bill of Materials (BOM)

| Component                   | Quantity | Notes                                                                        |
| --------------------------- | :------: | ---------------------------------------------------------------------------- |
| Louder-ESP32S3              |    1     | **The Player**: An ESP32 with a built-in amplifier.                          |
| A generic ESP32 Dev Board   |    1     | **The Controller**: A cheap ESP32 to handle the physical inputs.             |
| AIYIMA Speakers             |    2     | 10W 4 Ohm speakers. Basically selected for the copper color.                 |
| PN532 RFID Reader           |    1     | The I2C version is used in this guide. Connects to the **Controller** ESP32. |
| Keyes KY-040 Rotary Encoder |    1     | For volume control. Connects to the **Controller** ESP32.                    |
| Cherry MX Style Switches    |    2     | For next/previous track buttons. Connects to the **Controller** ESP32.       |
| 3D Printed Enclosure        |    1     | Files will be made available separately.                                     |
| USB-C Panel Mount           |    1     | For a clean external power connection.                                       |
| Power Bank                  |    1     | Optional, for making the jukebox portable.                                   |
| Wires, Screws, Inserts      | Various  | M3 screws and threaded inserts are needed for the enclosure.                 |

---

## 🚀 Setup Guide

### Step 1: Prepare Your Music Library (Optional, but Recommended)

This integration plays music from a folder inside your Home Assistant `config` directory. For a large music library, mounting a network share (like from a NAS) is the best approach.

<details>
<summary>Click to see an example `docker-compose.yml` for mounting an NFS share</summary>

Here is an example of how to mount a read-only NFS share into your Home Assistant Docker container.

1.  **Edit your `docker-compose.yml`** to add the volume mapping under the `homeassistant` service:
    ```yaml
    services:
      homeassistant:
        # ... your other config ...
        volumes:
          - /path/to/your/config:/config
          # Add this line to mount the music volume
          - jukebox_music_data:/config/www/jukebox_music:ro
    ```

2.  **Define the volume** at the end of your `docker-compose.yml`:
    ```yaml
    volumes:
      # ... other volumes ...
      jukebox_music_data:
        driver_opts:
          type: "nfs"
          o: "addr=192.168.1.61,nfsvers=4,ro" # Change the IP to your NAS IP
          device: ":/mnt/storage/phoniebox"   # Change this to the path on your NAS
    ```
> **Note:** The default music path for the integration is `/config/www/jukebox_music`. If you use a different path, make sure you use the same path when configuring the integration in Home Assistant.

</details>

### Step 2: Flash the ESPHome Firmware

This setup uses two ESP32 boards.

1.  **Flash the Player (Louder-ESP32S3)**:
    *   Use the official [ESPHome YAML from Sonocotta](https://github.com/sonocotta/esp32-audio-dock/blob/main/firmware/esphome/louder-esp32-s3-idf.yaml).
    *   This will create the `media_player` entity in Home Assistant that plays the music.

2.  **Flash the Controller (Generic ESP32)**:
    *   Connect the PN532, buttons, and rotary encoder to this ESP32.
    *   Open the `esphome/jukebox.yaml` file from this repository.
    *   Modify your Wi-Fi credentials and flash it. This will create the RFID `text_sensor` and button entities.

> **Advanced Alternative**: It is theoretically possible to use a single Louder-ESP32S3 for everything. However, this would require soldering the buttons, knob, and RFID reader to the board's small test points, which is difficult. The two-board approach is much simpler.

### Step 3: Install and Configure the Home Assistant Integration

1.  **Install**: Use HACS to install the "RFID Jukebox" integration, or manually copy the `custom_components/rfid_jukebox` folder into your `custom_components` directory.
2.  **Restart Home Assistant**.
3.  **Add Integration**: Go to **Settings > Devices & Services**, click **Add Integration**, and search for **RFID Jukebox**.
4.  **Configure**: The setup wizard will ask for:
    *   **Tag Sensor**: The `text_sensor` from your **Controller** ESP32 (e.g., `text.rfid_jukebox_tag`).
    *   **Media Player**: The `media_player` entity from your **Player** ESP32 (e.g., `media_player.pau_phonie`).
    *   **Music Folder**: The path to your music library. The default is `/config/www/jukebox_music`.

---

## 🎶 How to Use the Jukebox

### Mapping a New Tag

To map a tag, you need a UI in your Lovelace dashboard.

<details>
<summary>Click to see an example Lovelace card for mapping tags</summary>

This card provides a simple UI to see the last scanned tag and map it to the folder name you type in.

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    subtitle: Map the last scanned tag to a folder
  - type: custom:layout-card
    layout_type: grid
    layout:
      grid-template-columns: 70% 30%
      grid-gap: 12px
    cards:
      - type: entities
        show_header_toggle: false
        entities:
          - entity: text.rfid_jukebox_folder_to_map
            name: Last read folder/ID, type to map new
        card_mod:
          style: |
            ha-card { box-shadow: none; background: transparent; padding: 0; }
            .card-content, .mdc-list { padding: 0 !important; }
            .mdc-list-item {
              min-height: 56px;
              padding: 0 12px !important;
              border: 1px solid var(--divider-color);
              border-radius: var(--ha-card-border-radius, 12px);
            }
            ha-icon { display: none !important; }
      - type: custom:mushroom-template-card
        primary: Map
        icon: mdi:link-variant
        icon_color: green
        fill_container: true
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.rfid_jukebox_map_last_tag
        disabled: "{{ states('text.rfid_jukebox_folder_to_map')|length == 0 }}"
        card_mod:
          style: >
            ha-card { min-height: 56px; display:flex; align-items:center;
            justify-content:center; }
```

</details>

**To map a tag:**
1.  **Scan a new RFID tag.** The `sensor.rfid_jukebox_last_tag` entity will update.
2.  **Enter the folder name** in the Lovelace card you just created.
3.  **Press the `Map` button.** The mapping is saved, and the tag is ready to use!

### Controlling Playback

You can control the jukebox in a few ways:
-   **Physical Controls**: Use the buttons and knob on the jukebox itself.
-   **Home Assistant UI**: Use the media player card for your ESPHome device.
-   **Services**: Use the provided services in your automations or scripts.

#### Service Call Examples

Here are examples of how to call these services from the **Developer Tools > Services** tab.

**Play/Pause:**
```yaml
service: media_player.media_play_pause
target:
  entity_id: media_player.rfid_jukebox # <-- This is the virtual media player
```

**Next Track:**
```yaml
service: media_player.media_next_track
target:
  entity_id: media_player.rfid_jukebox # <-- This is the virtual media player
```

**Previous Track:**
```yaml
service: media_player.media_previous_track
target:
  entity_id: media_player.rfid_jukebox # <-- This is the virtual media player
