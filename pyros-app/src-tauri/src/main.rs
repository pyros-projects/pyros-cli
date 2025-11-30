#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::Command;
use std::path::PathBuf;
use std::fs;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct GenerationResult {
    images: Vec<String>,
    error: Option<String>,
}

/// Get the output directory for generated images
fn get_output_dir() -> PathBuf {
    // Navigate to pyros-cli output directory
    let current_dir = std::env::current_dir().unwrap_or_default();
    let output_dir = current_dir.parent()
        .unwrap_or(&current_dir)
        .join("output");
    
    if !output_dir.exists() {
        fs::create_dir_all(&output_dir).ok();
    }
    
    output_dir
}

/// List existing images in the output directory
#[tauri::command]
fn list_images() -> Vec<String> {
    let output_dir = get_output_dir();
    
    let mut images: Vec<(String, std::time::SystemTime)> = fs::read_dir(&output_dir)
        .ok()
        .map(|entries| {
            entries
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path()
                        .extension()
                        .map(|ext| ext == "png" || ext == "jpg" || ext == "jpeg")
                        .unwrap_or(false)
                })
                .filter_map(|e| {
                    let path = e.path();
                    let modified = e.metadata().ok()?.modified().ok()?;
                    Some((path.to_string_lossy().to_string(), modified))
                })
                .collect()
        })
        .unwrap_or_default();
    
    // Sort by modification time, newest first
    images.sort_by(|a, b| b.1.cmp(&a.1));
    
    images.into_iter().map(|(path, _)| path).collect()
}

/// Generate images using the Python backend
#[tauri::command]
async fn generate_image(
    prompt: String,
    count: u32,
    width: u32,
    height: u32,
) -> Result<Vec<String>, String> {
    // Get the path to the Python backend
    let current_dir = std::env::current_dir().map_err(|e| e.to_string())?;
    let backend_dir = current_dir.parent()
        .unwrap_or(&current_dir)
        .to_path_buf();

    // Build the command to run the Python generator
    let output = Command::new("uv")
        .current_dir(&backend_dir)
        .args([
            "run", "python", "-c",
            &format!(r#"
import json
import sys
sys.path.insert(0, 'src')

from pyros_cli.local.image_generator import generate_image
from pyros_cli.local.llm_provider import generate_prompt_variable_values
from pyros_cli.models.prompt_vars import load_prompt_vars, save_prompt_var
import re
import random

prompt = '''{prompt}'''
count = {count}
width = {width}
height = {height}

# Load existing variables
prompt_vars = load_prompt_vars()

# Substitute variables
pattern = r'(__[a-zA-Z0-9_\-/]+__)'
for match in re.findall(pattern, prompt):
    if match in prompt_vars:
        var = prompt_vars[match]
        if var.values:
            replacement = random.choice(var.values)
            prompt = prompt.replace(match, replacement, 1)

# Generate images
results = []
for i in range(count):
    try:
        image, path = generate_image(prompt, width=width, height=height)
        results.append(path)
    except Exception as e:
        print(f"Error: {{e}}", file=sys.stderr)

print(json.dumps(results))
"#),
        ])
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Generation failed: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    
    // Parse JSON output
    let images: Vec<String> = serde_json::from_str(stdout.trim())
        .map_err(|e| format!("Failed to parse output: {} - {}", e, stdout))?;

    Ok(images)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            list_images,
            generate_image,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
