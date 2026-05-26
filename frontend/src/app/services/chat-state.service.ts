import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ChatStateService {
  isOpen   = signal(false);
  prefill  = signal('');

  open(message = '') {
    this.prefill.set(message);
    this.isOpen.set(true);
  }
}
