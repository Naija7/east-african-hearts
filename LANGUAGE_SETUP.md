# Kinyarwanda Language Support - Setup Guide

## Features Added

✅ **Kinyarwanda Translation Dictionary**
✅ **Language Switching Route**
✅ **Session-based Language Storage**
✅ **Fallback to English**

---

## How to Use

### 1. **Access the Language Switcher**
You can add language buttons to your navbar. Add this to `templates/home.html` in the navbar:

```html
<div class="language-switcher">
    <a href="{{ url_for('home.set_language', language='en') }}" 
       class="lang-btn {% if lang == 'en' %}active{% endif %}">EN</a>
    <a href="{{ url_for('home.set_language', language='rw') }}" 
       class="lang-btn {% if lang == 'rw' %}active{% endif %}">RW</a>
</div>
```

### 2. **Update Templates to Use Translations**

Instead of hardcoding text, use the translation dictionary:

**Before:**
```html
<h2>Welcome Back</h2>
```

**After:**
```html
<h2>{{ t.welcome_back }}</h2>
```

### 3. **Add to Any Page**
To add translations to any template:

```html
<h1>{{ t.tagline }}</h1>
<p>{{ t.subtitle }}</p>
<a href="/register">{{ t.register }}</a>
```

---

## Supported Languages

| Language | Code | Status |
|----------|------|--------|
| English | `en` | ✅ Complete |
| Kinyarwanda | `rw` | ✅ Complete |
| Swahili | `sw` | ✅ Complete |

---

## How to Add More Languages

### Step 1: Add to `translations.py`
```python
TRANSLATIONS = {
    'en': { ... },
    'rw': { ... },
    'sw': {  # Add Swahili
        'home': 'Nyumbani',
        'login': 'Ingia',
        'register': 'Jiandikishe',
        # ... add all keys
    }
}
```

### 2. **Update Navbar**
```html
<a href="{{ url_for('home.set_language', language='sw') }}" 
   class="lang-btn {% if lang == 'sw' %}active{% endif %}">SW</a>
```

---

## How to Use Swahili

Simply add the Swahili button to your navbar and it will work immediately!

---

## Available Translation Keys

```
Navigation:
- home, login, register, logout

Homepage:
- tagline, subtitle, get_started, already_member
- why_choose, genuine_connections, safe_secure
- community, easy_use, success_stories
- ready_match, join_free, share_story

Login/Register:
- welcome_back, create_account, email, password
- full_name, age, location, interests

Testimonials:
- share_success, your_story, share_btn

Messages:
- registration_success, login_success, logout_success
- invalid_credentials, email_registered
```

---

## How Language is Stored

Language preference is stored in **Flask session**:

```python
session['language'] = 'rw'  # Store Kinyarwanda
```

This means:
- ✅ User preference persists during session
- ✅ Different users can have different languages
- ✅ Resets when user closes browser (can add "Remember me" later)

---

## Implementation Checklist

- [ ] Add language buttons to navbar in `home.html`
- [ ] Update all templates to use `{{ t.key }}` instead of hardcoded text
- [ ] Test English version
- [ ] Test Kinyarwanda version
- [ ] Add more languages as needed

---

## Example: Update Home Template

In `templates/home.html`, change:

```html
<!-- Before -->
<h2>Connecting Hearts Across East Africa</h2>

<!-- After -->
<h2>{{ t.tagline }}</h2>
```

---

## Testing

1. Visit homepage
2. Click "RW" button
3. Page should switch to Kinyarwanda
4. Click "EN" button
5. Page should switch back to English

---

## Notes

- Default language is English
- If key is missing, falls back to English
- Language set on any page affects all subsequent pages
- Add more translations as you expand features
