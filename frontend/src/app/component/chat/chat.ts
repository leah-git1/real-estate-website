import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ChatService } from '../../services/chat_service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [FormsModule, DatePipe],
  templateUrl: './chat.html',
  styleUrls: ['./chat.scss']
})
export class ChatComponent {
  messages: {role: string; content: string; timestamp: Date}[] = [];
  input = '';
  loading = false;
  isOpen = false;
  error = '';

  constructor(private chatService: ChatService, private router: Router, private sanitizer: DomSanitizer) {}

  send() {
    if (!this.input.trim() || this.loading) return;
    const msg = this.input;
    this.input = '';
    this.loading = true;
    this.error = '';
    this.messages.push({ role: 'user', content: msg, timestamp: new Date() });

    this.chatService.send(msg, this.messages.slice(0, -1)).subscribe({
      next: (res: {reply: string}) => {
        this.messages.push({ role: 'assistant', content: res.reply, timestamp: new Date() });
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.message || err?.message || `Error ${err?.status}: ${err?.statusText}`;
      }
    });
  }

  onKey(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.send(); }
  }

  renderMarkdown(text: string): SafeHtml {
    const html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
        try {
          const path = new URL(url).pathname;
          return `<a class="chat-link" data-path="${path}">${label}</a>`;
        } catch {
          return `<a class="chat-link" data-path="${url}">${label}</a>`;
        }
      })
      .replace(/\n/g, '<br>');
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  handleClick(e: MouseEvent) {
    const target = (e.target as HTMLElement).closest('.chat-link') as HTMLElement;
    if (target) {
      e.preventDefault();
      const path = target.getAttribute('data-path') || '';
      this.router.navigateByUrl(path);
      this.isOpen = false;
    }
  }
}
