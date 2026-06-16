import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-valuation-btn',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- Ad Popup -->
    <div class="ad-popup" *ngIf="showAd" (click)="dismissAd()">
      <div class="ad-card" (click)="$event.stopPropagation()">
        <button class="ad-close" (click)="dismissAd()">✕</button>
        <div class="ad-icon">{{ currentAd.icon }}</div>
        <h3 class="ad-title">{{ currentAd.title }}</h3>
        <p class="ad-body">{{ currentAd.body }}</p>
        <button class="ad-cta" (click)="onAdCta()">
          <span>{{ currentAd.cta }}</span>
          <i class="pi pi-arrow-left"></i>
        </button>
      </div>
    </div>

    <!-- Slim side tab -->
    <div class="side-tab" (click)="go()" title="הערכת שווי AI">
      <span class="side-icon">✨</span>
      <span class="side-label">שווי</span>
    </div>
  `,
  styles: [`
    /* ── Slim side tab ─────────────────────────────────── */
    .side-tab {
      position: fixed;
      top: 42%;
      right: 0;
      transform: translateY(-50%);
      z-index: 1099;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      padding: 14px 0;
      width: 28px;
      background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
      border-radius: 8px 0 0 8px;
      cursor: pointer;
      box-shadow: -2px 0 12px rgba(102,126,234,0.45);
      transition: width 0.2s ease, box-shadow 0.2s ease;
    }
    .side-tab:hover {
      width: 34px;
      box-shadow: -4px 0 20px rgba(102,126,234,0.6);
    }
    .side-icon {
      font-size: 13px;
      line-height: 1;
      filter: drop-shadow(0 0 3px rgba(255,215,0,.9));
    }
    .side-label {
      font-size: 9px;
      font-weight: 800;
      color: rgba(255,255,255,0.92);
      writing-mode: vertical-rl;
      text-orientation: mixed;
      letter-spacing: 1px;
      white-space: nowrap;
    }

    /* ── Ad Popup ──────────────────────────────────────── */
    .ad-popup {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.45);
      z-index: 2000;
      display: flex;
      align-items: center;
      justify-content: center;
      animation: fadeIn 0.3s ease;
    }
    .ad-card {
      background: white;
      border-radius: 24px;
      padding: 36px 32px 28px;
      max-width: 400px;
      width: 90%;
      text-align: center;
      direction: rtl;
      position: relative;
      box-shadow: 0 20px 60px rgba(0,0,0,0.25);
      animation: slideUp 0.35s ease;
    }
    .ad-close {
      position: absolute;
      top: 14px;
      left: 14px;
      background: #f1f5f9;
      border: none;
      border-radius: 50%;
      width: 30px;
      height: 30px;
      cursor: pointer;
      font-size: 13px;
      color: #64748b;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    }
    .ad-close:hover { background: #e2e8f0; color: #1e293b; }
    .ad-icon  { font-size: 52px; margin-bottom: 12px; }
    .ad-title { font-size: 1.3rem; font-weight: 800; color: #1a2e44; margin: 0 0 10px; }
    .ad-body  { font-size: 0.95rem; color: #475569; margin: 0 0 22px; line-height: 1.6; }
    .ad-cta {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 13px 28px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border: none;
      border-radius: 50px;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .ad-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(102,126,234,0.45); }

    @keyframes fadeIn  { from { opacity:0 } to { opacity:1 } }
    @keyframes slideUp { from { transform:translateY(30px); opacity:0 } to { transform:translateY(0); opacity:1 } }

    @media (max-width: 480px) {
      .side-tab { width: 24px; padding: 12px 0; }
      .side-label { font-size: 8px; }
    }
  `]
})
export class ValuationBtnComponent implements OnInit, OnDestroy {
  showAd = false;
  private timer: ReturnType<typeof setTimeout> | null = null;

  ads = [
    {
      icon: '🏡',
      title: 'כמה שווה הדירה שלך?',
      body: 'הכלי החדש שלנו מנתח תמונות + נתוני שוק ומחזיר הערכת שווי מדויקת תוך שניות, מבוסס GPT-4o Vision.',
      cta: 'לנסות חינם',
      route: '/valuation'
    },
    {
      icon: '🤖',
      title: 'הסוכן החכם שלך לנדל"ן',
      body: 'שאל בעברית או אנגלית, קבל המלצות נכסים, מחירים ולינקים ישירים — הכל בצ\'אט אחד.',
      cta: 'לסוכן החכם',
      route: '/ai-guide'
    },
    {
      icon: '🎤',
      title: 'חיפוש קולי בעברית',
      body: 'פשוט תגיד "דירה ב-4 חדרים בתל אביב עד 2 מיליון" — הסוכן החכם יסנן את התוצאות עבורך.',
      cta: 'לנסות עכשיו',
      route: '/ai-guide'
    }
  ];

  currentAd = this.ads[0];
  private adIndex = 0;

  constructor(private router: Router) {}

  ngOnInit() { this.scheduleNextAd(25000); }

  private scheduleNextAd(delay: number) {
    this.timer = setTimeout(() => {
      this.currentAd = this.ads[this.adIndex % this.ads.length];
      this.adIndex++;
      this.showAd = true;
      this.scheduleNextAd(90000);
    }, delay);
  }

  dismissAd() { this.showAd = false; }

  onAdCta() {
    this.showAd = false;
    this.router.navigate([this.currentAd.route]);
  }

  go() { this.router.navigate(['/valuation']); }

  ngOnDestroy() { if (this.timer) clearTimeout(this.timer); }
}
