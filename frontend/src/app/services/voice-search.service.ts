import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';

export interface PropertySearchParams {
  city:       string  | null;
  rooms:      number  | null;
  maxPrice:   number  | null;
  hasBalcony: boolean | null;
  hasParking: boolean | null;
}

export interface VoiceSearchResponse {
  filters: PropertySearchParams;
  results: any[];
}

@Injectable({ providedIn: 'root' })
export class VoiceSearchService {
  private readonly apiUrl = 'https://localhost:44305/api/search/voice';
  private readonly SR: any;
  private recognition: any = null;

  readonly transcript$ = new Subject<string>();
  readonly listening$  = new Subject<boolean>();

  constructor(private http: HttpClient) {
    this.SR = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition ?? null;
  }

  get isSupported(): boolean { return !!this.SR; }

  start(): void {
    if (!this.SR) return;

    // Always create a fresh instance — reusing a stopped instance throws InvalidStateError
    this.recognition = new this.SR();
    this.recognition.lang           = 'he-IL';
    this.recognition.interimResults = false;
    this.recognition.continuous     = false;

    this.recognition.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      this.transcript$.next(transcript);
    };
    this.recognition.onend  = () => this.listening$.next(false);
    this.recognition.onerror = (e: any) => {
      console.error('SpeechRecognition error:', e.error);
      this.listening$.next(false);
    };

    this.listening$.next(true);
    this.recognition.start();
  }

  stop(): void {
    this.recognition?.stop();
    this.recognition = null;
  }

  search(transcript: string): Observable<VoiceSearchResponse> {
    return this.http.post<VoiceSearchResponse>(this.apiUrl, { transcript });
  }
}
