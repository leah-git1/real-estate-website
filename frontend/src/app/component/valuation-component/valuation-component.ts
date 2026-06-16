import { Component, ViewChild, ElementRef, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ValuationService, ValuationResponse } from '../../services/valuation.service';
import { UserService } from '../../services/user-service';

@Component({
  selector: 'app-valuation',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule,
    ButtonModule, InputTextModule, InputNumberModule,
    ProgressBarModule, ToastModule
  ],
  providers: [MessageService],
  templateUrl: './valuation-component.html',
  styleUrl: './valuation-component.scss'
})
export class ValuationComponent implements OnDestroy {
  @ViewChild('videoEl') videoEl!: ElementRef<HTMLVideoElement>;

  // ── Camera state ──────────────────────────────────────────────────────────
  cameraActive  = false;
  recording     = false;
  cameraError   = '';
  recordingSecs = 0;
  readonly MAX_FRAMES = 4;

  private stream:          MediaStream | null = null;
  private timerInterval:   ReturnType<typeof setInterval> | null = null;
  private captureInterval: ReturnType<typeof setInterval> | null = null;

  // ── Wizard state ──────────────────────────────────────────────────────────
  step          = 1;
  loading       = false;
  uploadPct     = 0;
  previewUrls:  string[] = [];
  selectedFiles: File[]  = [];
  result: ValuationResponse | null = null;

  form: FormGroup;

  constructor(
    private fb:          FormBuilder,
    private valuation:   ValuationService,
    private userService: UserService,
    private router:      Router,
    private toast:       MessageService,
    private cdr:         ChangeDetectorRef
  ) {
    this.form = this.fb.group({
      address: ['', [Validators.required, Validators.minLength(5)]],
      city:    ['', Validators.required],
      rooms:   [null, [Validators.required, Validators.min(1), Validators.max(20)]],
      sqm:     [null, [Validators.required, Validators.min(20), Validators.max(1000)]]
    });
  }

  // ── Camera ────────────────────────────────────────────────────────────────

  async startCamera(): Promise<void> {
    this.cameraError  = '';
    this.cameraActive = true;
    await new Promise(r => setTimeout(r, 80));
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
        audio: false
      });
      this.videoEl.nativeElement.srcObject = this.stream;
      await this.videoEl.nativeElement.play();
    } catch {
      this.cameraActive = false;
      this.cameraError  = 'לא ניתן לגשת למצלמה. אנא אפשר גישה בהגדרות הדפדפן.';
    }
  }

  stopCamera(): void {
    this._stopAllIntervals();
    this.stream?.getTracks().forEach(t => t.stop());
    this.stream       = null;
    this.cameraActive = false;
    this.recording    = false;
  }

  startRecording(): void {
    if (!this.stream || this.recording) return;

    // Clear old frames
    this.previewUrls.forEach(u => URL.revokeObjectURL(u));
    this.selectedFiles = [];
    this.previewUrls   = [];

    this.recording     = true;
    this.recordingSecs = 0;

    // Seconds counter
    this.timerInterval = setInterval(() => {
      this.recordingSecs++;
      this.cdr.detectChanges();
    }, 1000);

    // Capture a frame immediately, then every 2 s until MAX_FRAMES
    this._captureFrameNow();
    this.captureInterval = setInterval(() => {
      if (this.selectedFiles.length < this.MAX_FRAMES) {
        this._captureFrameNow();
      } else {
        this.stopRecording();
      }
    }, 2000);
  }

  stopRecording(): void {
    this._stopAllIntervals();
    this.recording = false;
    this.cdr.detectChanges();
    if (this.selectedFiles.length > 0) {
      this.toast.add({
        severity: 'success',
        summary: 'צילום הושלם!',
        detail: `${this.selectedFiles.length} תמונות נלכדו — ניתן לנתח`
      });
    }
  }

  /** Snapshot one frame directly from the live <video> element */
  private _captureFrameNow(): void {
    const video = this.videoEl?.nativeElement;
    if (!video || video.readyState < 2) return;

    const canvas  = document.createElement('canvas');
    canvas.width  = video.videoWidth  || 1280;
    canvas.height = video.videoHeight || 720;
    canvas.getContext('2d')!.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
      if (!blob) return;
      const file    = new File([blob], `rec-${Date.now()}.jpg`, { type: 'image/jpeg' });
      const preview = URL.createObjectURL(blob);
      this.selectedFiles = [...this.selectedFiles, file];
      this.previewUrls   = [...this.previewUrls, preview];
      this.cdr.detectChanges();
    }, 'image/jpeg', 0.85);
  }

  /** Single manual snapshot while camera is open (not recording) */
  capturePhoto(): void {
    if (this.selectedFiles.length >= this.MAX_FRAMES) {
      this.toast.add({ severity: 'warn', summary: 'הגעת למקסימום', detail: `ניתן להעלות עד ${this.MAX_FRAMES} תמונות` });
      return;
    }
    this._captureFrameNow();
    this.toast.add({ severity: 'success', summary: 'צולם!', detail: 'התמונה נוספה לניתוח' });
  }

  private _stopAllIntervals(): void {
    if (this.timerInterval)   { clearInterval(this.timerInterval);   this.timerInterval   = null; }
    if (this.captureInterval) { clearInterval(this.captureInterval); this.captureInterval = null; }
  }

  ngOnDestroy(): void { this.stopCamera(); }

  // ── Step 1 ────────────────────────────────────────────────────────────────

  nextToUpload(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.step = 2;
  }

  // ── Step 2 — file picker ──────────────────────────────────────────────────

  onFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this._addFiles(Array.from(input.files ?? []));
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this._addFiles(Array.from(event.dataTransfer?.files ?? []));
  }

  onDragOver(event: DragEvent): void { event.preventDefault(); }

  removeFile(index: number): void {
    URL.revokeObjectURL(this.previewUrls[index]);
    this.selectedFiles = this.selectedFiles.filter((_, i) => i !== index);
    this.previewUrls   = this.previewUrls.filter((_, i) => i !== index);
  }

  private _addFiles(files: File[]): void {
    const images = files.filter(f => f.type.startsWith('image/')).slice(0, this.MAX_FRAMES - this.selectedFiles.length);
    images.forEach(f => {
      this.selectedFiles = [...this.selectedFiles, f];
      const reader = new FileReader();
      reader.onload = e => {
        this.previewUrls = [...this.previewUrls, e.target!.result as string];
        this.cdr.detectChanges();
      };
      reader.readAsDataURL(f);
    });
  }

  // ── Step 2 — analyze ─────────────────────────────────────────────────────

  async analyze(): Promise<void> {
    this.loading   = true;
    this.uploadPct = 0;

    const progressInterval = setInterval(() => {
      this.uploadPct = Math.min(this.uploadPct + 10, 90);
    }, 300);

    const { address, city, rooms, sqm } = this.form.value;

    this.valuation.analyzeMultipart(this.selectedFiles, address, city, rooms, sqm)
      .subscribe({
        next: res => {
          clearInterval(progressInterval);
          this.uploadPct = 100;
          this.result    = res;
          this.step      = 3;
          this.loading   = false;
        },
        error: (err) => {
          clearInterval(progressInterval);
          this.loading = false;
          const detail = err.status === 413
            ? 'הקבצים גדולים מדי. נסה תמונות קטנות יותר.'
            : 'הניתוח נכשל. נסה שוב.';
          this.toast.add({ severity: 'error', summary: 'שגיאה', detail });
        }
      });
  }

  // ── Step 3 helpers ────────────────────────────────────────────────────────

  get isLoggedIn(): boolean { return this.userService.isLoggedIn(); }

  get confidencePct(): number {
    return Math.round((this.result?.confidence ?? 0) * 100);
  }

  formatPrice(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M ₪`;
    return `${(n / 1_000).toFixed(0)}K ₪`;
  }

  goToAuth(): void { this.router.navigate(['/auth']); }

  restart(): void {
    this.previewUrls.forEach(u => URL.revokeObjectURL(u));
    this.step = 1; this.result = null;
    this.previewUrls = []; this.selectedFiles = [];
    this.recordingSecs = 0;
    this.form.reset();
  }
}
