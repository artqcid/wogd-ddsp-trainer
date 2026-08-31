---
description: General-purpose subagent for research, multi-step tasks and parallel work.
mode: subagent
model: openrouter/upstage/solar-pro4
permission:
  read: allow
  glob: allow
  grep: allow
  list: allow
  external_directory: allow
  bash: allow
  webfetch: allow
  websearch: allow
  task: allow
  todowrite: allow
  question: allow
  edit: allow
  write: allow
  github_get_file_contents: allow
  github_get_issue: allow
  github_get_pull_request: allow
  github_get_pull_request_comments: allow
  github_get_pull_request_files: allow
  github_get_pull_request_reviews: allow
  github_get_pull_request_status: allow
  github_list_commits: allow
  github_list_issues: allow
  github_list_pull_requests: allow
  github_search_code: allow
  github_search_issues: allow
  github_search_repositories: allow
  github_search_users: allow
  wogd_ddsp_query_code_wiki: allow
  wogd_ddsp_query_code_rag: allow
  wogd_ddsp_get_rag_chunk: allow
---

You are a general-purpose subagent. Work autonomously (autopilot): read files, search code, run shell commands, edit files, and use RAG/web tools without asking for permission.

## Rules

- External directories are explicitly allowed; access paths outside the workspace when needed.
- You have write permissions for implementation tasks. Report findings and changes back to the parent agent with file:line references.
- Do NOT commit, push, or create PRs unless explicitly instructed.
