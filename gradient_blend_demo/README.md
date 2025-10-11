# Gradient Blend Demo

This directory contains a comprehensive demonstration of the gradient blending functionality from the asabaal-utils image processing module.

## 🎨 What You'll See

### Original Images
- **`demo_top.png`** - Blue background with white circles labeled "TOP"
- **`demo_bottom.png`** - Green background with yellow squares labeled "BOTTOM"

### Blending Examples

| Image | Description | Overlap | Easing | Size |
|-------|-------------|---------|--------|------|
| `blend_light.png` | Subtle transition | 10% | Cosine | 600×727 |
| `blend_medium.png` | Balanced transition (default) | 25% | Cosine | 600×640 |
| `blend_heavy.png` | Gradual transition | 40% | Cosine | 600×571 |
| `blend_linear.png` | Sharp linear transition | 30% | Linear | 600×615 |
| `blend_fixed.png` | Exact pixel overlap | 150px | Cosine | 600×650 |
| `blend_padded.png` | Padded to specific height | 20% | Cosine | 600×1000 |

### Preview Masks
Each blend has a corresponding `_preview_mask.png` file that shows the exact gradient shape:
- **White areas** = Top image (fully visible)
- **Black areas** = Bottom image (fully visible)  
- **Gray gradient** = Transition zone

### Comparison
- **`comparison.png`** - Side-by-side comparison of all blending results

## 🔍 How to Understand the Gradient Effect

1. **Look at the shapes**: Notice how the blue circles gradually transition to green squares
2. **Check the overlap region**: The middle section shows the smooth gradient blend
3. **Compare easing functions**: Linear vs cosine - notice cosine is smoother
4. **Examine preview masks**: These show exactly where the transition happens

## 💡 Key Insights

- **Light overlap (10%)**: Quick transition, most of each image visible
- **Medium overlap (25%)**: Balanced blend, good for most use cases
- **Heavy overlap (40%)**: Very gradual transition, large blended area
- **Linear vs Cosine**: Linear has a straight fade, cosine has smooth S-curve
- **Fixed pixels**: Precise control when you need exact overlap dimensions
- **Padding**: Useful for creating specific output dimensions (e.g., social media formats)

## 🚀 Usage Examples

```bash
# Recreate these blends with the CLI
gradient-blend demo_top.png demo_bottom.png my_blend.png --overlap 0.25 --preview

# Instagram story format
gradient-blend demo_top.png demo_bottom.png story.png --width 1080 --out-height 1920 --pad

# Sharp linear transition
gradient-blend demo_top.png demo_bottom.png linear.png --overlap 0.3 --ease linear
```

```python
# Python API usage
from asabaal_utils.image_processing import blend_images

result = blend_images(
    "demo_top.png", 
    "demo_bottom.png", 
    "output.png",
    width=600,
    overlap=0.25,
    preview=True
)
print(f"Created blend: {result['output_size']}")
```

This demo clearly shows how gradient blending can seamlessly combine two different images with smooth, professional-looking transitions.