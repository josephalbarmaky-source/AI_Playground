# AI Playground Tools

Collection of AI agent tools and skills installed at `~/tools/`.

## Installed Tools

| Tool | Location | Type | Status |
|------|----------|------|--------|
| **Auto-Research** (Karpathy) | `~/tools/auto-research` | Python (uv) | Requires NVIDIA GPU + `uv run prepare.py` |
| **OpenSpace** | `~/tools/openspace` | Python MCP | Ready - needs LLM API key in `.env` |
| **CLI-Anything** | `~/tools/cli-anything` | Python Hub | Ready - `cli-hub install <name>` |
| **Claude Peers** | `~/tools/claude-peers` | Bun/TypeScript MCP | Ready - `bun install` done |
| **GWS** (Google Workspace CLI) | `~/tools/gws` | Rust binary | Built - needs `gws auth setup` |
| **Impeccable** | `~/tools/impeccable` | Node.js Skills | Ready - `npm install` done |
| **Awesome Design.md** | `~/tools/awesome-design` | Markdown collection | Ready to use |
| **Playwright Skill** | `~/tools/playwright-cli` | Node.js Plugin | Ready - run `npm run setup` in skill dir |
| **Remotion Kickstart** | `~/tools/remotion` | Node.js (pnpm) | Ready - `pnpm install` done |

## Setup Notes

### Tools requiring API keys / manual config:

- **Auto-Research**: Needs NVIDIA GPU with CUDA. Run `cd ~/tools/auto-research && uv sync && uv run prepare.py`
- **OpenSpace**: Set `OPENSPACE_MODEL` and LLM provider keys in `~/tools/openspace/.env`
- **GWS**: Run `~/tools/gws/target/release/gws auth setup` to configure Google Cloud OAuth
- **Remotion**: Optional AI features need `REPLICATE_API_TOKEN`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`
- **Playwright**: Run `cd ~/tools/playwright-cli/skills/playwright-skill && npm run setup` to install browsers

### Ready to use immediately:

- **CLI-Anything**: `cli-hub install <name>` to install any CLI wrapper
- **Claude Peers**: Register MCP with `claude mcp add --scope user --transport stdio claude-peers -- bun ~/tools/claude-peers/server.ts`
- **Impeccable**: Copy skills to project or use `npx skills add pbakaus/impeccable`
- **Awesome Design.md**: Copy any DESIGN.md from `~/tools/awesome-design/design-md/` into your project

## Source Repos

- Auto-Research: https://github.com/karpathy/autoresearch
- OpenSpace: https://github.com/HKUDS/OpenSpace
- CLI-Anything: https://github.com/HKUDS/CLI-Anything
- Claude Peers: https://github.com/louislva/claude-peers-mcp
- GWS: https://github.com/googleworkspace/cli
- Impeccable: https://github.com/pbakaus/impeccable
- Awesome Design.md: https://github.com/VoltAgent/awesome-design-md
- Playwright Skill: https://github.com/lackeyjb/playwright-skill
- Remotion Kickstart: https://github.com/jhartquist/claude-remotion-kickstart
