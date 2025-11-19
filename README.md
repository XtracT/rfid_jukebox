# 🎵 Owlbox ( RFID Jukebox / Phoniebox )

<p align="center">
  <img src="owlbox.png" alt="Jukebox" width="320">
</p>

A simple, kid-proof jukebox you can build with an ESP32 based DAC amplifier, a PN532 RFID reader, and a pair of speakers. 
This build focuses on **ESPHome** for device firmware, **Music Assistant** for playback, and **Home Assistant** for orchestration/UI.

---

## ✨ Highlights

- **Present a tag → music starts** (Music Assistant folder or playlist)
- **Remove tag → music pauses**
- **Present the same tag → music resumes**, **new tag → start playing new media**
- **Rotary encoder** for volume, **buttons** for prev/next
- **HA Mute button** to make sure your toddler does not start partying at night.
- Fully controllable / scriptable from Home Assistant
- You can also use it as a wifi speaker!

---

## 🧱 Owlbox Hardware

- [Louder-ESP32S3](https://sonocotta.com/louder-esp32/) (from Sonocotta, highly recommended!)
    - Pinouts in the sample YAMLs target Louder-ESP32S3 + PN532 (SPI). Adjust as needed.
- PN532 RFID reader (**SPI** recommended)
    - I²C hasn’t been tested here to avoid interfering with the DAC interface.
- Rotary encoder (e.g., Keyestudio 040)
- 2× momentary buttons
- Passive speakers + 5V/3A power (enough for a kid!)
- And if you have a 3D printer: [3D-printed enclosure](https://makerworld.com/en/models/1914879)

---

## 🚀 Quick Start 

### 1) Flash the basic ESPHome firmware
- Use `esphome/jukebox.yaml`.
- Adjust pins to your wiring.
- Compile & flash with ESPHome.

### 2) Install the integration via HACS
- In Home Assistant: **HACS → Integrations → Search “RFID Jukebox” → Install**.  
  If it’s not listed yet, add this repo as a **Custom Repository** (category: *Integration*), then install via HACS.
- **Restart Home Assistant**.

### 3) Add the integration
- Go to **Settings → Devices & Services → Add Integration → RFID Jukebox**.
- Select:
  - The **RFID tag sensor** (from ESPHome, e.g. `text_sensor.rfid_jukebox_tag`)
  - Your **Music Assistant player** entity (e.g. `media_player.jukebox_*`)
  - Your **Music Assistant Filesystem ID** (e.g. `filesystem_local--tkx9ahNv`). This is required for playing folders.
  - Tip: you can discover `<filesystem_id>` in Music Assistant UI (top bar), e.g. `filesystem_local--tkx9ahNv`.

### 4) Map tags from the HA UI
- Scan a tag → `sensor.rfid_jukebox_last_tag` updates.
- Select the media type (`playlist` or `folder`).
- Enter the media name (e.g., "Kids Party Time" or "audiobooks/stories_for_kids").
- Optionally, enter an alias for the tag (e.g Snoopy).
- Press `button.rfid_jukebox_map_tag_button`. Done!

---

## Further details

**Integration:** `homeassistant/custom_components/rfid_jukebox`  
**ESPHome Firmware:** `esphome/jukebox.yaml`

What it does:
- ESPHome publishes the tag to HA (`text_sensor`).
- The integration maintains the **tag → folder** mapping and calls Music Assistant.
- ESPHome starts reproducing your media. 

**Integration UI entities:**
- `sensor.rfid_jukebox_last_tag` — last scanned UID
- `select.rfid_jukebox_media_type` — choose between `playlist` and `folder`
- `text.rfid_jukebox_media_name_to_map` — enter the name of the media
- `text.rfid_jukebox_alias` — optionally, provide a friendly name for the tag
- `button.rfid_jukebox_map_tag_button` — save the mapping

**Mapping File (`rfid_mappings.yaml`):**

The integration supports a mapping format that includes aliases and media types.

```yaml
"01:23:45:67:89:AB":
  alias: "Kids' Party Mix"
  type: "playlist"
  name: "Kids Party Time"
"CD:EF:01:23:45:67":
  alias: "Bedtime Stories"
  type: "folder"
  name: "audiobooks/stories_for_kids"
```
This makes it easy to keep track of the tags and mappings. 

**Mute Functionality:**

The firmware includes a software-based mute feature, perfect for controlling playback times without physical intervention. When muted, the volume is set to 0%, and the rotary encoder is disabled, preventing manual volume changes. For example, you can create a Home Assistant automation to mute the jukebox from 8 PM to 8 AM.

---

## 🗺️ Roadmap

- Improve reliability and startup behavior
- Test with **snapclient** 

---

## 🤝 Contributing

PRs and issues welcome! Add support for other boards/readers, improve playback, docs, or reliability.

---

## 🙏 Acknowledgements

- [Phoniebox](https://phoniebox.de/index-en.html)
- [ESPHome](https://esphome.io/)
- [Music Assistant](https://music-assistant.io/)
- Sonocotta’s Louder-ESP32S3 & TAS5805M component
- Everyone building kid-friendly players and sharing their tricks 💿🧸
