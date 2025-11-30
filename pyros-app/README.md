# Pyros App

A native desktop application for AI image generation, built with **Tauri + Svelte**.

![Pyros App](preview.png)

## Features

- 🎨 **Gallery View** - Browse and preview generated images
- 💻 **Fake CLI** - Familiar command-line interface with autocomplete
- ⚡ **Native Performance** - Small binary, fast startup
- 🔌 **Offline Mode** - Uses local Z-Image-Turbo + Qwen3-4B

## Architecture

```
┌─────────────────────────────────────────────┐
│  Svelte Frontend                            │
│  ├─ Gallery.svelte (image grid + preview)   │
│  └─ FakeCLI.svelte (input + autocomplete)   │
├─────────────────────────────────────────────┤
│  Tauri (Rust)                               │
│  └─ Spawns Python backend via subprocess    │
├─────────────────────────────────────────────┤
│  Python Backend (pyros-cli)                 │
│  ├─ Z-Image-Turbo (image generation)        │
│  └─ Qwen3-4B (prompt enhancement/vars)      │
└─────────────────────────────────────────────┘
```

## Prerequisites

1. **Rust** (for Tauri)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Node.js** (v18+)
   ```bash
   # Using nvm
   nvm install 18
   nvm use 18
   ```

3. **Tauri CLI**
   ```bash
   cargo install tauri-cli
   ```

4. **Python dependencies** (already set up in parent pyros-cli)
   ```bash
   cd ..
   uv sync --extra local
   ```

## Development

```bash
# Install JS dependencies
npm install

# Run in development mode
npm run tauri:dev
```

This will:
1. Start the Vite dev server (frontend)
2. Compile and run the Tauri app (backend)
3. Hot-reload on changes

## Building

```bash
# Build for production
npm run tauri:build
```

Output will be in `src-tauri/target/release/bundle/`

## Project Structure

```
pyros-app/
├── src/                    # Svelte frontend
│   ├── App.svelte          # Main app component
│   ├── app.css             # Global styles
│   ├── main.ts             # Entry point
│   └── lib/
│       ├── Gallery.svelte  # Image gallery
│       └── FakeCLI.svelte  # CLI input
├── src-tauri/              # Rust backend
│   ├── src/main.rs         # Tauri commands
│   ├── Cargo.toml          # Rust dependencies
│   └── tauri.conf.json     # Tauri config
├── index.html              # HTML template
├── package.json            # JS dependencies
└── vite.config.ts          # Vite config
```

## CLI Syntax (same as pyros-cli)

```bash
# Basic prompt
>>> a cute cat sitting on a windowsill

# With variable substitution
>>> a __animal__ in __art_style__ style

# With enhancement
>>> a samurai > make it epic and cinematic

# Batch generation with custom size
>>> __scene_cyberpunk_city__ : x5,h832,w1216
```

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/vars` | List available variables |
| `/seed N` | Set random seed |
| `/size WxH` | Set output dimensions |

## Customization

### Theme

Edit `src/app.css` to customize colors:

```css
:root {
  --accent-primary: #7c3aed;    /* Purple */
  --bg-primary: #0d0d0d;        /* Background */
  /* ... */
}
```

### Window Size

Edit `src-tauri/tauri.conf.json`:

```json
{
  "tauri": {
    "windows": [{
      "width": 1400,
      "height": 900,
      "minWidth": 800,
      "minHeight": 600
    }]
  }
}
```

## Troubleshooting

### "Python not found"

Make sure `uv` is in your PATH and pyros-cli dependencies are installed:

```bash
cd ..
uv sync --extra local
```

### "Cannot connect to backend"

The Tauri app needs to find the parent `pyros-cli` directory. Run from the `pyros-app` folder.

### Slow first generation

The first generation loads models into GPU memory. Subsequent generations are faster.

---

Built with ❤️ using [Tauri](https://tauri.app) + [Svelte](https://svelte.dev)


