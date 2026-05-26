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
  private recognition: any;

  readonly transcript$ = new Subject<string>();
  readonly listening$  = new Subject<boolean>();

  constructor(private http: HttpClient) {
    const SR = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
    if (!SR) return;

    this.recognition = new SR();
    this.recognition.lang            = 'he-IL';
    this.recognition.interimResults  = false;
    this.recognition.continuous      = false;
    this.recognition.onresult        = (e: any) => this.transcript$.next(e.results[0][0].transcript);
    this.recognition.onend           = ()       => this.listening$.next(false);
    this.recognition.onerror         = ()       => this.listening$.next(false);
  }

  start(): void {
    if (!this.recognition) return;
    this.listening$.next(true);
    this.recognition.start();
  }

  stop(): void {
    this.recognition?.stop();
  }

  search(transcript: string): Observable<VoiceSearchResponse> {
    return this.http.post<VoiceSearchResponse>(this.apiUrl, { transcript });
  }
}
