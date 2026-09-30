# AutoScript Web Scraping & Lead Generator Template
# Author: Founder & Creator

set $url = "https://portal.novasmart.io/leads"
log "Starting Lead Scraper on " $url

open $url
click "#btn-login"
type "#input-search" "Enterprise Clients"
click "#btn-search"
wait 1s

set $data = extract "table.leads-grid"
log "Extracted leads dataset successfully!"

http_get "https://api.novasmart.io/enrich" -> ai "Analyze these leads and categorize by revenue potential" -> export "leads_summary.json"

log "Scraping and AI Enrichment finished!"
