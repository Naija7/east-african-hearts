# How to Add Couple Images to Your Gallery

## Step 1: Get Images
Download couple images from these free sources:
- **Unsplash** (unsplash.com) - Search: "couple", "African couple", "happy couple"
- **Pexels** (pexels.com) - Similar search
- **Pixabay** (pixabay.com) - Diverse couple photos
- **Freepik** (freepik.com) - Various styles (free version available)

## Step 2: Prepare Your Images
1. Download 6 high-quality couple images
2. Rename them as:
   - `couple1.jpg`
   - `couple2.jpg`
   - `couple3.jpg`
   - `couple4.jpg`
   - `couple5.jpg`
   - `couple6.jpg`

3. Recommended image specs:
   - Size: At least 500x600px (landscape or portrait)
   - Format: JPG or PNG
   - File size: Optimize to <2MB each for faster loading

## Step 3: Place Images
Move your renamed images to:
```
C:\East african dating\static\images\
```

Your folder should look like:
```
static/
  ├── images/
  │   ├── couple1.jpg
  │   ├── couple2.jpg
  │   ├── couple3.jpg
  │   ├── couple4.jpg
  │   ├── couple5.jpg
  │   └── couple6.jpg
  ├── style.css
  └── logo.svg
```

## Step 4: View Your Gallery
Run your Flask app and visit the homepage to see your beautiful gallery!

```bash
python app.py
```

## Customization
You can edit the couple names and locations in `templates/home.html`:
- Line 69: Change "Sarah & John" and "Kenya"
- Line 76: Change "Amara & David" and "Uganda"
- And so on...

## Tips
- Use images with good lighting and clear faces
- Prefer diverse, genuine-looking couples
- Ensure all faces are visible and centered
- Test on mobile to ensure images display well
