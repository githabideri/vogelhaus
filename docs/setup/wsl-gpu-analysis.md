# WSL2 GPU Analysis Setup

> Last updated: 2026-03

This guide covers setting up Windows Subsystem for Linux 2 (WSL2) for video analysis tasks in the Vogelhaus project, with support for various GPU configurations.

## What WSL2 Provides

WSL2 allows running Linux video analysis tools on Windows while leveraging GPU acceleration:

- **Video processing**: ffmpeg with hardware acceleration
- **Machine learning**: PyTorch, TensorFlow with GPU support
- **Computer vision**: OpenCV with CUDA/OpenCL
- **Stream analysis**: Real-time bird detection and behavior analysis

## GPU Support Options

| GPU Type | Acceleration | Setup Complexity | Performance |
|----------|--------------|------------------|-------------|
| NVIDIA RTX/GTX | CUDA | Medium | Excellent |
| AMD Radeon | ROCm/OpenCL | High | Good |
| Intel iGPU | OpenCL | Medium | Fair |
| CPU only | None | Low | Limited |

## Base WSL2 Setup

### Step 1: Enable WSL2 Features

In PowerShell (as Administrator):

```powershell
# Enable Windows features
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart required
Restart-Computer
```

### Step 2: Install Linux Distribution

```powershell
# Install Ubuntu (or preferred distribution)
wsl --install -d Ubuntu-22.04

# Set WSL2 as default
wsl --set-default-version 2
```

### Step 3: Configure systemd

In WSL2 Ubuntu:

```bash
# Enable systemd
echo -e '[boot]\nsystemd=true' | sudo tee /etc/wsl.conf

# Configure user
echo -e '[user]\ndefault=<YOUR_USERNAME>' | sudo tee -a /etc/wsl.conf
```

Restart WSL2:
```powershell
wsl --shutdown
wsl
```

## NVIDIA GPU Setup

### Prerequisites
- NVIDIA GPU (GTX 10 series or newer)
- Latest NVIDIA drivers installed on Windows
- CUDA Compute Capability 6.0+

### Install NVIDIA Container Toolkit

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
```

### Verify NVIDIA Support

```bash
# Check GPU detection
nvidia-smi

# Test CUDA
nvidia-container-cli info
```

## AMD GPU Setup

### Prerequisites
- AMD Radeon RX 400 series or newer
- Latest AMD drivers installed on Windows

### Install ROCm

```bash
# Add ROCm repository
wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian/ ubuntu main' | sudo tee /etc/apt/sources.list.d/rocm.list

sudo apt update
sudo apt install -y rocm-dkms rocm-dev rocm-libs
```

### Configure ROCm

```bash
# Add user to render group
sudo usermod -a -G render $USER

# Set environment variables
echo 'export PATH=$PATH:/opt/rocm/bin:/opt/rocm/profiler/bin:/opt/rocm/opencl/bin' >> ~/.bashrc
echo 'export HSA_PATH=/opt/rocm' >> ~/.bashrc
source ~/.bashrc
```

## Intel iGPU Setup

### Install OpenCL Runtime

```bash
# Install Intel OpenCL
sudo apt update
sudo apt install -y intel-opencl-icd ocl-icd-opencl-dev

# Verify OpenCL
clinfo
```

## Performance Optimization

### WSL2 Configuration

Create `C:\Users\<USERNAME>\.wslconfig`:

```ini
[wsl2]
memory=16GB          # Adjust based on available RAM
processors=8         # Adjust based on CPU cores
swap=2GB            # Reduce if using SSD
guiApplications=true

[experimental]
autoMemoryReclaim=dropCache  # Free memory when idle
sparseVhd=true              # Dynamic disk allocation
```

### Resource Monitoring

```bash
# Monitor GPU usage (NVIDIA)
watch -n 1 nvidia-smi

# Monitor system resources
htop

# Check memory usage
free -h
```

## Video Analysis Tools

### Install ffmpeg with GPU Support

```bash
# For NVIDIA
sudo apt install -y ffmpeg nvidia-cuda-toolkit

# Test hardware acceleration
ffmpeg -encoders | grep nvenc  # NVIDIA
ffmpeg -encoders | grep vaapi  # Intel/AMD
```

### Install Python Environment

```bash
# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv ~/venv/vogelhaus
source ~/venv/vogelhaus/bin/activate

# Install packages based on GPU type
pip install torch torchvision opencv-python-headless

# For NVIDIA CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For AMD ROCm
pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.4.2
```

## Network Access Setup

### SSH Server

```bash
# Install and configure SSH
sudo apt install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

# Configure SSH keys (if needed)
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Add public key to ~/.ssh/authorized_keys
```

### Tailscale Integration

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable --now tailscaled

# Connect to network
sudo tailscale up

# Get Tailscale IP
tailscale ip -4
```

## File System Access

### Mount Windows Drives

Windows drives are automatically mounted under `/mnt/`:
- C: drive → `/mnt/c/`
- D: drive → `/mnt/d/`

### Network Shares

Mount network storage:
```bash
# Create mount point
sudo mkdir -p /mnt/nas

# Mount with credentials
sudo mount -t cifs //<NAS_IP>/share /mnt/nas -o username=<USER>,password=<PASS>,uid=$UID,gid=$GID
```

## Troubleshooting

### GPU Not Detected

**NVIDIA:**
- Verify Windows NVIDIA drivers are latest version
- Check CUDA compatibility: `nvidia-smi`
- Restart WSL2: `wsl --shutdown` then `wsl`

**AMD:**
- Ensure ROCm supports your GPU model
- Check render group membership: `groups`
- Verify OpenCL: `clinfo`

**Intel:**
- Update Intel graphics drivers on Windows
- Install missing OpenCL packages: `sudo apt install intel-opencl-icd`

### Memory Issues

- Increase memory allocation in `.wslconfig`
- Disable swap if using SSD: `swap=0`
- Enable memory reclaim: `autoMemoryReclaim=dropCache`

### Network Connectivity

- Check WSL2 IP: `ip addr`
- Verify port forwarding for services
- Test SSH: `ssh <username>@<wsl-ip>`

## Performance Benchmarks

### Expected Performance (1080p video processing)

| Configuration | Encoding Speed | Analysis FPS |
|---------------|---------------|--------------|
| RTX 4080 | 200-300x realtime | 60-120 FPS |
| RTX 3060 | 100-200x realtime | 30-60 FPS |
| RX 6700 XT | 80-150x realtime | 25-45 FPS |
| Intel iGPU | 20-50x realtime | 5-15 FPS |
| CPU only | 5-15x realtime | 1-5 FPS |

### Test Scripts

```bash
# Quick GPU test
ffmpeg -f lavfi -i testsrc2=duration=10:size=1920x1080:rate=30 -c:v h264_nvenc test.mp4

# Benchmark encoding
time ffmpeg -i input.mp4 -c:v h264_nvenc -b:v 5M output.mp4

# Python GPU test
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Integration with Vogelhaus

### Stream Analysis Pipeline

1. **Capture streams** from Pi cameras via RTSP
2. **Process video** in WSL2 with GPU acceleration
3. **Detect birds** using computer vision models
4. **Store results** on network storage
5. **Generate reports** and alerts

### Automation Scripts

```bash
# Example: Automated bird detection
#!/bin/bash
source ~/venv/vogelhaus/bin/activate

# Capture stream segment
ffmpeg -i rtsp://<PI4_IP>:8554/vogl-noir -t 60 -c copy segment.mp4

# Run analysis
python3 bird_detection.py segment.mp4

# Store results
cp results.json /mnt/nas/analysis/$(date +%Y%m%d_%H%M%S).json
```