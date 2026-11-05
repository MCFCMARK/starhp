# StarHub manifest redirect service for Render

Prepared from the supplied Python service. Live upstream playback is unverified.
It returns a temporary CDN URL using HTTP 307; it does not relay video or provide
decryption keys. A player still needs the provider's required playback licence.

## Upload to GitHub

1. Create a new private repository named `starhub-proxy`.
2. Extract the ZIP on your computer.
3. In the repository select **Add file → Upload files**.
4. Upload the contents of this folder: `app.py`, `requirements.txt`, `render.yaml`,
   this README, and `.gitignore` if visible. Do not upload the ZIP itself.
5. Commit the files. `app.py` and `render.yaml` must be at the repository root.

## Deploy on Render

1. Sign into Render and choose **New → Web Service**.
2. Connect GitHub and grant Render access to the `starhub-proxy` repository.
3. Select that repository and its `main` branch.
4. Runtime: Python 3. Leave Root Directory blank.
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT --no-access-log`
7. Add environment variable `PYTHON_VERSION` with value `3.11.11`.
8. Select the **Free** instance type and deploy.

Alternatively, choose **New → Blueprint** and select the repository to use
`render.yaml`, which includes these settings. Check that the plan remains Free.
No paid resources are requested by this configuration.

## Test

After Render reports Live, open its generated HTTPS address. The root should
return JSON with `success: true`; that only verifies the service is running.

Append this path to the generated address for your player:

`/bpk-tv/BeINSportsHD/output/manifest.mpd`

Other routes:

- `/BeINSportsHD/index.mpd` — temporary redirect
- `/star/get-stream?channel_id=BeINSportsHD` — JSON diagnostic

JSON diagnostic success confirms URL resolution, not successful video playback.
Do not share temporary stream URLs returned in JSON: they contain access tokens.
The deployed endpoints will be public. Keeping the GitHub repository private
keeps source private but does not restrict the Render service's audience.

## Limits and errors

Free Render web services sleep after 15 minutes of inactivity; waking can take
about one minute, which can cause a player timeout. Open the root page first
and wait for JSON before retrying the player. See https://render.com/docs/free.

Upstream 403 means access was denied. Switching host does not guarantee provider
access, and token/CDN restrictions can still prevent playback. The service is
not a replacement for an authorised provider subscription or licence.

## Checks completed

Local tests with mocked upstream resolution passed for health, three redirect
routes, cache prevention, missing/unknown channels, JSON and OPTIONS. No live
provider playback or Render deployment has been verified.
