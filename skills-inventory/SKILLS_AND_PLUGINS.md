# Claude Code Skills & Plugins Inventory

Generated: 2026-03-24

---

## Built-in Tools (Core)

| Tool | Description |
|------|-------------|
| **Bash** | Execute shell commands |
| **Read** | Read files (text, images, PDFs, notebooks) |
| **Write** | Create new files |
| **Edit** | Make precise string replacements in existing files |
| **Glob** | Fast file pattern matching (e.g. `**/*.ts`) |
| **Grep** | Content search using ripgrep regex |
| **Agent** | Launch specialized sub-agents for complex tasks |
| **TodoWrite** | Task tracking and progress management |
| **WebFetch** | Fetch content from URLs |
| **WebSearch** | Search the web |
| **NotebookEdit** | Edit Jupyter notebook cells |
| **Skill** | Invoke user-invocable skills (slash commands) |
| **ToolSearch** | Discover and load deferred tool schemas |

---

## Specialized Sub-Agents (via Agent tool)

| Agent Type | Purpose |
|------------|---------|
| **general-purpose** | Multi-step tasks, code search, research |
| **Explore** | Fast codebase exploration (quick/medium/very thorough) |
| **Plan** | Software architecture and implementation planning |
| **claude-code-guide** | Answer questions about Claude Code, Agent SDK, Claude API |
| **statusline-setup** | Configure Claude Code status line settings |

---

## Slash Command Skills (user-invocable)

| Skill | Description |
|-------|-------------|
| **/update-config** | Configure Claude Code harness settings (hooks, permissions, env vars) |
| **/simplify** | Review changed code for reuse, quality, efficiency and fix issues |
| **/loop** | Run a prompt or slash command on a recurring interval |
| **/claude-api** | Build apps with the Claude API or Anthropic SDK |
| **/session-start-hook** | Create startup hooks for Claude Code on the web |

---

## GitHub MCP Server Plugin (53 tools)

All tools prefixed with `mcp__github__`, scoped to `josephalbarmaky-source/ai_playground`.

### Repository Management
| Tool | Description |
|------|-------------|
| `create_repository` | Create a new GitHub repository |
| `fork_repository` | Fork a repository |
| `create_branch` | Create a new branch |
| `list_branches` | List branches |
| `list_tags` | List git tags |
| `get_tag` | Get tag details |
| `get_file_contents` | Read file/directory contents from GitHub |
| `create_or_update_file` | Create or update a single file remotely |
| `delete_file` | Delete a file from a repository |
| `push_files` | Push multiple files in a single commit |
| `search_repositories` | Search for repositories |
| `search_code` | Search code across repositories |

### Issues
| Tool | Description |
|------|-------------|
| `issue_read` | Get issue details, comments, sub-issues, labels |
| `issue_write` | Create or update issues |
| `list_issues` | List issues with filtering |
| `search_issues` | Search issues with GitHub syntax |
| `list_issue_types` | List supported issue types for an org |
| `sub_issue_write` | Add/remove/reprioritize sub-issues |
| `add_issue_comment` | Comment on an issue |
| `get_label` | Get a specific label |

### Pull Requests
| Tool | Description |
|------|-------------|
| `create_pull_request` | Create a new PR |
| `update_pull_request` | Update an existing PR |
| `update_pull_request_branch` | Sync PR branch with base |
| `merge_pull_request` | Merge a PR |
| `list_pull_requests` | List PRs with filtering |
| `search_pull_requests` | Search PRs with GitHub syntax |
| `pull_request_read` | Get PR details, diff, files, status, comments, reviews, check runs |
| `enable_pr_auto_merge` | Enable auto-merge on a PR |
| `disable_pr_auto_merge` | Disable auto-merge on a PR |

### PR Reviews
| Tool | Description |
|------|-------------|
| `pull_request_review_write` | Create, submit, or delete PR reviews |
| `add_comment_to_pending_review` | Add comment to a pending review |
| `add_reply_to_pull_request_comment` | Reply to an existing PR comment |
| `resolve_review_thread` | Mark a review thread as resolved |
| `unresolve_review_thread` | Unresolve a review thread |

### PR Monitoring
| Tool | Description |
|------|-------------|
| `subscribe_pr_activity` | Subscribe to PR webhook events |
| `unsubscribe_pr_activity` | Unsubscribe from PR events |

### Copilot Integration
| Tool | Description |
|------|-------------|
| `assign_copilot_to_issue` | Assign Copilot agent to an issue |
| `create_pull_request_with_copilot` | Delegate a task to Copilot agent |
| `get_copilot_job_status` | Check Copilot agent job status |
| `request_copilot_review` | Request automated Copilot code review |

### Commits & Releases
| Tool | Description |
|------|-------------|
| `get_commit` | Get commit details and diff |
| `list_commits` | List commits on a branch |
| `list_releases` | List releases |
| `get_latest_release` | Get the latest release |
| `get_release_by_tag` | Get a release by tag name |

### Users & Teams
| Tool | Description |
|------|-------------|
| `get_me` | Get authenticated user details |
| `search_users` | Search for GitHub users |
| `get_teams` | Get teams the user belongs to |
| `get_team_members` | Get members of a specific team |

### Security
| Tool | Description |
|------|-------------|
| `run_secret_scanning` | Scan files/diffs for leaked secrets |

---

## Summary

| Category | Count |
|----------|-------|
| Core Tools | 14 |
| Sub-Agent Types | 5 |
| Slash Command Skills | 5 |
| GitHub MCP Tools | 53 |
| **Total Capabilities** | **77** |
