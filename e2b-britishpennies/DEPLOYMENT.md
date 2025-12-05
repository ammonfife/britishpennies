# British Pennies Deployment Summary

## Deployment Date
December 5, 2025

## Hosting Solution
**GitHub Pages** - Free static site hosting from GitHub

## Repository
- **URL**: https://github.com/ammonfife/britishpennies
- **Branch**: main
- **Source**: / (root directory)

## Live URLs
- **Primary Domain**: http://britishpennies.com (LIVE)
- **Secondary Domain**: http://britishpennies.org (LIVE - same content)
- **GitHub Pages URL**: https://ammonfife.github.io/britishpennies/

## DNS Configuration

### britishpennies.com
- **A Records** (pointing to GitHub Pages):
  - 185.199.108.153
  - 185.199.109.153
  - 185.199.110.153
  - 185.199.111.153
- **CNAME Record**:
  - www → ammonfife.github.io
- **TTL**: 600 seconds (10 minutes)

### britishpennies.org
- **A Records** (pointing to GitHub Pages):
  - 185.199.108.153
  - 185.199.109.153
  - 185.199.110.153
  - 185.199.111.153
- **CNAME Record**:
  - www → ammonfife.github.io
- **TTL**: 600 seconds (10 minutes)

## HTTPS Status
- HTTPS certificate is being provisioned by GitHub Pages
- This typically takes 15 minutes to 24 hours
- Once provisioned, HTTPS will be automatically enforced
- Current status: HTTP only (temporary)

## Site Structure
```
britishpennies/
├── index.html          # Homepage with comprehensive guide
├── CNAME              # Custom domain configuration
├── css/
│   └── style.css      # Styling
├── pages/
│   ├── grading.html
│   ├── key-dates.html
│   ├── large-pennies.html
│   └── small-pennies.html
├── images/            # (for future use)
└── js/                # (for future use)
```

## Content Overview
The site is a comprehensive reference guide for British copper and bronze pennies from 1707-1967, including:
- Large copper pennies (1707-1860)
- Small bronze pennies (1860-1967)
- Key dates and rarities (including the famous 1933 penny)
- Grading guides
- Historical timeline
- Valuation tables
- Monarch-by-monarch coverage

## DNS Propagation
- **Status**: Complete (verified via dig)
- Both domains are resolving to GitHub Pages IPs
- Site is accessible and serving correct content

## Next Steps
1. Monitor HTTPS certificate provisioning (check back in 1-24 hours)
2. Once HTTPS is active, update canonical URLs in HTML to use https://
3. Consider adding:
   - Favicon
   - Images of actual coins
   - Varieties and errors page content
   - Resources page content
   - Google Analytics (if desired)

## Update Process
To update the site:
```bash
cd /Users/benfife/github/ammonfife/e2b/britishpennies
# Make changes to files
git add .
git commit -m "Description of changes"
git push
```
Changes will be live within 1-2 minutes after pushing.

## API Credentials Used
- **GoDaddy API**: Successfully used for DNS configuration
  - API Key: AQB4J8WuFd1_Bjsxg5frDYCExX9cvQ4kRV
  - Manages: britishpennies.com, britishpennies.org

## Issues Encountered
None - deployment was successful on first attempt.
