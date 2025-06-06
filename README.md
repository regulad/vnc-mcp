# vnc-mcp

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/vnc-mcp/
[read the docs]: https://vnc-mcp.readthedocs.io/
[tests]: https://github.com/regulad/vnc-mcp/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/regulad/vnc-mcp
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

🤖🖥 vnc-mcp allows MCP-compatible LLMs to interact with any desktop accessible over VNC

https://github.com/user-attachments/assets/5eff0be6-81f4-4baf-ad67-2f68041a022a

> Claude 4 Opus getting comfortable in a Kubuntu X11 session. The real limit to this application of LLMs is now the speed of LLMs: it is possible they could be better at this task if they had reinforcement learning to more efficiently decode embeddings or prefer OCR at all times.

## Features

- Connects to any [RFC6143](https://datatracker.ietf.org/doc/html/rfc6143) RFB spec-compliant VNC server using [`pyvnc`](https://github.com/regulad/pyvnc).
- Exposes a number of MCP tools that an LLM can use to interact with a computer through the VNC client.
- OCR for screen reading and text extraction, offering much better integration with non-multimodal LLMs. (Support for all languages unfortunately makes the image pretty huge...)

## Requirements

- A VNC server that is [RFC6143](https://datatracker.ietf.org/doc/html/rfc6143) RFB spec-compliant.
- A VNC server that supports spec-compliant authentication (not sure which RFC this aligns with). This means ARD (Apple Remote Desktop) servers are not supported. Mac users should consider using the project https://github.com/baryhuang/mcp-remote-macos-use instead.
- (Optional) A VNC server that reuses your existing desktop session so you can see the actions an LLM is making and collaborate with it. This project was tested with [`krfb`](https://github.com/KDE/krfb), the preferred VNC server for both X11 and Wayland KDE sessions. It should be built into most KDE distros (I use Fedora 42 Kinoite). It may work with other DEs, but I am unsure. GNOME should also have a built-in VNC server. Windows (ew) users may have to experiment with alternative clients like TightVNC and TigerVNC. My experience with desktop-sharing VNC servers on this platform is not good. I would either suggest using RDP or switching to a Linux distribution with KDE or Gnome as a DE.
- (Optional) A graphics-accelerated VM running KDE/another DE with a same-session VNC server. Having a VM is preferred because then your AI UI will not have access to itself, which can cause frustration as you wrestle the mouse away from your LLM in order to see its output. **NOTE:** if you want to use Qemu virtio OpenGL acceleration, make sure you do NOT have the proprietary Nvidia drivers installed. They will prohibit you from starting a VM with OpenGL acceleration. This is not a problem on MacOS if you are starting a VM through UTM, as virtio should work perfectly there with Metal.

The following DEs and VNC servers have been tested in a VM with `virgl` acceleration:

- ❔ Fedora 42 Workstation (Gnome)
- ❌ Fedora 42 KDE - VNC server raised by krfb does not work, only shows a black screen with no resolution. krdp is no better: only shows a white screen. It is possible this may be an artifact of my VM setup, but I cannot be sure.
- ❔ Ubuntu 24.04 (Gnome)
- ✅ Kubuntu 24.04 (KDE) - Krfb had to be downloaded from the Ubuntu repositories, but it works fine. Only worked with unattended access. Possibly works because it uses x11 instead of Wayland.

VNC is used as opposed to RDP for two reasons:

- The RDP protocol is much more difficult to implement and much more computationally expensive.
- RDP servers (even moreso than most VNC servers) tend to be session-based, meaning that a new desktop environment will be spawned with each new connection. This prevents working collaboratively with an LLM, and obscures the actions the LLM is taking. This is not good, considering the broad access to your computer an LLM will have.

Even still, VNC appears to be on its way out. Work is currently in progress to develop a Python wrapper for [moonlight](https://moonlight-stream.org/), a modern KMS-based streaming server based on the Nvidia Gamestream protocol

Check its progress here:

- [`pymoonlight`](https://github.com/regulad/pymoonlight)
- [`moonlight-mcp`](https://github.com/regulad/moonlight-mcp)

(psst... if the repositories don't exist yet, it means I haven't started work :p)

## Installation

Although `vnc-mcp` is a Python package and could theoretically be started with `uvx`, the best way to use it with an MCP client is with a Docker container.

Docker provides several advantages:

- Scoping access
- Security
- Privacy
- Portability (important because `vnc-mcp` requires Python 3.12, which may be replaced by 3.13 on modern distributions)

If you do not have a docker daemon set up on your host yet, I suggest using rootless podman. [See their documentation for setup.](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md)

If you decide to go with a rootless docker or podman approach, please be mindful to set the `DOCKER_HOST` or `CONTAINER_HOST` environment variables respectively.

If your UID is 1000, a rootless podman socket address would be `unix:///run/user/1000/podman/podman.sock` and a rootless docker socket address would be `unix:///run/user/1000/docker.sock` (unless you configure them in another way).

With podman, you must then additionally install the Docker CLI (available as `docker-cli` in most distribution repositories) and make sure the `DOCKER_HOST` environment variable is configured to point to your podman sock.

### Installation into an MCP client

The below configuration is given in [`mcphost`](https://github.com/mark3labs/mcphost)/[Claude Desktop](https://claude.ai/download) format. Be sure to correctly configure the environment variables in the `env` block to match your setup.

The docker container will automatically update itself and operate with the host's network (useful for getting `localhost` as the host without any trickery).

```json
{
  ...
  "mcpServers": {
    ...
    "desktop": {
      "command": "docker",
      "args": [
        "run",
        "--env", "VNCMCP_HOST",
        "--env", "VNCMCP_PORT",
        "--env", "VNCMCP_TIMEOUT",
        "--env", "VNCMCP_USERNAME",
        "--env", "VNCMCP_PASSWORD",
        "-i",
        "--rm",
        "--pull=always",
        "--network=host",
        "ghcr.io/regulad/vnc-mcp:latest"
      ],
      "env": {
        "DOCKER_HOST": "unix:///run/user/1000/podman/podman.sock",
        "VNCMCP_HOST": "localhost",
        "VNCMCP_PORT": "5900",
        "VNCMCP_TIMEOUT": "15.0",
        "VNCMCP_USERNAME": "regulad",
        "VNCMCP_PASSWORD": "ChangeMeImInsecure!!"
      }
    },
    ...
  },
  ...
},
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

Test with `nox`, but if you want to interactively test `mcp`, do this:

```bash
npx @modelcontextprotocol/inspector poetry run vnc-mcp
```

## License

Distributed under the terms of the [AGPL 3.0 or later license][license],
_vnc-mcp_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@regulad]'s [neopy] template.

[@regulad]: https://github.com/regulad
[pypi]: https://pypi.org/
[neopy]: https://github.com/regulad/cookiecutter-neopy
[file an issue]: https://github.com/regulad/vnc-mcp/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/regulad/vnc-mcp/blob/main/LICENSE
[contributor guide]: https://github.com/regulad/vnc-mcp/blob/main/CONTRIBUTING.md
[command-line reference]: https://vnc-mcp.readthedocs.io/en/latest/usage.html
