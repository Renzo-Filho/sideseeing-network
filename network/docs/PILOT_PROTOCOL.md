# Near West Side pilot: field protocol

Renzo will collect this pilot **alone**, using a **moto g 5G (2023)**, the MultiSensor app, and the collection vest. The aim is to test whether one phone can produce usable video, GPS, and inertial data along the chosen walking routes.

## 1. Chosen location and routes

![Pilot map with blue passages and pink, green, and red walking arrows](pilot-routes-hand-drawn.png)

The pilot covers the **drawn passages between S Aberdeen St and S Morgan St, from W Polk St to W Taylor St**. The **colored arrows** show where and in which direction to walk. Ignore the Google Maps white circles and A/B markers. The drawing is a field guide, so check the actual path and crossing on site.

| Route | Area | Recording ID |
|---|---|---|
| **Pink** | Aberdeen to Carpenter, including the drawn Cabrini and Arthington links | P01 |
| **Green** | Carpenter to Miller, including the drawn mid-block paths | G01 |
| **Red** | Miller to Morgan, including the drawn mid-block links | R01 |

Record pink, then green, then red. They may be completed on different days. **Do not record UIC campus sidewalks or private passages.** The drawn public paths around Samuel Miller Park are included as a **pilot exception**; report them separately from street-adjacent sidewalks. A path that is closed or inaccessible stays in the log as a gap.

## 2. App setup and what to carry

**Set up MultiSensor before going to the pilot area:**

- Charge the phone, free enough storage for the planned outing, allow camera and precise location access, and turn **Battery Saver off**. Motorola's [guide](https://help.motorola.com/hc/help.php?c=&m=MOTO+G+5G+-+2023&os=&product=&sku=&type=pdf) says Battery Saver can stop location services when the screen is off.
- Mount the phone in the vest. Check that the video shows the sidewalk ahead and the full crossing approach without the vest blocking the view.
- Make a short **test recording (T00)** with a straight walk and a turn. Save it, play the video, and inspect the export for GPS and inertial files with usable timestamps. If any essential stream is missing, fix the setup and repeat the test before starting P01. Keep the same tested settings for all three routes.

**Carry:** the charged phone in its vest, a paper or offline copy of the route map, a simple field log, and a power bank/cable if available. In the log, note the Android and MultiSensor versions, camera setting, and phone orientation.

## 3. Rules for the field agent

1. **Prepare each route.** At a safe standing place, mark its actual start and finish on the map. Follow the arrows; if two drawn passages do not join directly, label the connecting walk as **repositioning**.
2. **Cover the drawn passages.** Walk each physical sidewalk side once in the arrow direction, at an ordinary pace. The opposite side of a street is a separate passage. Record the drawn public mid-block paths, but keep them in the separate pilot-exception category.
3. **Record crossings continuously.** Keep the camera and sensors running through the approach, wait, legal crossing, and arrival. A crossing seen from the sidewalk does not count as traversed. Do not take a diagonal road shortcut unless the marked crossing itself is diagonal.
4. **Make route joins visible.** Near Carpenter/Taylor, choose and mark a short section of the **same physical sidewalk** to record in both pink and green (**O-PG**). Do the same near Miller/Taylor for green and red (**O-GR**). Note the actual endpoints. Count each shared section once in unique coverage.
5. **Keep the phone fixed in the vest.** Do not handle it while walking or crossing. If the view fails, stop safely, note the problem, and retake the affected passage under a new recording ID.
6. **Log changes honestly.** Note missed turns, closed paths, interruptions, repositioning, and repeats. Do not treat a detour or a map line as proof of a sidewalk connection.
7. **Check every session before moving on.** Confirm that the recording saved and the video plays. Log the recording ID (P01/G01/R01), original MultiSensor folder, start/end landmarks and times, passages and crossings actually covered, overlaps, and problems. Give restarts new IDs such as P02; keep failed files.
8. **Preserve the raw data.** After each outing, copy the original folders intact and check that the video, GPS, and inertial files copied before deleting anything from the phone. Mark each target **usable**, **needs revisit**, **unavailable**, or **excluded**. Revisit only missing or unusable targets; never silently edit the GPS points.

The pilot is complete when every eligible drawn passage and planned crossing has a recorded outcome, the original files are preserved, and the two overlaps and any gaps are documented. The [route plan](PILOT_NEAR_WEST_SIDE.md) and [broader collection protocol](COLLECTION_PROTOCOL.md) contain the research rationale and later-study details.
