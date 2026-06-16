import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ChatStateService } from '../../services/chat-state.service';

@Component({
  selector: 'app-ai-guide',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ai-guide-component.html',
  styleUrl: './ai-guide-component.scss'
})
export class AiGuideComponent {
  constructor(private router: Router, private chatState: ChatStateService) {}

  goToProducts() { this.router.navigate(['/products']); }
  goToValuation() { this.router.navigate(['/valuation']); }

  openChat(message = '') {
    this.router.navigate(['/']).then(() => this.chatState.open(message));
  }

  chatExamples = [
    { icon: '🏠', text: 'מצא לי דירה בתל אביב עד 3 מיליון' },
    { icon: '🛏️', text: 'אני מחפש 4 חדרים עם חניה בירושלים' },
    { icon: '🌴', text: 'יש לכם נכסי נופש בים?' },
    { icon: '💰', text: 'מה העמלה שלכם על מכירה?' },
    { icon: '📞', text: 'איך יוצרים קשר עם בעל הנכס?' },
    { icon: '❤️', text: 'איך שומרים נכס למועדפים?' },
  ];

  voiceSteps = [
    { num: '1', icon: '🎤', title: 'לחץ על כפתור המיקרופון', desc: 'הכפתור יהפוך לאדום — זה אומר שאתה מוקלט' },
    { num: '2', icon: '🗣️', title: 'דבר בעברית או אנגלית', desc: 'אמור מה אתה מחפש, למשל: "דירה בחיפה 3 חדרים עד מיליון וחצי"' },
    { num: '3', icon: '🔴', title: 'לחץ שוב לעצור', desc: 'לחץ על הכפתור האדום כדי לסיים את ההקלטה' },
    { num: '4', icon: '✨', title: 'הסוכן החכם עונה לך', desc: 'ההודעה שלך נשלחת אוטומטית והסוכן החכם מחזיר תשובה' },
  ];

  tips = [
    { icon: '💡', text: 'ציין עיר, מספר חדרים ותקציב בשאלה אחת' },
    { icon: '🔗', text: 'הסוכן שולח לינקים ישירים לנכסים — לחץ עליהם לפרטים' },
    { icon: '🌐', text: 'אפשר לדבר עברית או אנגלית — הסוכן מבין את שתיהן' },
    { icon: '📱', text: 'עובד גם בנייד — Chrome ו-Edge תומכים בהקלטה' },
  ];
}
