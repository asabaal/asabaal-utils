#!/usr/bin/env python3
"""
CLI tool for generating images using OpenRouter API.
Supports direct prompt input or reading from file.
"""

import argparse
import os
import sys
import requests
import json
import base64
from pathlib import Path


def generate_image(prompt, output_filename, api_key, model="google/gemini-2.5-flash-image-preview"):
    """Generate an image using OpenRouter API."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["image", "text"]
    }
    
    try:
        print(f"Generating image...")
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
    parser = argparse.ArgumentParser(
        description="Generate images using OpenRouter API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with direct prompt
  image-generator "A beautiful sunset over mountains" -o sunset.png
  
  # Generate from prompt file
  image-generator -f prompt.txt -o output.png
  
  # Use different model
  image-generator "A cat" -o cat.png --model nanobanana/nanobanana
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        'prompt', 
        nargs='?', 
        help='Direct prompt for image generation'
    )
    input_group.add_argument(
        '-f', '--file', 
        type=str,
        help='File containing the prompt'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='generated.png',
        help='Output filename (default: generated.png)'
    )
    
    # API options
    parser.add_argument(
        '--model',
        type=str,
        default='google/gemini-2.5-flash-image-preview',
        help='OpenRouter model to use (default: google/gemini-2.5-flash-image-preview)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='OpenRouter API key (default: OPENROUTER_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OpenRouter API key required")
        print("Set OPENROUTER_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Get prompt
    if args.file:
        try:
            with open(args.file, 'r') as f:
                prompt = f.read().strip()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}")
            sys.exit(1)
    else:
        prompt = args.prompt
    
    if not prompt:
        print("Error: Empty prompt")
        sys.exit(1)
    
    # Get output filename
    output_filename = args.output
    
    # Generate image
    success = generate_image(prompt, output_filename, api_key, args.model)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()