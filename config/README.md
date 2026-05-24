# brcc-ads-private

Private configuration and credentials for Blue Ridge Comedy Club Google Ads management.

**This repo is private. Do not make it public.**

## Contents

- `credentials.yaml` — Google Ads API credentials
- `account.yaml` — Account config, benchmarks, brand rules
- `brand-voice.md` — Tone guidelines and writing samples
- `campaigns.md` — Managed campaigns and scope

## Usage

This repo is used alongside [ppc-os](https://github.com/sarahg423/ppc-os) (the public tool). Scheduled agents clone both repos — ppc-os for the code and this repo for the config.

To use locally, symlink or copy these files into ppc-os/config/:

```bash
cp *.yaml ../ppc-os/config/
cp *.md ../ppc-os/config/
```
