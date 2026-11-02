#!/bin/bash
# Launch CarROS on the Pi. Sourced by systemd and by hand.
set -euo pipefail
cd "${HOME}/CarROS"
set +u
for d in lyrical jazzy humble; do
  if [[ -f /opt/ros/$d/setup.bash ]]; then
    # shellcheck source=/dev/null
    source "/opt/ros/$d/setup.bash"
    break
  fi
done
set -u
if [[ ! -f install/setup.bash ]]; then
  echo "CarROS is not built. On the PC: ./deploy" >&2
  exit 1
fi
set +u
# shellcheck source=/dev/null
source install/setup.bash
exec ros2 launch carros sensors.launch.py record:=false
