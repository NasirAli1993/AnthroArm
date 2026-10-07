# Third-party model provenance and notices

These notices cover the included model assets and metadata. They do not grant a new license to the project's own code or CAD. Upstream model cards, attribution, and distribution terms remain applicable.

## MediaPipe Hand Landmarker

The included `hand_landmarker.task` is the unmodified upstream task bundle, downloaded on 5 October 2026. It is used by the preserved optional hand-landmark module; its inclusion does not establish validated physical-camera tracking.

- Publisher/project: Google MediaPipe.
- Asset source: <https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task>
- Included file SHA-256: `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`.
- Model documentation: <https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker>.
- License evidence: the official [Hand Tracking Lite/Full model card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Hand%20Tracking%20%28Lite_Full%29%20with%20Fairness%20Oct%202021.pdf), page 2, declares Apache License, Version 2.0.
- Applicable license text: [Apache License 2.0](licenses/Apache-2.0.txt), preserved from <https://www.apache.org/licenses/LICENSE-2.0.txt>.

The `latest` download endpoint is mutable; verify the recorded hash when reproducing this exact asset. See `docs/teleop_rl.txt` and `docs/official_sources.txt` for the original project download record.

## SmolVLM-256M-Instruct

The unmodified model card, tokenizer, configuration files, and download manifest are retained under `SmolVLM-256M-Instruct/`. The large `model.safetensors` weight file is intentionally omitted from ordinary Git and can be retrieved with `integration/download_vlm.py`.

- Publisher/model: `HuggingFaceTB/SmolVLM-256M-Instruct`.
- Pinned revision: `7e3e67edbbed1bf9888184d9df282b700a323964`.
- Upstream source: <https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct/tree/7e3e67edbbed1bf9888184d9df282b700a323964>.
- The retained [upstream model card](SmolVLM-256M-Instruct/README.md) declares `apache-2.0`; the complete license text is included at [licenses/Apache-2.0.txt](licenses/Apache-2.0.txt).
- File hashes and exact upstream revision remain in [download_manifest.json](SmolVLM-256M-Instruct/download_manifest.json).

The actual captioning experiment and its inaccuracies remain in the project results. The model is not credited with motor control or general scene understanding.

## Other included third-party source

The Arduino Servo library retains its original LGPL 2.1 license, metadata, source headers, and upstream author notices at `hardware/libraries/Servo/`. Installed application distributions and proprietary installers are not bundled. No upstream copyright or authorship notices were replaced with a project-owner claim.
