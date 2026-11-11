# Qubes Linux yum repository (obsolete)

This repository is obsolete and no longer used.

It held the layout and scripts for the Qubes OS RPM package repository served at
[yum.qubes-os.org](https://yum.qubes-os.org/): creating the repository
skeleton, building and signing the metadata, moving packages between
`current-testing` and `current`, and syncing to the server. It was part of the
legacy [qubes-builder](https://github.com/QubesOS/qubes-builder).

This is now done by the `publish_rpm` plugin of
[qubes-builderv2](https://github.com/QubesOS/qubes-builderv2).
