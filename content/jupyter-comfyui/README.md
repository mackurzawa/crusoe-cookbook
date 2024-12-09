# Getting Started with Jupyter Notebook and ComfyUI on Crusoe Cloud

This guide walks you through setting up a Crusoe Cloud Virtual Machine (VM) with Jupyter Notebook and ComfyUI, a powerful node-based tool for Stable Diffusion workflows. By the end of this tutorial, you'll have a working environment ready for building and experimenting with ComfyUI workflows interactively.

## What is Crusoe Cloud?

[Crusoe Cloud](https://crusoecloud.com/) provides cloud instances powered by efficient GPU resources, suitable for AI/ML workloads. This guide uses Crusoe Cloud to quickly spin up an environment for machine learning experimentation.

## What is ComfyUI?

[ComfyUI](https://github.com/comfyanonymous/ComfyUI) is a node-based interface for diffusion models that lets you visually construct complex image and video generation workflows. It’s a great tool for experimenting with new prompts, models, and pipelines.

## Why Use `uv`?

`uv` is a fast Python environment and package management tool. It helps streamline Python environment creation and dependency installation, making your workflow simpler and more reproducible.

## Prerequisites

- A Crusoe Cloud account
- Familiarity with command-line operations
- An SSH client on your local machine

## Instance Setup

1. **Create a Crusoe Cloud instance** with:
   - **GPU**: 1x L40s-48GB (recommended for Stable Diffusion workloads)
   - **Storage**: Ensure you have enough disk space for your chosen models (e.g., 100GB+)
   - **Base Image**: `ubuntu22.04-nvidia-slurm`
   - **Image Version**: 12.4

2. **Note your VM's Public IP Address** for SSH access.

## Initial Configuration

**Connect to Your VM:**

```bash
ssh ubuntu@<your-vm-ip>
```

### Storage Setup

Format and mount the additional storage volume (if attached):

```bash
sudo mkfs.ext4 /dev/vdb
sudo mkdir /scratch
sudo mount -t ext4 /dev/vdb /scratch
```

This `/scratch` directory will hold your ComfyUI files and models.

### Install and Configure `uv`

Install `uv`, which will help manage your Python environments and packages:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

`source $HOME/.local/bin/env` ensures that the `uv` command is available in your current shell.

## ComfyUI Installation

1. **Clone the ComfyUI Repository:**

```bash
cd /scratch
sudo git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
```

2. **Set Permissions:**

```bash
sudo chown -R ubuntu:ubuntu /scratch/ComfyUI
sudo chmod -R u+rw /scratch/ComfyUI
```

3. **Initialize Python Environment with uv:**

```bash
uv init
```

This creates a Python virtual environment that `uv` manages for you.

## Setting Up Jupyter Notebook

### Secure Jupyter Notebook

1. **Set a Password:**
   Jupyter Notebook can be protected with a password:

   ```bash
   uv run jupyter notebook password
   ```

   Follow the prompts to set a secure password.

2. **Generate a Configuration File:**

   ```bash
   uv run jupyter notebook --generate-config
   ```

3. **Edit the Configuration:**

   Use a text editor:

   ```bash
   nano /home/ubuntu/.jupyter/jupyter_notebook_config.py
   ```

   Add or modify the following lines:

   ```python
   c.NotebookApp.ip = '0.0.0.0'          # Listen on all interfaces
   c.NotebookApp.open_browser = False     # Don't open browser automatically
   c.NotebookApp.port = 8888             # Default port (adjust as needed)
   c.NotebookApp.allow_root = False
   c.NotebookApp.allow_origin = '*'      # Use cautiously in non-production environments
   ```

**Security Note:** For production, consider using more restrictive settings, like limiting origins or using an SSH tunnel exclusively.

### Start the Jupyter Notebook Server

```bash
uv run jupyter notebook --no-browser --ip=127.0.0.1 --port=8888
```

The notebook now runs locally on the VM. To access it on your local machine:

1. **Create an SSH Tunnel:**

   From your local machine:

   ```bash
   ssh -L 8888:localhost:8888 ubuntu@<your-vm-ip>
   ```

2. **Access in Your Browser:**

   Open your browser and navigate to:
   [http://localhost:8888](http://localhost:8888)

   Enter the password you set previously.

## Integrating ComfyUI with Jupyter

ComfyUI provides example notebooks (such as `comfyui_colab.ipynb`) for setup and workflows. To integrate:

1. **Open the provided ComfyUI Colab Notebook:**

   In Jupyter, navigate to `notebooks/comfyui_colab` within the ComfyUI repository.

2. **Adapt the Notebook for uv:**

   In the notebook’s installation cells, replace all instances of `pip` with:

   ```bash
   uv pip
   ```

   This ensures packages are installed in the `uv` environment.

3. **Follow the Official ComfyUI Instructions:**

   Complete the steps outlined in the [ComfyUI colab guide](https://github.com/comfyanonymous/ComfyUI/blob/master/notebooks/comfyui_colab.ipynb) to finalize the setup. This typically involves downloading models, configuring paths, and running demo workflows.

## Security Considerations

- **Password Security:** Use a strong, unique password for Jupyter.
- **Network Restrictions:** If possible, restrict access via firewall rules or by not exposing `0.0.0.0` directly to the internet.
- **Allow Origin:** If running in a production setting, remove `allow_origin = '*'` or limit it to known, trusted domains.
- **Non-Standard Ports:** Changing the default port (8888) can reduce unsolicited probing.

## Troubleshooting

- **Permission Issues:** Ensure `/scratch/ComfyUI` directory permissions are correct.
- **SSH Tunnel Errors:** Double-check the SSH command and that your local machine’s firewall allows port forwarding.
- **Jupyter Notebook Not Running:** Check logs by examining the terminal output where you ran `uv run jupyter notebook`. Ensure no processes are blocking port 8888.

## Next Steps

- **Install Additional Models:** Add Stable Diffusion models or other resources to `/scratch`.
- **Create Your First ComfyUI Workflow:** Experiment with the node-based interface to generate images.
- **Expand the Environment:** Use `uv` to install additional Python packages you need.
- **Version Control:** Consider integrating `git` for versioning notebooks and workflows.

By following these steps, you’ll have a robust and flexible environment for experimenting with Stable Diffusion and ComfyUI on Crusoe Cloud.
