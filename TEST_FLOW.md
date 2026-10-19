# Complete Test Flow Guide - East African Hearts

## PRE-TEST CHECKLIST
- [ ] Flask app running on http://127.0.0.1:5000
- [ ] Database connected (datingdb)
- [ ] 6 couple images in static/images/
- [ ] All routes registered

---

## STEP 1: HOMEPAGE TEST
**URL:** http://127.0.0.1:5000/

### Expected:
- [ ] Beautiful navbar with logo
- [ ] Hero section: "Connecting Hearts Across East Africa"
- [ ] Features section (4 cards)
- [ ] Success Stories gallery (6 generic placeholder couples)
- [ ] "Share Your Story" button
- [ ] Call-to-action section
- [ ] Footer

---

## STEP 2: USER REGISTRATION
**URL:** http://127.0.0.1:5000/register

### Test Data:
```
Full Name: John Mwangi
Email: john@example.com
Password: TestPass123
Gender: Male
Age: 28
Location: Nairobi, Kenya
Interests: Hiking, cooking, traveling
```

### Expected:
- [ ] Form displays correctly
- [ ] All fields render
- [ ] Submit button works
- [ ] Success message appears
- [ ] Redirects to login page

---

## STEP 3: USER LOGIN
**URL:** http://127.0.0.1:5000/login

### Test Data:
```
Email: john@example.com
Password: TestPass123
```

### Expected:
- [ ] Login form displays
- [ ] Credentials accepted
- [ ] Redirects to homepage
- [ ] User session created
- [ ] User appears logged in

---

## STEP 4: SUBMIT TESTIMONIAL
**URL:** http://127.0.0.1:5000/testimonials

### Test Data:
```
Partner 1 Name: John
Partner 2 Name: Sarah
Country: Kenya
Story: We met on East African Hearts and instantly connected! Sarah was everything I was looking for. We're planning our future together now!
```

### Expected:
- [ ] Form displays correctly
- [ ] All fields render
- [ ] Submit button works
- [ ] Success message
- [ ] Redirects to homepage

---

## STEP 5: ADMIN LOGIN & APPROVE
**URL:** http://127.0.0.1:5000/admin-login

### Admin Credentials:
```
Username: admin
Password: Admin@123
```

### Expected:
- [ ] Admin login form displays
- [ ] Credentials accepted
- [ ] Redirects to admin panel
- [ ] Dashboard shows:
  - Total Users: 1
  - Pending Testimonials: 1
  - Approved Testimonials: 0
- [ ] Pending testimonial listed
- [ ] "Approve" button visible

### Approve Testimonial:
- [ ] Click "Approve" button
- [ ] Success message appears
- [ ] Redirects to admin panel
- [ ] Stats update (Pending: 0, Approved: 1)

---

## STEP 6: VIEW APPROVED TESTIMONIAL
**URL:** http://127.0.0.1:5000/

### Expected:
- [ ] Homepage loads
- [ ] One placeholder couple replaced with real testimonial
- [ ] Shows: "John & Sarah" (Kenya)
- [ ] On hover: overlay appears with couple names
- [ ] Other 5 placeholders still generic

---

## STEP 7: USER LOGOUT
**URL:** http://127.0.0.1:5000/logout

### Expected:
- [ ] Session cleared
- [ ] Redirected to homepage
- [ ] Success message displayed
- [ ] User logged out

---

## STEP 8: ADMIN LOGOUT
**URL:** http://127.0.0.1:5000/admin-logout (from admin panel)

### Expected:
- [ ] Session cleared
- [ ] Redirected to admin login
- [ ] Success message displayed

---

## TROUBLESHOOTING

### Issue: "Database connection error"
- Ensure MySQL is running
- Check datingdb exists
- Verify credentials in auth.py

### Issue: "Image not found"
- Verify couple images in: c:\East african dating\static\images\
- Names should be: couple1.jpg through couple6.jpg

### Issue: "Flash messages not showing"
- Check that session secret key is set in app.py
- Line 8 should have: app.secret_key = "..."

### Issue: "Testimonial not appearing"
- Verify it's approved in admin panel
- Check database status field is 'approved'

---

## SUCCESS CRITERIA
All tests passed when:
- [ ] User can register & login
- [ ] User can submit testimonial
- [ ] Admin can approve testimonial
- [ ] Approved testimonial appears on homepage
- [ ] Gallery replaces placeholder with real couple name
- [ ] All pages load with correct styling
- [ ] All buttons are clickable
- [ ] Navigation works
