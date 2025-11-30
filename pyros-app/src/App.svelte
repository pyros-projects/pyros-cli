<script lang="ts">
  import './app.css';
  import Gallery from './lib/Gallery.svelte';
  import FakeCLI from './lib/FakeCLI.svelte';
  import { onMount } from 'svelte';

  let images: string[] = [];
  let isGenerating = false;
  let progress = 0;
  let currentPrompt = '';
  let selectedImage: string | null = null;

  let isTauriAvailable = false;
  let statusMessage = '';

  // Check if running in Tauri
  async function checkTauri() {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('list_images');
      isTauriAvailable = true;
      return true;
    } catch {
      isTauriAvailable = false;
      return false;
    }
  }

  // Handle generation from CLI
  async function handleGenerate(event: CustomEvent) {
    const { prompt, params } = event.detail;
    currentPrompt = prompt;
    isGenerating = true;
    progress = 0;
    statusMessage = '';

    if (!isTauriAvailable) {
      // Demo mode - simulate generation
      statusMessage = '⚠️ Running in demo mode (no Tauri backend)';
      await new Promise(r => setTimeout(r, 2000));
      isGenerating = false;
      statusMessage = '💡 To generate real images, run: npm run tauri:dev';
      return;
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core');
      
      const result = await invoke('generate_image', {
        prompt,
        count: params.count || 1,
        width: params.width || 1024,
        height: params.height || 1024,
      });

      if (Array.isArray(result)) {
        images = [...result, ...images];
      }
    } catch (error) {
      console.error('Generation failed:', error);
      statusMessage = `❌ Generation failed: ${error}`;
    } finally {
      isGenerating = false;
      progress = 0;
    }
  }

  function handleImageSelect(event: CustomEvent) {
    selectedImage = event.detail;
  }

  function closePreview() {
    selectedImage = null;
  }

  // Load existing images on mount
  onMount(async () => {
    const hasTauri = await checkTauri();
    
    if (hasTauri) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        images = await invoke('list_images');
      } catch (e) {
        console.log('Failed to load images:', e);
      }
    } else {
      // Demo mode - show sample images from output folder
      statusMessage = '🎨 Demo Mode - Connect Tauri backend to generate images';
      // Try to load from FastAPI backend if available
      try {
        const res = await fetch('http://localhost:8080/api/images');
        if (res.ok) {
          const data = await res.json();
          images = data.images.map((img: any) => `http://localhost:8080${img.path}`);
          statusMessage = '✅ Connected to FastAPI backend';
        }
      } catch {
        // No backend available
      }
    }
  });
</script>

<main class="app">
  {#if statusMessage}
    <div class="status-bar">{statusMessage}</div>
  {/if}
  
  <div class="gallery-container">
    <Gallery 
      {images} 
      {isGenerating} 
      {progress}
      on:select={handleImageSelect}
    />
  </div>
  
  <div class="cli-container">
    <FakeCLI 
      {isGenerating}
      on:generate={handleGenerate}
    />
  </div>

  {#if selectedImage}
    <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
    <div class="preview-overlay" role="dialog" aria-modal="true" on:click={closePreview} on:keydown={(e) => e.key === 'Escape' && closePreview()}>
      <img src={selectedImage} alt="Preview" class="preview-image" />
      <button class="close-btn" on:click={closePreview}>×</button>
    </div>
  {/if}
</main>

<style>
  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-primary);
  }

  .status-bar {
    padding: 8px 16px;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-color);
    font-size: 13px;
    color: var(--text-secondary);
    text-align: center;
  }

  .gallery-container {
    flex: 1;
    overflow: hidden;
    border-bottom: 1px solid var(--border-color);
  }

  .cli-container {
    height: 280px;
    min-height: 200px;
    max-height: 400px;
    background: var(--bg-secondary);
  }

  .preview-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    cursor: pointer;
  }

  .preview-image {
    max-width: 90vw;
    max-height: 90vh;
    object-fit: contain;
    border-radius: var(--border-radius);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  }

  .close-btn {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 40px;
    height: 40px;
    border: none;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    font-size: 24px;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: var(--accent-primary);
    transform: scale(1.1);
  }
</style>

