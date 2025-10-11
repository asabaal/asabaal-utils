#!/usr/bin/env python3
import os
import requests
import json
import time
from pathlib import Path

def load_prompts():
    """Load all prompt files from the current directory."""
    prompts = {}
    prompt_files = sorted(Path('.').glob('prompt-*.txt'))
    
    for prompt_file in prompt_files:
        with open(prompt_file, 'r') as f:
            prompt = f.read().strip()
            if prompt:
                prompts[prompt_file.name] = prompt
    
    return prompts

def generate_image(prompt, output_filename, api_key):
    """Generate an image using OpenRouter's Nano Banana model."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "google/gemini-2.5-flash-image-preview",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["image", "text"]
    }
    
    try:
        print(f"Generating image for {output_filename}...")
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the image from the response
        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0]['message']
            if 'images' in message and len(message['images']) > 0:
                # Get the first image
                image_data = message['images'][0]
                if 'image_url' in image_data and 'url' in image_data['image_url']:
                    image_url = image_data['image_url']['url']
                    
                    # Handle base64 data URLs
                    if image_url.startswith('data:'):
                        # Extract the base64 data
                        import base64
                        header, encoded = image_url.split(',', 1)
                        image_data = base64.b64decode(encoded)
                        
                        # Save the image
                        with open(output_filename, 'wb') as f:
                            f.write(image_data)
                    else:
                        # Download from regular URL
                        img_response = requests.get(image_url)
                        img_response.raise_for_status()
                        
                        # Save the image
                        with open(output_filename, 'wb') as f:
                            f.write(img_response.content)
                    
                    print(f"✓ Saved {output_filename}")
                    return True
        
        print(f"✗ Failed to extract image URL from response")
        print(f"Response: {json.dumps(result, indent=2)}")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error generating image: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def main():
    # Get API key from environment variable
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your-api-key-here'")
        return
    
    # Load all prompts
    prompts = load_prompts()
    if not prompts:
        print("No prompt files found!")
        return
    
    print(f"Found {len(prompts)} prompt(s)")
    
    # Generate image for each prompt
    success_count = 0
    for prompt_file, prompt in prompts.items():
        # Generate output filename
        prompt_num = prompt_file.split('-')[1].split('.')[0]
        output_filename = f"psalms-{prompt_num}.png"
        
        # Skip if file already exists
        if os.path.exists(output_filename):
            print(f"⏭ Skipping {output_filename} (already exists)")
            success_count += 1
            continue
        
        # Generate the image
        if generate_image(prompt, output_filename, api_key):
            success_count += 1
        
        # Add a small delay between requests to avoid rate limiting
        time.sleep(2)
    
    print(f"\nCompleted! Generated {success_count}/{len(prompts)} images successfully.")

if __name__ == "__main__":
    main()