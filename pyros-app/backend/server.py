"""
FastAPI backend for Pyros App.

Alternative to Tauri for easier debugging.
Run with: uvicorn backend.server:app --reload --port 8080
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import sys
import json
import re
import random

# Add parent src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pyros_cli.local.image_generator import generate_image
from pyros_cli.local.llm_provider import enhance_prompt, generate_prompt_variable_values
from pyros_cli.models.prompt_vars import load_prompt_vars, save_prompt_var

app = FastAPI(title="Pyros API", version="0.1.0")

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Mount output directory for serving images
app.mount("/images", StaticFiles(directory=str(OUTPUT_DIR)), name="images")


class GenerateRequest(BaseModel):
    prompt: str
    count: int = 1
    width: int = 1024
    height: int = 1024
    seed: int | None = None


class EnhanceRequest(BaseModel):
    prompt: str
    instruction: str = ""


@app.get("/api/images")
async def list_images():
    """List all generated images, newest first."""
    images = []
    for f in OUTPUT_DIR.glob("*.png"):
        images.append({
            "path": f"/images/{f.name}",
            "name": f.name,
            "modified": f.stat().st_mtime,
        })
    
    # Sort by modification time, newest first
    images.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"images": images}


@app.get("/api/variables")
async def list_variables():
    """List all available prompt variables."""
    prompt_vars = load_prompt_vars()
    return {
        "variables": [
            {"name": name, "count": len(var.values)}
            for name, var in prompt_vars.items()
        ]
    }


@app.post("/api/enhance")
async def enhance(request: EnhanceRequest):
    """Enhance a prompt using the local LLM."""
    try:
        enhanced = enhance_prompt(request.prompt, request.instruction)
        return {"enhanced": enhanced}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    """Generate images from a prompt."""
    try:
        prompt = request.prompt
        
        # Load and substitute variables
        prompt_vars = load_prompt_vars()
        pattern = r'(__[a-zA-Z0-9_\-/]+__)'
        
        for match in re.findall(pattern, prompt):
            var_name = match
            
            if var_name not in prompt_vars:
                # Generate missing variable
                try:
                    values = generate_prompt_variable_values(var_name, prompt, count=20)
                    if values:
                        save_prompt_var(var_name, values)
                        prompt_vars = load_prompt_vars()  # Reload
                except Exception as e:
                    print(f"Failed to generate variable {var_name}: {e}")
            
            if var_name in prompt_vars:
                var = prompt_vars[var_name]
                if var.values:
                    replacement = random.choice(var.values)
                    prompt = prompt.replace(match, replacement, 1)
        
        # Generate images
        results = []
        for i in range(request.count):
            seed = request.seed if request.seed else random.randint(0, 2**32 - 1)
            image, path = generate_image(
                prompt,
                width=request.width,
                height=request.height,
                seed=seed,
            )
            results.append({
                "path": f"/images/{Path(path).name}",
                "seed": seed,
            })
        
        return {
            "images": results,
            "final_prompt": prompt,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


