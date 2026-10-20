# Mass Driver V176

`mass-driver-v176-release-candidate-20261019` is the selected project build.
Use [PLAY_MASS_DRIVER.cmd](../PLAY_MASS_DRIVER.cmd) locally or the
[public Windows player](mass-driver-public-player.md). The fresh Sony-BIOS
main route and finite gameplay checks passed; see [release QA](mass-driver-release-qa.md)
for exact methods, version attribution and platform limits.

## Release repairs

V174 restored the native New Game / Continue / Sound title and repaired the
authorized north lift's straight approach. V175 restored the native entry value
when approaching the first memory cube from field 387. New saves on that route
now cold-load at the normal field-725 entry. Repairing an installation does not
migrate a malformed save produced by an older candidate.

V176 corrects Missile Command's title exit and pause button to physical
**Triangle**, matching its displayed directions. The old mask read Square.
Only four script operand bytes change from V175, all in field 376 resource 1358.
The other 165 replacements, all 33 field headers and dialogue components, and
the other 296 field components remain identical. The complete protected Central
Control resource remains identical, including Miang's memory and its boundaries.

The approved [V173 transcript](mass-driver-dialogue-v173.md), six native random
encounter passages, starting party, enemies, AI, Guardian and ending remain.

## Identity and validation

- BIN: 696,140,256 bytes, SHA-256
  `0dc54a5306e97f41989ddd519daec860821af1038817c29f35b5d4b5d8ad87f8`
- CUE SHA-256:
  `4c56a42f2011d4630d3e531850f694f0b8b1c81da2dd0145eec07c7ff725d690`
- Stage manifest SHA-256:
  `c03b89422c0187ca1e9a46c2495a3dad0e3a0e2075a29f227b5aaa1ccb465ad4`
- Source snapshot SHA-256:
  `9b1fd6e8a6e6b3ddd07f42cd7f6dcfc542a66438a6909b1f9a77e7db640bbfd4`

The profile suite ran 426 tests: 424 passed and two existing tests were skipped.
New regressions execute the actual Missile Command control branches using
observed physical controller words and pin the four-byte compiled delta.
Build and selected-media verification passed. Native gameplay and public
packaging results are recorded separately in the release QA record.

The foundation is the documented rebuilt Perfect Works 0.10.2 recipe, SHA-256
`7585d2ebadab82f9d982d871e05c02a9fb930167e8fe85d249c266a0e1885d8e`.
It differs from the unavailable historical development image. The supplied
Perfect Works 0.11.4 patch was not applied.
