# 🎵 RFID Jukebox — ESPHome + Music Assistant + Home Assistant

A dead-simple, kid-proof jukebox you can build with an ESP32, a PN532 RFID reader, and Music Assistant.
This repo focuses on **ESPHome** for device firmware, **Music Assistant** for playback, and **Home Assistant** for orchestration/UI.

You can achieve the same result in two ways. **Recommended is the HA-centric path (easier to manage, fewer moving parts).**  
The ESPHome-only “AIO” is provided as an advanced option.

- **Option 1 — Home Assistant-centric (Recommended):**  
  ESPHome only reports the tag. A custom **HA integration** (HACS install) keeps the mapping and fires the Music Assistant call. Best for lots of tags, central tag mapping, backups, and multi-room.
- **Option 2 — ESPHome-centric “AIO” (Advanced):**  
  Tag → folder mapping is stored **on the device** (ESP-NVS). The ESP32 calls `music_assistant.play_media` directly. Lowest latency, but more firmware logic and less convenient mapping/backup.

---

## ✨ Highlights

- **Present a tag → music starts** (Music Assistant folder)
- **Remove tag → pause**
- **Hold the same tag → resume**, **new tag → start playing new folder**
- **Rotary encoder** for volume, **buttons** for prev/next
- Two approaches (device-centric vs HA-centric), switchable

---

## 🧱 Hardware (tested)

- Louder-ESP32S3 (by Sonocotta, highly recommended!) or any ESP32 with I²S DAC/amp  
- PN532 RFID reader (**SPI** tested; **I²C** likely fine but **not tested** here)  
- Rotary encoder (e.g., Keyestudio 040)  
- 2× momentary buttons  
- Passive speakers + 5V/3A power (enough for a kid!)
- Optional 3D-printed enclosure (files/link coming soon)

> Pinouts in the sample YAMLs target Louder-ESP32S3 + PN532 (SPI). Adjust as needed.  
> I²C hasn’t been tested here to avoid interfering with the DAC interface.

---

## 🚀 Quick Start (Recommended HA-centric path)

### 1) Install the integration via HACS
- In Home Assistant: **HACS → Integrations → Search “RFID Jukebox” → Install**.  
  If it’s not listed yet, add this repo as a **Custom Repository** (category: *Integration*), then install via HACS.
- **Restart Home Assistant**.

### 2) Add the integration
- Go to **Settings → Devices & Services → Add Integration → RFID Jukebox**.
- Select:
  - The **RFID tag sensor** (from ESPHome, e.g. `text_sensor.rfid_jukebox_tag`)
  - Your **Music Assistant player** entity (e.g. `media_player.jukebox_*`)
  - Your **Music Assistant Filesystem ID** (e.g. `filesystem_local--tkx9ahNv`). This is required for playing folders.

### 3) Flash the basic ESPHome firmware
- Use `esphome/jukebox.yaml`.
- Adjust pins to your wiring.
- Compile & flash with ESPHome.

### 4) Map tags from the HA UI
- Scan a tag → `sensor.rfid_jukebox_last_tag` updates.
- Select the media type (`playlist` or `folder`).
- Enter the media name (e.g., "Kids Party Time" or "audiobooks/stories_for_kids").
- Optionally, enter an alias for the tag.
- Press `button.rfid_jukebox_map_tag_button`. Done!

---

## 🎚️ Music Assistant basics used here

We play **folders** by calling:

```yaml
service: music_assistant.play_media
data:
  entity_id: media_player.YOUR_MA_PLAYER
  media_type: folder
  media_id: <filesystem_id>://folder/<folder_name>
```

Tip: you can discover `<filesystem_id>` in Music Assistant (UI/logs), e.g. `filesystem_local--tkx9ahNv`.

---

## 🅰️ Option 1 — HA-centric (Custom Integration) ✅

**Folder:** `homeassistant/custom_components/rfid_jukebox`  
**Firmware:** `esphome/jukebox.yaml` (basic: tag + buttons/encoder)

What it does:
- ESPHome publishes the tag to HA (`text_sensor`) and can emit HA events.
- The integration maintains the **tag → folder** mapping and calls Music Assistant.

**Integration UI entities:**
- `sensor.rfid_jukebox_last_tag` — last scanned UID
- `select.rfid_jukebox_media_type` — choose between `playlist` and `folder`
- `text.rfid_jukebox_media_name_to_map` — enter the name of the media
- `text.rfid_jukebox_alias` — optionally, provide a friendly name for the tag
- `button.rfid_jukebox_map_tag_button` — save the mapping

**Why this path:**
- Clean separation of concerns
- Easy to edit/backup/share mappings (HA backups, versioning)
- Scales to multiple readers/rooms

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
---

## 🅱️ Option 2 — ESPHome-centric “AIO” (Just for testing, advanced)

**File:** `esphome/jukebox-aio.yaml`

What it adds (on top of the basic YAML):
- **On-device mapping in NVS:** each tag (normalized UID) stores a folder string (`char[64]` by default; bump to 128 if you use long names).
- **Direct Music Assistant call** from ESPHome (builds `<fs>://folder/<name>`).
- **Resume vs start:** same tag → `media_player.play`, different tag → play new folder.
- **ESPHome UI:** `text.rfid_folder_to_map` + `button.map_current_tag → folder`.

**Getting started:**
1. Set `ma_filesystem`, `ma_entity`, and pins under `substitutions`.
2. Compile & flash with ESPHome.  
   *Note:* `ma_entity` is your MA player entity in HA. If you don’t know it yet, flash once to bring up the player, then update `ma_entity` and re-flash.
3. In the device page, set **RFID Folder to Map**, scan a tag, press **Map Current Tag → Folder**.
4. Scan mapped tags to play.

**When to use this:**
- You want device-level mapping and the smallest perceived latency.
- You’re fine managing mappings per device instead of centrally in HA.

---

## 🤔 Which one should I choose?

- **Choose HA-centric (Integration)** if you want the **simplest, most maintainable** setup, clean UI, and easy backups.  
- **Choose AIO** only if you specifically want **on-device mapping** and are comfortable with more ESPHome logic.

You can switch later—both target the same Music Assistant player.

---

## 🛠️ Troubleshooting

- **Works from Dev Tools, not on scan**  
  - Confirm `entity_id` is your **MA player**.  
  - Check logs for the `media_id` you’re calling: it must look like `<fs>://folder/<name>` and the folder must exist in MA.  
  - If using AIO, increase PN532 `update_interval` slightly (e.g. 400–700 ms) to avoid blocking HA calls during reads.

- **Same tag restarts instead of resuming**  
  - In AIO, ensure you update the “previous UID” **after** taking the action.

- **Mapping not found**  
  - AIO: map **after** scanning; avoid leading `/`; increase NVS buffer 64→128 for long names.  
  - Integration: check for **exact** match of the MA folder name.

---

## 🗺️ Roadmap

- Improve reliability and startup behavior
- Test with **snapclient** (once stable in ESPHome)

---

## 🤝 Contributing

PRs and issues welcome! Add support for other boards/readers, improve the mapping UX, docs, or reliability.

---

## 🙏 Acknowledgements

- [ESPHome](https://esphome.io/)
- [Music Assistant](https://music-assistant.io/)
- Sonocotta’s Louder-ESP32S3 & TAS5805M component
- Everyone building kid-friendly players and sharing their tricks 💿🧸
