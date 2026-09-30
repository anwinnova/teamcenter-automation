# AutoScript API & Data Orchestration Pipeline
# Demonstrates chaining HTTP APIs, AI reasoning, and Exporting

set $endpoint = "https://api.github.com/orgs/novasmart/repos"

http_get $endpoint -> ai "Extract top 3 trending repositories and write release notes summary" -> export "release_notes.json"

set $count = 3
repeat $count times
  log "Polling system status check iteration..."
  wait 500ms
end

log "Pipeline execution finished successfully!"
