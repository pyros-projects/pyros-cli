# gallery_app.py
from fasthtml.common import *
import os
from pathlib import Path
import json # To safely inject the list into JavaScript
from starlette.responses import FileResponse
from starlette.exceptions import HTTPException


 # --- Configuration ---
IMAGE_DIR_NAME = "images"
IMAGE_DIR = Path(IMAGE_DIR_NAME)
# Add more image extensions if needed
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
# --- End Configuration ---

# Check if image directory exists on startup
if not IMAGE_DIR.is_dir():
    print(f"Error: Image directory '{IMAGE_DIR}' not found.")
    print(f"Please create it in the same directory as this script and add images.")
    # You could raise an exception here to stop the server from starting
    # raise FileNotFoundError(f"Image directory '{IMAGE_DIR}' not found.")

# Define headers for external libraries (CSS & JS)
# Using CDNs for simplicity
gallery_hdrs = (
    # PhotoSwipe Core CSS
    Link(rel="stylesheet", href="https://unpkg.com/photoswipe@5.4.3/dist/photoswipe.css"),
    # Masonry & imagesLoaded (JS loaded later in the body)
)

app, rt = fast_app(hdrs=gallery_hdrs)

# --- CSS Styles (Embedded) ---
# Using the same CSS as the previous static HTML example
gallery_style = Style("""
    /* --- Basic Reset & Body --- */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6; background-color: #141414; color: #333;
        padding: 20px;
    }
    h1 { text-align: center; margin-bottom: 30px; color: #2c3e50; }

    /* --- Gallery Container --- */
    .image-gallery-container { max-width: 1200px; margin: 0 auto; overflow: hidden; }

    /* --- Masonry Grid Items --- */
    .grid-sizer, .grid-item {
        width: calc(33.333% - 10px); /* 3 columns with gutter */
        margin-bottom: 15px; /* Vertical spacing */
    }
    .grid-item {
        float: left; background-color: #fff; border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        overflow: hidden; transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
    }
    .grid-item:hover { transform: translateY(-5px); box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15); }
    .grid-item img { display: block; width: 100%; height: auto; }
    .grid-item a { display: block; line-height: 0; } /* Prevent extra space */

    /* --- Responsive Adjustments --- */
    @media (max-width: 992px) { .grid-sizer, .grid-item { width: calc(50% - 8px); } }
    @media (max-width: 576px) { .grid-sizer, .grid-item { width: 100%; } h1 { font-size: 1.8em; } }

    /* --- PhotoSwipe Customizations --- */
    .pswp__bg { background: rgba(0, 0, 0, 0.85); }
    .pswp__caption { 
        background-color: rgba(0, 0, 0, 0.75); 
        color: #fff; 
        padding: 15px;
        font-size: 14px;
        max-height: 40%;
        overflow-y: auto;
        white-space: pre-wrap;
        font-family: monospace;
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 1500;
    }
    /* Custom prompt container */
    .prompt-container {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 15px;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 40%;
        overflow-y: auto;
        z-index: 1500;
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        font-size: 18px;
        line-height: 1.6;
    }
""")

# --- Client-Side JavaScript (Embedded) ---
# Very similar to the static version, but reads `imageFiles` variable injected by server
gallery_js = Script("""
// Ensure this runs after the DOM is ready and imageFiles is defined
document.addEventListener('DOMContentLoaded', () => {
    // `imageFiles` and `promptMap` variables are injected by the FastHTML server route below
    const galleryElement = document.getElementById('gallery');

    if (!galleryElement) {
        console.error("Gallery container element not found!");
        return; // Stop if gallery element is missing
    }

    if (typeof imageFiles === 'undefined' || !Array.isArray(imageFiles)) {
        console.error("`imageFiles` array not found or invalid. Check server template.");
        galleryElement.innerHTML = '<p style="text-align: center; color: red;">Error: Could not load image list from server.</p>';
        return;
    }

    if (imageFiles.length === 0) {
        galleryElement.innerHTML = '<p style="text-align: center;">No images found in the images directory.</p>';
        return; // No need to initialize libraries if no images
    }

    // Debug: Log the promptMap to verify data
    console.log('Prompt Map:', promptMap);

    // 1. Dynamically add image elements (already done by server-side FT rendering)
    //    We still need to prepare for PhotoSwipe dimension detection

    // 2. Import PhotoSwipe (requires type="module" which we'll add server-side)
    import('https://unpkg.com/photoswipe@5.4.3/dist/photoswipe-lightbox.esm.js').then(psLightboxModule => {
    import('https://unpkg.com/photoswipe@5.4.3/dist/photoswipe.esm.js').then(psModule => {
        const PhotoSwipeLightbox = psLightboxModule.default;
        const PhotoSwipe = psModule.default;

        // 3. Use imagesLoaded before initializing Masonry and PhotoSwipe
        imagesLoaded( galleryElement, function( instance ) {
            console.log('imagesLoaded: ALL IMAGES LOADED');

            // Add dimensions to links for PhotoSwipe *after* images are loaded
            galleryElement.querySelectorAll('.grid-item a').forEach(link => {
                const img = link.querySelector('img');
                if (img && img.naturalWidth > 0) { // Check if loaded correctly
                    link.dataset.pswpWidth = img.naturalWidth;
                    link.dataset.pswpHeight = img.naturalHeight;
                    
                    // Get the image filename and check if there's a prompt for it
                    const imgSrc = link.getAttribute('href');
                    const imgName = imgSrc.split('/').pop(); // Extract filename from path
                    
                    // Set caption if we have a prompt for this image
                    if (typeof promptMap !== 'undefined' && promptMap[imgName]) {
                        link.dataset.pswpCaption = promptMap[imgName];
                        console.log(`Set caption for ${imgName}`); // Debug
                    }
                } else {
                    console.warn(`Could not get dimensions for ${img ? img.src : 'an image'}. Hiding item.`);
                    link.closest('.grid-item').style.display = 'none'; // Hide items without dimensions
                }
            });

            // Re-check gallery element existence after potential async operations
            const finalGalleryElement = document.getElementById('gallery');
            if (!finalGalleryElement) return;


            // 4. Initialize Masonry
            try {
                const msnry = new Masonry( finalGalleryElement, {
                    itemSelector: '.grid-item',
                    columnWidth: '.grid-sizer',
                    gutter: 15,
                    percentPosition: true,
                    initLayout: true // Initialize layout immediately
                });
                // Optional: Relayout Masonry if window is resized
                window.addEventListener('resize', () => { msnry.layout(); });
                console.log('Masonry initialized.');

                // Sometimes an explicit layout call helps after setup
                setTimeout(() => msnry.layout(), 50);

            } catch (e) {
                console.error("Failed to initialize Masonry:", e);
                finalGalleryElement.innerHTML = '<p style="text-align: center; color: red;">Error: Failed to initialize grid layout.</p>';
                return; // Don't initialize PhotoSwipe if Masonry fails
            }


            // 5. Initialize PhotoSwipe
            try {
                // Create custom UI element for captions
                const createCustomUIElements = (gallery) => {
                    const promptContainer = document.createElement('div');
                    promptContainer.className = 'prompt-container';
                    promptContainer.style.display = 'none';
                    gallery.pswp.ui.registerElement({
                        name: 'custom-prompt-container',
                        order: 9,
                        isButton: false,
                        appendTo: 'root',
                        html: '',
                        onInit: (el) => {
                            promptContainer.onclick = (e) => {
                                // Prevent click from closing the gallery
                                e.stopPropagation();
                            };
                            el.appendChild(promptContainer);
                        }
                    });
                    return promptContainer;
                };

                const lightbox = new PhotoSwipeLightbox({
                    gallery: '#gallery',
                    children: 'a',
                    pswpModule: PhotoSwipe,
                    showHideAnimationType: 'fade',
                    imageClickAction: 'zoom',
                    tapAction: 'toggle-controls',
                });
                
                let promptContainer;
                
                // Initialize custom UI
                lightbox.on('uiRegister', () => {
                    promptContainer = createCustomUIElements(lightbox);
                });
                
                // Update caption when slide changes
                lightbox.on('change', () => {
                    if (!promptContainer) return;
                    
                    const currentSlide = lightbox.pswp.currSlide;
                    if (currentSlide && currentSlide.data.element.dataset.pswpCaption) {
                        promptContainer.textContent = currentSlide.data.element.dataset.pswpCaption;
                        promptContainer.style.display = 'block';
                        console.log('Showing caption:', currentSlide.data.element.dataset.pswpCaption);
                    } else {
                        promptContainer.style.display = 'none';
                        console.log('No caption for current slide');
                    }
                });
                
                // Also handle the initial open event
                lightbox.on('afterInit', () => {
                    setTimeout(() => {
                        if (promptContainer && lightbox.pswp && lightbox.pswp.currSlide) {
                            const caption = lightbox.pswp.currSlide.data.element.dataset.pswpCaption;
                            if (caption) {
                                promptContainer.textContent = caption;
                                promptContainer.style.display = 'block';
                                console.log('Initial caption set');
                            }
                        }
                    }, 100);
                });
                
                lightbox.init();
                console.log('PhotoSwipe initialized.');
            } catch (e) {
                console.error("Failed to initialize PhotoSwipe:", e);
                // Gallery still works, just no lightbox
            }

        }).on('fail', function() {
            console.error('imagesLoaded failed.');
            // Handle failure: maybe show an error message
            const gallery = document.getElementById('gallery');
            if(gallery) gallery.innerHTML = '<p style="text-align: center; color: red;">Error loading some images. Layout may be broken.</p>';
        }); // end imagesLoaded

    }).catch(e => console.error("Failed to load PhotoSwipe Core module:", e));
    }).catch(e => console.error("Failed to load PhotoSwipe Lightbox module:", e));

}); // End DOMContentLoaded
""", type="module") # Important: type="module" for PhotoSwipe imports

def show_gallery():

   
    serve() # Automatically uses uvicorn, checks __main__
    # --- Route Handlers ---

@rt("/")
def get_gallery():
    """Serves the main gallery page."""
    image_filenames = []
    if IMAGE_DIR.is_dir():
        for filename in os.listdir(IMAGE_DIR):
            if os.path.isfile(os.path.join(IMAGE_DIR, filename)):
                # Check extension (case-insensitive)
                if Path(filename).suffix.lower() in ALLOWED_EXTENSIONS:
                    image_filenames.append(filename)
        image_filenames.sort() # Optional: sort alphabetically
    else:
        # Directory doesn't exist, message handled by JS, but log server-side too
        print(f"Warning: Image directory '{IMAGE_DIR}' not found when generating gallery page.")

    # Load prompt text files for all images
    prompt_map = {}
    for image_filename in image_filenames:
        base_name = os.path.splitext(image_filename)[0]
        txt_file = os.path.join(IMAGE_DIR, f"{base_name}.txt")
        if os.path.exists(txt_file):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    prompt_text = f.read()
                    prompt_map[image_filename] = prompt_text
                    print(f"Loaded prompt for {image_filename}")
            except Exception as e:
                print(f"Error reading prompt file {txt_file}: {e}")
    
    # Debug log to see if prompts were loaded
    print(f"Loaded {len(prompt_map)} prompts for {len(image_filenames)} images")

    # Dynamically generate gallery items using FastTags (FTs)
    gallery_items = []
    for fname in image_filenames:
        # The links now point to our image serving route
        img_path = f"/{IMAGE_DIR_NAME}/{fname}"
        item = Div(
            A(Img(src=img_path, alt=fname, loading="lazy"), # Lazy loading for thumbs
            href=img_path, # Link for PhotoSwipe to full image
            data_pswp_src=img_path, # Explicit source for PhotoSwipe
            # data_pswp_width/height will be added by client-side JS
            target="_blank" # Fallback if JS fails
            ),
            cls='grid-item'
        )
        gallery_items.append(item)

    # Safely inject the list of filenames and prompt map for client-side JS
    # We point JS to the same image serving route
    js_image_list_script = Script(f"""
        const imageFiles = {json.dumps([f'/{IMAGE_DIR_NAME}/{fname}' for fname in image_filenames])};
        const promptMap = {json.dumps(prompt_map)};
    """)

    # Assemble the page content
    page_content = (
        Title("Pyro's CLI - Gallery"), # Sets the <title> tag
        gallery_style, # Embed CSS
        H1("Pyro's CLI - Gallery"),
        Div( # The main gallery container for Masonry & PhotoSwipe
            Div(cls="grid-sizer"), # Masonry requires this
            *gallery_items,        # Unpack the list of generated Divs
            id="gallery",
            cls="image-gallery-container masonry-grid" # Add class for clarity
        ),
        # External JS Libraries (CDNs) - Loaded after gallery HTML
        Script(src="https://unpkg.com/imagesloaded@5/imagesloaded.pkgd.min.js"),
        Script(src="https://unpkg.com/masonry-layout@4/dist/masonry.pkgd.min.js"),
        # Inject the image list for the main JS logic
        js_image_list_script,
        # The main JS logic for initialization
        gallery_js
    )

    return page_content

@rt(f"/{IMAGE_DIR_NAME}/{{filename:path}}")
async def get_image(filename: str):
    """Serves individual image files securely."""
    # Basic security check: ensure filename doesn't try directory traversal
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=404, detail="Not Found")

    file_path = IMAGE_DIR / filename

    # Double check it's a file and exists within the designated directory
    if file_path.is_file() and str(file_path.resolve()).startswith(str(IMAGE_DIR.resolve())):
        # Check extension again just to be safe
        if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            return FileResponse(file_path)

    # If any check fails, return 404
    raise HTTPException(status_code=404, detail="Image not found or not allowed")


# --- Run the application ---
if __name__ == "__main__":

    serve()
        

   