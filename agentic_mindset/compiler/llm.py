"""LLM client for the compiler. Supports Anthropic, MiniMax, and OpenAI-compatible APIs."""
from __future__ import annotations
import json
import os
from typing import Optional
import anthropic


def _looks_like_refusal(text: str) -> bool:
    """Check if response looks like a refusal or error rather than actual content."""
    if not text:
        return True
    text_lower = text.lower().strip()
    # Common refusal patterns
    refusal_phrases = [
        "i don't see",
        "i cannot",
        "i'm unable",
        "i'm not able",
        "please provide",
        "no extracted behaviors",
        "don't see any",
        "hasn't provided",
        "appears to be empty",
        "haven't included",
        "appears empty",
        "i can't help",
        "i'm not sure i can",
        "without more information",
        "could you provide",
        "unable to fulfill",
        "does not contain",
    ]
    # If response starts with an apology or request for more info, likely refusal
    if text_lower.startswith(("i'm sorry", "sorry,", "i apologize")):
        return True
    # Check for refusal phrases in first 200 chars
    preview = text_lower[:200]
    for phrase in refusal_phrases:
        if phrase in preview:
            return True
    return False


class LLMClient:
    """LLM client that calls the configured API.

    Priority:
    1. ANTHROPIC_API_KEY (standard Anthropic)
    2. CMINI_WRAPPER_API_KEY / ANTHROPIC_AUTH_TOKEN (MiniMax Anthropic-compatible)
    3. OPENAI_API_KEY (OpenAI compatible)
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature

        # Check available API keys
        self._api_key = (
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("CMINI_WRAPPER_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or os.environ.get("OPENAI_API_KEY")
        )
        self._provider: str = "anthropic"
        if not self._api_key:
            raise RuntimeError(
                "Set ANTHROPIC_API_KEY, CMINI_WRAPPER_API_KEY, or OPENAI_API_KEY "
                "in your environment to use the compiler."
            )
        if os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
            self._provider = "openai"
        elif os.environ.get("ANTHROPIC_BASE_URL"):
            self._provider = "minimax"

    def complete(self, prompt: str, system: Optional[str] = None, max_tokens: int = 4096) -> str:
        """Make a single LLM completion call with retry on refusal or error."""
        import urllib.request
        if self._provider == "minimax" and max_tokens < 1024:
            max_tokens = 1024
        last_error = None
        result = None
        for attempt in range(3):
            try:
                if self._provider == "anthropic":
                    result = self._anthropic_complete(prompt, system, max_tokens)
                elif self._provider == "minimax":
                    result = self._minimax_complete(prompt, system, max_tokens)
                else:
                    result = self._openai_complete(prompt, system, max_tokens)
                if result and not _looks_like_refusal(result):
                    return result
            except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
                last_error = e
                result = None
        if result is not None:
            return result
        raise RuntimeError(f"All LLM attempts failed: {last_error}") from last_error

    def _anthropic_complete(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        client = anthropic.Anthropic(api_key=self._api_key)
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text

    def _minimax_complete(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        """MiniMax Anthropic-compatible endpoint."""
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimax.io/anthropic")
        import urllib.request

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }).encode()
        url = f"{base_url}/v1/messages"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        # MiniMax returns content blocks; find the first text block
        for item in data.get("content", []):
            if item.get("type") == "text":
                return item["text"]
        raise RuntimeError(f"MiniMax response had no text block: {data.get('content')}")

    def _openai_complete(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        import urllib.request

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }).encode()
        url = f"{api_base}/chat/completions"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

    def complete_structured(self, prompt: str, system: Optional[str] = None) -> dict:
        """Parse structured data from LLM response.

        Handles JSON, YAML, and markdown formats. MiniMax models output inconsistent
        formats despite explicit instructions. Uses the LAST matching code block
        to handle thinking model outputs that wrap code blocks in thinking content.

        Priority:
        1. JSON/YAML in code blocks (```json or ```yaml)
        2. Plain JSON (try before YAML to avoid JSON-as-YAML flattening)
        3. Plain YAML
        4. Markdown bold-format parsing
        """
        import yaml, re, json
        raw = self.complete(prompt, system=system)
        raw = raw.strip()

        # Try JSON code blocks first
        json_matches = list(re.finditer(r'```json\n(.*?)```', raw, re.DOTALL))
        if json_matches:
            json_content = json_matches[-1].group(1).strip()
            return json.loads(json_content)

        # Try YAML code blocks
        yaml_matches = list(re.finditer(r'```yaml\n(.*?)```', raw, re.DOTALL))
        if yaml_matches:
            yaml_content = yaml_matches[-1].group(1).strip()
            return yaml.safe_load(yaml_content)

        # Try plain JSON (before YAML) to avoid JSON-string-as-YAML flattening
        # JSON strings start with '{' or '['
        if raw.startswith(('{', '[')):
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: try plain YAML
        try:
            parsed = yaml.safe_load(raw)
        except yaml.YAMLError:
            parsed = None

        # Guard: YAML can return bare strings (e.g. "no behaviors found");
        # callers expect dict, so raise instead of returning non-dict
        if isinstance(parsed, dict):
            return parsed

        # Last resort: parse markdown bold-format (e.g., "**Key:** value")
        result = self._parse_markdown_structured(raw)
        if isinstance(result, dict):
            return result

        raise RuntimeError(
            f"Could not parse LLM response as JSON, YAML, or markdown. "
            f"Response preview: {raw[:200]}"
        )

    def _parse_markdown_structured(self, raw: str) -> Optional[dict]:
        """Parse markdown bold-format into a dict or list.

        Handles:
        - **N.** → numbered list item (new behavior entry)
        - ### Section headers → section markers
        - **Key:** value → key-value pairs
        - - **Key:** value → indented key-value within current numbered item
        - | col | col | → table rows
        """
        import re

        if '**' not in raw:
            return None

        lines = raw.split('\n')
        parsed = {}
        current_section = None
        sections = {}
        current_item_index = None
        items_list = []
        # Table parsing state
        table_col_map: dict[str, int] = {}  # header name → column index

        def _store_item(idx, data):
            key = str(idx).replace('-', '_')
            sections[key] = data

        for line in lines:
            stripped = line.strip()

            # Plain numbered item: 1. or 2. etc. (no bold)
            plain_num_match = re.match(r'^(\d+)\.\s', stripped)
            if plain_num_match:
                current_item_index = int(plain_num_match.group(1))
                current_section = f"item_{current_item_index}"
                sections[current_section] = {}
                continue

            # Bold numbered item marker: **1.**, **2.** etc.
            num_match = re.match(r'^\*\*(\d+)\.\*\*\s*$', stripped)
            if num_match:
                current_item_index = int(num_match.group(1))
                current_section = f"item_{current_item_index}"
                sections[current_section] = {}
                continue

            # Behavior header: **Behavior 1:** or **Behavior 1: text**
            bh_match = re.match(r'^\*\*Behavior\s+(\d+):?\s*(.*)\*\*$', stripped)
            if bh_match:
                current_item_index = int(bh_match.group(1))
                current_section = f"item_{current_item_index}"
                sections[current_section] = {}
                # If there's text after the colon, it's the canonical form
                if bh_match.group(2).strip():
                    sections[current_section]['canonical_form'] = bh_match.group(2).strip()
                continue

            # Behavior key within item: **Behavior:** value
            bh_key_match = re.match(r'^\*\*Behavior:\*\*\s*(.*)', stripped)
            if bh_key_match and current_section:
                sections[current_section]['behavior'] = bh_key_match.group(1).strip()
                continue

            # Section header: ### section-id
            header_match = re.match(r'^###\s+(\S+)\s*$', stripped)
            if header_match:
                current_section = header_match.group(1)
                # Skip parenthetical headers like "### (High Confidence - ...)"
                if current_section.startswith('('):
                    current_section = None
                    continue
                current_item_index = None
                if current_section not in sections:
                    sections[current_section] = {}
                continue

            # Section header ## Source N: title — used in some LLM output formats
            source_match = re.match(r'^##\s+Source\s+(\d+):', stripped)
            if source_match:
                # Extract source identifier for provenance tracking
                src_num = int(source_match.group(1))
                src_title_match = re.match(r'^##\s+Source\s+\d+:\s*(.*)', stripped)
                src_title = src_title_match.group(1).strip() if src_title_match else f"Source {src_num}"
                current_item_index = src_num
                current_section = f"item_{current_item_index}"
                if current_section not in sections:
                    sections[current_section] = {}
                sections[current_section]['source_ref'] = src_title
                continue

            # Section header ## Behavioral Pattern N: or ## Pattern N:
            bp_match = re.match(r'^##\s+[Bb]ehavioral?\s+[Pp]attern\s+(\d+):', stripped)
            if bp_match:
                current_item_index = int(bp_match.group(1))
                current_section = f"item_{current_item_index}"
                if current_section not in sections:
                    sections[current_section] = {}
                continue

            # Section header ## N. ... (numbered section without bold)
            bp_plain = re.match(r'^##\s+(\d+)\.\s+(.*)', stripped)
            if bp_plain:
                current_item_index = int(bp_plain.group(1))
                current_section = f"item_{current_item_index}"
                if current_section not in sections:
                    sections[current_section] = {}
                # If there's text after the period, it might be a canonical form
                extra = bp_plain.group(2).strip()
                if extra:
                    sections[current_section]['canonical_form'] = extra
                continue

            # Section header with word+number: ### Source 1: title → treat as item_1
            header_source_match = re.match(r'^###\s+([A-Za-z]+)\s+(\d+):', stripped)
            if header_source_match:
                current_item_index = int(header_source_match.group(2))
                current_section = f"item_{current_item_index}"
                if current_section not in sections:
                    sections[current_section] = {}
                continue

            # Section header with word+number: ### Behavior 1 → treat as item_1
            header_word_match = re.match(r'^###\s+([A-Za-z]+)\s+(\d+)\s*$', stripped)
            if header_word_match:
                current_item_index = int(header_word_match.group(2))
                current_section = f"item_{current_item_index}"
                if current_section not in sections:
                    sections[current_section] = {}
                continue

            # Key-value: **Key:** value OR **Key**: value (bold) OR - Key: value (plain list item)
            line_for_match = stripped.lstrip('- ')
            # Handle pipe-separated key-value pairs: **Key:** value | **Key2:** value2
            # First, try to split by pipe and handle each pair
            if '|' in line_for_match and '**' in line_for_match:
                # Split by '|' and process each segment
                pipe_parts = line_for_match.split('|')
                for part in pipe_parts:
                    part = part.strip()
                    if not part or not part.startswith('**'):
                        continue
                    # Try **Key:** value format (colon inside bold)
                    kv = re.match(r'^\*\*([^*]+)\*\*:\s*(.*)', part)
                    if kv:
                        key = kv.group(1).strip().lower().replace(' ', '_')
                        value = kv.group(2).strip().strip('"\'')
                        if current_section and current_section in sections:
                            sections[current_section][key] = value
                        else:
                            parsed[key] = value
                    # Try **Key**: value format (colon after bold)
                    kv2 = re.match(r'^\*\*([^*]+):\*\*(.*)', part)
                    if kv2:
                        key = kv2.group(1).strip().lower().replace(' ', '_')
                        value = kv2.group(2).strip().strip('"\'')
                        if current_section and current_section in sections:
                            sections[current_section][key] = value
                        else:
                            parsed[key] = value
                continue
            # Try bold format with colon inside bold: **Key:** value
            kv_match = re.match(r'^\*\*([^*]+)\*\*:\s*(.*)', line_for_match)
            if kv_match:
                key = kv_match.group(1).strip().lower().replace(' ', '_')
                value = kv_match.group(2).strip().strip('"\'')
                if current_section and current_section in sections:
                    sections[current_section][key] = value
                else:
                    parsed[key] = value
                continue
            # Try bold format with colon outside bold: **Key:** value
            kv_match = re.match(r'^\*\*([^*]+):\*\*(.*)', line_for_match)
            if kv_match:
                key = kv_match.group(1).strip().lower().replace(' ', '_')
                value = kv_match.group(2).strip().strip('"\'')
                if current_section and current_section in sections:
                    sections[current_section][key] = value
                else:
                    parsed[key] = value
                continue
            # Try plain format: Key: value (after removing leading dash/space)
            plain_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_\s]*):\s*(.*)', line_for_match)
            if plain_match and ':' in stripped:
                key = plain_match.group(1).strip().lower().replace(' ', '_')
                value = plain_match.group(2).strip().strip('"\'')
                if current_section and current_section in sections:
                    sections[current_section][key] = value
                else:
                    parsed[key] = value
                continue

            # Bold list item: - **Source N:** "quote text" or - **Source:** text
            # After lstrip('- '), becomes **Source N:** "..." or **Source:** ...
            bold_list_match = re.match(r'^\*\*([^*]+)\*\*:\s*(.*)', line_for_match)
            if bold_list_match:
                key = bold_list_match.group(1).strip().lower().replace(' ', '_')
                value = bold_list_match.group(2).strip().strip('"\'')
                if current_section and current_section in sections:
                    sections[current_section][key] = value
                else:
                    parsed[key] = value
                continue

            # Table row: | col | col |
            if stripped.startswith('|') and stripped.endswith('|'):
                cells = [c.strip() for c in stripped.split('|')[1:-1]]
                if len(cells) < 2:
                    continue
                # Skip markdown table separator lines (e.g., |---|---|---|)
                if all(re.match(r'^[-:]+$', c) for c in cells):
                    continue
                # Header row: identify column mapping
                # Known header column names
                known_headers = {'quote', 'behavior', 'contrast', 'confidence', 'trigger',
                                'source_ref', 'page_or_section', 'aspect', 'assessment',
                                'field', 'key', 'id'}
                if cells[0].lower().rstrip(':') in known_headers and cells[0].lower() not in ('aspect', 'behavior', 'field', 'key'):
                    # This is a header row - identify column indices
                    table_col_map = {}
                    for idx, header in enumerate(cells):
                        h = header.lower().rstrip(':').replace(' ', '_')
                        if h in known_headers:
                            table_col_map[h] = idx
                    continue
                # Data row: extract fields and create new item
                if cells and table_col_map:
                    row_data = {}
                    for field_name, col_idx in table_col_map.items():
                        if col_idx < len(cells):
                            val = cells[col_idx].strip().strip('"\'')
                            if val.lower() not in ('null', 'none', ''):
                                row_data[field_name] = val
                    # If this looks like a valid behavior row (has quote or behavior), create item
                    if row_data and ('quote' in row_data or 'behavior' in row_data):
                        current_item_index = (current_item_index or 0) + 1
                        current_section = f"item_{current_item_index}"
                        sections[current_section] = row_data
                    continue
                # Fallback for non-bold-format tables or tables without known headers:
                # treat first cell as key, second as value
                first_cell = cells[0] if cells else ''
                second_cell = cells[1] if len(cells) > 1 else ''
                # Extract bold key: **Canonical form** → canonical_form
                key_match = re.match(r'^\*\*([^*]+)\*\*$', first_cell)
                if key_match:
                    key = key_match.group(1).strip().lower().replace(' ', '_')
                    value = second_cell.strip().strip('"\'')
                    if current_section and current_section in sections:
                        sections[current_section][key] = value
                    else:
                        parsed[key] = value
                    continue
                # Non-bold first cell: create new item entry for this row
                if first_cell and first_cell not in ('---',):
                    current_item_index = (current_item_index or 0) + 1
                    current_section = f"item_{current_item_index}"
                    # Pair up cells: (col0→col1), (col2→col3), ...
                    row_dict = {}
                    for i in range(0, len(cells) - 1, 2):
                        k = cells[i].lower().replace(' ', '_')
                        v = cells[i + 1].strip().strip('"\'') if i + 1 < len(cells) else ''
                        row_dict[k] = v
                    sections[current_section] = row_dict
                continue

            # Separator lines
            if stripped.startswith('---') or stripped.startswith('***') or not stripped:
                continue

        # Build final result
        if sections:
            # Normalize section names
            result = {}
            for section_id, content in sections.items():
                key = section_id.lower().replace('-', '_').replace(' ', '_')
                result[key] = content

            # Check for numbered items (item_1, item_2, ...) → collect as list
            item_keys = sorted([k for k in result if k.startswith('item_')],
                              key=lambda x: int(x.split('_')[1]))
            if item_keys:
                items = [result[k] for k in item_keys]
                first_item = items[0] if items else {}
                if 'behavior' in first_item or 'canonical_form' in first_item:
                    return {'extracted_behaviors': items}
                return {'items': items}

            # Post-process: detect orphaned keys that should be grouped
            # Keys that belong to canonical behaviors: canonical_form, variants, status, etc.
            cb_orphaned = ['canonical_form', 'variants', 'status', 'conditional_candidate',
                           'conditional_note', 'evidence_count', 'conditional_markers',
                           'contrast_signal', 'confidence']
            orphaned_found = [k for k in cb_orphaned if k in result]
            if orphaned_found and len(result) > len(orphaned_found):
                # Build canonical_behaviors from orphaned + remaining sections
                # Find section IDs (keys that look like b-001, b-002, cb-001, etc.)
                section_keys = [k for k in result if k != 'rationale' and k != 'potential_connection_note'
                               and not any(o in k for o in orphaned_found)]
                if section_keys:
                    canonicals = []
                    for sk in section_keys:
                        entry = dict(result[sk])  # copy
                        # Add orphaned keys that match this section
                        for ok in orphaned_found:
                            if ok in result and ok not in entry:
                                entry[ok] = result[ok]
                        canonicals.append(entry)
                    if canonicals:
                        return {'canonical_behaviors': canonicals}

            # If there's only one section with items, return items list
            if len(result) == 1:
                single = list(result.values())[0]
                if isinstance(single, dict) and 'items' in single:
                    return {'items': single['items']}
            # If there's "canonical_behaviors" or "behaviors" key, return it directly
            for key in ['canonical_behaviors', 'behaviors', 'items', 'extracted_behaviors']:
                if key in result:
                    return {key: result[key]}
            return result

        # Single-level key-value pairs
        if parsed:
            return parsed

        return None

