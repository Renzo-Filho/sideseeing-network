# Brás transfer preflight

Status: **transfer runner prepared, 21 October 2026; no copy started**. No speed test has started. The selected source is the complete [`2025_Auditoria_Calcadas` Drive folder](https://drive.google.com/drive/folders/1cIKFRLeKXzYAJ7VakP9dHFL1T3GKDzrV); the other Brás link is incomplete and excluded. Destination paths and naming are in [README.md](README.md).

## Size and likely bottlenecks

The 21 October read-only Drive inventory gives the following selected workload:

| Part | Files | Decimal GB | Main cost |
|---|---:|---:|---|
| Raw `video.mp4` | 216 | 164.255 | Sustained download and upload throughput |
| Other raw capture files | 1,728 | 5.405 | File requests |
| JPEG image sequences | 68,063 | 30.734 | Many small-file requests |
| Low-resolution MP4s | 216 | 29.899 | Sustained throughput |
| Audit GPKG | 1 | 0.042 | Small; source-to-target name change |
| **Total** | **70,224** | **230.335** | Both bandwidth and request rate |

Drive and RustFS are different providers, so this copy will stream **through the machine running rclone**. It will download roughly 230 GB from Drive and upload roughly 230 GB to RustFS, without requiring a full 230 GB local staging copy. The machine must stay powered and connected. This follows rclone's [remote-copy FAQ](https://rclone.org/faq/) and [S3 upload documentation](https://rclone.org/s3/).

At sustained *effective end-to-end* speeds (limited by the slower of Drive downloads, the machine's network, and RustFS uploads), the data-volume-only time is:

| Effective transfer speed | 230.335 GB transfer time |
|---:|---:|
| 10 Mbit/s | 51.2 hours |
| 20 Mbit/s | 25.6 hours |
| 50 Mbit/s | 10.2 hours |
| 100 Mbit/s | 5.1 hours |

These are ideal lower bounds; they exclude listing, per-file setup, retries and verification. Rclone's [Google Drive documentation](https://rclone.org/drive/) says rate limiting can reduce many-small-file jobs to roughly **two files per second**. At that illustrative rate, 70,224 files take **about 9.8 hours** just to process, with 68,063 frames contributing nearly all of that. The data and file-rate limits can overlap in time, so do **not** add the two numbers. A realistic schedule needs a measured pilot on the intended machine and connection. Hospital transfer time is still unknown because its full source inventory is unavailable to the current `gdrive:` remote.

## Pilot before the bulk copy

1. Recheck the selected Drive counts, bytes and checksums, plus read access to the four source branches. Check RustFS write access and available bucket capacity without printing credentials.
   The current `gdrive:` remote emitted rclone's warning that it uses the shared Google Drive client ID, which [rclone says is being retired during 2026](https://rclone.org/drive/#making-your-own-client-id). Configure a private client ID before relying on a long migration. No ID or secret belongs in this repository.
2. Generate and review a local source-to-destination manifest. The 216 processed products use compact source timestamps but hyphenated original capture IDs at the destination. Confirm the manifest has no missing or duplicate target keys. Run an rclone dry run against a small sample and inspect the proposed keys.
3. When a copy is authorized, transfer one representative capture with its nine raw files, image sequence and low-resolution video, plus the audit GPKG. Measure effective MB/s, completed files/s, error/retry count, CPU and memory, and whether a second `rclone copy` skips completed files. This sample is expected to be around a few GB at most, rather than the full 230 GB.
4. Use those observed rates to choose the run location and schedule. A continuously running machine with faster upstream bandwidth could help if this laptop's upload is the limit; that would require a separate secure setup for the two remotes.

## Bulk-copy approach after the pilot

- Use `rclone copy`/`copyto`, not `sync` or `move`, so source files remain intact and unrelated destination files are not deleted. Rclone [documents](https://rclone.org/commands/rclone_copy/) that `copy` skips matching files on rerun; the pilot must confirm that the current Drive/RustFS pair recognizes matches correctly, especially for multipart videos.
- [transfer_bras.py](../../scripts/transfer_bras.py) splits work into **649 jobs**: one GPKG, then raw, images and low-resolution video for each of 216 captures. A successful rclone command marks only its own job complete in a local, gitignored progress file. An unsuccessful or interrupted job stays pending and is retried in the next session; previously transferred matching files should be skipped by rclone. The script uses a lock so two local sessions cannot run against the same keys at once.
- Begin with conservative parallelism. Rclone defaults to four file transfers and eight checkers; increasing concurrency can raise memory use for [S3 multipart uploads](https://rclone.org/s3/) and may provoke more Drive rate limiting. Tune only from pilot measurements and error logs.
- Preserve logs and rerun failed batches. A restart can skip completed matching objects, but an interrupted in-flight file may need to be sent again. Do not assume that a multipart S3 ETag is a plain file MD5. Rclone's S3 documentation describes multipart hash behavior and the [check command](https://rclone.org/commands/rclone_check/) offers size/hash or streamed download checks.
- Verify the final 70,224 selected destination objects against the frozen manifest. Use file counts and sizes for every object, available hashes where supported, and streamed content checks for representative large multipart videos and any mismatches. Account for the deliberate renaming of the processed capture IDs and GPKG when comparing paths.

### Short laptop sessions

Run these from the repository root. `status` and `plan` are offline and read-only. **`run` starts copying data**, so use it only when ready for the pilot or migration.

```bash
python3 network/scripts/transfer_bras.py status
python3 network/scripts/transfer_bras.py plan --limit 4
python3 network/scripts/transfer_bras.py run --minutes 45 --max-jobs 4
```

The runner stops **starting new jobs** when 45 minutes have passed or four jobs have completed. Within each job, rclone uses `--max-duration` with `--cutoff-mode SOFT`: it stops starting new files at the deadline and lets files already in flight finish. The session can therefore extend beyond 45 minutes, especially for a raw video; the largest raw video in the inventory is about 2.53 GB. If the time cutoff interrupts a job, that job remains pending for the next session. `Ctrl+C` stops the session when needed. After shutdown or a move, run the same `run` command again. Do not move or delete `.bras-transfer-state.json` while the migration is in progress; keep a backup of it with the repository handoff, but never commit it. Session logs live in `.bras-transfer-logs/`. The markers record successful rclone commands, not independent proof that every object remains in RustFS. If the source manifest changes or the destination is altered outside the runner, inspect and reconcile before continuing; the runner refuses a changed manifest.

The first job is only the 41.6 MB GPKG. A pilot can start with `--max-jobs 1`, check its RustFS object, then continue. To pilot a full capture, run the next three jobs in a separate session and verify their objects and skip behavior before bulk copying. This schedule lets the laptop power off between sessions without losing completed-file progress. An interrupted individual file may have to upload from the beginning on the next session, so a connection must stay up long enough for the largest single file. Do not enable `--s3-leave-parts-on-error` without an explicit cleanup plan for abandoned multipart parts.

On 21 October, an rclone `--dry-run` of the GPKG was attempted and timed out after 45 seconds with no object result; it transferred no data. The source/destination path mapping and restart logic were checked offline, but live Drive/RustFS access and skip behavior remain to be measured during the pilot.

The copy should be scheduled only after the pilot gives an observed throughput and a credible total-time estimate. The hospital dataset remains a separate plan until a USP-authorized bulk inventory establishes its size.
