#!/bin/bash
# Run on the Pi: ROS 2 apt install + bashrc + systemd unit.
set -euo pipefail

sudo rm -f /etc/apt/sources.list.d/ros2.list

sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl gnupg lsb-release ca-certificates

if ! dpkg -s ros2-apt-source >/dev/null 2>&1; then
  ver=$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
    | grep -F tag_name | cut -d'"' -f4)
  codename=$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
  curl -fsSL -o /tmp/ros2-apt-source.deb \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ver}/ros2-apt-source_${ver}.${codename}_all.deb"
  sudo dpkg -i /tmp/ros2-apt-source.deb
fi

sudo apt-get update -qq

distro=
for d in lyrical jazzy; do
  if apt-cache show "ros-${d}-ros-base" >/dev/null 2>&1; then
    distro=$d
    break
  fi
done
if [[ -z $distro ]]; then
  echo "no ROS 2 ros-base package in apt (tried lyrical, jazzy)" >&2
  exit 1
fi

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  "ros-${distro}-ros-base" \
  "ros-${distro}-launch-ros" \
  "ros-${distro}-rosbag2" \
  python3-colcon-common-extensions \
  python3-argcomplete

marker="# carros ros"
if ! grep -qF "$marker" "$HOME/.bashrc"; then
  cat >> "$HOME/.bashrc" <<EOF
$marker
if [ -f /opt/ros/${distro}/setup.bash ]; then
  source /opt/ros/${distro}/setup.bash
fi
if [ -f "\$HOME/CarROS/install/setup.bash" ]; then
  source "\$HOME/CarROS/install/setup.bash"
fi
EOF
fi

if [[ -f $HOME/CarROS/scripts/carros.service ]]; then
  sudo cp "$HOME/CarROS/scripts/carros.service" /etc/systemd/system/carros.service
  sudo systemctl daemon-reload
fi

echo "ROS 2 ${distro} installed"
