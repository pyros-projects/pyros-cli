# Prompt Variable Generation Logic

This document explains how `pyros-cli` (local mode) automatically generates values for missing prompt variables using the local LLM.

## Overview

When you use a variable like `__cat_breed__` in your prompt and it doesn't exist yet, the system:
1. Detects the missing variable
2. Analyzes the variable name to determine what kind of values to generate
3. Uses the local LLM (Qwen3-4B) to generate 20+ appropriate values
4. Saves them to `src/pyros_cli/library/prompt_vars/`

## Variable Naming Patterns

The **name of your variable** determines what kind of content is generated:

### Full Scene Descriptions

Use these patterns when you want **complete, detailed scene prompts**:

| Pattern | Example Variable | Generated Output |
|---------|-----------------|------------------|
| `variations_of_X` | `__variations_of_a_knight__` | "A knight in obsidian armor stands at dawn on a misty cliff, his cape billowing..." |
| `scene_X` | `__scene_cozy_library__` | "Warm candlelight illuminates towering bookshelves, a leather chair by the fireplace..." |
| `scenes_X` | `__scenes_underwater_city__` | "Bioluminescent towers rise from the ocean floor, schools of silver fish..." |
| `description_X` | `__description_alien_forest__` | "Towering mushrooms with glowing caps pierce the violet sky, mist curling..." |
| `prompt_X` | `__prompt_cyberpunk_street__` | "Neon signs reflect off rain-slicked streets, a lone figure in a trench coat..." |
| `version_X` | `__version_sunset_beach__` | "Golden hour paints the waves in amber and rose, footprints trailing..." |

**Best for:** Creating diverse variations of a concept, batch generating related scenes.

### Simple Values (Substitution)

Use these patterns when you want **short values that fit into a larger prompt**:

| Pattern | Example Variable | Generated Output |
|---------|-----------------|------------------|
| `X_style` | `__art_style__` | "impressionist", "cyberpunk", "watercolor" |
| `X_color` | `__hair_color__` | "auburn", "platinum blonde", "raven black" |
| `X_type` | `__vehicle_type__` | "vintage motorcycle", "sports car", "horse-drawn carriage" |
| `X_mood` | `__lighting_mood__` | "dramatic noir", "soft golden hour", "harsh neon" |
| `X_artist` | `__famous_artist__` | "Van Gogh", "Monet", "H.R. Giger" |
| `X_genre` | `__movie_genre__` | "film noir", "sci-fi epic", "romantic comedy" |
| `X_setting` | `__fantasy_setting__` | "elven forest", "dwarven forge", "floating islands" |
| Generic nouns | `__animal__`, `__emotion__` | "wolf", "eagle" / "melancholic", "joyful" |

**Best for:** Mix-and-match prompt building, style experimentation.

## Examples

### Creating Scene Variations

```bash
# Full scene descriptions for a concept
>>> __scene_japanese_garden__ : x5

# Will generate 5 different complete scenes like:
# "A serene koi pond reflects cherry blossoms at twilight, stone lanterns casting soft shadows..."
# "Morning mist drifts through bamboo groves, a wooden bridge arching over still water..."
```

### Style Mixing

```bash
# Simple style values to mix into prompts
>>> a portrait of a warrior, __art_style__, __lighting_mood__

# Substitutes values like:
# "a portrait of a warrior, oil painting renaissance, dramatic chiaroscuro"
```

### Batch Generation with Custom Sizes

```bash
# Generate 10 variations at custom resolution
>>> __variations_of_enchanted_forest__ : x10,w1216,h832
```

## Syntax Reference

### Basic Variable Syntax

```
__variable_name__           # Random value from existing or auto-generated list
__variable_name:3__         # Specific value at index 3
```

### Prompt Enhancement

```
prompt > enhancement instruction
```

Example:
```bash
>>> a cat sitting on a windowsill > make it dramatic and cinematic
```

### Batch Parameters

```
prompt : x<count>,h<height>,w<width>
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `x<N>` | Number of images to generate | 1 |
| `h<N>` | Image height in pixels | 1024 |
| `w<N>` | Image width in pixels | 1024 |

Example:
```bash
>>> __scene_epic_battle__ : x5,h832,w1216
```

## Tips for Better Results

### Variable Naming

✅ **Good variable names:**
```
__scene_rainy_tokyo_street__          # Clear, descriptive
__variations_of_wizard_portrait__     # Explicit variation request
__art_style__                         # Clear suffix pattern
__emotion_intense__                   # Specific category
```

❌ **Ambiguous names:**
```
__cool_stuff__                        # Too vague
__things__                            # No context
__x__                                 # Meaningless
```

### Prompt Structure

For best results, structure your prompts like:
```
[subject] [action/pose] [setting], [style modifiers], __variable__
```

Example:
```bash
>>> a young woman reading in a cafe, soft morning light, __art_style__, by __famous_artist__
```

### Building a Library

Over time, your `library/prompt_vars/` folder becomes a curated collection:

```
prompt_vars/
├── animal.md                    # Basic categories
├── emotion.md
├── art_style.md                 # Style values
├── lighting_mood.md
├── scene_cozy_cafe.md           # Full scene collections
├── scene_cyberpunk_city.md
├── variations_of_samurai.md
└── ...
```

## How Generation is Optimized

When using batch mode (`: x10`), the system:

1. **Phase 1 (LLM):** Generates ALL prompts first
   - Variable substitution with fresh random values each time
   - Enhancement with local LLM if using `>`
   - LLM is loaded once, then unloaded

2. **Phase 2 (Image):** Generates ALL images
   - Image model loaded once
   - All images rendered sequentially
   - Previews shown after each

This is more efficient than loading/unloading models for each image!

## File Format

Generated variable files are simple markdown:

```markdown
# Description of the variable
value 1
value 2
value 3
...
```

Lines starting with `#` are comments/descriptions. All other non-empty lines are values.

---

*Last updated: November 2025*


