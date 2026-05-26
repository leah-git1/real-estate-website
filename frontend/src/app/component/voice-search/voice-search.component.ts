import { Component, OnDestroy, Output, Input, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { VoiceSearchService, VoiceSearchResponse } from '../../services/voice-search.service';

@Component({
  selector: 'app-voice-search',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="voice-search">
      <button (click)="toggle()" [class.active]="listening"
              [title]="listening ? 'לחץ לעצור ולשלוח' : 'לחץ לדבר'">
        {{ listening ? '🔴' : '🎤' }}
      </button>
      <span *ngIf="error" class="error">{{ error }}</span>
    </div>
  `,
  styles: [`
    .voice-search { display: inline-flex; align-items: center; gap: 6px; }
    button        { background: none; border: 2px solid #ccc; border-radius: 50%;
                    width: 40px; height: 40px; cursor: pointer; font-size: 18px;
                    transition: border-color .2s; }
    button.active { border-color: #e53935; animation: pulse 1s infinite; }
    .error        { font-size: 12px; color: #e53935; }
    @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:.4 } }
  `]
})
export class VoiceSearchComponent implements OnDestroy {
  @Input()  chatMode        = false;
  @Output() resultsFound    = new EventEmitter<VoiceSearchResponse>();
  @Output() transcriptReady = new EventEmitter<string>();

  listening = false;
  error     = '';

  private recognition: any = null;
  private subs = new Subscription();

  constructor(private voiceSearch: VoiceSearchService) {}

  toggle(): void {
    if (this.chatMode) {
      this.listening ? this.stopChat() : this.startChat();
    } else {
      if (!this.listening) {
        this.subs.add(
          this.voiceSearch.transcript$.pipe(
            switchMap(text => { this.error = ''; return this.voiceSearch.search(text); })
          ).subscribe({
            next:  res => this.resultsFound.emit(res),
            error: ()  => this.error = 'Search failed. Please try again.'
          })
        );
        this.subs.add(this.voiceSearch.listening$.subscribe(v => this.listening = v));
        this.voiceSearch.start();
      } else {
        this.voiceSearch.stop();
      }
    }
  }

  private startChat(): void {
    const SR = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
    if (!SR) { this.error = 'הדפדפן לא תומך בהקלטה'; return; }

    this.recognition = new SR();
    this.recognition.lang           = 'he-IL';
    this.recognition.interimResults = false;
    this.recognition.continuous     = true;   // keep recording until user clicks stop

    let collected = '';
    this.recognition.onresult = (e: any) => {
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) collected += e.results[i][0].transcript + ' ';
      }
    };
    this.recognition.onerror = (e: any) => {
      this.error = e.error === 'not-allowed' ? 'אנא אפשר גישה למיקרופון' : 'שגיאה בהקלטה';
      this.listening = false;
    };
    this.recognition.onend = () => {
      // only fires after stopChat() calls recognition.stop()
      if (collected.trim()) this.transcriptReady.emit(collected.trim());
      this.listening = false;
    };

    this.recognition.start();
    this.listening = true;
    this.error = '';
  }

  private stopChat(): void {
    this.recognition?.stop();
  }

  ngOnDestroy(): void {
    this.recognition?.stop();
    this.subs.unsubscribe();
  }
}
