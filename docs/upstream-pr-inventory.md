# Upstream Pull Request Inventory

Open PRs reviewed on 2026-05-29 from `balena-io-experimental/inkyshot`.

## Brought Forward

- [#54 Fixed Test Character testing](https://github.com/balena-io-experimental/inkyshot/pull/54): ported the font resizing fix so `TEST_CHARACTER` is measured against the current candidate font size.
- [#73 CSV Support](https://github.com/balena-io-experimental/inkyshot/pull/73): reimplemented as tested helper code for `CSV_MESSAGE`, `CSV_DELIMITER`, and `CSV_LOCAL_NAME`, with `csv_index` tag cycling when balena API credentials are present.
- [#75 Update weather app](https://github.com/balena-io-experimental/inkyshot/pull/75): ported the useful weather display behavior, including colour weather icons, `TEMP_THRESHOLD`, night-icon colour swaps, colour-display offsets, and `WEATHER_DARK_MODE`. The old Flowzone workflow change was not carried over.
- [#78 Bump pillow from 8.3.2 to 9.3.0](https://github.com/balena-io-experimental/inkyshot/pull/78): applied the Pillow security bump and replaced deprecated text-size APIs used by the quote layout loop.
- [#81 Add support for They said so api token](https://github.com/balena-io-experimental/inkyshot/pull/81): ported as `QOD_API_TOKEN`, using the current documented `X-TheySaidSo-Api-Secret` header instead of a bearer token.

## Deferred

- [#74 Bump numpy from 1.19.2 to 1.22.0](https://github.com/balena-io-experimental/inkyshot/pull/74): deferred because the current container is Python 3.7 and NumPy 1.22 drops Python 3.7 support.

## Skipped

- [#64 41 fix inky message override](https://github.com/balena-io-experimental/inkyshot/pull/64): skipped because the actual custom-message fix commit is already present in upstream `master`; the PR branch mostly shows stale history noise.
