---
title: "Building a Local ChatGPT-like Environment with Ollama and Open WebUI on Ubuntu"
emoji: "🦙"
type: "tech"
topics: ["Ollama", "OpenWebUI", "Ubuntu"]
published: true
---

## Introduction

This article serves as a personal memo on how to set up a local ChatGPT-like conversational environment using **Ollama** and **Open WebUI** on an Ubuntu system.  
Ollama is a tool that allows you to run various LLMs (Large Language Models) locally, and Open WebUI provides a web-based interface to interact with Ollama.

## Prerequisites

The following setup was verified on:

Although I mention "Ubuntu," I'm actually running it on a low-end **Mac mini 2018** with Ubuntu installed—so the specs are quite modest.

```bash
lsb_release -d
Description:	Ubuntu 24.04 LTS
```

```bash
ollama --version
ollama version is 0.6.8
```

## Setup Steps

### 1. Install Ollama

First, install Ollama using the following command:

```bash
curl -L https://ollama.ai/install.sh | bash
```

After installation, check if it works:

```bash
ollama --version
```

You can find models at [ollama.com](https://ollama.com/), and download or run them with commands like:

```bash
ollama pull <model_name>
ollama run <model_name>
```

Example:

```bash
ollama pull phi4
ollama run phi4

ollama pull gemma3
ollama run gemma3
```

### 2. Run Open WebUI

To start Open WebUI, run the following Docker command:

```bash
docker run -d -p 3000:8080  --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

### 2.5. If Docker Cannot Connect to Ollama

In my case, Open WebUI inside Docker couldn’t connect to Ollama directly, so I tested connectivity using `curl` from inside the container.

1. Check if the container can reach Ollama:

```bash
docker run --rm curlimages/curl http://172.17.0.1:11434
```

2. If not reachable, modify Ollama settings to allow external connections.

Edit `/etc/systemd/system/ollama.service` and add the following:

```bash
Environment="OLLAMA_HOST=0.0.0.0"
```

You can also run the server directly like this for testing:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

Then reload and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

:::message
Setting `OLLAMA_HOST=0.0.0.0` exposes Ollama to all external connections, which is suitable for debugging but **not recommended for production**. Please secure it appropriately.
:::

### 3. Using Open WebUI

Once Open WebUI is running, open your browser and navigate to `http://localhost:3000`.  
You’ll be able to select models already downloaded via Ollama and start chatting through the browser interface.

## Conclusion & Thoughts

In this article, I explained how to install **Ollama** and **Open WebUI** on Ubuntu to create a local ChatGPT-like experience.  
Since I ran this on a relatively underpowered machine, performance was predictably modest—the responses were slow and the models weren't particularly "smart."

I’ve started to explore the Agent mode feature, but so far I wouldn’t say it’s ready for serious use.  
Still, I'm curious about potential fun use cases and plan to experiment more.
