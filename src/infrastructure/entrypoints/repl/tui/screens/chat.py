"""Main chat screen for Local-RAG TUI."""


import re
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen

from ...session import get_session_manager
from ..modals import HelpModal, ProviderPalette
from ..widgets import (
    ChangesPanel,
    FooterWidget,
    HeaderWidget,
    InputArea,
    LoadingIndicator,
    MessageList,
)


class ChatScreen(Screen):
    """Main chat screen with header, messages, input, and footer."""

    BINDINGS = [
        Binding("ctrl+c", "cancel_or_quit", "Cancel", show=False),
        Binding("ctrl+l", "clear_chat", "Clear", show=False),
        Binding("ctrl+shift+c", "toggle_changes", "Changes", show=False),
        Binding("ctrl+p", "show_provider_palette", "Provider", show=False),
        Binding("escape", "escape_action", "Interrupt/Escape", show=False),
        Binding("h", "show_help", "Help", show=False),
        Binding("question_mark", "show_help", "Help", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_streaming = False
        self._command_history: list[str] = []
        self._history_index = -1
        self._changes_panel: ChangesPanel | None = None
        self._changes_visible = True

    @property
    def _session(self):
        return get_session_manager()

    @property
    def _app(self):
        return self.app

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield HeaderWidget()
        with Horizontal(id="main-container"):
            yield MessageList(id="message-list")
            yield ChangesPanel(id="changes-panel")
        yield LoadingIndicator(id="loading-indicator")
        yield InputArea(id="input-area")
        yield FooterWidget(id="footer")

    def on_mount(self) -> None:
        """Initialize screen."""
        from ..session_log import log_event, setup_logging
        setup_logging()
        log_event("app_started", screen="ChatScreen")
        state = self._session.get_state()
        header = self.query_one(HeaderWidget)
        header.update_status(
            mode=state.mode,
            provider=state.provider,
            model=state.model,
            rag_enabled=state.rag_enabled,
            docs_count=state.docs_count,
            local_model=state.local_model,
            work_mode=state.work_mode,
            input_tokens=state.input_tokens,
            output_tokens=state.output_tokens,
        )

        self._changes_panel = self.query_one(ChangesPanel)

        input_area = self.query_one(InputArea)
        input_area.focus()

        self._load_session_messages()
        self._show_startup_info()

    def _show_startup_info(self) -> None:
        """Show startup info immediately - LM Studio check happens in background."""
        msg_list = self.query_one(MessageList)

        import os
        from pathlib import Path

        from dotenv import load_dotenv

        env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        lines = ["[bold cyan]LOCAL-RAG TUI[/bold cyan] - Bienvenido!", ""]

        lines.append("[dim]⏳ Cargando modelo de embeddings en background...[/dim]")
        lines.append("    [dim](puedes escribir mientras carga)[/dim]")
        lines.append("")

        minimax_key = os.getenv("MINIMAX_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if minimax_key or groq_key or openai_key:
            providers_with_key = []
            if minimax_key:
                providers_with_key.append("minimax")
            if groq_key:
                providers_with_key.append("groq")
            if openai_key:
                providers_with_key.append("openai")
            lines.append(f"[green]API Keys:[/green] {', '.join(providers_with_key)}")
        else:
            lines.append("[yellow]API Keys:[/yellow] No configuradas")
            lines.append("  Edita .env o usa Ctrl+P → API Key")

        lines.append("")
        lines.append("[bold cyan]Atajos:[/bold cyan]")
        lines.append("  Ctrl+P     - Menu de comandos")
        lines.append("  Ctrl+L     - Limpiar chat")
        lines.append("  Ctrl+Q     - Salir")
        lines.append("  ESC        - 1ra: interrumpir / 2da: salir")
        lines.append("  ↑↓         - Historial de mensajes")

        msg_list.add_system_message("\n".join(lines))

        self.run_worker(self._check_lm_studio_background, exclusive=True, thread=True)
        msg_list.add_system_message("\n".join(lines))

        self.run_worker(self._check_lm_studio_background, exclusive=True, thread=True)

    def _check_lm_studio_background(self) -> None:
        """Check LM Studio availability in background thread."""
        import os
        from pathlib import Path

        from dotenv import load_dotenv

        env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        lm_studio_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
        try:
            import httpx
            response = httpx.get(f"{lm_studio_url}/v1/models", timeout=2)
            available = response.status_code == 200
        except Exception:
            available = False

        def update_ui():
            try:
                msg_list = self.query_one(MessageList)
                if available:
                    msg_list.add_system_message(f"[green]✓ LM Studio: Detectado en {lm_studio_url}[/green]")
                else:
                    msg_list.add_system_message(
                        f"[dim]LM Studio: no detectado en {lm_studio_url}\n"
                        f"  (usa Ctrl+P → Toggle Mode para activar local)[/dim]"
                    )
            except Exception:
                pass

        self.app.call_from_thread(update_ui)

    def _setup_logging(self) -> None:
        """Deprecated - use session_log module instead."""
        from ..session_log import setup_logging
        setup_logging()

    def _load_session_messages(self) -> None:
        """Load messages from session."""
        msg_list = self.query_one(MessageList)
        changes_panel = self.query_one(ChangesPanel)
        messages = self._session.get_messages()

        last_changes = None
        for msg in messages:
            if msg.role == "user":
                msg_list.add_user_message(msg.content, msg.timestamp)
            elif msg.role == "assistant":
                msg_list.add_assistant_message(
                    msg.content,
                    sources=msg.sources,
                    timestamp=msg.timestamp,
                )
                if msg.changes:
                    last_changes = msg.changes
            elif msg.role == "system":
                msg_list.add_system_message(msg.content, msg.timestamp)

        if last_changes:
            changes_panel.set_changes(last_changes)

    def on_key(self, event) -> None:
        """Global key handler to auto-focus input when typing."""
        input_area = self.query_one(InputArea)

        if self.focused is input_area:
            return

        char = None
        if event.character is not None:
            char = event.character
        elif event.key == "space":
            char = " "

        if char:
            input_area.focus()
            input_area.insert(char)

    def on_input_submitted(self, event) -> None:
        """Handle input submission - all messages go to the LLM."""
        if self._is_streaming:
            return

        text = event.text.strip()
        if not text:
            return

        input_area = self.query_one(InputArea)
        input_area.clear()

        self._command_history.append(text)
        self._history_index = len(self._command_history)

        from ..macros import get_macro_manager
        macros = get_macro_manager()

        if text.startswith("/") and text in macros.list_all():
            expanded = macros.get(text)
            if expanded:
                self.run_worker(self._handle_query(expanded), exclusive=True)
                return

        self.run_worker(self._handle_query(text), exclusive=True)

    async def _handle_query(self, query: str) -> None:
        """Handle a user query."""
        from ..session_log import log_error, log_event, log_user_message

        msg_list = self.query_one(MessageList)
        try:
            loading = self.query_one("#loading-indicator")
        except Exception:
            loading = None
        header = self.query_one(HeaderWidget)

        msg_list.add_user_message(query)
        if loading:
            loading.show()
        self._is_streaming = True

        state = self._session.get_state()
        log_user_message("user", query, mode=state.mode, provider=state.provider, model=state.model)

        input_tokens = len(query) // 4
        new_input_total = state.input_tokens + input_tokens
        self._session.update_state(input_tokens=new_input_total)

        self._session.add_message(role="user", content=query)

        try:
            response = await self._app.ask_streaming(query)
            loading.hide()

            output_tokens = len(response["content"]) // 4
            new_output_total = state.output_tokens + output_tokens
            self._session.update_state(output_tokens=new_output_total)
            header.update_status(input_tokens=new_input_total, output_tokens=new_output_total)

            content = response["content"]
            changes = self._parse_changes(content)

            log_user_message("assistant", content, sources=len(response.get("sources") or []))
            log_event("query_completed", tokens_in=input_tokens, tokens_out=output_tokens)

            msg_list.add_assistant_message(content, sources=response.get("sources"))
            self._session.add_message(
                role="assistant",
                content=content,
                sources=response.get("sources"),
                changes=changes,
            )

            if changes:
                self._changes_panel.set_changes(changes)
        except Exception as e:
            loading.hide()
            log_error(str(e), query_preview=query[:50])
            msg_list.add_system_message(f"Error: {str(e)}")
        finally:
            self._is_streaming = False

    def _parse_changes(self, content: str) -> list:
        """Parse code changes from message content."""
        from ....session.models import CodeChange

        changes = []
        current_file = None
        current_change = None
        in_code_block = False

        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            if line.strip().startswith("📄 "):
                if current_change and current_file:
                    changes.append(current_change)
                current_file = line.strip()[2:].strip()
                current_change = CodeChange(file_path=current_file)
                continue

            if current_change:
                stripped = line.strip()
                if stripped.startswith("+ ") and not stripped.startswith("+++"):
                    current_change.new_lines.append(stripped[2:])
                elif stripped.startswith("- "):
                    current_change.removed_lines.append(stripped[2:])

        if current_change and current_file:
            changes.append(current_change)

        git_diff_pattern = r"diff --git a/(.*?) b/(.*)"
        hunk_pattern = r"@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@"
        plus_pattern = r"\+([^\n+][^\n]*)"
        minus_pattern = r"-([^\n-][^\n]*)"

        in_diff = False
        current_file = None
        current_change = None

        for line in content.split("\n"):
            diff_match = re.match(git_diff_pattern, line)
            if diff_match:
                if current_change and current_file:
                    changes.append(current_change)
                current_file = diff_match.group(1)
                current_change = CodeChange(file_path=current_file)
                in_diff = True
                continue

            if in_diff:
                if re.match(hunk_pattern, line):
                    continue
                plus_match = re.match(plus_pattern, line)
                if plus_match:
                    current_change.new_lines.append(plus_match.group(1))
                    continue
                minus_match = re.match(minus_pattern, line)
                if minus_match:
                    current_change.removed_lines.append(minus_match.group(1))
                    continue
                if line.startswith("@@") or line.startswith("---") or line.startswith("+++"):
                    in_diff = False

        if current_change and current_file:
            changes.append(current_change)

        return changes

    def _handle_command(self, text: str) -> None:
        """Handle a slash command."""
        from ..session_log import log_command

        parts = text[1:].split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]
        log_command(text, args_count=len(args))

        msg_list = self.query_one(MessageList)
        header = self.query_one(HeaderWidget)
        state = self._session.get_state()

        if cmd in ("help", "?"):
            self.app.push_screen(HelpModal(self.app))
            return

        elif cmd in ("exit", "quit", "q"):
            self.app.exit()

        elif cmd == "clear":
            msg_list.clear_messages()
            self._session.clear_messages()
            return

        elif cmd in ("mode", "m"):
            if not args:
                msg_list.add_system_message(f"Current mode: {state.mode}")
                return
            new_mode = args[0].lower()
            if new_mode not in ("local", "cloud"):
                msg_list.add_system_message("Invalid mode. Use: /mode <local|cloud>")
                return
            self._session.update_state(mode=new_mode)
            header.update_status(mode=new_mode)
            self._app.set_mode(new_mode)
            return

        elif cmd == "provider":
            if not args:
                msg_list.add_system_message(f"Current provider: {state.provider}")
                return
            new_provider = args[0].lower()
            self._session.update_state(provider=new_provider)
            header.update_status(provider=new_provider)
            self._app.set_provider(new_provider)
            return

        elif cmd == "rag":
            if not args:
                status = "on" if state.rag_enabled else "off"
                msg_list.add_system_message(f"RAG is {status}, top_k={state.rag_top_k}")
                return
            if args[0].lower() == "on":
                self._session.update_state(rag_enabled=True)
                header.update_status(rag_enabled=True)
            elif args[0].lower() == "off":
                self._session.update_state(rag_enabled=False)
                header.update_status(rag_enabled=False)
            elif args[0].lower() == "topk" and len(args) > 1:
                try:
                    k = int(args[1])
                    if 1 <= k <= 20:
                        self._session.update_state(rag_top_k=k)
                        header.update_status(rag_enabled=state.rag_enabled)
                    else:
                        msg_list.add_system_message("top_k must be between 1 and 20")
                except ValueError:
                    msg_list.add_system_message("Invalid top_k value")
            return

        elif cmd == "stats":
            count = self._session.get_state().docs_count
            msg_list.add_system_message(f"Indexed documents: {count:,}")
            return

        elif cmd == "providers":
            providers = "Available providers: minimax, groq, openai, google, deepseek, anthropic"
            msg_list.add_system_message(providers)
            return

        elif cmd == "apikey":
            if not args:
                current_key = self._app.get_current_api_key()
                if current_key:
                    masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
                    msg_list.add_system_message(f"Current API key: {masked}")
                else:
                    msg_list.add_system_message("No API key set. Usage: /apikey <your_api_key>")
                return
            api_key = args[0]
            provider = state.provider if state else "minimax"
            if self._app.set_session_api_key(provider, api_key):
                msg_list.add_system_message(f"API key guardada para {provider}")
            else:
                msg_list.add_system_message("Error guardando API key")
            return

        elif cmd == "models":
            msg_list.add_system_message(f"Models for {state.provider}: (use /provider <name> first)")
            return

        elif cmd == "theme":
            if not args:
                msg_list.add_system_message(f"Current theme: {state.theme}")
                return
            new_theme = args[0].lower()
            if new_theme in ("dark", "light", "minimal"):
                self._session.update_state(theme=new_theme)
                self.app.theme = new_theme
            else:
                msg_list.add_system_message("Invalid theme. Use: /theme <dark|light|minimal>")
            return

        elif cmd == "index":
            if not args:
                msg_list.add_system_message("Usage: /index <file_path> or /index --reindex")
                return

            doc_store = self._app.get_doc_store()
            loader = self._app.get_loader_adapter()
            if not doc_store or not loader:
                msg_list.add_system_message("Document store not initialized. Please restart the app.")
                return

            if args[0] == "--reindex":
                msg_list.add_system_message("Reindexing all documents not implemented yet.")
                return

            file_path = args[0]
            file_path_expanded = str(Path(file_path).expanduser().resolve())

            if not Path(file_path_expanded).exists():
                msg_list.add_system_message(f"File not found: {file_path}")
                return

            try:
                msg_list.add_system_message(f"Indexing {file_path}...")
                chunks = loader.load_and_split(file_path_expanded)
                doc_store.add_documents(chunks)
                self._app.update_docs_count(doc_store.count())
                header.update_status(docs_count=doc_store.count())
                msg_list.add_system_message(f"Successfully indexed {len(chunks)} chunks from {file_path}")
            except Exception as e:
                msg_list.add_system_message(f"Error indexing file: {e}")
            return

        elif cmd in ("plan", "build"):
            new_mode = cmd
            self._session.update_state(work_mode=new_mode)
            header.update_status(work_mode=new_mode)
            msg_list.add_system_message(f"[dim]Switched to {new_mode.upper()} mode[/dim]")
            return

        elif cmd == "tokens":
            state = self._session.get_state()
            msg_list.add_system_message(f"Tokens - Input: {state.input_tokens:,} | Output: {state.output_tokens:,}")
            return

        elif cmd == "macro":
            from ..macros import get_macro_manager
            manager = get_macro_manager()

            if not args:
                macros = manager.list_all()
                lines = ["[bold cyan]Macros disponibles:[/bold cyan]"]
                for name, value in macros.items():
                    preview = value[:50] + "..." if len(value) > 50 else value
                    lines.append(f"  [bold]{name}[/bold] → {preview}")
                lines.append("\n[dim]Uso: /macro add <name> <text> | /macro remove <name> | /macro reset[/dim]")
                msg_list.add_system_message("\n".join(lines))
                return

            subcmd = args[0].lower()
            if subcmd == "list":
                macros = manager.list_all()
                msg_list.add_system_message(f"Total: {len(macros)} macros. Usa /macro para ver lista.")
                return
            elif subcmd == "add" and len(args) >= 3:
                name = args[1]
                text = " ".join(args[2:])
                manager.set(name, text)
                msg_list.add_system_message(f"[green]Macro guardado: [bold]{name}[/bold][/green]")
                return
            elif subcmd == "remove" and len(args) >= 2:
                if manager.delete(args[1]):
                    msg_list.add_system_message(f"[green]Macro [bold]{args[1]}[/bold] eliminado[/green]")
                else:
                    msg_list.add_system_message(f"[yellow]Macro [bold]{args[1]}[/bold] no existe[/yellow]")
                return
            elif subcmd == "reset":
                manager.reset_defaults()
                msg_list.add_system_message("[green]Macros restaurados a defaults[/green]")
                return
            else:
                msg_list.add_system_message("Uso: /macro [list|add <name> <text>|remove <name>|reset]")
                return

        else:
            msg_list.add_system_message(f"Unknown command: /{cmd}. Type /help for commands.")

    def action_show_help(self) -> None:
        """Show help modal."""
        self.app.push_screen(HelpModal(self.app))

    def action_show_provider_palette(self) -> None:
        """Show provider selection palette."""
        self.app.push_screen(ProviderPalette(self.app))

    def action_escape_action(self) -> None:
        """Handle escape key.

        1st press: interrupt streaming + show warning
        2nd press: exit application
        """
        import time

        now = time.time()

        if self._is_streaming:
            self._is_streaming = False
            msg_list = self.query_one(MessageList)
            try:
                loading = self.query_one("#loading-indicator")
                loading.hide()
            except Exception:
                pass
            msg_list.add_system_message("[yellow]⚠ Generacion interrumpida. Presiona ESC de nuevo para salir.[/yellow]")
            self._esc_pressed_at = now
            return

        if hasattr(self, "_esc_pressed_at") and (now - self._esc_pressed_at) < 2.0:
            self.app.exit()
            return

        self._esc_pressed_at = now
        msg_list = self.query_one(MessageList)
        msg_list.add_system_message("[dim]Presiona ESC de nuevo para salir. (o /help para ver comandos)[/dim]")

    def action_clear_chat(self) -> None:
        """Clear chat history."""
        msg_list = self.query_one(MessageList)
        msg_list.clear_messages()
        self._session.clear_messages()

    def action_cancel_or_quit(self) -> None:
        """Cancel current operation or quit."""
        if self._is_streaming:
            self._is_streaming = False
            msg_list = self.query_one(MessageList)
            try:
                loading = self.query_one("#loading-indicator")
                loading.hide()
            except Exception:
                pass
            msg_list.add_system_message("Generation cancelled.")
        else:
            self.app.exit()

    def action_toggle_changes(self) -> None:
        """Toggle changes panel visibility."""
        if self._changes_panel is None:
            return

        self._changes_visible = not self._changes_visible
        self._changes_panel.display = self._changes_visible

        msg_list = self.query_one(MessageList)
        if self._changes_visible:
            msg_list.add_system_message("[dim]Changes panel visible (Ctrl+Shift+C to hide)[/dim]")
        else:
            msg_list.add_system_message("[dim]Changes panel hidden (Ctrl+Shift+C to show)[/dim]")
