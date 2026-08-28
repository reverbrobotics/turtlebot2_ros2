# Upstream provenance

This repository used to be a thin superproject with six git submodules. Because
the ROS 2 Lyrical port (see [MIGRATION-lyrical.md](MIGRATION-lyrical.md)) required
changes *inside* five of those submodules — repositories we cannot push to — the
tree was flattened into a single ordinary repository. Every directory below is
now plain tracked content, not a gitlink.

## Where each directory came from

Flattened on 2026-08-28 from these exact upstream commits:

| directory | upstream | commit | describes as |
|---|---|---|---|
| `cmd_vel_mux` | https://github.com/kobuki-base/cmd_vel_mux.git | `bf9f4ce6ebfa04906d09d58b53af8302f68b9e2d` | `bf9f4ce` |
| `ecl_core` | https://github.com/stonier/ecl_core.git | `9d1c49c882c57668f3c46adb2a1a38c2d0957e59` | `1.2.1-1-g9d1c49c` |
| `ecl_lite` | https://github.com/stonier/ecl_lite.git | `f9b8aa04c97ea332ae8ea7e052a31f7ec2670c9a` | `1.2.0` |
| `kobuki_core` | https://github.com/kobuki-base/kobuki_core.git | `e2f0feac0f7a9964d021ac3241b7663f7728d5b9` | `1.4.0` |
| `kobuki_ros` | https://github.com/kobuki-base/kobuki_ros.git | `fb7ca00d361665fc0be49f37c2c7e94c018018a8` | `1.0.0-42-gfb7ca00` |
| `kobuki_ros_interfaces` | https://github.com/kobuki-base/kobuki_ros_interfaces.git | `7711d4fbec13c69bcf6477ce8e446c3ccca33113` | `1.0.0-4-g7711d4f` |
| `kobuki_velocity_smoother` | https://github.com/kobuki-base/velocity_smoother.git | `543f3f194b7069a8994fba6ff8bcad579bdc47f0` | `0.15.0-1-g543f3f1` |

`kobuki_core` and `kobuki_ros_interfaces` are byte-identical to upstream — they
needed no changes for Lyrical. The other five carry local modifications.

All of these projects are BSD licensed; their `LICENSE` files and per-package
`package.xml` license declarations are preserved in place.

## Recovering the diff against upstream

The submodule history is gone, but the commits above pin exactly what each
directory started as, so any local change can still be extracted:

```bash
git clone https://github.com/kobuki-base/kobuki_ros.git /tmp/upstream-kobuki_ros
cd /tmp/upstream-kobuki_ros && git checkout fb7ca00d361665fc0be49f37c2c7e94c018018a8
diff -ruN --exclude=.git /tmp/upstream-kobuki_ros /path/to/this/repo/kobuki_ros
```

That is also how to produce a patch if you ever want to send one of these fixes
upstream — several of them (the Foxy-era `node_executable=` launch arguments, the
`kobuki_bumper2pc` config install, the `velocity_smoother` package-name typo) are
plain bugs that are not specific to Lyrical.

## Pulling in newer upstream code

There is no `git submodule update` path any more. To take a newer upstream
revision of one directory:

1. Extract your local diff as above, and keep it.
2. Delete the directory and replace it with the new upstream checkout
   (minus its `.git`).
3. Re-apply your diff, resolve conflicts, rebuild.
4. Update the commit for that row in the table above.
