# West Loop October 22 capture transfer

Source: [West Loop Drive parent](https://drive.google.com/drive/folders/1hoU32tEZnDe_yZNE_OBcqmMttzM3l5gp) through the local `gdrive:` remote. Destination: `rustfs:sideseeing/chicago/west-loop/` in the `sideseeing` bucket.

On 23 October 2026, the source parent contained eight capture folders. The first four (October 19 and 20) were already in the RustFS destination. The four **new** folders selected here are:

| Capture folder | Drive files | Source video size |
|---|---:|---:|
| `2026-10-22-15-05-58-722` | 9 | 3,996,796,766 bytes |
| `2026-10-22-15-09-20-275` | 9 | 4,555,933,299 bytes |
| `2026-10-22-15-37-28-260` | 9 | 4,272,404,029 bytes |
| `2026-10-22-15-44-19-995` | 9 | 4,713,955,010 bytes |

The exact 36 source paths are in [west-loop-2026-10-22-files.txt](west-loop-2026-10-22-files.txt). That file limits `rclone copy` to these capture contents and preserves the folder names. The parent also has ZIP copies of capture folders; those ZIP files are excluded. Source and destination copies are kept; no `sync` or `move` is used.

The transfer was started on 23 October at 10:59 Chicago time with a 45-minute soft cutoff. The local log is `west-loop-2026-10-22-transfer.log` (gitignored). A cutoff or shutdown can leave incomplete files. Rerun this same command to skip matching completed files and retry the rest:

```bash
cd /home/renzo/Documents/GitHub/sideseeing-network
rclone copy gdrive: rustfs:sideseeing/chicago/west-loop \
  --drive-root-folder-id 1hoU32tEZnDe_yZNE_OBcqmMttzM3l5gp \
  --files-from network/docs/datasets/west-loop-2026-10-22-files.txt \
  --checksum --immutable --transfers 2 --checkers 4 \
  --max-duration 45m --cutoff-mode SOFT \
  --stats 30s --stats-one-line --log-level INFO \
  --log-file network/data/_transfers/west_loop/west-loop-2026-10-22-transfer.log
```

After rclone exits successfully, compare all 36 selected objects with Drive:

```bash
rclone check gdrive: rustfs:sideseeing/chicago/west-loop \
  --drive-root-folder-id 1hoU32tEZnDe_yZNE_OBcqmMttzM3l5gp \
  --files-from network/docs/datasets/west-loop-2026-10-22-files.txt \
  --one-way
```

If a session stops because the 45-minute window was reached, rclone exits with code 10; the copy is still incomplete. Wait for the current session to exit before rerunning. The shared Google Drive client ID used by `gdrive:` is being retired during 2026; rclone emits a warning to configure a private client ID before relying on it long term. No credentials are in this repository.

## October 26 captures (copied 27 October)

On 27 October 2026 the Drive parent had two new capture folders, each with the same nine files. Their ZIP copies and a stray `Untitled0.ipynb` were left out.

| Capture folder | Drive files | Source video size |
|---|---:|---:|
| `2026-10-26-15-45-51-706` | 9 | 2,164,747,150 bytes |
| `2026-10-26-16-03-17-016` | 9 | 2,178,632,875 bytes |

The same commands as above, with `west-loop-2026-10-26-files.txt` (18 paths) and the log `west-loop-2026-10-26-transfer.log`, without the 45-minute cutoff. `rclone copy` exited 0, and `rclone check --one-way` found 0 differences and 18 matching files.

## October 28 captures (started 30 October)

On 30 October 2026 the Drive parent had six new capture folders, each with the same nine files. Their ZIP copies and `Untitled0.ipynb` were left out.

| Capture folder | Drive files | Source video size |
|---|---:|---:|
| `2026-10-28-14-57-02-508` | 9 | 4,730,144,307 bytes |
| `2026-10-28-14-58-55-237` | 9 | 7,437,331,569 bytes |
| `2026-10-28-15-35-30-813` | 9 | 2,890,582,088 bytes |
| `2026-10-28-16-05-45-365` | 9 | 7,028,721,089 bytes |
| `2026-10-28-16-17-44-943` | 9 | 590,746,555 bytes |
| `2026-10-28-16-23-17-112` | 9 | 7,513,179,335 bytes |

Same commands as above, with `west-loop-2026-10-28-files.txt` (54 paths), the log `west-loop-2026-10-28-transfer.log`, and no cutoff. The run adds `--s3-upload-cutoff 64M --retries 10 --retries-sleep 60s`, because RustFS repeatedly dropped a ~190 MB single-request upload during the Brás copy, while multipart uploads succeeded. The copy and its `rclone check --one-way` run detached, and both exit codes are appended to `west-loop-2026-10-28-exit-code.txt`. Result (30 October 14:52): copy exit 0, and `rclone check --one-way` found 0 differences and 54 matching files.
